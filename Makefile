# ---------------------------------------------------------------------------
# Uniform EPS demo CLI (per eps-demo-devx / eps-demo-repo-hygiene). Same verbs
# in every repo: dev / test / lint / deploy. Targets auto-detect whether
# backend/frontend have been scaffolded yet so this works before AND after
# `/new-demo` runs — see AGENTS.md.
# ---------------------------------------------------------------------------
.DEFAULT_GOAL := help
.PHONY: help install dev dev-backend dev-frontend test test-backend test-frontend \
        lint lint-backend lint-frontend guidance-lint format deploy bicep-lint

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

install: ## Install backend + frontend dependencies (once scaffolded)
	@if [ -f frontend/package.json ]; then cd frontend && npm install; fi
	@if [ -f backend/package.json ]; then cd backend && npm install; fi
	@if ls backend/*.sln backend/*.slnx >/dev/null 2>&1; then cd backend && dotnet restore *.sln* ; fi
	@if [ -f backend/pyproject.toml ]; then cd backend && pip install -e .; elif [ -f backend/requirements.txt ]; then cd backend && pip install -r requirements.txt; fi
	@echo "install done (no-ops silently skip stacks that don't exist yet)"

dev: ## Run the full stack locally (no-ops for parts not scaffolded yet)
	@$(MAKE) -j2 dev-backend dev-frontend

dev-backend: ## (internal) run the backend dev server if scaffolded
	@if [ -f backend/package.json ]; then cd backend && npm run dev; elif ls backend/*.sln backend/*.slnx >/dev/null 2>&1; then cd backend && dotnet run; elif [ -f backend/pyproject.toml ] || [ -f backend/requirements.txt ]; then cd backend && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000; else echo "backend/ not scaffolded yet — run '/new-demo' in Copilot Chat or see AGENTS.md"; fi

dev-frontend: ## (internal) run the frontend dev server if scaffolded
	@if [ -f frontend/package.json ]; then cd frontend && npm run dev; else echo "frontend/ not scaffolded yet — run '/new-demo' in Copilot Chat or see AGENTS.md"; fi

test: ## Run all tests with coverage (FAKE_AI=1 — mandatory per eps-demo-testing-solid)
	@FAKE_AI=1 $(MAKE) test-backend test-frontend

test-backend: ## (internal) run backend tests if scaffolded
	@if ls backend/*.sln backend/*.slnx >/dev/null 2>&1; then cd backend && dotnet test *.sln*; elif [ -f backend/package.json ]; then cd backend && npm test; elif [ -f backend/pyproject.toml ] || [ -f backend/requirements.txt ]; then cd backend && pytest; else echo "no backend tests yet"; fi

test-frontend: ## (internal) run frontend tests if scaffolded
	@if [ -f frontend/package.json ]; then cd frontend && npm run test:coverage; else echo "no frontend tests yet"; fi

lint: guidance-lint lint-backend lint-frontend ## Lint guidance + backend + frontend

guidance-lint: ## Validate skills, custom agents, and prompt routing
	python3 tools/validate-guidance.py

lint-backend: ## (internal) lint backend if scaffolded
	@if ls backend/*.sln backend/*.slnx >/dev/null 2>&1; then cd backend && dotnet format *.sln* --verify-no-changes; elif [ -f backend/package.json ]; then cd backend && npm run lint; elif [ -f backend/pyproject.toml ] || [ -f backend/requirements.txt ]; then cd backend && ruff check .; else echo "no backend to lint yet"; fi

lint-frontend: ## (internal) lint frontend if scaffolded
	@if [ -f frontend/package.json ]; then cd frontend && npm run lint; else echo "no frontend to lint yet"; fi

format: ## Auto-format backend + frontend
	@if ls backend/*.sln backend/*.slnx >/dev/null 2>&1; then cd backend && dotnet format *.sln*; fi
	@if [ -f backend/pyproject.toml ] || [ -f backend/requirements.txt ]; then cd backend && ruff format .; fi
	@if [ -f frontend/package.json ]; then cd frontend && npm run format; fi

ingest: ## Generate and upload the current ADLS Gen2 Strategy files
	cd backend && python -m app.ingest_adls

ingest-local: ## Generate ADLS files locally without uploading
	cd backend && python -m app.ingest_adls --local-only

bicep-lint: ## Validate the Bicep templates compile
	az bicep build --file infra/main.bicep --stdout > /dev/null && echo "infra/main.bicep OK"

deploy: bicep-lint ## Deploy via Azure Developer CLI (azd up)
	@command -v azd >/dev/null 2>&1 || { echo "azd not found — see https://aka.ms/azd"; exit 1; }
	azd up
