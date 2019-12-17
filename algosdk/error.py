class BadTxnSenderError(Exception):
    def __init__(self):
        Exception.__init__(self, "transaction sender does not " +
                                 "match multisig parameters")


class InvalidThresholdError(Exception):
    def __init__(self):
        Exception.__init__(self, "invalid multisig threshold")


class InvalidSecretKeyError(Exception):
    def __init__(self):
        Exception.__init__(self, "secret key has no corresponding " +
                                 "public key in multisig")


class MergeKeysMismatchError(Exception):
    def __init__(self):
        Exception.__init__(self, "multisig parameters do not match")


class DuplicateSigMismatchError(Exception):
    def __init__(self):
        Exception.__init__(self, "mismatched duplicate signatures in multisig")


class WrongChecksumError(Exception):
    def __init__(self):
        Exception.__init__(self, "checksum failed to validate")


class WrongKeyLengthError(Exception):
    def __init__(self):
        Exception.__init__(self, "key length must be 58")


class WrongMnemonicLengthError(Exception):
    def __init__(self):
        Exception.__init__(self, "mnemonic length must be 25")


class WrongKeyBytesLengthError(Exception):
    def __init__(self):
        Exception.__init__(self, "key length in bytes must be 32")


class UnknownMsigVersionError(Exception):
    def __init__(self):
        Exception.__init__(self, "unknown multisig version != 1")


class WrongMetadataLengthError(Exception):
    def __init(self):
        Exception.__init__(self, "metadata length must be 32 bytes")


class WrongLeaseLengthError(Exception):
    def __init(self):
        Exception.__init__(self, "lease length must be 32 bytes")


class InvalidProgram(Exception):
    def __init__(self, message="invalid program for logic sig"):
        Exception.__init__(self, message)


class NotDivisibleError(Exception):
    def __init(self):
        Exception.__init__(self, "amount is not exactly divisible based on " +
                                 "the given ratio")


class TransactionGroupSizeError(Exception):
    def __init__(self):
        Exception.__init__(self, "transaction groups are limited to 16 " +
                                 "transactions")


class MultisigAccountSizeError(Exception):
    def __init__(self):
        Exception.__init__(self, "multisig accounts are limited to 256 " +
                                 "addresses")


class OutOfRangeDecimalsError(Exception):
    def __init__(self):
        Exception.__init__(self, "decimals must be between 0 and 19, " +
                                 "inclusive")


class EmptyAddressError(Exception):
    def __init__(self):
        Exception.__init__(self, "manager, freeze, reserve, and clawback " +
                                 "should not be empty unless " +
                                 "strict_empty_address_check is set to False")


class KMDHTTPError(Exception):
    pass


class AlgodHTTPError(Exception):
    pass
