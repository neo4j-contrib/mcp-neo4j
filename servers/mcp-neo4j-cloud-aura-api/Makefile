.PHONY: docker-local-build-run install-dev test-unit test-integration test-http test-all all

docker-local-build-run:
	docker build -t mcp-neo4j-aura-manager .
	docker run -p 8000:8000 mcp-neo4j-aura-manager:latest

install-dev:
	uv sync

test-unit:
	uv run pytest tests/unit/ -v

test-integration:
	uv run pytest tests/integration/ -v

test-http:
	uv run pytest tests/integration/test_http_transport.py -v

test-all:
	uv run pytest tests/ -v

all: install-dev test-all 