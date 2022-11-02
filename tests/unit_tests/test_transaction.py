import base64
import copy
import os
import unittest
import uuid

from algosdk import account, constants, encoding, error, logic, mnemonic
from algosdk.future import transaction


class TestPaymentTransaction(unittest.TestCase):
    def test_min_txn_fee(self):
        address = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
        gh = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
        sp = transaction.SuggestedParams(0, 1, 100, gh)
        txn = transaction.PaymentTxn(address, sp, address, 1000, note=b"\x00")
        self.assertEqual(constants.min_txn_fee, txn.fee)

    def test_zero_txn_fee(self):
        address = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
        gh = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
        sp = transaction.SuggestedParams(0, 1, 100, gh, flat_fee=True)
        txn = transaction.PaymentTxn(address, sp, address, 1000, note=b"\x00")
        self.assertEqual(0, txn.fee)

    def test_txn_flat_fee(self):
        address = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
        gh = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
        sp = transaction.SuggestedParams(100, 1, 100, gh, flat_fee=True)
        txn = transaction.PaymentTxn(address, sp, address, 1000, note=b"\x00")
        self.assertEqual(100, txn.fee)

    def test_note_wrong_type(self):
        address = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
        gh = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
        sp = transaction.SuggestedParams(0, 1, 100, gh)
        f = lambda: transaction.PaymentTxn(address, sp, address, 1000, note=45)
        self.assertRaises(error.WrongNoteType, f)

    def test_note_strings_allowed(self):
        address = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
        gh = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
        sp = transaction.SuggestedParams(0, 1, 100, gh)
        txn = transaction.PaymentTxn(address, sp, address, 1000, note="helo")
        self.assertEqual(constants.min_txn_fee, txn.fee)

    def test_note_wrong_length(self):
        address = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
        gh = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
        sp = transaction.SuggestedParams(0, 1, 100, gh)
        f = lambda: transaction.PaymentTxn(
            address, sp, address, 1000, note=("0" * 1025).encode()
        )
        self.assertRaises(error.WrongNoteLength, f)

    def test_leases(self):
        address = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
        gh = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
        sp = transaction.SuggestedParams(0, 1, 100, gh)
        # 32 byte zero lease should be dropped from msgpack
        txn1 = transaction.PaymentTxn(
            address, sp, address, 1000, lease=(b"\0" * 32)
        )
        txn2 = transaction.PaymentTxn(address, sp, address, 1000)

        self.assertEqual(txn1.dictify(), txn2.dictify())
        self.assertEqual(txn1, txn2)
        self.assertEqual(txn2, txn1)

    def test_serialize(self):
        address = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
        gh = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
        sp = transaction.SuggestedParams(3, 1, 100, gh)
        txn = transaction.PaymentTxn(
            address, sp, address, 1000, note=bytes([1, 32, 200])
        )
        enc = encoding.msgpack_encode(txn)
        re_enc = encoding.msgpack_encode(encoding.msgpack_decode(enc))
        self.assertEqual(enc, re_enc)

    def test_serialize_with_note_string_encode(self):
        address = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
        gh = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
        sp = transaction.SuggestedParams(3, 1, 100, gh)
        txn = transaction.PaymentTxn(
            address, sp, address, 1000, note="hello".encode()
        )
        enc = encoding.msgpack_encode(txn)
        re_enc = encoding.msgpack_encode(encoding.msgpack_decode(enc))
        self.assertEqual(enc, re_enc)

    def test_serialize_with_note_max_length(self):
        address = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
        gh = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
        sp = transaction.SuggestedParams(3, 1, 100, gh)
        txn = transaction.PaymentTxn(
            address, sp, address, 1000, note=("0" * 1024).encode()
        )
        enc = encoding.msgpack_encode(txn)
        re_enc = encoding.msgpack_encode(encoding.msgpack_decode(enc))
        self.assertEqual(enc, re_enc)

    def test_serialize_zero_amt(self):
        address = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
        gh = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
        sp = transaction.SuggestedParams(3, 1, 100, gh)
        txn = transaction.PaymentTxn(
            address, sp, address, 0, note=bytes([1, 32, 200])
        )
        enc = encoding.msgpack_encode(txn)
        re_enc = encoding.msgpack_encode(encoding.msgpack_decode(enc))
        self.assertEqual(enc, re_enc)

    def test_serialize_gen(self):
        address = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
        gh = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
        sp = transaction.SuggestedParams(3, 1, 100, gh, "testnet-v1.0")
        txn = transaction.PaymentTxn(
            address, sp, address, 1000, close_remainder_to=address
        )
        enc = encoding.msgpack_encode(txn)
        re_enc = encoding.msgpack_encode(encoding.msgpack_decode(enc))
        self.assertEqual(enc, re_enc)

    def test_serialize_txgroup(self):
        address = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
        gh = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
        sp = transaction.SuggestedParams(3, 1, 100, gh, "testnet-v1.0")
        txn = transaction.PaymentTxn(
            address, sp, address, 1000, close_remainder_to=address
        )
        txid = txn.get_txid().encode()
        txid = base64.decodebytes(txid)

        txgroup = transaction.TxGroup([txid])
        enc = encoding.msgpack_encode(txgroup)
        re_enc = encoding.msgpack_encode(encoding.msgpack_decode(enc))
        self.assertEqual(enc, re_enc)

        txgroup = transaction.TxGroup([txid] * 11)
        enc = encoding.msgpack_encode(txgroup)
        re_enc = encoding.msgpack_encode(encoding.msgpack_decode(enc))
        self.assertEqual(enc, re_enc)

        # check group field serialization
        gid = transaction.calculate_group_id([txn, txn])
        txn.group = gid
        enc = encoding.msgpack_encode(txn)
        re_enc = encoding.msgpack_encode(encoding.msgpack_decode(enc))
        self.assertEqual(enc, re_enc)

    def test_sign(self):
        mn = (
            "advice pudding treat near rule blouse same whisper inner electric"
            " quit surface sunny dismiss leader blood seat clown cost exist ho"
            "spital century reform able sponsor"
        )
        gh = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
        address = "PNWOET7LLOWMBMLE4KOCELCX6X3D3Q4H2Q4QJASYIEOF7YIPPQBG3YQ5YI"
        close = "IDUTJEUIEVSMXTU4LGTJWZ2UE2E6TIODUKU6UW3FU3UKIQQ77RLUBBBFLA"
        sk = mnemonic.to_private_key(mn)
        pk = account.address_from_private_key(sk)
        sp = transaction.SuggestedParams(4, 12466, 13466, gh, "devnet-v33.0")
        txn = transaction.PaymentTxn(
            pk,
            sp,
            address,
            1000,
            note=base64.b64decode("6gAVR0Nsv5Y="),
            close_remainder_to=close,
        )
        stx = txn.sign(sk)
        golden = (
            "gqNzaWfEQPhUAZ3xkDDcc8FvOVo6UinzmKBCqs0woYSfodlmBMfQvGbeUx3Srxy3d"
            "yJDzv7rLm26BRv9FnL2/AuT7NYfiAWjdHhui6NhbXTNA+ilY2xvc2XEIEDpNJKIJW"
            "TLzpxZpptnVCaJ6aHDoqnqW2Wm6KRCH/xXo2ZlZc0EmKJmds0wsqNnZW6sZGV2bmV"
            "0LXYzMy4womdoxCAmCyAJoJOohot5WHIvpeVG7eftF+TYXEx4r7BFJpDt0qJsds00"
            "mqRub3RlxAjqABVHQ2y/lqNyY3bEIHts4k/rW6zAsWTinCIsV/X2PcOH1DkEglhBH"
            "F/hD3wCo3NuZMQg5/D4TQaBHfnzHI2HixFV9GcdUaGFwgCQhmf0SVhwaKGkdHlwZa"
            "NwYXk="
        )
        self.assertEqual(golden, encoding.msgpack_encode(stx))
        txid_golden = "5FJDJD5LMZC3EHUYYJNH5I23U4X6H2KXABNDGPIL557ZMJ33GZHQ"
        self.assertEqual(txn.get_txid(), txid_golden)

        # check group field serialization
        gid = transaction.calculate_group_id([txn])
        stx.group = gid
        enc = encoding.msgpack_encode(stx)
        re_enc = encoding.msgpack_encode(encoding.msgpack_decode(enc))
        self.assertEqual(enc, re_enc)

    def test_sign_logic_multisig(self):
        program = b"\x01\x20\x01\x01\x22"
        lsig = transaction.LogicSig(program)
        passphrase = "sight garment riot tattoo tortoise identify left talk sea ill walnut leg robot myth toe perfect rifle dizzy spend april build legend brother above hospital"
        sk = mnemonic.to_private_key(passphrase)
        addr = account.address_from_private_key(sk)

        passphrase2 = "sentence spoil search picnic civil quote question express uniform laundry visit wisdom level domain pigeon pattern search animal upper joke fiscal latin they ability stove"
        sk2 = mnemonic.to_private_key(passphrase2)
        addr2 = account.address_from_private_key(sk2)

        msig = transaction.Multisig(1, 2, [addr, addr2])
        lsig.sign(sk, msig)
        lsig.append_to_multisig(sk2)

        receiver = "DOMUC6VGZH7SSY5V332JR5HRLZSOJDWNPBI4OI2IIBU6A3PFLOBOXZ3KFY"
        gh = "zNQES/4IqimxRif40xYvzBBIYCZSbYvNSRIzVIh4swo="

        params = transaction.SuggestedParams(
            0, 447, 1447, gh, gen="network-v1"
        )
        txn = transaction.PaymentTxn(msig.address(), params, receiver, 1000000)
        lstx = transaction.LogicSigTransaction(txn, lsig)

        golden = (
            "gqRsc2lngqFsxAUBIAEBIqRtc2lng6ZzdWJzaWeSgqJwa8QgeUdQSBmJmLH5xdID"
            "nkf+V3AQH6usPifhfJVwnJ7d7nOhc8RAuP0Ms22j1xXTcXYOivDMztXm7vY2uBi8"
            "vJCDlpWhVxLoEDKhqmqEbT7SfvCrS2aNXPiJUSZ7cNMyUdytOpFdD4KicGvEILxI"
            "bwe4gu5YCR4TLASEBpTJ25cdJZqxMqhkgMHQqr61oXPEQGOeeZZ1FAJjJ65N5Asj"
            "i1bK+Q2LZblC77u7NYcw4gPAig8rRUKJYNQtiKVVJQ53A8ufQkn9dZ6uybbaIPxu"
            "bQejdGhyAqF2AaN0eG6Jo2FtdM4AD0JAo2ZlZc0D6KJmds0Bv6NnZW6qbmV0d29y"
            "ay12MaJnaMQgzNQES/4IqimxRif40xYvzBBIYCZSbYvNSRIzVIh4swqibHbNBaej"
            "cmN2xCAbmUF6psn/KWO13vSY9PFeZOSOzXhRxyNIQGngbeVbgqNzbmTEIIytL7Xv"
            "2XuuO6mS+3IetwlKVPM0qdKBIiMVdhzAOMPKpHR5cGWjcGF5"
        )

        encoded = encoding.msgpack_encode(lstx)
        self.assertEqual(encoded, golden)

    def test_serialize_zero_receiver(self):
        address = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
        receiver = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAY5HFKQ"
        gh = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
        sp = transaction.SuggestedParams(3, 1, 100, gh)
        txn = transaction.PaymentTxn(
            address, sp, receiver, 1000, note=bytes([1, 32, 200])
        )

        golden = (
            "iKNhbXTNA+ijZmVlzQPoomZ2AaJnaMQgJgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMe"
            "K+wRSaQ7dKibHZkpG5vdGXEAwEgyKNzbmTEIP5oQQPnKvM7kbGuuSOunAVfSbJzHQ"
            "tAtCP3Bf2XdDxmpHR5cGWjcGF5"
        )

        self.assertEqual(golden, encoding.msgpack_encode(txn))

    def test_error_empty_receiver_txn(self):
        address = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
        receiver = None
        gh = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
        sp = transaction.SuggestedParams(3, 1, 100, gh)

        with self.assertRaises(error.ZeroAddressError):
            transaction.PaymentTxn(address, sp, receiver, 1000)

    def test_error_empty_receiver_asset_txn(self):
        address = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
        receiver = None
        gh = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
        sp = transaction.SuggestedParams(3, 1, 100, gh)

        with self.assertRaises(error.ZeroAddressError):
            transaction.AssetTransferTxn(address, sp, receiver, 1000, 24)

    def test_serialize_pay(self):
        mn = (
            "advice pudding treat near rule blouse same whisper inner electric"
            " quit surface sunny dismiss leader blood seat clown cost exist ho"
            "spital century reform able sponsor"
        )
        sk = mnemonic.to_private_key(mn)
        pk = account.address_from_private_key(sk)
        to = "PNWOET7LLOWMBMLE4KOCELCX6X3D3Q4H2Q4QJASYIEOF7YIPPQBG3YQ5YI"
        fee = 4
        first_round = 12466
        last_round = 13466
        gh = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
        gen = "devnet-v33.0"
        note = base64.b64decode("6gAVR0Nsv5Y=")
        close = "IDUTJEUIEVSMXTU4LGTJWZ2UE2E6TIODUKU6UW3FU3UKIQQ77RLUBBBFLA"
        amount = 1000
        sp = transaction.SuggestedParams(fee, first_round, last_round, gh, gen)
        txn = transaction.PaymentTxn(pk, sp, to, amount, close, note)
        signed_txn = txn.sign(sk)

        golden = (
            "gqNzaWfEQPhUAZ3xkDDcc8FvOVo6UinzmKBCqs0woYSfodlmBMfQvGbeUx3Srxy3d"
            "yJDzv7rLm26BRv9FnL2/AuT7NYfiAWjdHhui6NhbXTNA+ilY2xvc2XEIEDpNJKIJW"
            "TLzpxZpptnVCaJ6aHDoqnqW2Wm6KRCH/xXo2ZlZc0EmKJmds0wsqNnZW6sZGV2bmV"
            "0LXYzMy4womdoxCAmCyAJoJOohot5WHIvpeVG7eftF+TYXEx4r7BFJpDt0qJsds00"
            "mqRub3RlxAjqABVHQ2y/lqNyY3bEIHts4k/rW6zAsWTinCIsV/X2PcOH1DkEglhBH"
            "F/hD3wCo3NuZMQg5/D4TQaBHfnzHI2HixFV9GcdUaGFwgCQhmf0SVhwaKGkdHlwZa"
            "NwYXk="
        )

        self.assertEqual(golden, encoding.msgpack_encode(signed_txn))

    def test_serialize_pay_lease(self):
        mn = (
            "advice pudding treat near rule blouse same whisper inner electric"
            " quit surface sunny dismiss leader blood seat clown cost exist ho"
            "spital century reform able sponsor"
        )
        sk = mnemonic.to_private_key(mn)
        pk = account.address_from_private_key(sk)
        to = "PNWOET7LLOWMBMLE4KOCELCX6X3D3Q4H2Q4QJASYIEOF7YIPPQBG3YQ5YI"
        fee = 4
        first_round = 12466
        last_round = 13466
        gh = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
        gen = "devnet-v33.0"
        note = base64.b64decode("6gAVR0Nsv5Y=")
        close = "IDUTJEUIEVSMXTU4LGTJWZ2UE2E6TIODUKU6UW3FU3UKIQQ77RLUBBBFLA"
        amount = 1000
        lease = bytes([1, 2, 3, 4] * 8)
        sp = transaction.SuggestedParams(fee, first_round, last_round, gh, gen)
        txn = transaction.PaymentTxn(
            pk,
            sp,
            to,
            amount,
            close_remainder_to=close,
            note=note,
            lease=lease,
        )
        signed_txn = txn.sign(sk)

        golden = (
            "gqNzaWfEQOMmFSIKsZvpW0txwzhmbgQjxv6IyN7BbV5sZ2aNgFbVcrWUnqPpQQxfP"
            "hV/wdu9jzEPUU1jAujYtcNCxJ7ONgejdHhujKNhbXTNA+ilY2xvc2XEIEDpNJKIJW"
            "TLzpxZpptnVCaJ6aHDoqnqW2Wm6KRCH/xXo2ZlZc0FLKJmds0wsqNnZW6sZGV2bmV"
            "0LXYzMy4womdoxCAmCyAJoJOohot5WHIvpeVG7eftF+TYXEx4r7BFJpDt0qJsds00"
            "mqJseMQgAQIDBAECAwQBAgMEAQIDBAECAwQBAgMEAQIDBAECAwSkbm90ZcQI6gAVR"
            "0Nsv5ajcmN2xCB7bOJP61uswLFk4pwiLFf19j3Dh9Q5BIJYQRxf4Q98AqNzbmTEIO"
            "fw+E0GgR358xyNh4sRVfRnHVGhhcIAkIZn9ElYcGihpHR5cGWjcGF5"
        )

        self.assertEqual(golden, encoding.msgpack_encode(signed_txn))

    def test_serialize_keyreg_online(self):
        mn = (
            "awful drop leaf tennis indoor begin mandate discover uncle seven "
            "only coil atom any hospital uncover make any climb actor armed me"
            "asure need above hundred"
        )
        sk = mnemonic.to_private_key(mn)
        pk = account.address_from_private_key(sk)
        fee = 1000
        gh = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
        votepk = "Kv7QI7chi1y6axoy+t7wzAVpePqRq/rkjzWh/RMYyLo="
        selpk = "bPgrv4YogPcdaUAxrt1QysYZTVyRAuUMD4zQmCu9llc="
        votefirst = 10000
        votelast = 10111
        votedilution = 11
        sprfKey = "mYR0GVEObMTSNdsKM6RwYywHYPqVDqg3E4JFzxZOreH9NU8B+tKzUanyY8AQ144hETgSMX7fXWwjBdHz6AWk9w=="

        sp = transaction.SuggestedParams(
            fee, 322575, 323575, gh, flat_fee=True
        )
        txn = transaction.KeyregTxn(
            pk,
            sp,
            votepk,
            selpk,
            votefirst,
            votelast,
            votedilution,
            sprfkey=sprfKey,
        )
        signed_txn = txn.sign(sk)

        golden = (
            "gqNzaWfEQDDDuwMXAJM2JISVLu0yjeLT5zf9d4p/TBiEr26zny/M72GfLpciu1jSRv"
            "sM4zlp3V92Ix5/4iN52lhVwspabA2jdHhujKNmZWXNA+iiZnbOAATsD6JnaMQgSGO1"
            "GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiKibHbOAATv96ZzZWxrZXnEIGz4K7"
            "+GKID3HWlAMa7dUMrGGU1ckQLlDA+M0JgrvZZXo3NuZMQgCfvSdiwI+Gxa5r9t16ep"
            "Ad5mdddQ4H6MXHaYZH224f2nc3ByZmtlecRAmYR0GVEObMTSNdsKM6RwYywHYPqVDqg"
            "3E4JFzxZOreH9NU8B+tKzUanyY8AQ144hETgSMX7fXWwjBdHz6AWk96R0eXBlpmtleX"
            "JlZ6d2b3RlZnN0zScQpnZvdGVrZAundm90ZWtlecQgKv7QI7chi1y6axoy+t7wzAVpe"
            "PqRq/rkjzWh/RMYyLqndm90ZWxzdM0nfw=="
        )
        print(encoding.msgpack_encode(signed_txn))
        self.assertEqual(golden, encoding.msgpack_encode(signed_txn))

    def test_serialize_keyreg_offline(self):
        mn = (
            "awful drop leaf tennis indoor begin mandate discover uncle seven "
            "only coil atom any hospital uncover make any climb actor armed "
            "measure need above hundred"
        )
        sk = mnemonic.to_private_key(mn)
        pk = account.address_from_private_key(sk)
        fee = 1000
        gh = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
        votepk = None
        selpk = None
        votefirst = None
        votelast = None
        votedilution = None

        sp = transaction.SuggestedParams(
            fee, 12299691, 12300691, gh, flat_fee=True
        )
        txn = transaction.KeyregTxn(
            pk, sp, votepk, selpk, votefirst, votelast, votedilution
        )
        signed_txn = txn.sign(sk)

        golden = (
            "gqNzaWfEQJosTMSKwGr+eWN5XsAJvbjh2DkzOtEN6lrDNM4TAnYIjl9L43zU70gAX"
            "USAehZo9RyejgDA12B75SR6jIdhzQCjdHhuhqNmZWXNA+iiZnbOALutq6JnaMQgSG"
            "O1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiKibHbOALuxk6NzbmTEIAn70nYs"
            "CPhsWua/bdenqQHeZnXXUOB+jFx2mGR9tuH9pHR5cGWma2V5cmVn"
        )
        self.assertEqual(golden, encoding.msgpack_encode(signed_txn))

    def test_serialize_keyreg_nonpart(self):
        mn = (
            "awful drop leaf tennis indoor begin mandate discover uncle seven "
            "only coil atom any hospital uncover make any climb actor armed "
            "measure need above hundred"
        )
        sk = mnemonic.to_private_key(mn)
        pk = account.address_from_private_key(sk)
        fee = 1000
        gh = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
        nonpart = True

        sp = transaction.SuggestedParams(
            fee, 12299691, 12300691, gh, flat_fee=True
        )
        txn = transaction.KeyregTxn(
            pk, sp, None, None, None, None, None, nonpart=nonpart
        )
        signed_txn = txn.sign(sk)

        golden = (
            "gqNzaWfEQN7kw3tLcC1IweQ2Ru5KSqFS0Ba0cn34ncOWPIyv76wU8JPLxyS8alErm4"
            "PHg3Q7n1Mfqa9SQ9zDY+FMeZLLgQyjdHhuh6NmZWXNA+iiZnbOALutq6JnaMQgSGO1"
            "GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiKibHbOALuxk6dub25wYXJ0w6Nzbm"
            "TEIAn70nYsCPhsWua/bdenqQHeZnXXUOB+jFx2mGR9tuH9pHR5cGWma2V5cmVn"
        )
        self.assertEqual(golden, encoding.msgpack_encode(signed_txn))

    def test_serialize_keyregonlinetxn(self):
        mn = (
            "awful drop leaf tennis indoor begin mandate discover uncle seven "
            "only coil atom any hospital uncover make any climb actor armed me"
            "asure need above hundred"
        )
        sk = mnemonic.to_private_key(mn)
        pk = mnemonic.to_public_key(mn)
        fee = 1000
        gh = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
        votepk = "Kv7QI7chi1y6axoy+t7wzAVpePqRq/rkjzWh/RMYyLo="
        selpk = "bPgrv4YogPcdaUAxrt1QysYZTVyRAuUMD4zQmCu9llc="
        votefirst = 10000
        votelast = 10111
        votedilution = 11
        sprfKey = "mYR0GVEObMTSNdsKM6RwYywHYPqVDqg3E4JFzxZOreH9NU8B+tKzUanyY8AQ144hETgSMX7fXWwjBdHz6AWk9w=="
        sp = transaction.SuggestedParams(
            fee, 322575, 323575, gh, flat_fee=True
        )
        txn = transaction.KeyregOnlineTxn(
            pk,
            sp,
            votepk,
            selpk,
            votefirst,
            votelast,
            votedilution,
            sprfkey=sprfKey,
        )
        signed_txn = txn.sign(sk)
        golden = (
            "gqNzaWfEQDDDuwMXAJM2JISVLu0yjeLT5zf9d4p/TBiEr26zny/M72GfLpciu1jSRv"
            "sM4zlp3V92Ix5/4iN52lhVwspabA2jdHhujKNmZWXNA+iiZnbOAATsD6JnaMQgSGO1"
            "GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiKibHbOAATv96ZzZWxrZXnEIGz4K7"
            "+GKID3HWlAMa7dUMrGGU1ckQLlDA+M0JgrvZZXo3NuZMQgCfvSdiwI+Gxa5r9t16ep"
            "Ad5mdddQ4H6MXHaYZH224f2nc3ByZmtlecRAmYR0GVEObMTSNdsKM6RwYywHYPqVDqg"
            "3E4JFzxZOreH9NU8B+tKzUanyY8AQ144hETgSMX7fXWwjBdHz6AWk96R0eXBlpmtleX"
            "JlZ6d2b3RlZnN0zScQpnZvdGVrZAundm90ZWtlecQgKv7QI7chi1y6axoy+t7wzAVpe"
            "PqRq/rkjzWh/RMYyLqndm90ZWxzdM0nfw=="
        )
        self.assertEqual(golden, encoding.msgpack_encode(signed_txn))

    def test_serialize_write_read_keyregonlinetxn(self):
        mn = (
            "awful drop leaf tennis indoor begin mandate discover uncle seven "
            "only coil atom any hospital uncover make any climb actor armed me"
            "asure need above hundred"
        )
        sk = mnemonic.to_private_key(mn)
        pk = mnemonic.to_public_key(mn)
        fee = 1000
        gh = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
        votepk = "Kv7QI7chi1y6axoy+t7wzAVpePqRq/rkjzWh/RMYyLo="
        selpk = "bPgrv4YogPcdaUAxrt1QysYZTVyRAuUMD4zQmCu9llc="
        votefirst = 10000
        votelast = 10111
        votedilution = 11
        sprfKey = "mYR0GVEObMTSNdsKM6RwYywHYPqVDqg3E4JFzxZOreH9NU8B+tKzUanyY8AQ144hETgSMX7fXWwjBdHz6AWk9w=="
        sp = transaction.SuggestedParams(
            fee, 322575, 323575, gh, flat_fee=True
        )
        txn = transaction.KeyregOnlineTxn(
            pk,
            sp,
            votepk,
            selpk,
            votefirst,
            votelast,
            votedilution,
            sprfkey=sprfKey,
        )
        path = "/tmp/%s" % uuid.uuid4()
        transaction.write_to_file([txn], path)
        txnr = transaction.retrieve_from_file(path)[0]
        print("txn:", txn)
        print("txnr:", txnr)
        os.remove(path)
        self.assertEqual(txn, txnr)

    def test_init_keyregonlinetxn_with_none_values(self):
        mn = (
            "awful drop leaf tennis indoor begin mandate discover uncle seven "
            "only coil atom any hospital uncover make any climb actor armed me"
            "asure need above hundred"
        )
        sk = mnemonic.to_private_key(mn)
        pk = mnemonic.to_public_key(mn)
        fee = 1000
        gh = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
        votepk = "Kv7QI7chi1y6axoy+t7wzAVpePqRq/rkjzWh/RMYyLo="
        selpk = "bPgrv4YogPcdaUAxrt1QysYZTVyRAuUMD4zQmCu9llc="
        votefirst = 10000
        votelast = None
        votedilution = 11
        sprfKey = "mYR0GVEObMTSNdsKM6RwYywHYPqVDqg3E4JFzxZOreH9NU8B+tKzUanyY8AQ144hETgSMX7fXWwjBdHz6AWk9w=="
        sp = transaction.SuggestedParams(
            fee, 322575, 323575, gh, flat_fee=True
        )
        with self.assertRaises(error.KeyregOnlineTxnInitError) as cm:
            transaction.KeyregOnlineTxn(
                pk,
                sp,
                votepk,
                selpk,
                votefirst,
                votelast,
                votedilution,
                sprfkey=sprfKey,
            )
        the_exception = cm.exception
        self.assertTrue("votelst" in the_exception.__repr__())

    def test_serialize_keyregofflinetxn(self):
        mn = (
            "awful drop leaf tennis indoor begin mandate discover uncle seven "
            "only coil atom any hospital uncover make any climb actor armed "
            "measure need above hundred"
        )
        sk = mnemonic.to_private_key(mn)
        pk = mnemonic.to_public_key(mn)
        fee = 1000
        gh = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="

        sp = transaction.SuggestedParams(
            fee, 12299691, 12300691, gh, flat_fee=True
        )
        txn = transaction.KeyregOfflineTxn(pk, sp)
        signed_txn = txn.sign(sk)

        golden = (
            "gqNzaWfEQJosTMSKwGr+eWN5XsAJvbjh2DkzOtEN6lrDNM4TAnYIjl9L43zU"
            "70gAXUSAehZo9RyejgDA12B75SR6jIdhzQCjdHhuhqNmZWXNA+iiZnbOALut"
            "q6JnaMQgSGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiKibHbOALux"
            "k6NzbmTEIAn70nYsCPhsWua/bdenqQHeZnXXUOB+jFx2mGR9tuH9pHR5cGWm"
            "a2V5cmVn"
        )
        self.assertEqual(golden, encoding.msgpack_encode(signed_txn))

    def test_write_read_keyregofflinetxn(self):
        mn = (
            "awful drop leaf tennis indoor begin mandate discover uncle seven "
            "only coil atom any hospital uncover make any climb actor armed "
            "measure need above hundred"
        )
        sk = mnemonic.to_private_key(mn)
        pk = account.address_from_private_key(sk)
        fee = 1000
        gh = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="

        sp = transaction.SuggestedParams(
            fee, 12299691, 12300691, gh, flat_fee=True
        )
        txn = transaction.KeyregOfflineTxn(pk, sp)
        path = "/tmp/%s" % uuid.uuid4()
        transaction.write_to_file([txn], path)
        txnr = transaction.retrieve_from_file(path)[0]
        os.remove(path)
        self.assertEqual(txn, txnr)

    def test_serialize_keyregnonparttxn(self):
        mn = (
            "awful drop leaf tennis indoor begin mandate discover uncle seven "
            "only coil atom any hospital uncover make any climb actor armed "
            "measure need above hundred"
        )
        sk = mnemonic.to_private_key(mn)
        pk = mnemonic.to_public_key(mn)
        fee = 1000
        gh = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="

        sp = transaction.SuggestedParams(
            fee, 12299691, 12300691, gh, flat_fee=True
        )
        txn = transaction.KeyregNonparticipatingTxn(pk, sp)
        signed_txn = txn.sign(sk)

        golden = (
            "gqNzaWfEQN7kw3tLcC1IweQ2Ru5KSqFS0Ba0cn34ncOWPIyv76wU8JPLxyS"
            "8alErm4PHg3Q7n1Mfqa9SQ9zDY+FMeZLLgQyjdHhuh6NmZWXNA+iiZnbOAL"
            "utq6JnaMQgSGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiKibHbOA"
            "Luxk6dub25wYXJ0w6NzbmTEIAn70nYsCPhsWua/bdenqQHeZnXXUOB+jFx2"
            "mGR9tuH9pHR5cGWma2V5cmVn"
        )
        self.assertEqual(golden, encoding.msgpack_encode(signed_txn))

    def test_write_read_keyregnonparttxn(self):
        mn = (
            "awful drop leaf tennis indoor begin mandate discover uncle seven "
            "only coil atom any hospital uncover make any climb actor armed "
            "measure need above hundred"
        )
        sk = mnemonic.to_private_key(mn)
        pk = account.address_from_private_key(sk)
        fee = 1000
        gh = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="

        sp = transaction.SuggestedParams(
            fee, 12299691, 12300691, gh, flat_fee=True
        )
        txn = transaction.KeyregNonparticipatingTxn(pk, sp)
        path = "/tmp/%s" % uuid.uuid4()
        transaction.write_to_file([txn], path)
        txnr = transaction.retrieve_from_file(path)[0]
        os.remove(path)
        self.assertEqual(txn, txnr)

    def test_serialize_asset_create(self):
        mn = (
            "awful drop leaf tennis indoor begin mandate discover uncle seven "
            "only coil atom any hospital uncover make any climb actor armed me"
            "asure need above hundred"
        )
        sk = mnemonic.to_private_key(mn)
        pk = account.address_from_private_key(sk)
        fee = 10
        first_round = 322575
        last_round = 323575
        gh = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="

        total = 100
        assetname = "testcoin"
        unitname = "tst"
        url = "website"
        metadata = bytes("fACPO4nRgO55j1ndAK3W6Sgc4APkcyFh", "ascii")
        sp = transaction.SuggestedParams(fee, first_round, last_round, gh)
        txn = transaction.AssetConfigTxn(
            pk,
            sp,
            total=total,
            manager=pk,
            reserve=pk,
            freeze=pk,
            clawback=pk,
            unit_name=unitname,
            asset_name=assetname,
            url=url,
            metadata_hash=metadata,
            default_frozen=False,
        )
        signed_txn = txn.sign(sk)
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
        self.assertEqual(golden, encoding.msgpack_encode(signed_txn))

    def test_serialize_asset_create_decimal(self):
        mn = (
            "awful drop leaf tennis indoor begin mandate discover uncle seven "
            "only coil atom any hospital uncover make any climb actor armed me"
            "asure need above hundred"
        )
        sk = mnemonic.to_private_key(mn)
        pk = account.address_from_private_key(sk)
        fee = 10
        first_round = 322575
        last_round = 323575
        gh = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="

        total = 100
        assetname = "testcoin"
        unitname = "tst"
        url = "website"
        metadata = bytes("fACPO4nRgO55j1ndAK3W6Sgc4APkcyFh", "ascii")
        sp = transaction.SuggestedParams(fee, first_round, last_round, gh)
        txn = transaction.AssetConfigTxn(
            pk,
            sp,
            total=total,
            manager=pk,
            reserve=pk,
            freeze=pk,
            clawback=pk,
            unit_name=unitname,
            asset_name=assetname,
            url=url,
            metadata_hash=metadata,
            default_frozen=False,
            decimals=1,
        )
        signed_txn = txn.sign(sk)
        golden = (
            "gqNzaWfEQCj5xLqNozR5ahB+LNBlTG+d0gl0vWBrGdAXj1ibsCkvAwOsXs5KHZK1Y"
            "dLgkdJecQiWm4oiZ+pm5Yg0m3KFqgqjdHhuh6RhcGFyiqJhbcQgZkFDUE80blJnTz"
            "U1ajFuZEFLM1c2U2djNEFQa2N5RmiiYW6odGVzdGNvaW6iYXWnd2Vic2l0ZaFjxCA"
            "J+9J2LAj4bFrmv23Xp6kB3mZ111Dgfoxcdphkfbbh/aJkYwGhZsQgCfvSdiwI+Gxa"
            "5r9t16epAd5mdddQ4H6MXHaYZH224f2hbcQgCfvSdiwI+Gxa5r9t16epAd5mdddQ4"
            "H6MXHaYZH224f2hcsQgCfvSdiwI+Gxa5r9t16epAd5mdddQ4H6MXHaYZH224f2hdG"
            "SidW6jdHN0o2ZlZc0P3KJmds4ABOwPomdoxCBIY7UYpLPITsgQ8i1PEIHLD3HwWae"
            "sIN7GL39w5Qk6IqJsds4ABO/3o3NuZMQgCfvSdiwI+Gxa5r9t16epAd5mdddQ4H6M"
            "XHaYZH224f2kdHlwZaRhY2Zn"
        )
        self.assertEqual(golden, encoding.msgpack_encode(signed_txn))

    def test_asset_empty_address_error(self):
        pk = "DN7MBMCL5JQ3PFUQS7TMX5AH4EEKOBJVDUF4TCV6WERATKFLQF4MQUPZTA"
        fee = 10
        first_round = 322575
        last_round = 323575
        gh = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
        index = 1234
        sp = transaction.SuggestedParams(fee, first_round, last_round, gh)
        self.assertRaises(
            error.EmptyAddressError,
            transaction.AssetConfigTxn,
            pk,
            sp,
            reserve=pk,
            freeze=pk,
            clawback=pk,
            index=index,
        )

    def test_serialize_asset_config(self):
        mn = (
            "awful drop leaf tennis indoor begin mandate discover uncle seven "
            "only coil atom any hospital uncover make any climb actor armed me"
            "asure need above hundred"
        )
        sk = mnemonic.to_private_key(mn)
        pk = account.address_from_private_key(sk)
        fee = 10
        first_round = 322575
        last_round = 323575
        gh = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
        index = 1234
        sp = transaction.SuggestedParams(fee, first_round, last_round, gh)
        txn = transaction.AssetConfigTxn(
            pk, sp, manager=pk, reserve=pk, freeze=pk, clawback=pk, index=index
        )
        signed_txn = txn.sign(sk)
        golden = (
            "gqNzaWfEQBBkfw5n6UevuIMDo2lHyU4dS80JCCQ/vTRUcTx5m0ivX68zTKyuVRrHa"
            "TbxbRRc3YpJ4zeVEnC9Fiw3Wf4REwejdHhuiKRhcGFyhKFjxCAJ+9J2LAj4bFrmv2"
            "3Xp6kB3mZ111Dgfoxcdphkfbbh/aFmxCAJ+9J2LAj4bFrmv23Xp6kB3mZ111Dgfox"
            "cdphkfbbh/aFtxCAJ+9J2LAj4bFrmv23Xp6kB3mZ111Dgfoxcdphkfbbh/aFyxCAJ"
            "+9J2LAj4bFrmv23Xp6kB3mZ111Dgfoxcdphkfbbh/aRjYWlkzQTSo2ZlZc0NSKJmd"
            "s4ABOwPomdoxCBIY7UYpLPITsgQ8i1PEIHLD3HwWaesIN7GL39w5Qk6IqJsds4ABO"
            "/3o3NuZMQgCfvSdiwI+Gxa5r9t16epAd5mdddQ4H6MXHaYZH224f2kdHlwZaRhY2Z"
            "n"
        )

        self.assertEqual(golden, encoding.msgpack_encode(signed_txn))

    def test_serialize_asset_destroy(self):
        mn = (
            "awful drop leaf tennis indoor begin mandate discover uncle seven "
            "only coil atom any hospital uncover make any climb actor armed me"
            "asure need above hundred"
        )
        sk = mnemonic.to_private_key(mn)
        pk = account.address_from_private_key(sk)
        fee = 10
        first_round = 322575
        last_round = 323575
        gh = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
        index = 1
        sp = transaction.SuggestedParams(fee, first_round, last_round, gh)
        txn = transaction.AssetConfigTxn(
            pk, sp, index=index, strict_empty_address_check=False
        )
        signed_txn = txn.sign(sk)
        golden = (
            "gqNzaWfEQBSP7HtzD/Lvn4aVvaNpeR4T93dQgo4LvywEwcZgDEoc/WVl3aKsZGcZk"
            "cRFoiWk8AidhfOZzZYutckkccB8RgGjdHhuh6RjYWlkAaNmZWXNB1iiZnbOAATsD6"
            "JnaMQgSGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiKibHbOAATv96NzbmT"
            "EIAn70nYsCPhsWua/bdenqQHeZnXXUOB+jFx2mGR9tuH9pHR5cGWkYWNmZw=="
        )
        self.assertEqual(golden, encoding.msgpack_encode(signed_txn))

    def test_serialize_asset_freeze(self):
        mn = (
            "awful drop leaf tennis indoor begin mandate discover uncle seven "
            "only coil atom any hospital uncover make any climb actor armed me"
            "asure need above hundred"
        )
        sk = mnemonic.to_private_key(mn)
        pk = account.address_from_private_key(sk)
        fee = 10
        first_round = 322575
        last_round = 323576
        gh = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
        index = 1
        target = "BH55E5RMBD4GYWXGX5W5PJ5JAHPGM5OXKDQH5DC4O2MGI7NW4H6VOE4CP4"
        sp = transaction.SuggestedParams(fee, first_round, last_round, gh)
        txn = transaction.AssetFreezeTxn(
            pk, sp, index=index, target=target, new_freeze_state=True
        )
        signed_txn = txn.sign(sk)
        golden = (
            "gqNzaWfEQAhru5V2Xvr19s4pGnI0aslqwY4lA2skzpYtDTAN9DKSH5+qsfQQhm4oq"
            "+9VHVj7e1rQC49S28vQZmzDTVnYDQGjdHhuiaRhZnJ6w6RmYWRkxCAJ+9J2LAj4bF"
            "rmv23Xp6kB3mZ111Dgfoxcdphkfbbh/aRmYWlkAaNmZWXNCRqiZnbOAATsD6JnaMQ"
            "gSGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiKibHbOAATv+KNzbmTEIAn7"
            "0nYsCPhsWua/bdenqQHeZnXXUOB+jFx2mGR9tuH9pHR5cGWkYWZyeg=="
        )
        self.assertEqual(golden, encoding.msgpack_encode(signed_txn))

    def test_serialize_asset_transfer(self):
        mn = (
            "awful drop leaf tennis indoor begin mandate discover uncle seven "
            "only coil atom any hospital uncover make any climb actor armed me"
            "asure need above hundred"
        )
        sk = mnemonic.to_private_key(mn)
        pk = account.address_from_private_key(sk)
        fee = 10
        first_round = 322575
        last_round = 323576
        gh = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
        index = 1
        amount = 1
        to = "BH55E5RMBD4GYWXGX5W5PJ5JAHPGM5OXKDQH5DC4O2MGI7NW4H6VOE4CP4"
        close = "BH55E5RMBD4GYWXGX5W5PJ5JAHPGM5OXKDQH5DC4O2MGI7NW4H6VOE4CP4"
        sp = transaction.SuggestedParams(fee, first_round, last_round, gh)
        txn = transaction.AssetTransferTxn(pk, sp, to, amount, index, close)
        signed_txn = txn.sign(sk)
        golden = (
            "gqNzaWfEQNkEs3WdfFq6IQKJdF1n0/hbV9waLsvojy9pM1T4fvwfMNdjGQDy+Lees"
            "uQUfQVTneJD4VfMP7zKx4OUlItbrwSjdHhuiqRhYW10AaZhY2xvc2XEIAn70nYsCP"
            "hsWua/bdenqQHeZnXXUOB+jFx2mGR9tuH9pGFyY3bEIAn70nYsCPhsWua/bdenqQH"
            "eZnXXUOB+jFx2mGR9tuH9o2ZlZc0KvqJmds4ABOwPomdoxCBIY7UYpLPITsgQ8i1P"
            "EIHLD3HwWaesIN7GL39w5Qk6IqJsds4ABO/4o3NuZMQgCfvSdiwI+Gxa5r9t16epA"
            "d5mdddQ4H6MXHaYZH224f2kdHlwZaVheGZlcqR4YWlkAQ=="
        )
        self.assertEqual(golden, encoding.msgpack_encode(signed_txn))

    def test_serialize_asset_accept(self):
        mn = (
            "awful drop leaf tennis indoor begin mandate discover uncle seven "
            "only coil atom any hospital uncover make any climb actor armed me"
            "asure need above hundred"
        )
        sk = mnemonic.to_private_key(mn)
        pk = account.address_from_private_key(sk)
        fee = 10
        first_round = 322575
        last_round = 323575
        gh = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
        index = 1
        amount = 0
        to = "BH55E5RMBD4GYWXGX5W5PJ5JAHPGM5OXKDQH5DC4O2MGI7NW4H6VOE4CP4"
        sp = transaction.SuggestedParams(fee, first_round, last_round, gh)
        txn = transaction.AssetTransferTxn(pk, sp, to, amount, index)
        signed_txn = txn.sign(sk)
        golden = (
            "gqNzaWfEQJ7q2rOT8Sb/wB0F87ld+1zMprxVlYqbUbe+oz0WM63FctIi+K9eYFSqT"
            "26XBZ4Rr3+VTJpBE+JLKs8nctl9hgijdHhuiKRhcmN2xCAJ+9J2LAj4bFrmv23Xp6"
            "kB3mZ111Dgfoxcdphkfbbh/aNmZWXNCOiiZnbOAATsD6JnaMQgSGO1GKSzyE7IEPI"
            "tTxCByw9x8FmnrCDexi9/cOUJOiKibHbOAATv96NzbmTEIAn70nYsCPhsWua/bden"
            "qQHeZnXXUOB+jFx2mGR9tuH9pHR5cGWlYXhmZXKkeGFpZAE="
        )
        self.assertEqual(golden, encoding.msgpack_encode(signed_txn))

    def test_serialize_asset_revoke(self):
        mn = (
            "awful drop leaf tennis indoor begin mandate discover uncle seven "
            "only coil atom any hospital uncover make any climb actor armed me"
            "asure need above hundred"
        )
        sk = mnemonic.to_private_key(mn)
        pk = account.address_from_private_key(sk)
        fee = 10
        first_round = 322575
        last_round = 323575
        gh = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
        index = 1
        amount = 1
        to = "BH55E5RMBD4GYWXGX5W5PJ5JAHPGM5OXKDQH5DC4O2MGI7NW4H6VOE4CP4"
        sp = transaction.SuggestedParams(fee, first_round, last_round, gh)
        txn = transaction.AssetTransferTxn(
            pk, sp, to, amount, index, revocation_target=to
        )
        signed_txn = txn.sign(sk)
        golden = (
            "gqNzaWfEQHsgfEAmEHUxLLLR9s+Y/yq5WeoGo/jAArCbany+7ZYwExMySzAhmV7M7"
            "S8+LBtJalB4EhzEUMKmt3kNKk6+vAWjdHhuiqRhYW10AaRhcmN2xCAJ+9J2LAj4bF"
            "rmv23Xp6kB3mZ111Dgfoxcdphkfbbh/aRhc25kxCAJ+9J2LAj4bFrmv23Xp6kB3mZ"
            "111Dgfoxcdphkfbbh/aNmZWXNCqqiZnbOAATsD6JnaMQgSGO1GKSzyE7IEPItTxCB"
            "yw9x8FmnrCDexi9/cOUJOiKibHbOAATv96NzbmTEIAn70nYsCPhsWua/bdenqQHeZ"
            "nXXUOB+jFx2mGR9tuH9pHR5cGWlYXhmZXKkeGFpZAE="
        )
        self.assertEqual(golden, encoding.msgpack_encode(signed_txn))

    def test_pay_float_amt(self):
        address = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
        gh = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
        sp = transaction.SuggestedParams(3, 1, 100, gh)
        f = lambda: transaction.PaymentTxn(
            address, sp, address, 10.0, note=bytes([1, 32, 200])
        )
        self.assertRaises(error.WrongAmountType, f)

    def test_pay_negative_amt(self):
        address = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
        gh = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
        sp = transaction.SuggestedParams(3, 1, 100, gh)
        f = lambda: transaction.PaymentTxn(
            address, sp, address, -5, note=bytes([1, 32, 200])
        )
        self.assertRaises(error.WrongAmountType, f)

    def test_asset_transfer_float_amt(self):
        address = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
        fee = 10
        first_round = 322575
        last_round = 323576
        gh = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
        index = 1
        amount = 1.0
        to = "BH55E5RMBD4GYWXGX5W5PJ5JAHPGM5OXKDQH5DC4O2MGI7NW4H6VOE4CP4"
        close = "BH55E5RMBD4GYWXGX5W5PJ5JAHPGM5OXKDQH5DC4O2MGI7NW4H6VOE4CP4"
        sp = transaction.SuggestedParams(fee, first_round, last_round, gh)
        f = lambda: transaction.AssetTransferTxn(
            address, sp, to, amount, index, close
        )
        self.assertRaises(error.WrongAmountType, f)

    def test_asset_transfer_negative_amt(self):
        address = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
        fee = 10
        first_round = 322575
        last_round = 323576
        gh = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
        index = 1
        amount = -1
        to = "BH55E5RMBD4GYWXGX5W5PJ5JAHPGM5OXKDQH5DC4O2MGI7NW4H6VOE4CP4"
        close = "BH55E5RMBD4GYWXGX5W5PJ5JAHPGM5OXKDQH5DC4O2MGI7NW4H6VOE4CP4"
        sp = transaction.SuggestedParams(fee, first_round, last_round, gh)
        f = lambda: transaction.AssetTransferTxn(
            address, sp, to, amount, index, close
        )
        self.assertRaises(error.WrongAmountType, f)

    def test_group_id(self):
        address = "UPYAFLHSIPMJOHVXU2MPLQ46GXJKSDCEMZ6RLCQ7GWB5PRDKJUWKKXECXI"
        fromAddress, toAddress = address, address
        fee = 1000
        amount = 2000
        genesisID = "devnet-v1.0"
        genesisHash = "sC3P7e2SdbqKJK0tbiCdK9tdSpbe6XeCGKdoNzmlj0E="

        firstRound1 = 710399
        note1 = base64.b64decode("wRKw5cJ0CMo=")

        sp = transaction.SuggestedParams(
            fee,
            firstRound1,
            firstRound1 + 1000,
            genesisHash,
            genesisID,
            flat_fee=True,
        )
        tx1 = transaction.PaymentTxn(
            fromAddress, sp, toAddress, amount, note=note1
        )

        firstRound2 = 710515
        note2 = base64.b64decode("dBlHI6BdrIg=")

        sp.first = firstRound2
        sp.last = firstRound2 + 1000
        tx2 = transaction.PaymentTxn(
            fromAddress, sp, toAddress, amount, note=note2
        )

        # goal clerk send dumps unsigned transaction as signed with empty
        # signature in order to save tx type
        stx1 = transaction.SignedTransaction(tx1, None)
        stx2 = transaction.SignedTransaction(tx2, None)

        goldenTx1 = (
            "gaN0eG6Ko2FtdM0H0KNmZWXNA+iiZnbOAArW/6NnZW6rZGV2bmV0LXYxLjCiZ2jEI"
            "LAtz+3tknW6iiStLW4gnSvbXUqW3ul3ghinaDc5pY9Bomx2zgAK2uekbm90ZcQIwR"
            "Kw5cJ0CMqjcmN2xCCj8AKs8kPYlx63ppj1w5410qkMRGZ9FYofNYPXxGpNLKNzbmT"
            "EIKPwAqzyQ9iXHremmPXDnjXSqQxEZn0Vih81g9fEak0spHR5cGWjcGF5"
        )
        goldenTx2 = (
            "gaN0eG6Ko2FtdM0H0KNmZWXNA+iiZnbOAArXc6NnZW6rZGV2bmV0LXYxLjCiZ2jEI"
            "LAtz+3tknW6iiStLW4gnSvbXUqW3ul3ghinaDc5pY9Bomx2zgAK21ukbm90ZcQIdB"
            "lHI6BdrIijcmN2xCCj8AKs8kPYlx63ppj1w5410qkMRGZ9FYofNYPXxGpNLKNzbmT"
            "EIKPwAqzyQ9iXHremmPXDnjXSqQxEZn0Vih81g9fEak0spHR5cGWjcGF5"
        )

        self.assertEqual(goldenTx1, encoding.msgpack_encode(stx1))
        self.assertEqual(goldenTx2, encoding.msgpack_encode(stx2))

        # preserve original tx{1,2} objects
        tx1 = copy.deepcopy(tx1)
        tx2 = copy.deepcopy(tx2)

        gid = transaction.calculate_group_id([tx1, tx2])
        stx1.transaction.group = gid
        stx2.transaction.group = gid

        # goal clerk group sets Group to every transaction and concatenate
        # them in output file
        # simulating that behavior here
        txg = base64.b64encode(
            base64.b64decode(encoding.msgpack_encode(stx1))
            + base64.b64decode(encoding.msgpack_encode(stx2))
        ).decode()

        goldenTxg = (
            "gaN0eG6Lo2FtdM0H0KNmZWXNA+iiZnbOAArW/6NnZW6rZGV2bmV0LXYxLjCiZ2jEI"
            "LAtz+3tknW6iiStLW4gnSvbXUqW3ul3ghinaDc5pY9Bo2dycMQgLiQ9OBup9H/bZL"
            "SfQUH2S6iHUM6FQ3PLuv9FNKyt09SibHbOAAra56Rub3RlxAjBErDlwnQIyqNyY3b"
            "EIKPwAqzyQ9iXHremmPXDnjXSqQxEZn0Vih81g9fEak0so3NuZMQgo/ACrPJD2Jce"
            "t6aY9cOeNdKpDERmfRWKHzWD18RqTSykdHlwZaNwYXmBo3R4boujYW10zQfQo2ZlZ"
            "c0D6KJmds4ACtdzo2dlbqtkZXZuZXQtdjEuMKJnaMQgsC3P7e2SdbqKJK0tbiCdK9"
            "tdSpbe6XeCGKdoNzmlj0GjZ3JwxCAuJD04G6n0f9tktJ9BQfZLqIdQzoVDc8u6/0U"
            "0rK3T1KJsds4ACttbpG5vdGXECHQZRyOgXayIo3JjdsQgo/ACrPJD2Jcet6aY9cOe"
            "NdKpDERmfRWKHzWD18RqTSyjc25kxCCj8AKs8kPYlx63ppj1w5410qkMRGZ9FYofN"
            "YPXxGpNLKR0eXBlo3BheQ=="
        )

        self.assertEqual(goldenTxg, txg)

        # repeat test above for assign_group_id
        txa1 = copy.deepcopy(tx1)
        txa2 = copy.deepcopy(tx2)

        txns = transaction.assign_group_id([txa1, txa2])
        self.assertEqual(len(txns), 2)
        stx1 = transaction.SignedTransaction(txns[0], None)
        stx2 = transaction.SignedTransaction(txns[1], None)

        # goal clerk group sets Group to every transaction and concatenate
        # them in output file
        # simulating that behavior here
        txg = base64.b64encode(
            base64.b64decode(encoding.msgpack_encode(stx1))
            + base64.b64decode(encoding.msgpack_encode(stx2))
        ).decode()

        self.assertEqual(goldenTxg, txg)

        # check filtering
        txns = transaction.assign_group_id([tx1, tx2], address=fromAddress)
        self.assertEqual(len(txns), 2)
        self.assertEqual(stx1.transaction.group, txns[0].group)

        txns = transaction.assign_group_id([tx1, tx2], address="NONEXISTENT")
        self.assertEqual(len(txns), 0)


