DATE ?= $(shell date +%F)

.PHONY: collect digest run-daily verify

collect:
	python collectors/collect_sources.py --date $(DATE) --config configs/sources.example.json --out-dir inputs/$(DATE)

digest:
	bash scripts/run_daily.sh $(DATE)

run-daily: digest

verify:
	bash scripts/ci.sh
