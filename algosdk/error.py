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
                                 "public key in multisig ")


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


class WrongAssetNameLengthError(Exception):
    def __init(self):
        Exception.__init__(self, "asset name length must be less than or equal to 32 bytes")


class WrongUnitNameLengthError(Exception):
    def __init(self):
        Exception.__init__(self, "asset unit name length must be less than or equal to 8 bytes")


class KMDHTTPError(Exception):
    pass


class AlgodHTTPError(Exception):
    pass
