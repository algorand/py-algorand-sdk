UNIT_TAGS :=  $(subst :, or ,$(shell awk '{print $2}' tests/unit.tags | paste -s -d: -))
INTEGRATIONS_TAGS := $(subst :, or ,$(shell awk '{print $2}' tests/integration.tags | paste -s -d: -))

unit:
	behave --tags=$(UNITS) tests -f progress2

integration:
	behave --tags=$(INTEGRATIONS) tests -f progress2 --no-capture

harness:
	./test-harness.sh

PYTHON_VERSION ?= 3.8
docker-pysdk-build:
	docker build -t py-sdk-testing --build-arg PYTHON_VERSION="${PYTHON_VERSION}" .

docker-pysdk-run:
	docker ps -a
	docker run -it --network host py-sdk-testing:latest

docker-test: harness docker-pysdk-build docker-pysdk-run
