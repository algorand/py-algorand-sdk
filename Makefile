unit:
	behave --tags="@unit" test -f progress2

integration:
	behave --tags="@unit or @algod or @assets or @auction or @kmd or @unit or @send or @template or @indexer" test -f progress2

docker-test:
	./run_integration.sh