class TestAssetConfigConveniences(unittest.TestCase):
    """Tests that the simplified versions of Config are equivalent to Config"""

    sender = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
    genesis = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
    params = transaction.SuggestedParams(0, 1, 100, genesis)

    def test_asset_create(self):
        create = transaction.AssetCreateTxn(
            self.sender,
            self.params,
            1000,
            "2",
            False,
            manager=None,
            reserve=None,
            freeze=None,
            clawback=None,
            unit_name="NEWCOIN",
            asset_name="A new kind of coin",
            url="https://newcoin.co/",
        )
        config = transaction.AssetConfigTxn(
            self.sender,
            self.params,
            index=None,
            total="1000",
            decimals=2,
            unit_name="NEWCOIN",
            asset_name="A new kind of coin",
            url="https://newcoin.co/",
            strict_empty_address_check=False,
        )
        self.assertEqual(create.dictify(), config.dictify())
        self.assertEqual(config, create)

        self.assertEqual(
            transaction.AssetCreateTxn.undictify(create.dictify()), config
        )

    def test_asset_update(self):
        update = transaction.AssetUpdateTxn(
            self.sender,
            self.params,
            6,
            manager=None,
            reserve=self.sender,
            freeze=None,
            clawback=None,
        )
        config = transaction.AssetConfigTxn(
            self.sender,
            self.params,
            index="6",
            reserve=self.sender,
            strict_empty_address_check=False,
        )
        self.assertEqual(update.dictify(), config.dictify())
        self.assertEqual(config, update)

        self.assertEqual(
            transaction.AssetUpdateTxn.undictify(update.dictify()), config
        )

    def test_asset_destroy(self):
        destroy = transaction.AssetDestroyTxn(self.sender, self.params, 23)
        config = transaction.AssetConfigTxn(
            self.sender,
            self.params,
            index="23",
            strict_empty_address_check=False,
        )
        self.assertEqual(destroy.dictify(), config.dictify())
        self.assertEqual(config, destroy)

        self.assertEqual(
            transaction.AssetDestroyTxn.undictify(destroy.dictify()), config
        )


