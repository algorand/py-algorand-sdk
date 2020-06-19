unit:
	behave --tags="@unit" test -f progress2

integration:
        behave --tags="@applications" test -f progress2

docker-test:
	./run_integration.sh
