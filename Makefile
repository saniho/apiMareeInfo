.PHONY: lint typecheck test check install

lint:
	ruff check custom_components/ tests/

typecheck:
	mypy custom_components/apiMareeInfo/

test:
	pytest tests/ -v --tb=short --cov=custom_components/apiMareeInfo --cov-report=term-missing

check: lint typecheck test

install:
	pip install -r requirements-test.txt
