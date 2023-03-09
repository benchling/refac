install:
	pip install -r requirements.txt

test: install
	python -m unittest tests/**/*.py

lint: install
	ruff check .
