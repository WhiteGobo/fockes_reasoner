DOCS=docs

default: test

.PHONY: test
test:
	pytest --log-cli-level=INFO tests -k RIFimport
	#pytest --log-cli-level=DEBUG tests -k simpleReasoning
	#pytest --log-cli-level=DEBUG tests -k positiveEntailment -x
	#pytest tests

opendoc:
	xdg-open docs-build/html/index.html

documentation:
	cd $(DOCS) && env SPHINXOPTS=-a $(MAKE) html

mypy:
	mypy fockes_reasoner

clean:
	cd $(DOCS) && env SPHINXOPTS=-a $(MAKE) clean
