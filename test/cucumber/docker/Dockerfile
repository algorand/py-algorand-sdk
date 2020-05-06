FROM python:3.7.7

# SDK Dependencies
RUN pip3 install behave
RUN pip3 install git+https://github.com/algorand/py-algorand-sdk/

RUN mkdir -p $HOME/py-algorand-sdk
COPY . $HOME/py-algorand-sdk
WORKDIR $HOME/py-algorand-sdk

CMD ["/bin/bash", "-c", "behave test/cucumber -f progress2"]
