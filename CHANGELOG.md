# Changelog

# v2.0.0

## What's Changed

### Breaking Changes

* Remove v1 algod API (`algosdk/algod.py`) due to API end-of-life (2022-12-01).  Instead, use v2 algod API (`algosdk/v2client/algod.py`).
* Remove `algosdk.future` package.  Move package contents to `algosdk`.
* Remove `encoding.future_msgpack_decode` method in favor of `encoding.msgpack_decode` method.
* Remove `cost` field in `DryrunTxnResult` in favor of 2 fields:  `budget-added` and `budget-consumed`.  `cost` can be derived by `budget-consumed - budget-added`.
* Remove `mnemonic.to_public_key` in favor of `account.address_from_private_key`.
* Remove logicsig templates, `algosdk/data/langspec.json` and all methods in `logic` depending on it.

# v1.20.2

## What's Changed
### Bugfixes
* Bug-Fix: encode ABI string with non-ASCII characters by @ahangsu in https://github.com/algorand/py-algorand-sdk/pull/402
### Enhancements
* Tests: Migrate v1 algod dependencies to v2 in cucumber tests by @algochoi in https://github.com/algorand/py-algorand-sdk/pull/400
* Enhancement: allowing zero length static array by @ahangsu in https://github.com/algorand/py-algorand-sdk/pull/401
* README: Delete Travis CI Badge  by @algochoi in https://github.com/algorand/py-algorand-sdk/pull/404
* examples: Migrate v1 algod usage to v2 algod by @algochoi in https://github.com/algorand/py-algorand-sdk/pull/403

**Full Changelog**: https://github.com/algorand/py-algorand-sdk/compare/v1.20.1...v1.20.2

# v1.20.1

## What's Changed
### Bugfixes
* Bug-fix: Implement `TransactionRejectedError` by @jdtzmn in https://github.com/algorand/py-algorand-sdk/pull/396
* Decoding: Fix roundtrip encode/decode tests for transactions by @algochoi in https://github.com/algorand/py-algorand-sdk/pull/398

**Full Changelog**: https://github.com/algorand/py-algorand-sdk/compare/v1.20.0...v1.20.1

# v1.20.0

## What's Changed
### New Features
* Boxes: Add support for Boxes by @algochoi in https://github.com/algorand/py-algorand-sdk/pull/348
* `class StateSchema`'s method `undictify()` now returns a `StateSchema` object instead of a python `dict`

**Full Changelog**: https://github.com/algorand/py-algorand-sdk/compare/v1.19.0...v1.20.0

# v1.19.0

## What's Changed
### Enhancements
* REST API: Add algod block hash endpoint, add indexer block header-only param. by @winder in https://github.com/algorand/py-algorand-sdk/pull/390

**Full Changelog**: https://github.com/algorand/py-algorand-sdk/compare/v1.18.0...v1.19.0

# v1.18.0
### Enhancements
* Deprecation: Add deprecation warnings on v1 algod API and old transaction format by @algochoi in https://github.com/algorand/py-algorand-sdk/pull/381
* enhancement: add unit test for ParticipationUpdates field by @shiqizng in https://github.com/algorand/py-algorand-sdk/pull/386

# v1.17.0
## What's Changed
### Bugfixes
* Bug-fix: Pass verbosity through to testing harness by @tzaffi in https://github.com/algorand/py-algorand-sdk/pull/373
### Enhancements
* Enhancement: Trim the indexer images and use the sandbox instead of custom dockers by @tzaffi in https://github.com/algorand/py-algorand-sdk/pull/367
* Enhancement: Add State Proof support by @shiqizng in https://github.com/algorand/py-algorand-sdk/pull/370
* Enhancement: Deprecating use of langspec  by @ahangsu in https://github.com/algorand/py-algorand-sdk/pull/371

## New Contributors
* @ahangsu made their first contribution in https://github.com/algorand/py-algorand-sdk/pull/371

**Full Changelog**: https://github.com/algorand/py-algorand-sdk/compare/v1.16.1...v1.17.0

