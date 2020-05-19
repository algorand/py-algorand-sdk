FROM python:3.7.7

# Copy SDK code into the container
RUN mkdir -p $HOME/py-algorand-sdk
COPY . $HOME/py-algorand-sdk
WORKDIR $HOME/py-algorand-sdk

RUN wget https://github.com/algorand/py-algorand-sdk/archive/evan/rekey.zip \
    && pip3 install rekey.zip \
    && pip3 install behave -q

# Run integration tests
CMD ["/bin/bash", "-c", "behave test -f progress2"]

