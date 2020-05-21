FROM python:3.7.7

# Copy SDK code into the container
RUN mkdir -p $HOME/py-algorand-sdk
COPY . $HOME/py-algorand-sdk
WORKDIR $HOME/py-algorand-sdk

# SDK dependencies, and source version of behave with tag expression support
RUN pip3 install git+https://github.com/algorand/py-algorand-sdk/ -q \
    && pip install git+https://github.com/behave/behave

# Run integration tests
CMD ["/bin/bash", "-c", "make integration"]

