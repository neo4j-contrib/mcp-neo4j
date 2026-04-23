docker-local-build-run:
	docker build -t mcp-neo4j-memory .
	docker run -p 8000:8000 mcp-neo4j-memory:latest

install-dev:
	uv run python3 -m uv pip install -e .

test-unit:
	uv run python3 -m pytest tests/unit/ -v

test-integration:
	uv run python3 -m pytest tests/integration/ -v

test-http:
	uv run python3 -m pytest tests/integration/test_http_transport.py -v

test-all:
	uv run python3 -m pytest tests/ -v

all: install-dev test-all 