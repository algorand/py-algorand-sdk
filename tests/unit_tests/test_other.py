import base64
import random
import unittest

import pytest
from algosdk import (
    account,
    constants,
    encoding,
    error,
    logic,
    mnemonic,
    util,
    wordlist,
)

from nacl.signing import SigningKey


class TestMnemonic(unittest.TestCase):
    zero_bytes = bytes([0] * 32)

    def test_mnemonic_private_key(self):
        priv_key, _ = account.generate_account()
        mn = mnemonic.from_private_key(priv_key)
        self.assertEqual(len(mn.split(" ")), constants.mnemonic_len)
        self.assertEqual(priv_key, mnemonic.to_private_key(mn))

    def test_zero_mnemonic(self):
        expected_mnemonic = (
            "abandon abandon abandon abandon abandon abandon abandon abandon "
            "abandon abandon abandon abandon abandon abandon abandon abandon "
            "abandon abandon abandon abandon abandon abandon abandon abandon "
            "invest"
        )
        result = mnemonic._from_key(self.zero_bytes)
        self.assertEqual(expected_mnemonic, result)
        result = mnemonic._to_key(result)
        self.assertEqual(self.zero_bytes, result)

    def test_whitespace_irrelevance(self):
        padded = """
        abandon abandon abandon abandon abandon abandon abandon abandon
        abandon abandon abandon abandon abandon abandon abandon abandon
        abandon abandon abandon abandon abandon abandon abandon abandon
        invest
        """
        result = mnemonic._to_key(padded)
        self.assertEqual(self.zero_bytes, result)

    def test_case_irrelevance(self):
        padded = """
        abandon ABANDON abandon abandon abandon abandon abandon abandon
        abandon abandon abandon abandon abandon abandon abandon abandon
        abandon abandon abandon abandon abandon abandon abandon abandon
        invEST
        """
        result = mnemonic._to_key(padded)
        self.assertEqual(self.zero_bytes, result)

    def test_short_words(self):
        padded = """
        aban abandon abandon abandon abandon abandon abandon abandon
        aban abandon abandon abandon abandon abandon abandon abandon
        aban abandon abandon abandon abandon abandon abandon abandon
        inve
        """
        result = mnemonic._to_key(padded)
        self.assertEqual(self.zero_bytes, result)

    def test_wrong_checksum(self):
        mn = (
            "abandon abandon abandon abandon abandon abandon abandon abandon "
            "abandon abandon abandon abandon abandon abandon abandon abandon "
            "abandon abandon abandon abandon abandon abandon abandon abandon "
            "abandon"
        )
        self.assertRaises(error.WrongChecksumError, mnemonic._to_key, mn)

    def test_word_not_in_list(self):
        mn = (
            "abandon abandon abandon abandon abandon abandon abandon abandon "
            "abandon abandon abandon abandon abandon abandon abandon abandon "
            "abandon abandon abandon venues abandon abandon abandon abandon "
            "invest"
        )
        self.assertRaises(ValueError, mnemonic._to_key, mn)
        mn = (
            "abandon abandon abandon abandon abandon abandon abandon abandon "
            "abandon abandon abandon abandon abandon abandon abandon abandon "
            "abandon abandon abandon abandon abandon abandon abandon abandon "
            "x-ray"
        )
        self.assertRaises(ValueError, mnemonic._to_key, mn)

    def test_wordlist_integrity(self):
        """This isn't a test of _checksum, it reminds us not to change the
        wordlist.

        """
        result = mnemonic._checksum(bytes(wordlist.word_list_raw(), "utf-8"))
        self.assertEqual(result, 1939)

    def test_mnemonic_wrong_len(self):
        mn = "abandon abandon abandon"
        self.assertRaises(error.WrongMnemonicLengthError, mnemonic._to_key, mn)

    def test_bytes_wrong_len(self):
        key = bytes([0] * 31)
        self.assertRaises(
            error.WrongKeyBytesLengthError, mnemonic._from_key, key
        )

    def test_key_wrong_len(self):
        address = "WRONG_LENGTH_TOO_SHORT"
        self.assertRaises(
            error.WrongKeyLengthError, encoding.decode_address, address
        )


