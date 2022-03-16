# UNITS = "@unit.abijson or @unit.algod or @unit.applications or @unit.atomic_transaction_composer or @unit.dryrun or @unit.feetest or @unit.indexer or @unit.indexer.logs or @unit.offline or @unit.rekey or @unit.transactions.keyreg or @unit.responses or @unit.responses.231 or @unit.tealsign or @unit.transactions or @unit.transactions.payment or @unit.dryrun.trace.application"
UNITS = "@unit.abijson or @unit.algod or @unit.applications or @unit.atomic_transaction_composer or @unit.dryrun or @unit.feetest or @unit.offline or @unit.rekey or @unit.transactions.keyreg or @unit.responses or @unit.responses.231 or @unit.tealsign or @unit.transactions or @unit.transactions.payment or @unit.dryrun.trace.application"
unit:
	behave --tags=$(UNITS) test -f progress2

# INTEGRATIONS = "@abi or @algod or @applications or @applications.verified or @assets or @auction or @c2c or @compile or @dryrun or @dryrun.testing or @indexer or @indexer.231 or @indexer.applications or @kmd or @rekey or @send.keyregtxn or @send"
INTEGRATIONS = "@abi or @algod or @applications or @applications.verified or @assets or @auction or @c2c or @compile or @dryrun or @dryrun.testing or @kmd or @rekey or @send.keyregtxn or @send"
integration: blackbox
	behave --tags=$(INTEGRATIONS) test -f progress2

blackbox:
	pytest -sv x/blackbox

docker-test:
	./run_integration.sh

