unit:
	behave --tags="@unit.offline,@unit.algod,@unit.indexer,@unit.rekey,@unit.tealsign,@unit.dryrun,@unit.applications,@unit.responses,@unit.transactions,@unit.transactions.payment,@unit.responses.231,@unit.feetest,@unit.indexer.logs,@unit.abijson,@unit.atomic_transaction_composer" test -f progress2

integration:
	behave --tags="@algod,@assets,@auction,@kmd,@send,@template,@indexer,@indexer.applications,@rekey,@compile,@dryrun,@dryrun.testing,@applications,@applications.verified,@indexer.231,@abi" test -f progress2

docker-test:
	./run_integration.sh
