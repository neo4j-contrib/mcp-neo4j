.PHONY: format test clean inspector build_local_docker_image install-dev test-unit test-integration test-http test-all all

format:
	uv run ruff check --select I . --fix
	uv run ruff check --fix .
	uv run ruff format .

test:
	uv run pytest tests/ -s 

inspector:
	npx @modelcontextprotocol/inspector uv --directory src/mcp_neo4j_data_modeling run mcp-neo4j-data-modeling

docker-build-deploy-local:
	docker build -t mcp-neo4j-data-modeling:dev-latest .
	docker run -p 8000:8000 mcp-neo4j-data-modeling:dev-latest

clean:
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf .pytest_cache/
	rm -rf .vscode/
	rm -rf .venv/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf .pytest_cache/

install-dev:
	 uv pip install -e .

test-unit:
	uv run pytest tests/unit/ -v

test-integration:
	uv run pytest tests/integration/ -v

test-http:
	uv run pytest tests/integration/test_http_transport.py -v

test-all:
	uv run pytest tests/ -v

all: install-dev test-all