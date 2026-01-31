SHELL := /bin/bash
SERVICE := methodd

.PHONY: run verify clean

run:
	@rm -rf logs outputs && mkdir -p logs outputs
	@docker compose run --rm -T $(SERVICE)

verify:
	@set -e; \
	echo "== latest log =="; \
	LATEST_LOG="$$(ls -t logs/run_*.log | head -n 1)"; \
	echo "$$LATEST_LOG"; \
	echo "== exit criteria =="; \
	grep -n "ERROR\|Traceback\|❌" -n "$$LATEST_LOG" || echo "NO_ERROR_FOUND"; \
	test -s outputs/checksums.md5 && echo "CHECKSUM_OK"; \
	ls -lh logs outputs

clean:
	@rm -rf logs outputs