class TestAssetTransferConveniences(unittest.TestCase):
    sender = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
    receiver = "DOMUC6VGZH7SSY5V332JR5HRLZSOJDWNPBI4OI2IIBU6A3PFLOBOXZ3KFY"
    genesis = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
    params = transaction.SuggestedParams(0, 1, 100, genesis)

    def test_asset_optin(self):
        optin = transaction.AssetOptInTxn(self.sender, self.params, "7")
        xfer = transaction.AssetTransferTxn(
            self.sender, self.params, self.sender, 0, index=7
        )
        self.assertEqual(optin.dictify(), xfer.dictify())
        self.assertEqual(xfer, optin)

        self.assertEqual(
            transaction.AssetOptInTxn.undictify(optin.dictify()), xfer
        )

    def test_asset_closeout(self):
        closeout = transaction.AssetCloseOutTxn(
            self.sender, self.params, self.receiver, "7"
        )
        xfer = transaction.AssetTransferTxn(
            self.sender,
            self.params,
            self.receiver,
            0,
            index=7,
            close_assets_to=self.receiver,
        )
        self.assertEqual(closeout.dictify(), xfer.dictify())
        self.assertEqual(xfer, closeout)

        self.assertEqual(
            transaction.AssetCloseOutTxn.undictify(closeout.dictify()), xfer
        )


