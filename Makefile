.PHONY: demo founder-demo unknown-company-demo evidence-demo validate-evidence-engine-real validate-evidence-engine-independent validate-evidence-engine-v035-development compare-evidence-engine-ai-finops validate-event-context-v031 validate-event-context-v032 validate-event-context-v033 validate-event-context-v034 semantic-provider-preflight semantic-batch-prepare semantic-batch-preflight semantic-batch-submit semantic-batch-status semantic-batch-collect semantic-contract-smoke test build api validate-restructuring-v2

PYTHON ?= .venv/bin/python3
NODE ?= $(shell command -v node 2>/dev/null || printf '%s' '/Users/roseattridge/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node')

demo:
	$(PYTHON) scripts/self_check.py

founder-demo:
	cd piotw-web && "$(NODE)" node_modules/next/dist/bin/next dev --webpack --hostname 127.0.0.1 --port 3000

unknown-company-demo:
	$(PYTHON) scripts/run_unknown_company_v01.py --company cloudflare --as-of 2026-08-19T00:00:00Z

evidence-demo:
	$(PYTHON) scripts/run_evidence_demo.py

validate-event-context-v031:
	$(PYTHON) scripts/validate_event_context_v031.py

validate-event-context-v032:
	$(PYTHON) scripts/validate_event_context_v032.py

validate-event-context-v033:
	$(PYTHON) scripts/validate_event_context_v033.py

validate-event-context-v034:
	$(PYTHON) scripts/validate_event_context_v034.py

semantic-provider-preflight:
	@set -a; . "$(HOME)/.codex/.env"; set +a; $(PYTHON) scripts/semantic_provider_preflight.py

semantic-batch-prepare:
	$(PYTHON) scripts/semantic_batch_v034.py prepare

semantic-batch-preflight:
	@set -a; . "$(HOME)/.codex/.env"; set +a; $(PYTHON) scripts/semantic_batch_v034.py preflight

semantic-batch-submit:
	@set -a; . "$(HOME)/.codex/.env"; set +a; $(PYTHON) scripts/semantic_batch_v034.py submit

semantic-batch-status:
	@set -a; . "$(HOME)/.codex/.env"; set +a; $(PYTHON) scripts/semantic_batch_v034.py status

semantic-batch-collect:
	@set -a; . "$(HOME)/.codex/.env"; set +a; $(PYTHON) scripts/semantic_batch_v034.py collect

semantic-contract-smoke:
	@set -a; . "$(HOME)/.codex/.env"; set +a; $(PYTHON) scripts/semantic_batch_v034.py contract-smoke

validate-evidence-engine-real:
	$(PYTHON) scripts/validate_evidence_engine_real.py

validate-evidence-engine-independent:
	$(PYTHON) scripts/validate_evidence_engine_independent.py

validate-evidence-engine-v035-development:
	$(PYTHON) scripts/validate_evidence_engine_v035_development.py

compare-evidence-engine-ai-finops:
	$(PYTHON) scripts/compare_evidence_v03_ai_finops.py

test:
	$(PYTHON) -m pytest -q

build:
	pnpm run build

api:
	$(PYTHON) scripts/serve_api.py

validate-restructuring-v2:
	$(PYTHON) scripts/build_restructuring_v2_coverage_queue.py
	$(PYTHON) scripts/build_restructuring_v2_evidence.py
	$(PYTHON) scripts/validate_restructuring_v2.py
