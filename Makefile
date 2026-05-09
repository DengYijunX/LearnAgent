.PHONY: install run test lint clean

install:
	pip install -e ".[dev]"

run:
	python -m src.main

test:
	pytest -v

test-cov:
	pytest -v --cov=src --cov-report=term-missing

test-integration:
	pytest -v -m "integration"

lint:
	ruff check src/ tests/

clean:
	rm -rf __pycache__ .pytest_cache .coverage
	find src -name '__pycache__' -exec rm -rf {} +
	find tests -name '__pycache__' -exec rm -rf {} +