class TestApplicationTransactions(unittest.TestCase):
    sender = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
    genesis = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
    lschema = transaction.StateSchema(1, 2)
    gschema = transaction.StateSchema(3, 4)

    def test_application_address(self):
        appID = 77
        expected = "PCYUFPA2ZTOYWTP43MX2MOX2OWAIAXUDNC2WFCXAGMRUZ3DYD6BWFDL5YM"
        actual = logic.get_application_address(appID)
        self.assertEqual(actual, expected)

        appID = "seventy seven"
        with self.assertRaises(AssertionError):
            logic.get_application_address(appID)

    def test_application_call(self):
        params = transaction.SuggestedParams(0, 1, 100, self.genesis)
        for oc in transaction.OnComplete:
            b = transaction.ApplicationCallTxn(
                self.sender, params, 10, oc, app_args=[b"hello"]
            )
            s = transaction.ApplicationCallTxn(
                self.sender, params, "10", oc, app_args=["hello"]
            )
            self.assertEqual(
                b, s
            )  # string is encoded same as corresponding bytes
            transaction.ApplicationCallTxn(
                self.sender, params, 10, oc, app_args=[2, 3, 0]
            )  # ints work
            with self.assertRaises(TypeError):
                transaction.ApplicationCallTxn(
                    self.sender, params, 10, oc, app_args=[3.4]
                )  # floats don't
            with self.assertRaises(OverflowError):
                transaction.ApplicationCallTxn(
                    self.sender, params, 10, oc, app_args=[-10]
                )  # nor negative
            transaction.ApplicationCallTxn(
                self.sender,
                params,
                10,
                oc,  # maxuint64
                app_args=[18446744073709551615],
            )
            with self.assertRaises(OverflowError):
                transaction.ApplicationCallTxn(
                    self.sender,
                    params,
                    10,
                    oc,  # too big
                    app_args=[18446744073709551616],
                )

            i = transaction.ApplicationCallTxn(
                self.sender,
                params,
                10,
                oc,
                foreign_apps=[4, 3],
                foreign_assets=(2, 1),
            )
            s = transaction.ApplicationCallTxn(
                self.sender,
                params,
                "10",
                oc,
                foreign_apps=["4", 3],
                foreign_assets=[2, "1"],
            )
            self.assertEqual(
                i, s
            )  # string is encoded same as corresponding int

    def test_application_create(self):
        approve = b"\0"
        clear = b"\1"
        params = transaction.SuggestedParams(0, 1, 100, self.genesis)
        for oc in transaction.OnComplete:
            # We will confirm that the Create is just shorthand for
            # the Call.  But note that the programs come before the
            # schemas and the schemas are REVERSED!  That's
            # unfortunate, and we should consider adding "*" to the
            # argument list after on_completion, thereby forcing the
            # use of named arguments.
            create = transaction.ApplicationCreateTxn(
                self.sender,
                params,
                oc,
                approve,
                clear,
                self.lschema,
                self.gschema,
            )
            call = transaction.ApplicationCallTxn(
                self.sender,
                params,
                0,
                oc,
                self.gschema,
                self.lschema,
                approve,
                clear,
            )
            # Check the dict first, it's important on it's own, and it
            # also gives more a meaningful error if they're not equal.
            self.assertEqual(create.dictify(), call.dictify())
            self.assertEqual(create, call)
            self.assertEqual(call, create)

    def test_application_create_schema(self):
        approve = b"\0"
        clear = b"\1"
        zero_schema = transaction.StateSchema(0, 0)
        params = transaction.SuggestedParams(0, 1, 100, self.genesis)
        for oc in transaction.OnComplete:
            # verify that a schema with 0 uints and 0 bytes behaves the same as no schema
            txn_zero_schema = transaction.ApplicationCreateTxn(
                self.sender,
                params,
                oc,
                approve,
                clear,
                zero_schema,
                zero_schema,
            )
            txn_none_schema = transaction.ApplicationCreateTxn(
                self.sender, params, oc, approve, clear, None, None
            )
            # Check the dict first, it's important on its own, and it
            # also gives more a meaningful error if they're not equal.
            self.assertEqual(
                txn_zero_schema.dictify(), txn_none_schema.dictify()
            )
            self.assertEqual(txn_zero_schema, txn_none_schema)
            self.assertEqual(txn_none_schema, txn_zero_schema)

    def test_application_update(self):
        empty = b""
        params = transaction.SuggestedParams(0, 1, 100, self.genesis)
        i = transaction.ApplicationUpdateTxn(
            self.sender, params, 10, empty, empty
        )
        s = transaction.ApplicationUpdateTxn(
            self.sender, params, "10", empty, empty
        )
        self.assertEqual(i, s)  # int and string encoded same

        call = transaction.ApplicationCallTxn(
            self.sender,
            params,
            10,
            transaction.OnComplete.UpdateApplicationOC,
            None,
            None,
            empty,
            empty,
        )
        self.assertEqual(i.dictify(), call.dictify())
        self.assertEqual(i, call)

    def test_application_delete(self):
        params = transaction.SuggestedParams(0, 1, 100, self.genesis)
        i = transaction.ApplicationDeleteTxn(self.sender, params, 10)
        s = transaction.ApplicationDeleteTxn(self.sender, params, "10")
        self.assertEqual(i, s)  # int and string encoded same

        call = transaction.ApplicationCallTxn(
            self.sender, params, 10, transaction.OnComplete.DeleteApplicationOC
        )
        self.assertEqual(i.dictify(), call.dictify())
        self.assertEqual(i, call)


