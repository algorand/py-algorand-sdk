unit:
	behave --tags="@unit.offline or @unit.algod or @unit.indexer" test -f progress2

integration:
	behave --tags="@algod or @assets or @auction or @kmd or @send or @template or @indexer" test -f progress2

docker-test:
	./run_integration.sh
