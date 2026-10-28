.PHONY: test demo schema verify

test:
	python -m pytest -q

demo:
	python -m workflow_platform.cli

schema:
	python scripts/export_openapi.py

verify: test
	python -m workflow_platform.cli
	python scripts/export_openapi.py --check
	python scripts/verify_demo.py
