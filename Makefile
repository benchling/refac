install:
	pip install -r requirements.txt

test:
	python -m unittest tests/**/*.py

install-linters:
	pip install ruff

lint:
	ruff check .
