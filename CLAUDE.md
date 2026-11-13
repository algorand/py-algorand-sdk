# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

**Build and Quality:**
- `make lint` - Run all linting checks (includes format check, type check, and sdist check)
- `make black` - Check code formatting with black (line length: 79)
- `make mypy` - Run type checking with mypy on algosdk package
- `make generate-init` - Update algosdk/__init__.pyi for downstream type analysis
- `make check-generate-init` - Verify __init__.pyi is up to date

**Testing:**
- `make docker-test` - Run full test suite in Docker with test harness
- `make ci-test` - Run CI test pipeline (harness + unit + integration + smoke tests)
- `make pytest-unit` - Run unit tests only (tests/unit_tests)
- `make unit` - Run unit tests with behave framework using unit.tags
- `make integration` - Run integration tests with behave using integration.tags
- `make smoke-test-examples` - Test example scripts

**Development Environment:**
- `make harness` - Set up Algorand Sandbox test environment
- `make harness-down` - Tear down test harness
- `pip3 install -r requirements.txt` - Install dependencies

## Code Architecture

**Core Package Structure (`algosdk/`):**
- `transaction.py` - Transaction construction and signing (main transaction types)
- `atomic_transaction_composer.py` - Compose and execute atomic transaction groups
- `v2client/` - API clients for algod and indexer nodes
  - `algod.py` - Algorand node client for transaction submission
  - `indexer.py` - Indexer client for blockchain queries
  - `models/` - Response model classes
- `abi/` - Application Binary Interface support for smart contracts
- `account.py` - Account generation and key management
- `encoding.py` - Address validation and encoding utilities
- `mnemonic.py` - BIP-39 mnemonic phrase handling
- `logic.py` - Logic signature utilities
- `kmd.py` - Key Management Daemon client

**Testing Framework:**
- Uses `behave` (Gherkin/Cucumber) for BDD testing shared across SDKs
- Unit tests tagged in `tests/unit.tags`, integration in `tests/integration.tags`
- Unit tests also available as pytest in `tests/unit_tests/`
- Test harness uses Algorand Sandbox for integration testing

**Key Dependencies:**
- `pynacl` - Cryptographic operations
- `pycryptodomex` - Additional crypto functions
- `msgpack` - MessagePack serialization (Algorand's wire format)
- Minimum Python 3.10

**CI/CD Process:**
- CI tests run on Python 3.10, 3.11, and 3.12 on ubuntu-24.04
- All PRs must pass: linting (`make lint`) and unit tests (`make pytest-unit`)
- Integration tests run full CI pipeline (`make ci-test`)
- Documentation builds with Sphinx (in `docs/` directory)
- Release process uses `python -m build` and publishes to PyPI with twine

**Development Notes:**
- Code style enforced by black with 79 character line length
- Type hints required, checked by mypy
- The `__init__.pyi` file is auto-generated for downstream IDE support
- Examples in `examples/` directory with smoke testing
- Follows semantic versioning in `setup.py`