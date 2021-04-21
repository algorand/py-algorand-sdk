unit:
	behave --tags="@unit.offline or @unit.algod or @unit.indexer or @unit.rekey or @unit.tealsign or @unit.dryrun or @unit.applications or @unit.responses or @unit.transactions or @unit.responses.231" test -f progress2

integration:
	behave --tags="@algod or @assets or @auction or @kmd or @send or @template or @indexer or @indexer.applications or @rekey or @compile or @dryrun or @dryrun.testing or @applications or @applications.verified or @indexer.231" test -f progress2

docker-test:
	./run_integration.sh
