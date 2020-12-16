FROM python:3.7.9

# Copy SDK code into the container
RUN mkdir -p $HOME/py-algorand-sdk
COPY . $HOME/py-algorand-sdk
WORKDIR $HOME/py-algorand-sdk

# SDK dependencies, and source version of behave with tag expression support
RUN pip install . -q \
    && pip install git+https://github.com/behave/behave -q

# Run integration tests
CMD ["/bin/bash", "-c", "make unit && make integration"]

