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