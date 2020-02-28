# Changelog
# 2.0.0
# Added
- Added support for Algorand Smart Contracts (ASC) 
    - Dynamic fee contract
    - Limit order contract
    - Periodic payment contract

# Changed
- Transactions and templates now take suggested params obtained from algod as an argument; the SuggestedParams object contains fee, first valid round, last valid round, genesis hash, and genesis ID

# 1.1.1
# Added
- Added asset decimals field.

# 1.1.0
# Added
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