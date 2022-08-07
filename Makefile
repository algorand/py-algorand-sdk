UNITS = "@unit.abijson or @unit.abijson.byname or @unit.algod or @unit.algod.ledger_refactoring or @unit.applications or @unit.atc_method_args or @unit.atomic_transaction_composer or @unit.dryrun or @unit.dryrun.trace.application or @unit.feetest or @unit.indexer or @unit.indexer.ledger_refactoring or @unit.indexer.logs or @unit.offline or @unit.rekey or @unit.transactions.keyreg or @unit.responses or @unit.responses.231 or @unit.tealsign or @unit.transactions or @unit.transactions.payment or @unit.responses.unlimited_assets or @unit.sourcemap"
unit:
	behave --tags=$(UNITS) tests -f progress2

INTEGRATIONS = "@abi or @algod or @applications or @applications.verified or @assets or @auction or @c2c or @compile or @dryrun or @dryrun.testing or @indexer or @indexer.231 or @indexer.applications or @kmd or @rekey_v1 or @send.keyregtxn or @send or @compile.sourcemap"
integration:
	behave --tags=$(INTEGRATIONS) tests -f progress2 --no-capture

# channel or source
TYPE ?= channel
harness:
	TYPE='$(TYPE)' ./test-harness.sh

PYTHON_VERSION ?= 3.8
docker-pysdk-build:
	docker build -t py-sdk-testing --build-arg PYTHON_VERSION="${PYTHON_VERSION}" .

docker-pysdk-run:
	docker ps -a
	docker run -it --network host py-sdk-testing:latest

docker-test: harness docker-pysdk-build docker-pysdk-run

# algorand-sdk-testing's git branch:
TBRANCH = master
# go-algorand's git branch:
ABRANCH = master
get-trepo:
	rm -rf test-harness && rm -rf tests/features \
	&& git clone --single-branch --branch $(TBRANCH) https://github.com/algorand/algorand-sdk-testing.git test-harness \
	&& sed -i "" -e "s#ALGOD_BRANCH=\".*\"#ALGOD_BRANCH=\"$(ABRANCH)\"#g" test-harness/.up-env \
	&& mkdir -p test/features \
	&& cp -r test-harness/features/* test/features

up:
	./test-harness/scripts/up.sh

down:
	./test-harness/scripts/down.sh

restart-test-harness: get-trepo up

ps:
	cd test-harness \
	&& docker-compose ps

pause:
	cd test-harness \
	&& docker-compose pause 

unpause:
	cd test-harness \
	&& docker-compose unpause 


# sdk-harness-algod \
# && docker-compose pause sdk-harness-indexer-23x-1 \
# && docker-compose pause sdk-harness-indexer-23x-2 \
# && docker-compose pause sdk-harness-indexer-applications  \
# && docker-compose pause sdk-harness-indexer-live \
# && docker-compose pause sdk-harness-indexer-release \
# && docker-compose pause sdk-harness-algod \


docker-cleanup:
	docker container prune \
	&& docker rmi $$(docker images -q) \
	&& docker rm -v $$(docker ps -qa)

docker-nuke:
	docker system prune

TBRANCH = zc2c
ABRANCH = features/contract-to-contract
z: restart-test-harness 


c2c-integration:
	behave -D BEHAVE_ON_ERROR --tags=c2c test/features/integration/c2c.feature -f pretty

BINARY_FILE = ""
show-binary:
	xxd -p $(BINARY_FILE) | tr -d '\n'

# c2c-integration:
# 	behave --tags=c2c test/features/integration/c2c.feature -f plain

# Available formatters:
#   json           JSON dump of test run
#   json.pretty    JSON dump of test run (human readable)
#   null           Provides formatter that does not output anything.
#   plain          Very basic formatter with maximum compatibility
#   pretty         Standard colourised pretty formatter
#   progress       Shows dotted progress for each executed scenario.
#   progress2      Shows dotted progress for each executed step.
#   progress3      Shows detailed progress for each step of a scenario.
#   rerun          Emits scenario file locations of failing scenarios
#   sphinx.steps   Generate sphinx-based documentation for step definitions.
#   steps          Shows step definitions (step implementations).
#   steps.catalog  Shows non-technical documentation for step definitions.
#   steps.doc      Shows documentation for step definitions.
#   steps.usage    Shows how step definitions are used by steps.
#   tags           Shows tags (and how often they are used).
#   tags.location  Shows tags and the location where they are used.

zymlinkize:
	mv test/cucumber/features test_cucumber_features \
	&& ln -s ~/github/algorand/algorand-sdk-testing/features test/cucumber/features

de-zymlinkize:
	rm -f test/cucumber/features \
	&& mv test_cucumber_features test/cucumber/features

local-docker-testing:
	PYTHON_VERSION='3.8' ./run_integration_after_git_and_docker.sh

compliant-behave:
	ln -s ~/github/algorand/algorand-sdk-testing/features test/features
	ln -s test/


docker-restart:
	./test-harness/scripts/restart.sh

abi-args-integration:
	behave -D BEHAVE_ON_ERROR --tags="@z" -k -f plain test/features/integration/abi.feature

abi-args-unit:
	behave -D BEHAVE_ON_ERROR --tags="@unit.atc_method_args" -k -f plain test/features/unit/atomic_transaction_composer.feature
	# behave -D BEHAVE_ON_ERROR --tags="@z" -k -f plain test/features/unit/atomic_transaction_composer.feature

