.PHONY: image
image: ## Create Docker image containing the script
	@docker buildx build --platform linux/amd64,linux/arm/v6,linux/arm/v7,linux/arm64/v8 -t jwbennet/daily-summary-generator:latest . --build-arg TIMESTAMP=$(date --iso-8601=seconds) --push

.PHONY: run
run: export GOOGLE_APPLICATION_CREDENTIALS=$(CURDIR)/gcp-credentials.json
run: ## Run script locally
	@pipenv run update

.PHONY: test
test: ## Test built Docker image
	@docker container run -ti --rm -v $(CURDIR)/gcp-credentials.json:/usr/src/app/gcp-credentials.json -v $(CURDIR)/.env:/usr/src/app/.env -e GOOGLE_APPLICATION_CREDENTIALS=/usr/src/app/gcp-credentials.json jwbennet/daily-summary-generator:latest /home/app/.local/bin/pipenv run update

.PHONY: deploy
deploy: ## Deploy Kubernetes assets
	@kubectl apply -f k8s/cronjob.yaml

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
