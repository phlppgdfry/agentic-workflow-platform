FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN groupadd --gid 10001 app && useradd --uid 10001 --gid app --no-create-home app
COPY requirements.lock pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir -r requirements.lock && pip install --no-cache-dir --no-deps . && mkdir data && chown app:app data
USER 10001:10001
EXPOSE 8012
CMD ["uvicorn", "workflow_platform.api:create_app", "--factory", "--host", "0.0.0.0", "--port", "8012"]
