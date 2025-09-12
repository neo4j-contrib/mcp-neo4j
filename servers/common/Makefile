format-and-lint:
	uv run ruff check --select I . --fix
	uv run ruff check --fix .
	uv run ruff format .

test-all:
	uv run pytest tests/ -v



all: test-all format-and-lint