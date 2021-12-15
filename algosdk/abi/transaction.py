from algosdk import constants


class ABITransactionType:
    # Any transaction type
    ANY = "txn"

    # Payment transaction type
    PAY = constants.PAYMENT_TXN

    # Key registration transaction type
    KEYREG = constants.KEYREG_TXN

    # Asset configuration transaction type
    ACFG = constants.ASSETCONFIG_TXN

    # Asset transfer transaction type
    AXFER = constants.ASSETTRANSFER_TXN

    # Asset freeze transaction type
    AFRZ = constants.ASSETFREEZE_TXN

    # Application transaction type
    APPL = constants.APPCALL_TXN


def is_abi_transaction_type(t):
    return t in (
        ABITransactionType.ANY,
        ABITransactionType.PAY,
        ABITransactionType.KEYREG,
        ABITransactionType.ACFG,
        ABITransactionType.AXFER,
        ABITransactionType.AFRZ,
        ABITransactionType.APPL,
    )
