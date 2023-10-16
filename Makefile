DOCS=docs
PYTHON ?= python3
PYTHON_TEST=python3 -m pytest
PYTEST_OPT=--log-level=INFO
MYPY ?= mypy

default: test

.PHONY: test
test:
	$(PYTHON_TEST) $(PYTEST_OPT) tests

opendoc:
	xdg-open docs-build/html/index.html

documentation:
	cd $(DOCS) && env SPHINXOPTS=-a $(MAKE) html

mypy:
	#$(MYPY) fockes_reasoner
	unbuffer $(MYPY) fockes_reasoner 2>&1 | head -n5

clean:
	cd $(DOCS) && env SPHINXOPTS=-a $(MAKE) clean
