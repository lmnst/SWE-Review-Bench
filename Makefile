.PHONY: install smoke run test clean

install:
	pip install -e .[dev]

smoke:
	python -m swe_review_bench.run --smoke-test

run:
	python -m swe_review_bench.run --n 20 --tolerance 3

test:
	pytest -q

clean:
	rm -rf .cache/repos/* .cache/llm/* outputs/*.csv outputs/*.png outputs/*.jsonl

# Note: GNU make is not installed by default on Windows.
# If make is unavailable, run the underlying commands directly, e.g.:
#   pip install -e .[dev]
#   python -m swe_review_bench.run --smoke-test