class TestAddress(unittest.TestCase):
    def test_is_valid(self):
        valid = "MO2H6ZU47Q36GJ6GVHUKGEBEQINN7ZWVACMWZQGIYUOE3RBSRVYHV4ACJI"
        self.assertTrue(encoding.is_valid_address(valid))
        invalid = "MO2H6ZU47Q36GJ6GVHUKGEBEQINN7ZWVACMWZQGIYUOE3RBSRVYHV4ACJG"
        self.assertFalse(encoding.is_valid_address(invalid))

    def test_encode_decode(self):
        sk, pk = account.generate_account()
        self.assertEqual(
            pk, encoding.encode_address(encoding.decode_address(pk))
        )
        self.assertEqual(pk, account.address_from_private_key(sk))


class TestMsgpack(unittest.TestCase):
    def test_bid(self):
        bid = (
            "gqFigqNiaWSGo2FpZAGjYXVjxCCokNFWl9DCqHrP9trjPICAMGOaRoX/OR+M6tHWh"
            "fUBkKZiaWRkZXLEIP1rCXe2x5+exPBfU3CZwGPMY8mzwvglET+QtgfCPdCmo2N1cs"
            "8AAADN9kTOAKJpZM5JeDcCpXByaWNlzQMgo3NpZ8RAiR06J4suAixy13BKHlw4VrO"
            "RKzLT5CJr9n3YSj0Ao6byV23JHGU0yPf7u9/o4ECw4Xy9hc9pWopLW97xKXRfA6F0"
            "oWI="
        )
        self.assertEqual(
            bid, encoding.msgpack_encode(encoding.msgpack_decode(bid))
        )

    def test_signed_txn(self):
        stxn = (
            "gqNzaWfEQGdpjnStb70k2iXzOlu+RSMgCYLe25wkUfbgRsXs7jx6rbW61ivCs6/zG"
            "s3gZAZf4L2XAQak7OjMh3lw9MTCIQijdHhuiaNhbXTOAAGGoKNmZWXNA+iiZnbNcl"
            "+jZ2Vuq25ldHdvcmstdjM4omdoxCBN/+nfiNPXLbuigk8M/TXsMUfMK7dV//xB1wk"
            "oOhNu9qJsds1yw6NyY3bEIPRUuVDPVUFC7Jk3+xDjHJfwWFDp+Wjy+Hx3cwL9ncVY"
            "o3NuZMQgGC5kQiOIPooA8mrvoHRyFtk27F/PPN08bAufGhnp0BGkdHlwZaNwYXk="
        )
        self.assertEqual(
            stxn, encoding.msgpack_encode(encoding.msgpack_decode(stxn))
        )

    def test_payment_txn(self):
        paytxn = (
            "iaNhbXTOAAGGoKNmZWXNA+iiZnbNcq2jZ2Vuq25ldHdvcmstdjM4omdoxCBN/+nfi"
            "NPXLbuigk8M/TXsMUfMK7dV//xB1wkoOhNu9qJsds1zEaNyY3bEIAZ2cvp4J0OiBy"
            "5eAHIX/njaRko955rEdN4AUNEl4rxTo3NuZMQgGC5kQiOIPooA8mrvoHRyFtk27F/"
            "PPN08bAufGhnp0BGkdHlwZaNwYXk="
        )
        self.assertEqual(
            paytxn, encoding.msgpack_encode(encoding.msgpack_decode(paytxn))
        )

    def test_payment_txn_future(self):
        paytxn = (
            "iKVjbG9zZcQgYMak0FPHfqBp4So5wS5p7g+O4rLkqwo/ILSjXWQVKpGjZmVlzQPoom"
            "Z2KqNnZW6qc2FuZG5ldC12MaJnaMQgNCTHAIMgeYC+4MCSbMinkrlsgtRD6jhfJEXz"
            "IP3mH9SibHbNBBKjc25kxCARM5ng7Z1RkubT9fUef5nT9w0MGQKRGbwgOva8/tx3qqR"
            "0eXBlo3BheQ=="
        )
        self.assertEqual(
            paytxn,
            encoding.msgpack_encode(encoding.future_msgpack_decode(paytxn)),
        )

    def test_asset_xfer_txn_future(self):
        axfer = (
            "iaZhY2xvc2XEIGDGpNBTx36gaeEqOcEuae4PjuKy5KsKPyC0o11kFSqRo2ZlZc0D6KJmdi"
            "qjZ2VuqnNhbmRuZXQtdjGiZ2jEIDQkxwCDIHmAvuDAkmzIp5K5bILUQ+o4XyRF8yD95h/U"
            "omx2zQQSo3NuZMQgETOZ4O2dUZLm0/X1Hn+Z0/cNDBkCkRm8IDr2vP7cd6qkdHlwZaVheGZ"
            "lcqR4YWlkCg=="
        )
        self.assertEqual(
            axfer,
            encoding.msgpack_encode(encoding.future_msgpack_decode(axfer)),
        )

    def test_multisig_txn(self):
        msigtxn = (
            "gqRtc2lng6ZzdWJzaWeSgqJwa8Qg1ke3gkLuR0MUN/Ku0oyiRVIm9P1QFDaiEhT5v"
            "tfLmd+hc8RAIEbfnhccjWfYQFQp/P4aJjATFdgaDDpnhyJF0tU/37CO5I5hhoCvUC"
            "RH/A/6X94Ewz9YEtk5dANEGKQW+/WyAIKicGvEIKgAZfZ4iDC+UY/P5F3tgs5rqey"
            "Yt08LT0c/D78u0V7KoXPEQCxUkQgTVC9lLpKVzcZGKesSCQcZL9UjXTzrteADicvc"
            "ca7KT3WP0crGgAfJ3a17Na5cykJzFEn7pq2SHgwD/QujdGhyAqF2AaN0eG6Jo2Ftd"
            "M0D6KNmZWXNA+iiZnbNexSjZ2Vuq25ldHdvcmstdjM4omdoxCBN/+nfiNPXLbuigk"
            "8M/TXsMUfMK7dV//xB1wkoOhNu9qJsds17eKNyY3bEIBguZEIjiD6KAPJq76B0chb"
            "ZNuxfzzzdPGwLnxoZ6dARo3NuZMQgpuIJvJzW8E4uxsQGCW0S3n1u340PbHTB2zht"
            "Xo/AiI6kdHlwZaNwYXk="
        )
        self.assertEqual(
            msigtxn, encoding.msgpack_encode(encoding.msgpack_decode(msigtxn))
        )

    def test_keyreg_txn_online(self):
        keyregtxn = (
            "jKNmZWXNA+iiZnbNcoqjZ2Vuq25ldHdvcmstdjM4omdoxCBN/+nfiNPXLbuigk8M/"
            "TXsMUfMK7dV//xB1wkoOhNu9qJsds1y7qZzZWxrZXnEIBguZEIjiD6KAPJq76B0ch"
            "bZNuxfzzzdPGwLnxoZ6dARo3NuZMQgGC5kQiOIPooA8mrvoHRyFtk27F/PPN08bAu"
            "fGhnp0BGkdHlwZaZrZXlyZWendm90ZWZzdM1yiqZ2b3Rla2TNMDmndm90ZWtlecQg"
            "GC5kQiOIPooA8mrvoHRyFtk27F/PPN08bAufGhnp0BGndm90ZWxzdM1y7g=="
        )
        self.assertEqual(
            keyregtxn,
            encoding.msgpack_encode(encoding.msgpack_decode(keyregtxn)),
        )

    def test_keyreg_txn_offline(self):
        keyregtxn = (
            "hqNmZWXNA+iiZnbOALutq6JnaMQgSGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/c"
            "OUJOiKibHbOALuxk6NzbmTEIAn70nYsCPhsWua/bdenqQHeZnXXUOB+jFx2mGR9tu"
            "H9pHR5cGWma2V5cmVn"
        )
        # using future_msgpack_decode instead of msgpack_decode
        # because non-future transactions do not support offline keyreg
        self.assertEqual(
            keyregtxn,
            encoding.msgpack_encode(encoding.future_msgpack_decode(keyregtxn)),
        )

    def test_keyreg_txn_nonpart(self):
        keyregtxn = (
            "h6NmZWXNA+iiZnbOALutq6JnaMQgSGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/c"
            "OUJOiKibHbOALuxk6dub25wYXJ0w6NzbmTEIAn70nYsCPhsWua/bdenqQHeZnXXUO"
            "B+jFx2mGR9tuH9pHR5cGWma2V5cmVn"
        )
        # using future_msgpack_decode instead of msgpack_decode
        # because non-future transactions do not support nonpart keyreg
        self.assertEqual(
            keyregtxn,
            encoding.msgpack_encode(encoding.future_msgpack_decode(keyregtxn)),
        )

    def test_asset_create(self):
        golden = (
            "gqNzaWfEQEDd1OMRoQI/rzNlU4iiF50XQXmup3k5czI9hEsNqHT7K4KsfmA/0DUVk"
            "bzOwtJdRsHS8trm3Arjpy9r7AXlbAujdHhuh6RhcGFyiaJhbcQgZkFDUE80blJnTz"
            "U1ajFuZEFLM1c2U2djNEFQa2N5RmiiYW6odGVzdGNvaW6iYXWnd2Vic2l0ZaFjxCA"
            "J+9J2LAj4bFrmv23Xp6kB3mZ111Dgfoxcdphkfbbh/aFmxCAJ+9J2LAj4bFrmv23X"
            "p6kB3mZ111Dgfoxcdphkfbbh/aFtxCAJ+9J2LAj4bFrmv23Xp6kB3mZ111Dgfoxcd"
            "phkfbbh/aFyxCAJ+9J2LAj4bFrmv23Xp6kB3mZ111Dgfoxcdphkfbbh/aF0ZKJ1bq"
            "N0c3SjZmVlzQ+0omZ2zgAE7A+iZ2jEIEhjtRiks8hOyBDyLU8QgcsPcfBZp6wg3sY"
            "vf3DlCToiomx2zgAE7/ejc25kxCAJ+9J2LAj4bFrmv23Xp6kB3mZ111Dgfoxcdphk"
            "fbbh/aR0eXBlpGFjZmc="
        )
        self.assertEqual(
            golden, encoding.msgpack_encode(encoding.msgpack_decode(golden))
        )

    def test_asset_config(self):
        assettxn = (
            "gqNzaWfEQBBkfw5n6UevuIMDo2lHyU4dS80JCCQ/vTRUcTx5m0ivX68zTKyuVRrHa"
            "TbxbRRc3YpJ4zeVEnC9Fiw3Wf4REwejdHhuiKRhcGFyhKFjxCAJ+9J2LAj4bFrmv2"
            "3Xp6kB3mZ111Dgfoxcdphkfbbh/aFmxCAJ+9J2LAj4bFrmv23Xp6kB3mZ111Dgfox"
            "cdphkfbbh/aFtxCAJ+9J2LAj4bFrmv23Xp6kB3mZ111Dgfoxcdphkfbbh/aFyxCAJ"
            "+9J2LAj4bFrmv23Xp6kB3mZ111Dgfoxcdphkfbbh/aRjYWlkzQTSo2ZlZc0NSKJmd"
            "s4ABOwPomdoxCBIY7UYpLPITsgQ8i1PEIHLD3HwWaesIN7GL39w5Qk6IqJsds4ABO"
            "/3o3NuZMQgCfvSdiwI+Gxa5r9t16epAd5mdddQ4H6MXHaYZH224f2kdHlwZaRhY2Z"
            "n"
        )
        self.assertEqual(
            assettxn,
            encoding.msgpack_encode(encoding.msgpack_decode(assettxn)),
        )

    def test_asset_config_with_decimal(self):
        assettxn = (
            "gqNzaWfEQBBkfw5n6UevuIMDo2lHyU4dS80JCCQ/vTRUcTx5m0ivX68zTKyuVRrHa"
            "TbxbRRc3YpJ4zeVEnC9Fiw3Wf4REwejdHhuiKRhcGFyhaFjxCAJ+9J2LAj4bFrmv2"
            "3Xp6kB3mZ111Dgfoxcdphkfbbh/aJkYwyhZsQgCfvSdiwI+Gxa5r9t16epAd5mddd"
            "Q4H6MXHaYZH224f2hbcQgCfvSdiwI+Gxa5r9t16epAd5mdddQ4H6MXHaYZH224f2h"
            "csQgCfvSdiwI+Gxa5r9t16epAd5mdddQ4H6MXHaYZH224f2kY2FpZM0E0qNmZWXND"
            "UiiZnbOAATsD6JnaMQgSGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiKibH"
            "bOAATv96NzbmTEIAn70nYsCPhsWua/bdenqQHeZnXXUOB+jFx2mGR9tuH9pHR5cGW"
            "kYWNmZw=="
        )
        self.assertEqual(
            assettxn,
            encoding.msgpack_encode(encoding.msgpack_decode(assettxn)),
        )

    def test_asset_destroy(self):
        assettxn = (
            "gqNzaWfEQBSP7HtzD/Lvn4aVvaNpeR4T93dQgo4LvywEwcZgDEoc/WVl3aKsZGcZk"
            "cRFoiWk8AidhfOZzZYutckkccB8RgGjdHhuh6RjYWlkAaNmZWXNB1iiZnbOAATsD6"
            "JnaMQgSGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiKibHbOAATv96NzbmT"
            "EIAn70nYsCPhsWua/bdenqQHeZnXXUOB+jFx2mGR9tuH9pHR5cGWkYWNmZw=="
        )
        self.assertEqual(
            assettxn,
            encoding.msgpack_encode(encoding.msgpack_decode(assettxn)),
        )

    def test_asset_freeze(self):
        assettxn = (
            "gqNzaWfEQAhru5V2Xvr19s4pGnI0aslqwY4lA2skzpYtDTAN9DKSH5+qsfQQhm4oq"
            "+9VHVj7e1rQC49S28vQZmzDTVnYDQGjdHhuiaRhZnJ6w6RmYWRkxCAJ+9J2LAj4bF"
            "rmv23Xp6kB3mZ111Dgfoxcdphkfbbh/aRmYWlkAaNmZWXNCRqiZnbOAATsD6JnaMQ"
            "gSGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiKibHbOAATv+KNzbmTEIAn7"
            "0nYsCPhsWua/bdenqQHeZnXXUOB+jFx2mGR9tuH9pHR5cGWkYWZyeg=="
        )
        self.assertEqual(
            assettxn,
            encoding.msgpack_encode(encoding.msgpack_decode(assettxn)),
        )

    def test_asset_transfer(self):
        assettxn = (
            "gqNzaWfEQNkEs3WdfFq6IQKJdF1n0/hbV9waLsvojy9pM1T4fvwfMNdjGQDy+Lees"
            "uQUfQVTneJD4VfMP7zKx4OUlItbrwSjdHhuiqRhYW10AaZhY2xvc2XEIAn70nYsCP"
            "hsWua/bdenqQHeZnXXUOB+jFx2mGR9tuH9pGFyY3bEIAn70nYsCPhsWua/bdenqQH"
            "eZnXXUOB+jFx2mGR9tuH9o2ZlZc0KvqJmds4ABOwPomdoxCBIY7UYpLPITsgQ8i1P"
            "EIHLD3HwWaesIN7GL39w5Qk6IqJsds4ABO/4o3NuZMQgCfvSdiwI+Gxa5r9t16epA"
            "d5mdddQ4H6MXHaYZH224f2kdHlwZaVheGZlcqR4YWlkAQ=="
        )
        self.assertEqual(
            assettxn,
            encoding.msgpack_encode(encoding.msgpack_decode(assettxn)),
        )

    def test_asset_accept(self):
        assettxn = (
            "gqNzaWfEQJ7q2rOT8Sb/wB0F87ld+1zMprxVlYqbUbe+oz0WM63FctIi+K9eYFSqT"
            "26XBZ4Rr3+VTJpBE+JLKs8nctl9hgijdHhuiKRhcmN2xCAJ+9J2LAj4bFrmv23Xp6"
            "kB3mZ111Dgfoxcdphkfbbh/aNmZWXNCOiiZnbOAATsD6JnaMQgSGO1GKSzyE7IEPI"
            "tTxCByw9x8FmnrCDexi9/cOUJOiKibHbOAATv96NzbmTEIAn70nYsCPhsWua/bden"
            "qQHeZnXXUOB+jFx2mGR9tuH9pHR5cGWlYXhmZXKkeGFpZAE="
        )
        self.assertEqual(
            assettxn,
            encoding.msgpack_encode(encoding.msgpack_decode(assettxn)),
        )

    def test_asset_revoke(self):
        assettxn = (
            "gqNzaWfEQHsgfEAmEHUxLLLR9s+Y/yq5WeoGo/jAArCbany+7ZYwExMySzAhmV7M7"
            "S8+LBtJalB4EhzEUMKmt3kNKk6+vAWjdHhuiqRhYW10AaRhcmN2xCAJ+9J2LAj4bF"
            "rmv23Xp6kB3mZ111Dgfoxcdphkfbbh/aRhc25kxCAJ+9J2LAj4bFrmv23Xp6kB3mZ"
            "111Dgfoxcdphkfbbh/aNmZWXNCqqiZnbOAATsD6JnaMQgSGO1GKSzyE7IEPItTxCB"
            "yw9x8FmnrCDexi9/cOUJOiKibHbOAATv96NzbmTEIAn70nYsCPhsWua/bdenqQHeZ"
            "nXXUOB+jFx2mGR9tuH9pHR5cGWlYXhmZXKkeGFpZAE="
        )
        self.assertEqual(
            assettxn,
            encoding.msgpack_encode(encoding.msgpack_decode(assettxn)),
        )


