import setuptools


setuptools.setup(
    name="algosdk",
    description="Algorand SDK in Python",
    url="https://github.com/algorand/py-algorand-sdk",
    install_requires=["pynacl", "cryptography", "msgpack"],
    packages=["algosdk"]
)