import setuptools


with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="algosdk",
    description="Algorand SDK in Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/algorand/py-algorand-sdk",
    install_requires=["pynacl", "cryptography", "msgpack"],
    packages=["algosdk"]
)