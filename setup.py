import setuptools


with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="py-algorand-sdk",
    description="Algorand SDK in Python",
    author="Algorand",
    author_email="pypiservice@algorand.com",
    version="v2.0.0",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/algorand/py-algorand-sdk",
    license="MIT",
    project_urls={
        "Source": "https://github.com/algorand/py-algorand-sdk",
    },
    install_requires=[
        "pynacl>=1.4.0,<2",
        "pycryptodomex>=3.6.0,<4",
        "msgpack>=1.0.0,<2",
    ],
    packages=setuptools.find_packages(
        include=(
            "algosdk",
            "algosdk.*",
        )
    ),
    python_requires=">=3.8",
    package_data={"": ["*.pyi", "py.typed"]},
    include_package_data=True,
)
