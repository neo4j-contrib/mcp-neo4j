format:
	uv run ruff check --select I . --fix
	uv run ruff check --fix .
	uv run ruff format .
	
install-dev:
	uv sync

test-unit:
	uv run pytest tests/unit/ -v

test-integration:
	uv run pytest tests/integration/ -v

test-http:
	uv run pytest tests/integration/test_http_transport_IT.py -v

test-all:
	uv run pytest tests/ -v

docker-build-deploy-local:
	docker build -t mcp-neo4j-cypher:dev-latest .
	docker run -p 8000:8000 mcp-neo4j-cypher:dev-latest

all: install-dev test-all 