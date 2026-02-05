# Makefile for Library Indexer

.PHONY: all index dryrun clean server

all: index

index:
	@python3 incremental_indexer.py

full-index:
	@python3 incremental_indexer.py --full

dryrun:
	@python3 incremental_indexer.py --dry-run

clean:
	rm -rf .metadata_cache
	rm -f library.json

server:
	./start_server.sh