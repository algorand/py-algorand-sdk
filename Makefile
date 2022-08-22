UNIT_TAGS :=  "$(subst :, or ,$(shell awk '{print $2}' tests/unit.tags | paste -s -d: -))"
INTEGRATION_TAGS := "$(subst :, or ,$(shell awk '{print $2}' tests/integration.tags | paste -s -d: -))"

unit:
	behave --tags=$(UNIT_TAGS) tests -f progress2

INTEGRATIONS = "@abi or @algod or @applications or @applications.verified or @assets or @auction or @c2c or @compile or @dryrun or @dryrun.testing or @indexer or @indexer.231 or @indexer.applications or @kmd or @rekey or @send.keyregtxn or @send or @compile.sourcemap"
integration:
	behave --tags=$(INTEGRATION_TAGS) tests -f progress2 --no-capture

display-all-python-steps:
	find tests/steps -name "*.py" | xargs grep "behave" 2>/dev/null | cut -d: -f1 | sort | uniq | xargs awk "/@(given|step|then|when)/,/[)]/" | grep -E "(\".+\"|\'.+\')"

harness:
	./test-harness.sh

PYTHON_VERSION ?= 3.8
docker-pysdk-build:
	docker build -t py-sdk-testing --build-arg PYTHON_VERSION="${PYTHON_VERSION}" .

docker-pysdk-run:
	docker ps -a
	docker run -it --network host py-sdk-testing:latest

docker-test: harness docker-pysdk-build docker-pysdk-run
