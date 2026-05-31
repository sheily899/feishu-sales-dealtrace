.PHONY: install dev validate test lint demo clean

install:        ## install the package (no LLM deps)
	pip install -e .

dev:            ## install with dev + llm extras
	pip install -e ".[dev]"

validate:       ## check the YAML knowledge base for integrity problems
	python -m gtmsi validate

test:           ## run the test suite
	pytest

lint:           ## lint with ruff
	ruff check .

demo:           ## classify the bundled example discovery transcript (needs ANTHROPIC_API_KEY)
	python -m gtmsi coach examples/transcripts/discovery_acme.txt

clean:
	rm -rf build dist *.egg-info .pytest_cache .ruff_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