# v1.17.0b1
## What's Changed
### Bugfixes
* Bug-fix: Pass verbosity through to testing harness by @tzaffi in https://github.com/algorand/py-algorand-sdk/pull/373
### Enhancements
* Enhancement: Trim the indexer images and use the sandbox instead of custom dockers by @tzaffi in https://github.com/algorand/py-algorand-sdk/pull/367
* Enhancement: Add State Proof support by @shiqizng in https://github.com/algorand/py-algorand-sdk/pull/370
* Enhancement: Deprecating use of langspec  by @ahangsu in https://github.com/algorand/py-algorand-sdk/pull/371

## New Contributors
* @ahangsu made their first contribution in https://github.com/algorand/py-algorand-sdk/pull/371

**Full Changelog**: https://github.com/algorand/py-algorand-sdk/compare/v1.16.1...v1.17.0b1


# v1.16.1
### Bugfixes
* bug-fix: add check to desc so we dont output null if undefined by @barnjamin in https://github.com/algorand/py-algorand-sdk/pull/368
### Enhancements
* AVM:  Consolidate TEAL and AVM versions by @michaeldiamant in https://github.com/algorand/py-algorand-sdk/pull/361
* Testing: Modify cucumber steps to use dev mode network by @algochoi in https://github.com/algorand/py-algorand-sdk/pull/360

# v1.16.0

## What's Changed

### New Features
* Dev Tools: Source map decoder by @barnjamin in https://github.com/algorand/py-algorand-sdk/pull/353

### Enhancements
* Github-Actions: Adding pr title and label checks by @algojack in https://github.com/algorand/py-algorand-sdk/pull/358

### Other
* Implement new step asserting that AtomicTransactionComposer's attempt to add a method can fail with a particular error by @tzaffi in https://github.com/algorand/py-algorand-sdk/pull/347
* Split up  unit test files and rename tests directory to test by @algochoi in https://github.com/algorand/py-algorand-sdk/pull/351
* App page const by @barnjamin in https://github.com/algorand/py-algorand-sdk/pull/357

**Full Changelog**: https://github.com/algorand/py-algorand-sdk/compare/v1.15.0...v1.16.0


# v1.15.0

## What's Changed
* Break v2_step.py into account_, application_, and other_ by @tzaffi in https://github.com/algorand/py-algorand-sdk/pull/341
* Add method to ABIResult by @barnjamin in https://github.com/algorand/py-algorand-sdk/pull/342
* Add method to get Method by name by @barnjamin in https://github.com/algorand/py-algorand-sdk/pull/345

**Full Changelog**: https://github.com/algorand/py-algorand-sdk/compare/v1.14.0...v1.15.0


# v1.14.0

## What's Changed

* Update client API to support new cost fields in dryrun result by @algoidurovic in https://github.com/algorand/py-algorand-sdk/pull/336

## New Contributors

* @algoidurovic made their first contribution in https://github.com/algorand/py-algorand-sdk/pull/336

