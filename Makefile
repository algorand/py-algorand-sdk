UNITS = "@unit.abijson or @unit.abijson.byname or @unit.algod or @unit.algod.ledger_refactoring or @unit.applications or @unit.atc_method_args or @unit.atomic_transaction_composer or @unit.dryrun or @unit.dryrun.trace.application or @unit.feetest or @unit.indexer or @unit.indexer.ledger_refactoring or @unit.indexer.logs or @unit.offline or @unit.rekey or @unit.transactions.keyreg or @unit.responses or @unit.responses.231 or @unit.tealsign or @unit.transactions or @unit.transactions.payment or @unit.responses.unlimited_assets"
unit:
	behave --tags=$(UNITS) tests -f progress2

INTEGRATIONS = "@abi or @algod or @applications or @applications.verified or @assets or @auction or @c2c or @compile or @dryrun or @dryrun.testing or @indexer or @indexer.231 or @indexer.applications or @kmd or @rekey or @send.keyregtxn or @send"
integration:
	behave --tags=$(INTEGRATIONS) tests -f progress2

PYTHON_VERSION ?= 3.8
docker-test: export PYTHON_VERSION := $(PYTHON_VERSION)
docker-test: export DOCKERIZE_PYSDK ?= true
docker-test: export TESTING_URL ?= https://github.com/algorand/algorand-sdk-testing.git
docker-test: export TESTING_BRANCH ?= control-my-test-branches # revert to master before merge
docker-test:
	./integration.sh

# these are utilized if run locally:
LOCAL_TESTENV ?= .local-env
prep-local-testenv:
	python tests/prep_local_testenv.py $(LOCAL_TESTENV)

show-local-testenv:
	echo "contents of $(LOCAL_TESTENV)"
	cat $(LOCAL_TESTENV) || echo "DNE"

# configure the repos and branches that a local test will build off of:
local-test: export TESTING_URL ?= https://github.com/algorand/algorand-sdk-testing.git
local-test: export TESTING_BRANCH ?= control-my-test-branches # revert to master before merge
local-test: export ALGOD_URL ?= https://github.com/algorand/go-algorand
local-test: export ALGOD_BRANCH ?= feature/avm-boxes # revert to master before merge
local-test: export INDEXER_URL ?= https://github.com/algorand/indexer
local-test: export INDEXER_BRANCH ?= localledger/integration # revert to develop before merge

# other exports for `local-test`:
local-test: export PYTHON_VERSION := $(PYTHON_VERSION)
local-test: export LOCAL_TESTENV := $(abspath .)/$(LOCAL_TESTENV)
local-test: export DOCKERIZE_PYSDK ?= false
local-test: export TYPE_OVERRIDE ?= source

# local-test bootstraps the necessary algod and indexer docker containers
# for integration tests, but does not run the tests
local-test: prep-local-testenv show-local-testenv
	./integration.sh
