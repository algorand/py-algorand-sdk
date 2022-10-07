UNIT_TAGS :=  "$(subst :, or ,$(shell awk '{print $2}' tests/unit.tags | paste -s -d: -))"
INTEGRATION_TAGS := "$(subst :, or ,$(shell awk '{print $2}' tests/integration.tags | paste -s -d: -))"

unit:
	behave --tags=$(UNIT_TAGS) tests -f progress2

integration:
	behave --tags=$(INTEGRATION_TAGS) tests -f progress2 --no-capture

display-all-python-steps:
	find tests/steps -name "*.py" | xargs grep "behave" 2>/dev/null | cut -d: -f1 | sort | uniq | xargs awk "/@(given|step|then|when)/,/[)]/" | grep -E "(\".+\"|\'.+\')"

harness:
	./test-harness.sh up

harness-down:
	./test-harness.sh down

PYTHON_VERSION ?= 3.8
docker-pysdk-build:
	docker build -t py-sdk-testing --build-arg PYTHON_VERSION="${PYTHON_VERSION}" .

docker-pysdk-run:
	docker ps -a
	docker run -it --network host py-sdk-testing:latest

docker-test: harness docker-pysdk-build docker-pysdk-run
