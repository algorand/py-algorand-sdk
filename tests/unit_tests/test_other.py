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

    def test_stateproof_txn(self):
        stateprooftxn = (
            "gqNzaWfEQHsgfEAmEHUxLLLR9s+Y/yq5WeoGo/jAArCbany+7ZYwExMySzAhmV7M7S8"
            "+LBtJalB4EhzEUMKmt3kNKk6+vAWjdHhuh6Jmds0CaaJnaMQgSGO1GKSzyE7IEPItTx"
            "CByw9x8FmnrCDexi9/cOUJOiKibHbNBlGjc25kxCC7PFJiqdXHTSAn46fq5Nb/cM9sT"
            "OTF4FfBHtOblTRCBaJzcIahUIKjaHNogaF0AaJ0ZAGhU4KjaHNogaF0AaJ0ZAGhY8RA"
            "dWo+1yk/97WVvXRuLLyywild8Xe6PxjtmuB/lShfdOXs0Au7Q67KkT5LzC88hX5fFvj"
            "Bx/AqKREhoEd14JiTt6JwctwAlAAAAAAAAAAAAQAAAAABAQAAAAAAAAAAAAAAAQAAAA"
            "AAAAEAAAAAAAAAAAAAAQAAAAABAAABAQEAAAAAAAABAAEAAAAAAAEAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAEAAQABAAEBAAABAAAAAAAAAAEAAAAAAQAAAAABAAAA"
            "AAAAAAEAAAAAAAAAAQAAAAChcoKhMIKhcIKhcIKjY210xECJ3vxgEUPuCXmKeJQmasV"
            "fhmraJZoVu+p8MTJc6EzU4PGZWuxd6DU80//HXDfVCImipmSQhSwkNEmea+Pg0lMwom"
            "xmzQEAoXfPAA41/zsxyAChc4Ghc4SjaWR4AqNwcmaDo2hzaIGhdAGjcHRolNlYeEFKc"
            "TJhL1ZITzA0NG1iYjBmZlZpeDE4dk5jYUdZNDFWbDh0VytIVDEzcEJmcDlTdjVWaitz"
            "SHFSTUs5OW9GNU53SWlFM2ljRGRoNlhZL2d1eHRNdXc9PdlYZkVRTzFvSmpBNXZiSmZ"
            "MT2JIQlNNQ3pqYkNDODZ1aVlJNUNDdW9yaDdFNEJlRTlSZFVjYmRqVkE1VWFDOHIzan"
            "padjlseU95UmVVdjZVQUluN283cWc9PdlYNTNnZDBuM09LVU9yYXJNcG1SdnJ5UE8wc"
            "Vpqb3V5c1BPVHVuQ2NTUnZRdG1BR1N6dllDWUZqYmxGZXZ0c3JQVUtYbnI0cGFWZXcy"
            "V21Hb2tZSFVXOVE9PdlYZUZtME5iQlpaYlp0NzliS3JhblU5UUFCUnFldVhoOEk4Ry9"
            "qNkZ6NmJsRE1NQmwvWkpMSFNMUEVpVmU0UkQzVkp6d1Y4Nyt4NHl1NGEzdDZnQW5rcl"
            "E9PaJ0ZASjc2lnxQTOugB5kmml+p3OT2CTyptlHbu4StA4uMw18AmTGSjOHby//nkdx"
            "yQKLAGGWCUMh97xgeiNo48bWTg7qZWXP+/KHQlVOhJSsEZvUEejaBiFiXdZEcfDnMdN"
            "y8CjpvG76mmlMTiEaRuNorePq4OXMuRK0XFvIVZ7FStnkXLoaBk3IHm8nAOX9ONzEIm"
            "/jmVKyQ50ruDUKcsJrZXkkrSfcuTMPRGktZDftS0dl3whEj67KHLf7vO3MVmTgi94iD"
            "BjPMswf+m6fWVnjmKlwlb8PAG3EkRrBocQdUuJv1i0akuXtznVKaaccJ2kWGkTK/xB0"
            "Gj01u97hrLtne3hNY+rbicjc/hT2tju8fJOY01BCzgpMauHpPSKDMo/01dgHv+E/0KY"
            "tLRT12byyWNxh5F6mCYYjDxiopJZM8JhA8+yyGerBpckNXLMmmPcR7ICTV18Rrt/bA0"
            "jXKcY1gik+VH4ahh2G97cwZDOW11+7WGZbnmdjoYa5mGJRlnmamJkWuZ7cp/bD3tJmr"
            "nLSnKO4b6aGMCBnPJVo4PgmFafOlKnRh/pNeMhhc7Uq8xuGi9uJKdmVKOjqqdhzCIDw"
            "lKhsdqO4N9DOt28vGGlZGasZg24kZKx/7oxBMYtTnv/mF/+WZvZ4dTmjbubqdMkbi/n"
            "8fauUr3Vq5vxzFBpMIIURVLNXTm5snvRlsVgYak3JPhMk92J6r9kYmmixz3mJUzS3aD"
            "OuhP1x/HssSQEjQSJ/AsCZFI2x3obzIZoJk8zS5ZRkeYQ9Frl7pqxGU+Zw0NI2ju7L3"
            "KsrnmSJUaQr1fPCn3JfQnxg6NV0GLDgR7U34FbiFXRCgqawJaYhWn9z8ycvvX2z/1EV"
            "X4HUvt/K1hj/Qx5Q1KRYNZcr5E0b4TGUJHzJyy5uZm7sKKJQsLhPaSqYM7TVzuUVVS1"
            "fbDDMrRdP/BW79Gmdnd5dZ/JnYagaFGZllq8XLr9WqphtBtCNnEMp6rN/vzvJlA75on"
            "00ieZM2vpblLX66yo6IKLM40QZq4/62mEmJm+2n4LrZxWaaqR44ZP8XpKMyVzTiPYN0"
            "Fz7VIf46SUbtKDFLgzcr05nG2m07ZJYdLEHSMVjG36fmx7uoRkNzAarROL9dYyCx2vY"
            "MkxK555xZcqBRIfC3281BErhOgVFiIRMZeaHXeeISTMRHJZNR+ZecfjHySlVEOjGQ8z"
            "bY6fUtnUBhmm8azJPpYb1maT2iXGURF5om89C/9dq+Onr8QKINJJo7FvnSMjudAnHQs"
            "d6v/y/UKYE1mteWeOWhUNTxRBjM+iTMnQ5MNMLUXQ1qOZpgZE5GDUi5yHEY77HZa9V7"
            "YVAuMHQYYQ7FNsW0WkTwxIg8hLHkYKvsVNWnqqsbGd756xvWN9vrHR3fj8UhQj/TlNn"
            "An8uaf+TjKpvhJQlYznIYmIQepmkjeNodsxMcUVQDk5uC4akyCJwOeYWf+UXiWX72QN"
            "mkOW9RVJ/8K98f3bgCHy74t57M5NyE5vQs8u0GYKo02EQD5QWF4ul1vlIInkV8dB/yP"
            "rkoP08Jd9V6PF0UVii37d89NKUCZjz7Bpa86gjPwWPSmJbUyhCYbUI1rVwo0SJkiERT"
            "SfQtdPJGyJKhx0g2xECUIs3/SpslWPDJyVv72o7zPJQzOIqZKopHZrZXmBoWvFBwEKh"
            "IUZpbAkfnICuvtinX4VzrxVmCVTC84CmEwLwAIAMzVJr/pO8OjLCsLGhEhykCNENZtp"
            "9PWxk4uyaVwj82bhCRZhqPnJ+CcZTzXmne8XpMOWvOa9qc4RqTwTKCDQN4I/bB2Wyhb"
            "bhqU6vHIcOAoRxyGtFva7ILcRScpp4m0EZ0a5i4hXCh44ipLgwpC55qDqSSishPwPeL"
            "lMoZLUOrDZzLMAnZQo/Rw+AxVt88wr/I1l5BIYi09yLQfioRllLqq4E65f7bmVtSher"
            "/SCRilqoiFGekQthCCEg4U+3qvFouRlrMIlBuW9OjDfStreBYRJQ1WdSI4xuAQlz4id"
            "nw5ItDPS8lJu6UpqBnlNEhjjyGy7EM57c6QGI4kJBsVmrsiA+Rj3amBNLpyPwQssjHN"
            "oEXeIL5oTKo1omQbjWc0ReetPqwMJwTdPXkt0uF3wNWQ+Md2Q+Z8ekVNCExDyECt09j"
            "E44FfHvS0WtnBJoE7RAnaoHT426HcQ3MXSMA39g3qG3Z9W5lKvp46LHTi3i05cP4Lcw"
            "XFS/XIaiHUYBhWWCIhnhF7hoeqTicDKOlZxDWb3VrBpPn1UNpQ2stDd8U3dAlSpTUh7"
            "kd2fNn/R5w5oJ7VVl1gdli8OVIsKlz+kkDxhkBVhN7bVNAKrNiui7HZuDjW1HmM4xRc"
            "fZLGvSxavmFuMj4E/ZiUXCGgygK/CLH7CpzisJFDu5Qg1brsUUEIJbRp9bNIetUMqF4"
            "6i0pcTxskIEfhJt4twXrqWwfNHmH4+M4trS3ZcbPRywaYlH1FvGTye9aVV9SDamTWPW"
            "fh0EcRBp+B5Iw2O0LtypFjvQzlxcDMC5htWY6RBmxMdswCCcqU2CHMMuDrU96U8MpAX"
            "Cizov3xYUquX5GJMXDsr9ECjJ7CqSO+jMJAqI3kFHIqmbHkLJuBoY3JM9bot0bLYrot"
            "S6rcXgRAajNu4J3XuhGZOgHyxHSJ3j8WnajbWZZARNYRWAEUWjnOlSUF5QMUliMZipc"
            "NFPfb2+QCcbbzS7kUUw4RhMiWFKJxHsZzy1Wck/3+k1kDmVPeYYGoi14Qwb4q6yVwL4"
            "DCua/NWpIZrkW7IeFVsM7zdhjusULXWXYcO7PSWDI2Gzo5INIARQ2VjVGSWxeG90Gmu"
            "Nvgyh+gMWMgvolgtXHeZayiBErW3le3p76u3pg6bmEsYekqlb/LoKw1BDFK5UkmLhIg"
            "t03Lv9Kqh4RPoUDIEPctH6QeMFQFUgrIpqJfsn7A3XaVf2OyJRBUGdKzi0/0f/W0iwB"
            "U6E0ao8SzoKyyAYY3dS3wnD0B6SqU5RPWG8H8wZgaXC3RC4ZhFfwgo1+J+JE4/LCGaY"
            "wlME8bGCWFTzAS++MjBGPyJEtmCagneDPWJVLZA0wDaTelNwwM2dQiaZlV2FZGdA+8N"
            "OqzWDWjxUQArgIE6sINXetUbwOPoDr5S3RZpErmRYASJcozUL4nMGFxDxk/0C9fyCss"
            "rFR/ITuJaNLwvcP7XKZqa08OkwG8yoVBqhW5ksBj/pwOsBE71+7iYIwmF0e+oRaysBX"
            "U3iGgFjj3N8sL3l/FKaoimbgXrtqjVlmoHL7UiZMuEkARfkpgZ1BwKN35EQ/6WtWW9X"
            "OjjiMyvyLoDUZAfEdpQmp2sTzlWhBgcgBFBYD7QTGJoNh6+s7EKSQPw4QPZpS8uQIaV"
            "p50bY56ECrkenbz93WTvL89IXOLD4EDcYAycsZRCTH9E8iEdGQRKbm4Ks962KRFBUnM"
            "NqxLUURUMUjugUMIrnUGuXGg6MJTXCh3mn+TNl1mKGQn3fZ7ksFo9ND+ZTFSlwOE728"
            "cQ2H+Ao9quqYxvdmIWEDeuVDCVSbJYptNoHsu2fxiI4fRDRQNdUuTwypiBgQa6NaunL"
            "aAaA4Bs8r7sYURv6j0aJEYhishCaL6KNqrF+DYRJPZyiYcWJMHL0yPISAk9KYCW9gtM"
            "2IEfp8R5UliCvt3pEQyD5vXZthr89CNAiQElwMdCAA8iULb+8KoXBVriAFdm7M+HiLg"
            "7TZJbsZFoN1XerqvoyTOmIT0vKUcYLuMOOBzAUd4oGENxzWDhV1eO4sTzvaD9tEFO9c"
            "6k/Bx82BAC6HlBRVXLXJOxMPpNmqCpxKrE18bBAc9dfjkkS80rtJkBJ0opIzQx8YEoH"
            "QQcxstQa5L1UUbYGmpnqIGZY9XKwC4mYFBEtJxIM0RE8y2Ra0FJcIMeHQ8pJpjybW69"
            "XfIY+gBjona956scDOp10u/wPytquIjvOwFUM47Gm5cqS0QwUWMz1d/WCVwF627hlbw"
            "QDKis6EG54MnJlA/oOrCxEGiBZpusf7LB2vUWzd2nd23ZFzp6U4oQR7D0AKllo7tQgk"
            "pDVe0jgbp3CjJCX6T4CcFGX3tv0BvhtKp7Qk7gaScuZaExgqFwgqFwgqNjbXTEQNkzH"
            "iRX8wGA8aHIiiQS5KYeZps0Ek70Cb5dfULAvUKx/Zlienia5CW4EaV3JTD06XCsQKpw"
            "hgbahcYTgjzNVg+ibGbNAQChd88AA41/zsxyAKFzgqFszwAONf87McgAoXOEo2lkeAK"
            "jcHJmg6Noc2iBoXQBo3B0aJTZWDFIZ3d6d0VibUxCdEU2RGx3RVZwd0hyTTNhMEY1UW"
            "13aVFNdklqTndrdHJleXJwNW5Cc0xCcGlsSTJ3OW5DWERYVDlobW1SNFFRNG9Fcm51Z"
            "XN5S2lRPT3ZWERmTW91R0dkNUZUNlFJZkE5cXF6ci9vNDBRYWNzc25vdGh0RncvUHo4"
            "MHFRQ3QxUG1nNWFCZjZOcnhaLzRMaEtSb1I1Q2hQQitPVW5nOGNtZGRZQnVnPT3ZWDV"
            "UMEk2UDBHSHY5cm1vTlVteC9jMXllY3QwMlFvR3UxLy9sSFYyZEhxTHVEaXFmeTVrak"
            "1VU2xBR1Q1YSs3bzdiZzhDYk5VMnlpUmVIMjhRNnZQcWNBPT3ZWGhYT05jQVZ0cHpCe"
            "DR0dHE4ZVJOWUhkNy9TcmEzSEJQd01HR1hXcnNSNEtxVTdtRkk5UURpSEU2MDlMd0RE"
            "Nk1DYktXNWt2VnJsSVlzRWgvRWxMcERnPT2idGQEo3NpZ8UEzroApUZQwaeHxrhrTqd"
            "7aJVAazbex5N6mFD56ayeJPkqFA2BUMwvda3qNqG4vs+3pQ7KuWR2MtDCvYMS7cio1v"
            "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"
            "c3RwZg=="
        )

        self.assertEqual(
            stateprooftxn,
            encoding.msgpack_encode(
                encoding.future_msgpack_decode(stateprooftxn)
            ),
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

    def test_check_program_avm_2(self):
        # check AVM v2 opcodes
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

    def test_check_program_avm_3(self):
        # check AVM v2 opcodes
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

    def test_check_program_avm_4(self):
        # check AVM v4 opcodes
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

    def test_check_program_avm_5(self):
        # check AVM v5 opcodes
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

    def test_check_program_avm_6(self):
        # check AVM v6 opcodes

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


class TestEncoding(unittest.TestCase):
    """
    Miscellaneous unit tests for functions in `encoding.py` not covered elsewhere
    """

    def test_encode_as_bytes(self):
        bs = b"blahblah"
        assert bs == encoding.encode_as_bytes(bs)

        ba = bytearray("blueblue", "utf-8")
        assert ba == encoding.encode_as_bytes(ba)

        s = "i am a ho hum string"
        assert s.encode() == encoding.encode_as_bytes(s)

        i = 42
        assert i.to_bytes(8, "big") == encoding.encode_as_bytes(i)

        for bad_type in [
            13.37,
            type(self),
            None,
            {"hi": "there"},
            ["hello", "goodbye"],
        ]:
            with pytest.raises(TypeError) as te:
                encoding.encode_as_bytes(bad_type)

            assert f"{bad_type} is not bytes, bytearray, str, or int" == str(
                te.value
            )
