"""Small ASGI boundary: bounded bodies, safe validation errors, correlated metadata logs."""
import json
import asyncio
import threading
import logging
import time
from uuid import uuid4
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class RequestBoundary:
    def __init__(self, app, max_bytes=262144, max_active=32, body_timeout=30):
        if max_active < 1 or body_timeout <= 0:
            raise ValueError("Positive admission and body deadline limits required")
        self.app, self.max_bytes = app, max_bytes
        self.capacity = threading.BoundedSemaphore(max_active)
        self.body_timeout = body_timeout

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        started, request_id, status = time.perf_counter(), str(uuid4()), 500

        async def tracked_send(message):
            nonlocal status
            if message['type'] == 'http.response.start':
                status = message['status']
                message['headers'] = [*(h for h in message.get('headers', []) if h[0].lower() not in (b'cache-control', b'x-request-id')),
                                      (b'x-request-id', request_id.encode()), (b'cache-control', b'no-store')]
            await send(message)

        admitted = self.capacity.acquire(blocking=False)
        try:
            if not admitted:
                return await JSONResponse({'detail': 'Service concurrency limit reached'}, status_code=429,
                                          headers={'Retry-After': '1'})(scope, receive, tracked_send)
            if scope['method'] in {'POST', 'PUT', 'PATCH'}:
                limit = 5 * 1024 * 1024 if scope.get('path') == '/documents/extract' else self.max_bytes
                body = bytearray()
                deadline = time.monotonic() + self.body_timeout
                while True:
                    try:
                        remaining = max(0, deadline - time.monotonic())
                        message = await asyncio.wait_for(receive(), timeout=remaining)
                    except asyncio.TimeoutError:
                        return await JSONResponse({'detail': 'Request body deadline exceeded'}, status_code=408)(scope, receive, tracked_send)
                    if message['type'] == 'http.disconnect':
                        return
                    part = message.get('body', b'')
                    if len(body) + len(part) > limit:
                        return await JSONResponse({'detail': 'Request body exceeds configured limit'}, status_code=413)(scope, receive, tracked_send)
                    body.extend(part)
                    if not message.get('more_body', False):
                        break
                original_receive = receive
                consumed = False

                async def bounded_receive():
                    nonlocal consumed
                    if not consumed:
                        consumed = True
                        return {'type': 'http.request', 'body': bytes(body), 'more_body': False}
                    return await original_receive()

                await self.app(scope, bounded_receive, tracked_send)
            else:
                await self.app(scope, receive, tracked_send)
        finally:
            if admitted:
                self.capacity.release()
            route = scope.get('route')
            logging.getLogger('uvicorn.error').info(json.dumps({
                'event': 'http_request', 'request_id': request_id, 'route': getattr(route, 'path', 'unmatched'),
                'status': status, 'latency_ms': round((time.perf_counter() - started) * 1000, 3)}))


def install_security(app, max_bytes=262144):
    app.add_middleware(RequestBoundary, max_bytes=max_bytes)

    @app.exception_handler(RequestValidationError)
    async def safe_validation(request, exc):
        return JSONResponse({'detail': [{'location': list(error['loc']), 'type': error['type']}
                                         for error in exc.errors()]}, status_code=422)
