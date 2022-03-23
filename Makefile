local-unit:
	pytest test/unit
	
local-integ:
	# is this working: test/integration/integration_test.py
	python -m test.integration.integration_test
	pytest test/integration/blackbox_test.py test/integration/dryrun_mixin_docs_test.py
	pytest test/integration/integration_test.py

UNITS = "@unit.abijson or @unit.algod or @unit.applications or @unit.atomic_transaction_composer or @unit.dryrun or @unit.feetest or @unit.indexer or @unit.indexer.logs or @unit.offline or @unit.rekey or @unit.transactions.keyreg or @unit.responses or @unit.responses.231 or @unit.tealsign or @unit.transactions or @unit.transactions.payment or @unit.responses.unlimited_assets or @unit.indexer.ledger_refactoring or @unit.algod.ledger_refactoring"
cuke-unit:
	behave --tags=$(UNITS) test -f progress2

INTEGS = "@abi or @algod or @applications or @applications.verified or @assets or @auction or @c2c or @compile or @dryrun or @dryrun.testing or @indexer or @indexer.231 or @indexer.applications or @kmd or @rekey or @send.keyregtxn or @send"
cuke-integ: local-integration
	behave --tags=$(INTEGS) test -f progress2

unit: local-unit cuke-unit

integration: local-integ cuke-integ

docker-test:
	./run_integration.sh