class TestBoxReference(unittest.TestCase):
    def test_translate_box_references(self):
        # Test case: reference input, foreign app array, caller app id, expected output
        test_cases = [
            ([], [], 9999, []),
            (
                [(100, "potato")],
                [100],
                9999,
                [transaction.BoxReference(1, "potato".encode())],
            ),
            (
                [(9999, "potato"), (0, "tomato")],
                [100],
                9999,
                [
                    transaction.BoxReference(0, "potato".encode()),
                    transaction.BoxReference(0, "tomato".encode()),
                ],
            ),
            # Self referencing its own app id in foreign array.
            (
                [(100, "potato")],
                [100],
                100,
                [transaction.BoxReference(1, "potato".encode())],
            ),
            (
                [(777, "tomato"), (888, "pomato")],
                [100, 777, 888, 1000],
                9999,
                [
                    transaction.BoxReference(2, "tomato".encode()),
                    transaction.BoxReference(3, "pomato".encode()),
                ],
            ),
        ]
        for test_case in test_cases:
            expected = test_case[3]
            actual = transaction.BoxReference.translate_box_references(
                test_case[0], test_case[1], test_case[2]
            )

            self.assertEqual(len(expected), len(actual))
            for i, actual_refs in enumerate(actual):
                self.assertEqual(expected[i], actual_refs)

    def test_translate_invalid_box_references(self):
        # Test case: reference input, foreign app array, error
        test_cases_id_error = [
            ([(1, "tomato")], [], error.InvalidForeignIndexError),
            ([(-1, "tomato")], [1], error.InvalidForeignIndexError),
            (
                [(444, "pomato")],
                [2, 3, 100, 888],
                error.InvalidForeignIndexError,
            ),
            (
                [(2, "tomato"), (444, "pomato")],
                [2, 3, 100, 888],
                error.InvalidForeignIndexError,
            ),
            ([("tomato", "tomato")], [1], TypeError),
            ([(2, "zomato")], None, error.InvalidForeignIndexError),
        ]

        for test_case in test_cases_id_error:
            with self.assertRaises(test_case[2]) as e:
                transaction.BoxReference.translate_box_references(
                    test_case[0], test_case[1], 9999
                )
