.PHONY: build test lint shell prd design pipeline clean help

IMAGE_NAME := ai-agency

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

build: ## Build the Docker image
	docker compose build

test: ## Run tests in container
	docker compose run --rm test

lint: ## Run ruff linter in container
	docker compose run --rm lint

shell: ## Open a shell in the container
	docker compose run --rm --entrypoint /bin/bash cli

prd: ## Generate a PRD (use TEXT="..." or FILE=path)
ifdef FILE
	docker compose run --rm cli prd generate --input /app/output/$(notdir $(FILE))
else ifdef TEXT
	docker compose run --rm cli prd generate --text "$(TEXT)"
else
	@echo "Usage: make prd TEXT=\"Build a task management app\" or make prd FILE=requirements.txt"
endif

design: ## Generate Stitch prompts from a PRD
	docker compose run --rm cli design generate --prd /app/output/prd.json

pipeline: ## Full pipeline: requirements -> PRD -> Stitch prompts
ifdef FILE
	docker compose run --rm cli pipeline --input /app/output/$(notdir $(FILE))
else ifdef TEXT
	docker compose run --rm cli pipeline --text "$(TEXT)"
else
	@echo "Usage: make pipeline TEXT=\"Build a task management app\" or make pipeline FILE=requirements.txt"
endif

clean: ## Remove built images and output files
	docker compose down --rmi local --remove-orphans
	rm -rf output/*
