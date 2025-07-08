# Makefile for cypher-guard Python bindings

.PHONY: format test clean inspector build_local_docker_image install-dev test-unit test-integration test-http test-all all

format:
	uv run ruff check --select I . --fix
	uv run ruff check --fix .
	uv run ruff format .

test:
	uv run pytest tests/ -s 

inspector:
	npx @modelcontextprotocol/inspector uv --directory src/mcp_neo4j_data_modeling run mcp-neo4j-data-modeling

build_local_docker_image:
	docker build -t mcp-neo4j-data-modeling .

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
	python3 -m uv pip install -e .

test-unit:
	python3 -m pytest tests/unit/ -v

test-integration:
	python3 -m pytest tests/integration/ -v

test-http:
	python3 -m pytest tests/integration/test_http_transport.py -v

test-all:
	python3 -m pytest tests/ -v

all: install-dev test-all