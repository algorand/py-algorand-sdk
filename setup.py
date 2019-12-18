import setuptools


with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="py-algorand-sdk",
    description="Algorand SDK in Python",
    author="Algorand",
    author_email="pypiservice@algorand.com",
    version="1.1.1",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    project_urls={
        "Source": "https://github.com/algorand/py-algorand-sdk",
    },
    install_requires=["pynacl", "cryptography>=2.7", "msgpack"],
    packages=["algosdk"],
    python_requires=">=3.5",
    package_data={'': ['data/langspec.json']},
    include_package_data=True,
)
