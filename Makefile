VERSION := $(shell cat src/refac/__init__.py | grep __version__ | cut -d'=' -f2 | xargs)
COMMIT := $(shell git rev-parse HEAD)

install:
	pip install -r requirements.txt

test: install
	python -m unittest tests/**/*.py

lint: install
	ruff check .

publish:
	git tag -a v$(VERSION) $(COMMIT) -m 'v$(VERSION)'
	git push origin v$(VERSION)
	@echo Pushed tag with for v$(VERSION). https://github.com/benchling/refac/actions