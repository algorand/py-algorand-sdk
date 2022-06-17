UNITS = "@unit.abijson or @unit.abijson.byname or @unit.algod or @unit.algod.ledger_refactoring or @unit.applications or @unit.atc_method_args or @unit.atomic_transaction_composer or @unit.dryrun or @unit.dryrun.trace.application or @unit.feetest or @unit.indexer or @unit.indexer.ledger_refactoring or @unit.indexer.logs or @unit.offline or @unit.rekey or @unit.transactions.keyreg or @unit.responses or @unit.responses.231 or @unit.tealsign or @unit.transactions or @unit.transactions.payment or @unit.responses.unlimited_assets"
unit:
	behave --tags=$(UNITS) test -f progress2

INTEGRATIONS = "@abi or @algod or @applications or @applications.verified or @assets or @auction or @c2c or @compile or @dryrun or @dryrun.testing or @indexer or @indexer.231 or @indexer.applications or @kmd or @rekey or @send.keyregtxn or @send"
integration:
	behave --tags=$(INTEGRATIONS) test -f progress2

PYTHON_VERSION ?= 3.8
docker-test:
	PYTHON_VERSION='$(PYTHON_VERSION)' ./run_integration.sh