class TestSignBytes(unittest.TestCase):
    def test_sign(self):
        sk, pk = account.generate_account()
        message = bytes([random.randint(0, 255) for x in range(15)])
        signature = util.sign_bytes(message, sk)
        self.assertTrue(util.verify_bytes(message, signature, pk))

    def test_verify_negative(self):
        sk, pk = account.generate_account()
        intarray = [random.randint(0, 255) for x in range(15)]
        message = bytes(intarray)
        signature = util.sign_bytes(message, sk)
        intarray[0] = (intarray[0] + 1) % 256
        changed_message = bytes(intarray)
        self.assertFalse(util.verify_bytes(changed_message, signature, pk))
        # Check that wrong number of bytes returns false in verify function.
        self.assertFalse(util.verify_bytes(bytes(), signature, pk))


class TestLogic(unittest.TestCase):
    def test_parse_uvarint(self):
        data = b"\x01"
        value, length = logic.parse_uvarint(data)
        self.assertEqual(length, 1)
        self.assertEqual(value, 1)

        data = b"\x7b"
        value, length = logic.parse_uvarint(data)
        self.assertEqual(length, 1)
        self.assertEqual(value, 123)

        data = b"\xc8\x03"
        value, length = logic.parse_uvarint(data)
        self.assertEqual(length, 2)
        self.assertEqual(value, 456)

    def test_parse_intcblock(self):
        data = b"\x20\x05\x00\x01\xc8\x03\x7b\x02"
        size = logic.check_int_const_block(data, 0)
        self.assertEqual(size, len(data))

    def test_parse_bytecblock(self):
        data = (
            b"\x26\x02\x0d\x31\x32\x33\x34\x35\x36\x37\x38\x39\x30\x31"
            b"\x32\x33\x02\x01\x02"
        )
        size = logic.check_byte_const_block(data, 0)
        self.assertEqual(size, len(data))

    def test_parse_pushint(self):
        data = b"\x81\x80\x80\x04"
        size = logic.check_push_int_block(data, 0)
        self.assertEqual(size, len(data))

    def test_parse_pushbytes(self):
        data = b"\x80\x0b\x68\x65\x6c\x6c\x6f\x20\x77\x6f\x72\x6c\x64"
        size = logic.check_push_byte_block(data, 0)
        self.assertEqual(size, len(data))

    def test_check_program(self):
        program = b"\x01\x20\x01\x01\x22"  # int 1
        self.assertTrue(logic.check_program(program, None))

        self.assertTrue(logic.check_program(program, ["a" * 10]))

        # too long arg
        with self.assertRaises(error.InvalidProgram):
            logic.check_program(program, ["a" * 1000])

        program += b"\x22" * 10
        self.assertTrue(logic.check_program(program, None))

        # too long program
        program += b"\x22" * 1000
        with self.assertRaises(error.InvalidProgram):
            logic.check_program(program, [])

        # invalid opcode
        program = b"\x01\x20\x01\x01\x81"
        with self.assertRaises(error.InvalidProgram):
            logic.check_program(program, [])

        # check single keccak256 and 10x keccak256 work
        program = b"\x01\x26\x01\x01\x01\x01\x28\x02"  # byte 0x01 + keccak256
        self.assertTrue(logic.check_program(program, []))

        program += b"\x02" * 10
        self.assertTrue(logic.check_program(program, None))

        # check 800x keccak256 fail for v3 and below
        versions = [b"\x01", b"\x02", b"\x03"]
        program += b"\x02" * 800
        for v in versions:
            programv = v + program
            with self.assertRaises(error.InvalidProgram):
                logic.check_program(programv, [])

        versions = [b"\x04"]
        for v in versions:
            programv = v + program
            self.assertTrue(logic.check_program(programv, None))

    def test_check_program_teal_2(self):
        # check TEAL v2 opcodes
        self.assertIsNotNone(
            logic.spec, "Must be called after any of logic.check_program"
        )
        self.assertTrue(logic.spec["EvalMaxVersion"] >= 2)
        self.assertTrue(logic.spec["LogicSigVersion"] >= 2)

        # balance
        program = b"\x02\x20\x01\x00\x22\x60"  # int 0; balance
        self.assertTrue(logic.check_program(program, None))

        # app_opted_in
        program = b"\x02\x20\x01\x00\x22\x22\x61"  # int 0; int 0; app_opted_in
        self.assertTrue(logic.check_program(program, None))

        # asset_holding_get
        program = b"\x02\x20\x01\x00\x22\x22\x70\x00"  # int 0; int 0; asset_holding_get Balance
        self.assertTrue(logic.check_program(program, None))

    def test_check_program_teal_3(self):
        # check TEAL v2 opcodes
        self.assertIsNotNone(
            logic.spec, "Must be called after any of logic.check_program"
        )
        self.assertTrue(logic.spec["EvalMaxVersion"] >= 3)
        self.assertTrue(logic.spec["LogicSigVersion"] >= 3)

        # min_balance
        program = b"\x03\x20\x01\x00\x22\x78"  # int 0; min_balance
        self.assertTrue(logic.check_program(program, None))

        # pushbytes
        program = b"\x03\x20\x01\x00\x22\x80\x02\x68\x69\x48"  # int 0; pushbytes "hi"; pop
        self.assertTrue(logic.check_program(program, None))

        # pushint
        program = b"\x03\x20\x01\x00\x22\x81\x01\x48"  # int 0; pushint 1; pop
        self.assertTrue(logic.check_program(program, None))

        # swap
        program = (
            b"\x03\x20\x02\x00\x01\x22\x23\x4c\x48"  # int 0; int 1; swap; pop
        )
        self.assertTrue(logic.check_program(program, None))

    def test_teal_sign(self):
        """test tealsign"""
        data = base64.b64decode("Ux8jntyBJQarjKGF8A==")
        seed = base64.b64decode("5Pf7eGMA52qfMT4R4/vYCt7con/7U3yejkdXkrcb26Q=")
        program = base64.b64decode("ASABASI=")
        addr = "6Z3C3LDVWGMX23BMSYMANACQOSINPFIRF77H7N3AWJZYV6OH6GWTJKVMXY"

        key = SigningKey(seed)
        verify_key = key.verify_key
        private_key = base64.b64encode(
            key.encode() + verify_key.encode()
        ).decode()
        sig1 = logic.teal_sign(private_key, data, addr)
        sig2 = logic.teal_sign_from_program(private_key, data, program)
        self.assertEqual(sig1, sig2)

        msg = (
            constants.logic_data_prefix + encoding.decode_address(addr) + data
        )
        res = verify_key.verify(msg, sig1)
        self.assertIsNotNone(res)

    def test_check_program_teal_4(self):
        # check TEAL v4 opcodes
        self.assertIsNotNone(
            logic.spec, "Must be called after any of logic.check_program"
        )
        self.assertTrue(logic.spec["EvalMaxVersion"] >= 4)

        # divmodw
        program = b"\x04\x20\x03\x01\x00\x02\x22\x81\xd0\x0f\x23\x24\x1f"  # int 1; pushint 2000; int 0; int 2; divmodw
        self.assertTrue(logic.check_program(program, None))

        # gloads i
        program = b"\x04\x20\x01\x00\x22\x3b\x00"  # int 0; gloads 0
        self.assertTrue(logic.check_program(program, None))

        # callsub
        program = b"\x04\x20\x02\x01\x02\x22\x88\x00\x02\x23\x12\x49"  # int 1; callsub double; int 2; ==; double: dup;
        self.assertTrue(logic.check_program(program, None))

        # b>=
        program = b"\x04\x26\x02\x01\x11\x01\x10\x28\x29\xa7"  # byte 0x11; byte 0x10; b>=
        self.assertTrue(logic.check_program(program, None))

        # b^
        program = b"\x04\x26\x03\x01\x11\x01\x10\x01\x01\x28\x29\xad\x2a\x12"  # byte 0x11; byte 0x10; b>=
        self.assertTrue(logic.check_program(program, None))

        # callsub, retsub
        program = b"\x04\x20\x02\x01\x02\x22\x88\x00\x03\x23\x12\x43\x49\x08\x89"  # int 1; callsub double; int 2; ==; return; double: dup; +; retsub;
        self.assertTrue(logic.check_program(program, None))

        # loop
        program = b"\x04\x20\x04\x01\x02\x0a\x10\x22\x23\x0b\x49\x24\x0c\x40\xff\xf8\x25\x12"  # int 1; loop: int 2; *; dup; int 10; <; bnz loop; int 16; ==
        self.assertTrue(logic.check_program(program, None))

    def test_check_program_teal_5(self):
        # check TEAL v5 opcodes
        self.assertIsNotNone(
            logic.spec, "Must be called after any of logic.check_program"
        )
        self.assertTrue(logic.spec["EvalMaxVersion"] >= 5)

        # itxn ops
        program = b"\x05\x20\x01\xc0\x84\x3d\xb1\x81\x01\xb2\x10\x22\xb2\x08\x31\x00\xb2\x07\xb3\xb4\x08\x22\x12"
        # itxn_begin; int pay; itxn_field TypeEnum; int 1000000; itxn_field Amount; txn Sender; itxn_field Receiver; itxn_submit; itxn Amount; int 1000000; ==
        self.assertTrue(logic.check_program(program, None))

        # ECDSA ops
        program = bytes.fromhex(
            "058008746573746461746103802079bfa8245aeac0e714b7bd2b3252d03979e5e7a43cb039715a5f8109a7dd9ba180200753d317e54350d1d102289afbde3002add4529f10b9f7d3d223843985de62e0802103abfb5e6e331fb871e423f354e2bd78a384ef7cb07ac8bbf27d2dd1eca00e73c106000500"
        )
        # byte "testdata"; sha512_256; byte 0x79bfa8245aeac0e714b7bd2b3252d03979e5e7a43cb039715a5f8109a7dd9ba1; byte 0x0753d317e54350d1d102289afbde3002add4529f10b9f7d3d223843985de62e0; byte 0x03abfb5e6e331fb871e423f354e2bd78a384ef7cb07ac8bbf27d2dd1eca00e73c1; ecdsa_pk_decompress Secp256k1; ecdsa_verify Secp256k1
        self.assertTrue(logic.check_program(program, None))

        # cover, uncover, log
        program = b"\x05\x80\x01\x61\x80\x01\x62\x80\x01\x63\x4e\x02\x4f\x02\x50\x50\xb0\x81\x01"
        # byte "a"; byte "b"; byte "c"; cover 2; uncover 2; concat; concat; log; int 1
        self.assertTrue(logic.check_program(program, None))

    def test_check_program_teal_6(self):
        # check TEAL v6 opcodes

        self.assertIsNotNone(
            logic.spec, "Must be called after any of logic.check_program"
        )
        self.assertTrue(logic.spec["EvalMaxVersion"] >= 6)

        # bsqrt
        program = b"\x06\x80\x01\x90\x96\x80\x01\x0c\xa8"
        # byte 0x90; bsqrt; byte 0x0c; b==
        self.assertTrue(logic.check_program(program, None))

        # divw
        program = b"\x06\x81\x09\x81\xec\xff\xff\xff\xff\xff\xff\xff\xff\x01\x81\x0a\x97\x81\xfe\xff\xff\xff\xff\xff\xff\xff\xff\x01\x12"
        # int 9; int 18446744073709551596; int 10; divw; int 18446744073709551614; ==
        self.assertTrue(logic.check_program(program, None))

        # txn fields
        program = (
            b"\x06\x31\x3f\x15\x81\x40\x12\x33\x00\x3e\x15\x81\x0a\x12\x10"
        )
        # txn StateProofPK; len; int 64; ==; gtxn 0 LastLog; len; int 10; ==; &&
        self.assertTrue(logic.check_program(program, None))
