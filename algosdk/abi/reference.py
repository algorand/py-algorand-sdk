class ABIReferenceType:
    # Account reference type
    ACCOUNT = "account"

    # Application reference type
    APPLICATION = "application"

    # Asset reference type
    ASSET = "asset"


def is_abi_reference_type(t: "ABIReferenceType") -> bool:
    return t in (
        ABIReferenceType.ACCOUNT,
        ABIReferenceType.APPLICATION,
        ABIReferenceType.ASSET,
    )
