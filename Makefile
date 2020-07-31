unit:
	behave --tags="@unit.offline or @unit.algod or @unit.indexer or @unit.rekey or @unit.tealsign or @unit.dryrun or @unit.responses" test -f progress2

integration:
	behave --tags="@algod or @assets or @auction or @kmd or @send or @template or @indexer or @rekey or @compile or @dryrun or @dryrun.testing" test -f progress2

docker-test:
	./run_integration.sh
