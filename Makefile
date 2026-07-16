# Agentic-vs-human benchmark harness (paper §3.6).
# `make all` runs the five analysis stages in order and aggregates the tables.

PYTHON ?= python
SUBJECTS ?=            # e.g. make all SUBJECTS="flask swe_flask"
SUBJ_ARG := $(if $(SUBJECTS),--subjects $(SUBJECTS),)

.PHONY: all repo_stats correctness complexity smells security duplication \
        aggregate tables clean docker docker-run help

all: ## Run every stage + aggregate (the paper's `make all`)
	$(PYTHON) run_all.py $(SUBJ_ARG)

repo_stats: ## Structural characteristics table
	$(PYTHON) run_all.py --stages repo_stats $(SUBJ_ARG)

correctness: ## RQ1 oracle test pass rates
	$(PYTHON) run_all.py --stages correctness $(SUBJ_ARG)

complexity: ## RQ2 + MI (Radon + complexipy)
	$(PYTHON) run_all.py --stages complexity $(SUBJ_ARG)

smells: ## RQ3 pylint code smells
	$(PYTHON) run_all.py --stages smells $(SUBJ_ARG)

security: ## RQ4 Bandit findings
	$(PYTHON) run_all.py --stages security $(SUBJ_ARG)

duplication: ## RQ5 CPD duplication
	$(PYTHON) run_all.py --stages duplication $(SUBJ_ARG)

aggregate tables: ## Rebuild CSV tables from existing result JSON
	$(PYTHON) run_all.py --stages aggregate

clean: ## Remove all generated results
	rm -rf results/*/ results/*.csv

docker: ## Build the hermetic analysis image
	docker build -t agentic-benchmark .

docker-run: ## Run the full pipeline inside the container
	docker run --rm -v "$(PWD)/subjects:/work/subjects:ro" \
		-v "$(PWD)/results:/work/results" agentic-benchmark

help: ## Show this help
	@grep -E '^[a-zA-Z_ -]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'
