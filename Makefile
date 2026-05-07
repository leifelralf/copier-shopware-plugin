.PHONY: help install test test-fast test-functional test-snapshots snapshots try try-defaults try-clean clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install test dependencies
	pip install -r requirements-test.txt

test: ## Run all tests
	pytest

test-fast: ## Run all tests except functional ones (no external tools needed)
	pytest -m "not functional"

test-functional: ## Run only functional tests (requires php, composer, xmllint)
	pytest -m functional

test-snapshots: ## Run only snapshot tests
	pytest -m snapshot

snapshots: ## Update snapshots after intentional template changes
	pytest -m snapshot --snapshot-update

try: ## Generate a plugin into .out/<timestamp>/ for manual inspection
	./scripts/try-locally.sh

try-defaults: ## Like 'try' but non-interactive (uses all defaults)
	./scripts/try-locally.sh --defaults

try-clean: ## Delete the entire .out/ directory
	./scripts/try-locally.sh --clean

clean: ## Remove pytest and coverage caches
	rm -rf .pytest_cache __pycache__ tests/__pycache__
	find . -name '*.pyc' -delete