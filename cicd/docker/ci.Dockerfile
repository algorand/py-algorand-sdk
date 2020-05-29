FROM python:3.7

RUN pip install git+https://github.com/behave/behave -q

ADD cicd/docker/entrypoint.sh /entrypoint.sh

ENTRYPOINT [ "/entrypoint.sh" ]
