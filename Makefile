.PHONY: demo test build api validate-restructuring-v2

PYTHON ?= .venv/bin/python3

demo:
	$(PYTHON) scripts/self_check.py

test:
	$(PYTHON) -m pytest -q

build:
	pnpm run build

api:
	$(PYTHON) scripts/serve_api.py

validate-restructuring-v2:
	$(PYTHON) scripts/validate_restructuring_v2.py