# v1.13.1
## Fixed
- Fix readthedocs by providing root requirements.txt (#332)

# v1.13.0
## Added
- Adding condition for allowing rcv to be none if close to is set (#317)
- Adding foreign-app-addr to dryrun creator (#321)
## Changed
- Matrix test python versions integration tests (#327)
- Matrix test across Python versions for unit tests (#325)
- Bump minimum Python version to 3.8 (#323)
- Add minimum Python version policy to README (#322)
- Consistently reference `pip3` in README (#319)
## Fixed
- Fixed typo in lsig trace (#320)

# v1.12.0
## Fixed
- Catch TypeError and ValueError in verify functions (#309)
## Added
- Dryrun response (#283)

# v1.11.0
## Added
- Support unlimited assets REST API changes. (#295)

## Changed
- Fix the cucumber test wording around block rounds in indexer asset balance lookup (#301)

# v1.11.0b1

## Added
- Support unlimited assets REST API changes. (#295)

## Changed
- Fix the cucumber test wording around block rounds in indexer asset balance lookup (#301)

# 1.10.0

## Added:

- New keyreg txn field (#244)
- C2C Feature and Testing (#268)
- Add App creator to account balances (#277)
- Add ABI and ATC to Sphinx (#289)

## Changed:

- Change __init__.py to include v2client import (#243)
- Updates to pipeline (#279)
- Add CircleCI build step to generate docsets (#285)
- revert to point testing harness to sdk testing's master branch (#288)
- Partially fix types for atomic transaction composer (#290)
- Update `langspec.json` for Teal6 (#292)

## 1.9.0
### Added

- Create dryrun (#259)
- Support Foreign objects as ABI arguments and address ARC-4 changes (#251)
- Add requirement to fetch behave source code and update readme (#262)
- Fix wait for confirmation function (#263)
- Add a default User-Agent header to the v2 algod client (#260)
- ABI Interaction Support for Python SDK (#247)
- ABI Type encoding support (#238)
- Add type hints and clean up ABI code (#253)
- Add CircleCI configs to the Python SDK repo (#246)

### Changed
- Re-format local and global state to work with correct msgpack encoding (#274)

## 1.9.0b2
### Added

- Support Foreign objects as ABI arguments and address ARC-4 changes (#251)
- Add requirement to fetch behave source code and update readme (#262)
- Fix wait for confirmation function (#263)
- Add a default User-Agent header to the v2 algod client (#260)

## 1.9.0b1
### Added

- ABI Interaction Support for Python SDK (#247)
- ABI Type encoding support (#238)
- Add type hints and clean up ABI code (#253)
- Add CircleCI configs to the Python SDK repo (#246)

## 1.8.0
### Added

- Add wait_for_confirmation() to AlgodClient (#214)
- Support AVM 1.0 (#236)
- Support for < python 3.7 (#221)

### Bug Fixes
- Fix JSON decoding in AlgodHTTPError (#223)

## 1.7.0
### Added

- Add OnlineyKeyregTxn and OfflineKeyregTxn class and additional tests.
- Signing support for rekeying to LogicSig/MultiSig account

### Enhancements

- Deprecate to_public_key and remove internal usage of to_public_key
- Modified constants.py to match python.org PEP 8 style guidelines

### Bug Fixes

- Bugfix for newer Sphinx versions - m2r replaced with maintained m2r2
- Fix typo in min/max balance indexer & make clearer
- Merge Request headers in `algod.py`

## 1.6.0
### Added
- Support for dynamic opcode accounting, backward jumps, loops, callsub, retsub
- Ability to pay for more app space
- Ability to pool fees

### Bug Fix
- Raise JSONDecodeError instead of None (#193)

## 1.5.0
### Added
- Support new features for indexer 2.3.2
- Support for offline and nonparticipating key registration transactions.
- Add TEAL 3 support

### BugFix
- Detects the sending of unsigned transactions
- Add asset_info() and application_info() methods to the v2 AlgodClient class.

## 1.4.1
## Bugfix
- Dependency on missing constant removed
- Logic multisig signing fixed
- kmd.sign_transaction now works with application txn
- Added check for empty result in list_wallets
- Now zero receiver is handled in transactions
- Added init file for testing

## Changed
- Moved examples out of README into examples folder
- Added optional 'round_num' arguments to standardize 'round_num', 'round', and 'block'

## 1.4.0
## Added
- Support for Applications
## Bugfix
- Now content-type is set when sending transactions
- indexer client now allows no token for local development environment

### Added
- Support for indexer and algod 2.0

## 1.2.0
### Added
- Added support for Algorand Smart Contracts (ASC)
    - Dynamic fee contract
    - Limit order contract
    - Periodic payment contract
- Added SuggestedParams, which contains fee, first valid round, last valid round, genesis hash, and genesis ID; transactions and templates from 'future' take SuggestedParams as an argument.
    - Added suggested_params_as_object() in algod

## 1.1.1
### Added
- Added asset decimals field.

## 1.1.0
### Added
- Added support for Algorand Standardized Assets (ASA)
- Added support for Algorand Smart Contracts (ASC)
    - Added support for Hashed Time Lock Contract (HTLC)
    - Added support for Split contract
- Added support for Group Transactions
- Added support for leases

## 1.0.5
### Added
- custom headers and example

## 1.0.4
### Changed
- more flexibility in transactions_by_address()
- documentation changes

## 1.0.3
### Added
- signing and verifying signatures for arbitrary bytes

## 1.0.2
### Added
- option for flat fee when creating transactions
- functions for converting from microalgos to algos and from algos to microalgos

## 1.0.1
### Added
- algod.send_transaction(): sends SignedTransaction

### Changed
- algod.send_raw_transaction(): sends base64 encoded transaction
- Multisig.get_account_from_sig() is now Multisig.get_multisig_account

## 1.0.0
### Added
- SDK released
