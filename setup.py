import setuptools


with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="py-algorand-sdk",
    description="Algorand SDK in Python",
    author="Algorand",
    author_email="pypiservice@algorand.com",
    version="v1.11.0",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    project_urls={
        "Source": "https://github.com/algorand/py-algorand-sdk",
    },
    install_requires=[
        "pynacl>=1.4.0,<=1.5.0",
        "pycryptodomex>=3.9.8,<=3.14.1",
        "msgpack>=1.0.2,<=1.0.3",
    ],
    packages=setuptools.find_packages(),
    python_requires=">=3.5",
    package_data={"": ["data/langspec.json"]},
    include_package_data=True,
)
