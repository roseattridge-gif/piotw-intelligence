.PHONY: demo test build api

PYTHON ?= .venv/bin/python3

demo:
	$(PYTHON) scripts/self_check.py

test:
	$(PYTHON) -m pytest -q

build:
	pnpm run build

api:
	$(PYTHON) scripts/serve_api.py
