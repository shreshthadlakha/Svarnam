# Rupee Gold Stack — build commands (CODE-STRUCTURE.md §1)
PY := python

.PHONY: build update serve test

build:            ## regenerate site/dataset.json + sources.md + build_report.txt from data/
	$(PY) -m pipeline.build

update:           ## after dropping new raw files: rebuild + review the report diff
	$(PY) -m pipeline.build --diff-report

serve:            ## local preview of site/
	cd site && $(PY) -m http.server 8000

test:             ## parser fixtures + invariants (PRD §8 acceptance criteria)
	$(PY) -m pytest pipeline/tests -q
