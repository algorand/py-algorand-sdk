import base64
import copy
import random
import unittest
from unittest.mock import Mock

from nacl.signing import SigningKey

from algosdk import (account, constants, encoding, error, logic, mnemonic,
                     util, wordlist)
from algosdk.future import template, transaction
from algosdk.testing import dryrun


class TestPaymentTransaction(unittest.TestCase):
    def test_min_txn_fee(self):
        address = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
        gh = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
        sp = transaction.SuggestedParams(0, 1, 100, gh)
        txn = transaction.PaymentTxn(address, sp, address,
                                     1000, note=b'\x00')
        self.assertEqual(constants.min_txn_fee, txn.fee)

    def test_note_wrong_type(self):
        address = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
        gh = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
        sp = transaction.SuggestedParams(0, 1, 100, gh)
        f = lambda: transaction.PaymentTxn(address, sp, address,
                                           1000, note=45)
        self.assertRaises(error.WrongNoteType, f)

    def test_note_strings_allowed(self):
        address = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
        gh = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
        sp = transaction.SuggestedParams(0, 1, 100, gh)
        txn = transaction.PaymentTxn(address, sp, address,
                                     1000, note="helo")
        self.assertEqual(constants.min_txn_fee, txn.fee)

    def test_note_wrong_length(self):
        address = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
        gh = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
        sp = transaction.SuggestedParams(0, 1, 100, gh)
        f = lambda: transaction.PaymentTxn(address, sp, address,
                                           1000, note=("0"*1025).encode())
        self.assertRaises(error.WrongNoteLength, f)

    def test_leases(self):
        address = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
        gh = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
        sp = transaction.SuggestedParams(0, 1, 100, gh)
        # 32 byte zero lease should be dropped from msgpack
        txn1 = transaction.PaymentTxn(address, sp, address,
                                      1000, lease=(b"\0"*32))
        txn2 = transaction.PaymentTxn(address, sp, address,
                                      1000)

        self.assertEqual(txn1.dictify(), txn2.dictify())
        self.assertEqual(txn1, txn2)
        self.assertEqual(txn2, txn1)

    def test_serialize(self):
        address = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
        gh = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
        sp = transaction.SuggestedParams(3, 1, 100, gh)
        txn = transaction.PaymentTxn(address, sp, address,
                                     1000, note=bytes([1, 32, 200]))
        enc = encoding.msgpack_encode(txn)
        re_enc = encoding.msgpack_encode(encoding.msgpack_decode(enc))
        self.assertEqual(enc, re_enc)

    def test_serialize_with_note_string_encode(self):
        address = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
        gh = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
        sp = transaction.SuggestedParams(3, 1, 100, gh)
        txn = transaction.PaymentTxn(address, sp, address,
                                     1000, note="hello".encode())
        enc = encoding.msgpack_encode(txn)
        re_enc = encoding.msgpack_encode(encoding.msgpack_decode(enc))
        self.assertEqual(enc, re_enc)

    def test_serialize_with_note_max_length(self):
        address = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
        gh = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
        sp = transaction.SuggestedParams(3, 1, 100, gh)
        txn = transaction.PaymentTxn(address, sp, address,
                                     1000, note=("0"*1024).encode())
        enc = encoding.msgpack_encode(txn)
        re_enc = encoding.msgpack_encode(encoding.msgpack_decode(enc))
        self.assertEqual(enc, re_enc)

    def test_serialize_zero_amt(self):
        address = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
        gh = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
        sp = transaction.SuggestedParams(3, 1, 100, gh)
        txn = transaction.PaymentTxn(address, sp, address,
                                     0, note=bytes([1, 32, 200]))
        enc = encoding.msgpack_encode(txn)
        re_enc = encoding.msgpack_encode(encoding.msgpack_decode(enc))
        self.assertEqual(enc, re_enc)

    def test_serialize_gen(self):
        address = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
        gh = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
        sp = transaction.SuggestedParams(3, 1, 100, gh, "testnet-v1.0")
        txn = transaction.PaymentTxn(address, sp, address,
                                     1000, close_remainder_to=address)
        enc = encoding.msgpack_encode(txn)
        re_enc = encoding.msgpack_encode(encoding.msgpack_decode(enc))
        self.assertEqual(enc, re_enc)

    def test_serialize_txgroup(self):
        address = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
        gh = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
        sp = transaction.SuggestedParams(3, 1, 100, gh, "testnet-v1.0")
        txn = transaction.PaymentTxn(address, sp, address,
                                     1000, close_remainder_to=address)
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
            "spital century reform able sponsor")
        gh = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
        address = "PNWOET7LLOWMBMLE4KOCELCX6X3D3Q4H2Q4QJASYIEOF7YIPPQBG3YQ5YI"
        close = "IDUTJEUIEVSMXTU4LGTJWZ2UE2E6TIODUKU6UW3FU3UKIQQ77RLUBBBFLA"
        sk = mnemonic.to_private_key(mn)
        pk = account.address_from_private_key(sk)
        sp = transaction.SuggestedParams(4, 12466, 13466, gh, "devnet-v33.0")
        txn = transaction.PaymentTxn(
            pk, sp, address, 1000, note=base64.b64decode("6gAVR0Nsv5Y="),
            close_remainder_to=close)
        stx = txn.sign(sk)
        golden = (
            "gqNzaWfEQPhUAZ3xkDDcc8FvOVo6UinzmKBCqs0woYSfodlmBMfQvGbeUx3Srxy3d"
            "yJDzv7rLm26BRv9FnL2/AuT7NYfiAWjdHhui6NhbXTNA+ilY2xvc2XEIEDpNJKIJW"
            "TLzpxZpptnVCaJ6aHDoqnqW2Wm6KRCH/xXo2ZlZc0EmKJmds0wsqNnZW6sZGV2bmV"
            "0LXYzMy4womdoxCAmCyAJoJOohot5WHIvpeVG7eftF+TYXEx4r7BFJpDt0qJsds00"
            "mqRub3RlxAjqABVHQ2y/lqNyY3bEIHts4k/rW6zAsWTinCIsV/X2PcOH1DkEglhBH"
            "F/hD3wCo3NuZMQg5/D4TQaBHfnzHI2HixFV9GcdUaGFwgCQhmf0SVhwaKGkdHlwZa"
            "NwYXk=")
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

        params = transaction.SuggestedParams(0, 447, 1447, gh, gen="network-v1")
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
            "2XuuO6mS+3IetwlKVPM0qdKBIiMVdhzAOMPKpHR5cGWjcGF5")

        encoded = encoding.msgpack_encode(lstx)
        self.assertEqual(encoded, golden)

    def test_serialize_zero_receiver(self):
        address = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
        receiver = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAY5HFKQ"
        gh = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
        sp = transaction.SuggestedParams(3, 1, 100, gh)
        txn = transaction.PaymentTxn(address, sp, receiver,
                                     1000, note=bytes([1, 32, 200]))

        golden = (
            "iKNhbXTNA+ijZmVlzQPoomZ2AaJnaMQgJgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMe"
            "K+wRSaQ7dKibHZkpG5vdGXEAwEgyKNzbmTEIP5oQQPnKvM7kbGuuSOunAVfSbJzHQ"
            "tAtCP3Bf2XdDxmpHR5cGWjcGF5")

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
            "spital century reform able sponsor")
        sk = mnemonic.to_private_key(mn)
        pk = mnemonic.to_public_key(mn)
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
            "NwYXk=")

        self.assertEqual(golden, encoding.msgpack_encode(signed_txn))

    def test_serialize_pay_lease(self):
        mn = (
            "advice pudding treat near rule blouse same whisper inner electric"
            " quit surface sunny dismiss leader blood seat clown cost exist ho"
            "spital century reform able sponsor")
        sk = mnemonic.to_private_key(mn)
        pk = mnemonic.to_public_key(mn)
        to = "PNWOET7LLOWMBMLE4KOCELCX6X3D3Q4H2Q4QJASYIEOF7YIPPQBG3YQ5YI"
        fee = 4
        first_round = 12466
        last_round = 13466
        gh = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
        gen = "devnet-v33.0"
        note = base64.b64decode("6gAVR0Nsv5Y=")
        close = "IDUTJEUIEVSMXTU4LGTJWZ2UE2E6TIODUKU6UW3FU3UKIQQ77RLUBBBFLA"
        amount = 1000
        lease = bytes([1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3,
                       4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4])
        sp = transaction.SuggestedParams(fee, first_round, last_round, gh, gen)
        txn = transaction.PaymentTxn(
            pk, sp, to, amount, close_remainder_to=close, note=note,
            lease=lease)
        signed_txn = txn.sign(sk)

        golden = (
            "gqNzaWfEQOMmFSIKsZvpW0txwzhmbgQjxv6IyN7BbV5sZ2aNgFbVcrWUnqPpQQxfP"
            "hV/wdu9jzEPUU1jAujYtcNCxJ7ONgejdHhujKNhbXTNA+ilY2xvc2XEIEDpNJKIJW"
            "TLzpxZpptnVCaJ6aHDoqnqW2Wm6KRCH/xXo2ZlZc0FLKJmds0wsqNnZW6sZGV2bmV"
            "0LXYzMy4womdoxCAmCyAJoJOohot5WHIvpeVG7eftF+TYXEx4r7BFJpDt0qJsds00"
            "mqJseMQgAQIDBAECAwQBAgMEAQIDBAECAwQBAgMEAQIDBAECAwSkbm90ZcQI6gAVR"
            "0Nsv5ajcmN2xCB7bOJP61uswLFk4pwiLFf19j3Dh9Q5BIJYQRxf4Q98AqNzbmTEIO"
            "fw+E0GgR358xyNh4sRVfRnHVGhhcIAkIZn9ElYcGihpHR5cGWjcGF5")

        self.assertEqual(golden, encoding.msgpack_encode(signed_txn))

    def test_serialize_keyreg_online(self):
        mn = (
            "awful drop leaf tennis indoor begin mandate discover uncle seven "
            "only coil atom any hospital uncover make any climb actor armed me"
            "asure need above hundred")
        sk = mnemonic.to_private_key(mn)
        pk = mnemonic.to_public_key(mn)
        fee = 1000
        gh = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
        votepk = "Kv7QI7chi1y6axoy+t7wzAVpePqRq/rkjzWh/RMYyLo="
        selpk = "bPgrv4YogPcdaUAxrt1QysYZTVyRAuUMD4zQmCu9llc="
        votefirst = 10000
        votelast = 10111
        votedilution = 11

        sp = transaction.SuggestedParams(
            fee, 322575, 323575, gh, flat_fee=True)
        txn = transaction.KeyregTxn(pk, sp, votepk, selpk, votefirst, votelast,
                                    votedilution)
        signed_txn = txn.sign(sk)

        golden = (
            "gqNzaWfEQEA8ANbrvTRxU9c8v6WERcEPw7D/HacRgg4vICa61vEof60Wwtx6KJKDy"
            "vBuvViFeacLlngPY6vYCVP0DktTwQ2jdHhui6NmZWXNA+iiZnbOAATsD6JnaMQgSG"
            "O1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiKibHbOAATv96ZzZWxrZXnEIGz"
            "4K7+GKID3HWlAMa7dUMrGGU1ckQLlDA+M0JgrvZZXo3NuZMQgCfvSdiwI+Gxa5r9t"
            "16epAd5mdddQ4H6MXHaYZH224f2kdHlwZaZrZXlyZWendm90ZWZzdM0nEKZ2b3Rla"
            "2QLp3ZvdGVrZXnEICr+0CO3IYtcumsaMvre8MwFaXj6kav65I81of0TGMi6p3ZvdG"
            "Vsc3TNJ38=")
        self.assertEqual(golden, encoding.msgpack_encode(signed_txn))

    def test_serialize_keyreg_offline(self):
        mn = (
            "awful drop leaf tennis indoor begin mandate discover uncle seven "
            "only coil atom any hospital uncover make any climb actor armed "
            "measure need above hundred")
        sk = mnemonic.to_private_key(mn)
        pk = mnemonic.to_public_key(mn)
        fee = 1000
        gh = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
        votepk = None
        selpk = None
        votefirst = None
        votelast = None
        votedilution = None

        sp = transaction.SuggestedParams(
            fee, 12299691, 12300691, gh, flat_fee=True)
        txn = transaction.KeyregTxn(pk, sp, votepk, selpk, votefirst, votelast,
                                    votedilution)
        signed_txn = txn.sign(sk)

        golden = (
            "gqNzaWfEQJosTMSKwGr+eWN5XsAJvbjh2DkzOtEN6lrDNM4TAnYIjl9L43zU70gAX"
            "USAehZo9RyejgDA12B75SR6jIdhzQCjdHhuhqNmZWXNA+iiZnbOALutq6JnaMQgSG"
            "O1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiKibHbOALuxk6NzbmTEIAn70nYs"
            "CPhsWua/bdenqQHeZnXXUOB+jFx2mGR9tuH9pHR5cGWma2V5cmVn")
        self.assertEqual(golden, encoding.msgpack_encode(signed_txn))

    def test_serialize_keyreg_nonpart(self):
        mn = (
            "awful drop leaf tennis indoor begin mandate discover uncle seven "
            "only coil atom any hospital uncover make any climb actor armed "
            "measure need above hundred")
        sk = mnemonic.to_private_key(mn)
        pk = mnemonic.to_public_key(mn)
        fee = 1000
        gh = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
        nonpart = True

        sp = transaction.SuggestedParams(
            fee, 12299691, 12300691, gh, flat_fee=True)
        txn = transaction.KeyregTxn(pk, sp, None, None, None, None, None,
                                    nonpart=nonpart)
        signed_txn = txn.sign(sk)

        golden = (
            "gqNzaWfEQN7kw3tLcC1IweQ2Ru5KSqFS0Ba0cn34ncOWPIyv76wU8JPLxyS8alErm4"
            "PHg3Q7n1Mfqa9SQ9zDY+FMeZLLgQyjdHhuh6NmZWXNA+iiZnbOALutq6JnaMQgSGO1"
            "GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiKibHbOALuxk6dub25wYXJ0w6Nzbm"
            "TEIAn70nYsCPhsWua/bdenqQHeZnXXUOB+jFx2mGR9tuH9pHR5cGWma2V5cmVn")
        self.assertEqual(golden, encoding.msgpack_encode(signed_txn))

    def test_serialize_asset_create(self):
        mn = (
            "awful drop leaf tennis indoor begin mandate discover uncle seven "
            "only coil atom any hospital uncover make any climb actor armed me"
            "asure need above hundred")
        sk = mnemonic.to_private_key(mn)
        pk = mnemonic.to_public_key(mn)
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
            pk, sp, total=total, manager=pk, reserve=pk, freeze=pk,
            clawback=pk, unit_name=unitname, asset_name=assetname, url=url,
            metadata_hash=metadata, default_frozen=False)
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
            "fbbh/aR0eXBlpGFjZmc=")
        self.assertEqual(golden, encoding.msgpack_encode(signed_txn))

    def test_serialize_asset_create_decimal(self):
        mn = (
            "awful drop leaf tennis indoor begin mandate discover uncle seven "
            "only coil atom any hospital uncover make any climb actor armed me"
            "asure need above hundred")
        sk = mnemonic.to_private_key(mn)
        pk = mnemonic.to_public_key(mn)
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
            pk, sp, total=total, manager=pk, reserve=pk, freeze=pk,
            clawback=pk, unit_name=unitname, asset_name=assetname, url=url,
            metadata_hash=metadata, default_frozen=False, decimals=1)
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
            "XHaYZH224f2kdHlwZaRhY2Zn")
        self.assertEqual(golden, encoding.msgpack_encode(signed_txn))

    def test_asset_empty_address_error(self):
        pk = "DN7MBMCL5JQ3PFUQS7TMX5AH4EEKOBJVDUF4TCV6WERATKFLQF4MQUPZTA"
        fee = 10
        first_round = 322575
        last_round = 323575
        gh = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
        index = 1234
        sp = transaction.SuggestedParams(fee, first_round, last_round, gh)
        self.assertRaises(error.EmptyAddressError, transaction.AssetConfigTxn,
                          pk, sp, reserve=pk,
                          freeze=pk, clawback=pk, index=index)

    def test_serialize_asset_config(self):
        mn = (
            "awful drop leaf tennis indoor begin mandate discover uncle seven "
            "only coil atom any hospital uncover make any climb actor armed me"
            "asure need above hundred")
        sk = mnemonic.to_private_key(mn)
        pk = mnemonic.to_public_key(mn)
        fee = 10
        first_round = 322575
        last_round = 323575
        gh = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
        index = 1234
        sp = transaction.SuggestedParams(fee, first_round, last_round, gh)
        txn = transaction.AssetConfigTxn(
            pk, sp, manager=pk, reserve=pk, freeze=pk, clawback=pk,
            index=index)
        signed_txn = txn.sign(sk)
        golden = (
            "gqNzaWfEQBBkfw5n6UevuIMDo2lHyU4dS80JCCQ/vTRUcTx5m0ivX68zTKyuVRrHa"
            "TbxbRRc3YpJ4zeVEnC9Fiw3Wf4REwejdHhuiKRhcGFyhKFjxCAJ+9J2LAj4bFrmv2"
            "3Xp6kB3mZ111Dgfoxcdphkfbbh/aFmxCAJ+9J2LAj4bFrmv23Xp6kB3mZ111Dgfox"
            "cdphkfbbh/aFtxCAJ+9J2LAj4bFrmv23Xp6kB3mZ111Dgfoxcdphkfbbh/aFyxCAJ"
            "+9J2LAj4bFrmv23Xp6kB3mZ111Dgfoxcdphkfbbh/aRjYWlkzQTSo2ZlZc0NSKJmd"
            "s4ABOwPomdoxCBIY7UYpLPITsgQ8i1PEIHLD3HwWaesIN7GL39w5Qk6IqJsds4ABO"
            "/3o3NuZMQgCfvSdiwI+Gxa5r9t16epAd5mdddQ4H6MXHaYZH224f2kdHlwZaRhY2Z"
            "n")

        self.assertEqual(golden, encoding.msgpack_encode(signed_txn))

    def test_serialize_asset_destroy(self):
        mn = (
            "awful drop leaf tennis indoor begin mandate discover uncle seven "
            "only coil atom any hospital uncover make any climb actor armed me"
            "asure need above hundred")
        sk = mnemonic.to_private_key(mn)
        pk = mnemonic.to_public_key(mn)
        fee = 10
        first_round = 322575
        last_round = 323575
        gh = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
        index = 1
        sp = transaction.SuggestedParams(fee, first_round, last_round, gh)
        txn = transaction.AssetConfigTxn(
            pk, sp, index=index, strict_empty_address_check=False)
        signed_txn = txn.sign(sk)
        golden = (
            "gqNzaWfEQBSP7HtzD/Lvn4aVvaNpeR4T93dQgo4LvywEwcZgDEoc/WVl3aKsZGcZk"
            "cRFoiWk8AidhfOZzZYutckkccB8RgGjdHhuh6RjYWlkAaNmZWXNB1iiZnbOAATsD6"
            "JnaMQgSGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiKibHbOAATv96NzbmT"
            "EIAn70nYsCPhsWua/bdenqQHeZnXXUOB+jFx2mGR9tuH9pHR5cGWkYWNmZw==")
        self.assertEqual(golden, encoding.msgpack_encode(signed_txn))

    def test_serialize_asset_freeze(self):
        mn = (
            "awful drop leaf tennis indoor begin mandate discover uncle seven "
            "only coil atom any hospital uncover make any climb actor armed me"
            "asure need above hundred")
        sk = mnemonic.to_private_key(mn)
        pk = mnemonic.to_public_key(mn)
        fee = 10
        first_round = 322575
        last_round = 323576
        gh = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
        index = 1
        target = "BH55E5RMBD4GYWXGX5W5PJ5JAHPGM5OXKDQH5DC4O2MGI7NW4H6VOE4CP4"
        sp = transaction.SuggestedParams(fee, first_round, last_round, gh)
        txn = transaction.AssetFreezeTxn(
            pk, sp, index=index, target=target, new_freeze_state=True)
        signed_txn = txn.sign(sk)
        golden = (
            "gqNzaWfEQAhru5V2Xvr19s4pGnI0aslqwY4lA2skzpYtDTAN9DKSH5+qsfQQhm4oq"
            "+9VHVj7e1rQC49S28vQZmzDTVnYDQGjdHhuiaRhZnJ6w6RmYWRkxCAJ+9J2LAj4bF"
            "rmv23Xp6kB3mZ111Dgfoxcdphkfbbh/aRmYWlkAaNmZWXNCRqiZnbOAATsD6JnaMQ"
            "gSGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiKibHbOAATv+KNzbmTEIAn7"
            "0nYsCPhsWua/bdenqQHeZnXXUOB+jFx2mGR9tuH9pHR5cGWkYWZyeg==")
        self.assertEqual(golden, encoding.msgpack_encode(signed_txn))

    def test_serialize_asset_transfer(self):
        mn = (
            "awful drop leaf tennis indoor begin mandate discover uncle seven "
            "only coil atom any hospital uncover make any climb actor armed me"
            "asure need above hundred")
        sk = mnemonic.to_private_key(mn)
        pk = mnemonic.to_public_key(mn)
        fee = 10
        first_round = 322575
        last_round = 323576
        gh = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
        index = 1
        amount = 1
        to = "BH55E5RMBD4GYWXGX5W5PJ5JAHPGM5OXKDQH5DC4O2MGI7NW4H6VOE4CP4"
        close = "BH55E5RMBD4GYWXGX5W5PJ5JAHPGM5OXKDQH5DC4O2MGI7NW4H6VOE4CP4"
        sp = transaction.SuggestedParams(fee, first_round, last_round, gh)
        txn = transaction.AssetTransferTxn(
            pk, sp, to, amount, index, close)
        signed_txn = txn.sign(sk)
        golden = (
            "gqNzaWfEQNkEs3WdfFq6IQKJdF1n0/hbV9waLsvojy9pM1T4fvwfMNdjGQDy+Lees"
            "uQUfQVTneJD4VfMP7zKx4OUlItbrwSjdHhuiqRhYW10AaZhY2xvc2XEIAn70nYsCP"
            "hsWua/bdenqQHeZnXXUOB+jFx2mGR9tuH9pGFyY3bEIAn70nYsCPhsWua/bdenqQH"
            "eZnXXUOB+jFx2mGR9tuH9o2ZlZc0KvqJmds4ABOwPomdoxCBIY7UYpLPITsgQ8i1P"
            "EIHLD3HwWaesIN7GL39w5Qk6IqJsds4ABO/4o3NuZMQgCfvSdiwI+Gxa5r9t16epA"
            "d5mdddQ4H6MXHaYZH224f2kdHlwZaVheGZlcqR4YWlkAQ==")
        self.assertEqual(golden, encoding.msgpack_encode(signed_txn))

    def test_serialize_asset_accept(self):
        mn = (
            "awful drop leaf tennis indoor begin mandate discover uncle seven "
            "only coil atom any hospital uncover make any climb actor armed me"
            "asure need above hundred")
        sk = mnemonic.to_private_key(mn)
        pk = mnemonic.to_public_key(mn)
        fee = 10
        first_round = 322575
        last_round = 323575
        gh = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
        index = 1
        amount = 0
        to = "BH55E5RMBD4GYWXGX5W5PJ5JAHPGM5OXKDQH5DC4O2MGI7NW4H6VOE4CP4"
        sp = transaction.SuggestedParams(fee, first_round, last_round, gh)
        txn = transaction.AssetTransferTxn(
            pk, sp, to, amount, index)
        signed_txn = txn.sign(sk)
        golden = (
            "gqNzaWfEQJ7q2rOT8Sb/wB0F87ld+1zMprxVlYqbUbe+oz0WM63FctIi+K9eYFSqT"
            "26XBZ4Rr3+VTJpBE+JLKs8nctl9hgijdHhuiKRhcmN2xCAJ+9J2LAj4bFrmv23Xp6"
            "kB3mZ111Dgfoxcdphkfbbh/aNmZWXNCOiiZnbOAATsD6JnaMQgSGO1GKSzyE7IEPI"
            "tTxCByw9x8FmnrCDexi9/cOUJOiKibHbOAATv96NzbmTEIAn70nYsCPhsWua/bden"
            "qQHeZnXXUOB+jFx2mGR9tuH9pHR5cGWlYXhmZXKkeGFpZAE=")
        self.assertEqual(golden, encoding.msgpack_encode(signed_txn))

    def test_serialize_asset_revoke(self):
        mn = (
            "awful drop leaf tennis indoor begin mandate discover uncle seven "
            "only coil atom any hospital uncover make any climb actor armed me"
            "asure need above hundred")
        sk = mnemonic.to_private_key(mn)
        pk = mnemonic.to_public_key(mn)
        fee = 10
        first_round = 322575
        last_round = 323575
        gh = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
        index = 1
        amount = 1
        to = "BH55E5RMBD4GYWXGX5W5PJ5JAHPGM5OXKDQH5DC4O2MGI7NW4H6VOE4CP4"
        sp = transaction.SuggestedParams(fee, first_round, last_round, gh)
        txn = transaction.AssetTransferTxn(
            pk, sp, to, amount, index, revocation_target=to)
        signed_txn = txn.sign(sk)
        golden = (
            "gqNzaWfEQHsgfEAmEHUxLLLR9s+Y/yq5WeoGo/jAArCbany+7ZYwExMySzAhmV7M7"
            "S8+LBtJalB4EhzEUMKmt3kNKk6+vAWjdHhuiqRhYW10AaRhcmN2xCAJ+9J2LAj4bF"
            "rmv23Xp6kB3mZ111Dgfoxcdphkfbbh/aRhc25kxCAJ+9J2LAj4bFrmv23Xp6kB3mZ"
            "111Dgfoxcdphkfbbh/aNmZWXNCqqiZnbOAATsD6JnaMQgSGO1GKSzyE7IEPItTxCB"
            "yw9x8FmnrCDexi9/cOUJOiKibHbOAATv96NzbmTEIAn70nYsCPhsWua/bdenqQHeZ"
            "nXXUOB+jFx2mGR9tuH9pHR5cGWlYXhmZXKkeGFpZAE=")
        self.assertEqual(golden, encoding.msgpack_encode(signed_txn))

    def test_pay_float_amt(self):
        address = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
        gh = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
        sp = transaction.SuggestedParams(3, 1, 100, gh)
        f = lambda: transaction.PaymentTxn(address, sp, address,
                                           10., note=bytes([1, 32, 200]))
        self.assertRaises(error.WrongAmountType, f)

    def test_pay_negative_amt(self):
        address = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
        gh = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
        sp = transaction.SuggestedParams(3, 1, 100, gh)
        f = lambda: transaction.PaymentTxn(address, sp, address,
                                           -5, note=bytes([1, 32, 200]))
        self.assertRaises(error.WrongAmountType, f)

    def test_asset_transfer_float_amt(self):
        address = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
        fee = 10
        first_round = 322575
        last_round = 323576
        gh = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
        index = 1
        amount = 1.
        to = "BH55E5RMBD4GYWXGX5W5PJ5JAHPGM5OXKDQH5DC4O2MGI7NW4H6VOE4CP4"
        close = "BH55E5RMBD4GYWXGX5W5PJ5JAHPGM5OXKDQH5DC4O2MGI7NW4H6VOE4CP4"
        sp = transaction.SuggestedParams(fee, first_round, last_round, gh)
        f = lambda: transaction.AssetTransferTxn(
            address, sp, to, amount, index, close)
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
            address, sp, to, amount, index, close)
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
            fee, firstRound1, firstRound1+1000, genesisHash, genesisID,
            flat_fee=True)
        tx1 = transaction.PaymentTxn(
            fromAddress, sp, toAddress, amount,
            note=note1)

        firstRound2 = 710515
        note2 = base64.b64decode("dBlHI6BdrIg=")

        sp.first = firstRound2
        sp.last = firstRound2 + 1000
        tx2 = transaction.PaymentTxn(
            fromAddress, sp, toAddress, amount,
            note=note2)

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
            base64.b64decode(encoding.msgpack_encode(stx1)) +
            base64.b64decode(encoding.msgpack_encode(stx2))
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
            base64.b64decode(encoding.msgpack_encode(stx1)) +
            base64.b64decode(encoding.msgpack_encode(stx2))
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
        create = transaction.AssetCreateTxn(self.sender, self.params,
                                            1000, "2", False,
                                            manager=None,
                                            reserve=None,
                                            freeze=None,
                                            clawback=None,
                                            unit_name="NEWCOIN",
                                            asset_name="A new kind of coin",
                                            url="https://newcoin.co/")
        config = transaction.AssetConfigTxn(self.sender, self.params, index=None,
                                            total="1000", decimals=2,
                                            unit_name="NEWCOIN",
                                            asset_name="A new kind of coin",
                                            url="https://newcoin.co/",
                                            strict_empty_address_check=False)
        self.assertEqual(create.dictify(), config.dictify())
        self.assertEqual(config, create)

        self.assertEqual(transaction.AssetCreateTxn.undictify(create.dictify()),
                         config)


    def test_asset_update(self):
        update = transaction.AssetUpdateTxn(self.sender, self.params, 6,
                                            manager=None,
                                            reserve=self.sender,
                                            freeze=None,
                                            clawback=None)
        config = transaction.AssetConfigTxn(self.sender, self.params, index="6",
                                            reserve=self.sender,
                                            strict_empty_address_check=False)
        self.assertEqual(update.dictify(), config.dictify())
        self.assertEqual(config, update)

        self.assertEqual(transaction.AssetUpdateTxn.undictify(update.dictify()),
                         config)

    def test_asset_destroy(self):
        destroy = transaction.AssetDestroyTxn(self.sender, self.params, 23)
        config = transaction.AssetConfigTxn(self.sender, self.params, index="23",
                                            strict_empty_address_check=False)
        self.assertEqual(destroy.dictify(), config.dictify())
        self.assertEqual(config, destroy)

        self.assertEqual(transaction.AssetDestroyTxn.undictify(destroy.dictify()),
                         config)

class TestAssetTransferConveniences(unittest.TestCase):
    sender = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
    receiver = "DOMUC6VGZH7SSY5V332JR5HRLZSOJDWNPBI4OI2IIBU6A3PFLOBOXZ3KFY"
    genesis = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
    params = transaction.SuggestedParams(0, 1, 100, genesis)
    def test_asset_optin(self):
        optin = transaction.AssetOptInTxn(self.sender, self.params, "7")
        xfer = transaction.AssetTransferTxn(self.sender, self.params, self.sender,
                                            0, index=7)
        self.assertEqual(optin.dictify(), xfer.dictify())
        self.assertEqual(xfer, optin)

        self.assertEqual(transaction.AssetOptInTxn.undictify(optin.dictify()),
                         xfer)

    def test_asset_closeout(self):
        closeout = transaction.AssetCloseOutTxn(self.sender, self.params,
                                                self.receiver, "7")
        xfer = transaction.AssetTransferTxn(self.sender, self.params, self.receiver,
                                            0, index=7, close_assets_to=self.receiver)
        self.assertEqual(closeout.dictify(), xfer.dictify())
        self.assertEqual(xfer, closeout)

        self.assertEqual(transaction.AssetCloseOutTxn.undictify(closeout.dictify()),
                         xfer)

class TestApplicationTransactions(unittest.TestCase):
    sender = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
    genesis = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
    lschema = transaction.StateSchema(1, 2)
    gschema = transaction.StateSchema(3, 4)

    def test_application_call(self):
        params = transaction.SuggestedParams(0, 1, 100, self.genesis)
        for oc in transaction.OnComplete:
            b = transaction.ApplicationCallTxn(self.sender, params, 10, oc,
                                               app_args=[b"hello"])
            s = transaction.ApplicationCallTxn(self.sender, params, "10", oc,
                                               app_args=["hello"])
            self.assertEqual(b, s) # string is encoded same as corresponding bytes
            transaction.ApplicationCallTxn(self.sender, params, 10, oc,
                                           app_args=[2,3,0]) # ints work
            with self.assertRaises(AssertionError):
                transaction.ApplicationCallTxn(self.sender, params, 10, oc,
                                               app_args=[3.4]) # floats don't
            with self.assertRaises(OverflowError):
                transaction.ApplicationCallTxn(self.sender, params, 10, oc,
                                               app_args=[-10]) # nor negative
            transaction.ApplicationCallTxn(self.sender, params, 10, oc, # maxuint64
                                           app_args=[18446744073709551615])
            with self.assertRaises(OverflowError):
                transaction.ApplicationCallTxn(self.sender, params, 10, oc, # too big
                                               app_args=[18446744073709551616])

            i = transaction.ApplicationCallTxn(self.sender, params, 10, oc,
                                               foreign_apps=[4, 3],
                                               foreign_assets=(2,1))
            s = transaction.ApplicationCallTxn(self.sender, params, "10", oc,
                                               foreign_apps=["4", 3],
                                               foreign_assets=[2, "1"])
            self.assertEqual(i, s) # string is encoded same as corresponding int

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
            create = transaction.ApplicationCreateTxn(self.sender, params, oc,
                                                      approve, clear,
                                                      self.lschema, self.gschema)
            call = transaction.ApplicationCallTxn(self.sender, params, 0, oc,
                                                  self.gschema, self.lschema,
                                                  approve, clear)
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
            txn_zero_schema = transaction.ApplicationCreateTxn(self.sender, params, oc,
                                                      approve, clear,
                                                      zero_schema, zero_schema)
            txn_none_schema = transaction.ApplicationCreateTxn(self.sender, params, oc,
                                                      approve, clear,
                                                      None, None)
            # Check the dict first, it's important on its own, and it
            # also gives more a meaningful error if they're not equal.
            self.assertEqual(txn_zero_schema.dictify(), txn_none_schema.dictify())
            self.assertEqual(txn_zero_schema, txn_none_schema)
            self.assertEqual(txn_none_schema, txn_zero_schema)

    def test_application_update(self):
        empty = b""
        params = transaction.SuggestedParams(0, 1, 100, self.genesis)
        i = transaction.ApplicationUpdateTxn(self.sender, params, 10, empty, empty)
        s = transaction.ApplicationUpdateTxn(self.sender, params, "10", empty, empty)
        self.assertEqual(i, s) # int and string encoded same

        call = transaction.ApplicationCallTxn(self.sender, params, 10,
                                              transaction.OnComplete.UpdateApplicationOC,
                                              None, None,
                                              empty, empty)
        self.assertEqual(i.dictify(), call.dictify())
        self.assertEqual(i, call)

    def test_application_delete(self):
        params = transaction.SuggestedParams(0, 1, 100, self.genesis)
        i = transaction.ApplicationDeleteTxn(self.sender, params, 10)
        s = transaction.ApplicationDeleteTxn(self.sender, params, "10")
        self.assertEqual(i, s) # int and string encoded same

        call = transaction.ApplicationCallTxn(self.sender, params, 10,
                                              transaction.OnComplete.DeleteApplicationOC)
        self.assertEqual(i.dictify(), call.dictify())
        self.assertEqual(i, call)

class TestMnemonic(unittest.TestCase):
    zero_bytes = bytes([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

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
            "invest")
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
            "abandon")
        self.assertRaises(error.WrongChecksumError, mnemonic._to_key, mn)

    def test_word_not_in_list(self):
        mn = (
            "abandon abandon abandon abandon abandon abandon abandon abandon "
            "abandon abandon abandon abandon abandon abandon abandon abandon "
            "abandon abandon abandon venues abandon abandon abandon abandon "
            "invest")
        self.assertRaises(ValueError, mnemonic._to_key, mn)
        mn = (
            "abandon abandon abandon abandon abandon abandon abandon abandon "
            "abandon abandon abandon abandon abandon abandon abandon abandon "
            "abandon abandon abandon abandon abandon abandon abandon abandon "
            "x-ray")
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
        key = bytes([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        self.assertRaises(error.WrongKeyBytesLengthError,
                          mnemonic._from_key, key)

    def test_key_wrong_len(self):
        address = "WRONG_LENGTH_TOO_SHORT"
        self.assertRaises(error.WrongKeyLengthError,
                          encoding.decode_address, address)


class TestAddress(unittest.TestCase):
    def test_is_valid(self):
        valid = "MO2H6ZU47Q36GJ6GVHUKGEBEQINN7ZWVACMWZQGIYUOE3RBSRVYHV4ACJI"
        self.assertTrue(encoding.is_valid_address(valid))
        invalid = "MO2H6ZU47Q36GJ6GVHUKGEBEQINN7ZWVACMWZQGIYUOE3RBSRVYHV4ACJG"
        self.assertFalse(encoding.is_valid_address(invalid))

    def test_encode_decode(self):
        sk, pk = account.generate_account()
        self.assertEqual(pk, encoding.encode_address(
                         encoding.decode_address(pk)))
        self.assertEqual(pk, account.address_from_private_key(sk))


class TestMultisig(unittest.TestCase):
    def test_merge(self):
        msig = transaction.Multisig(1, 2, [
            "DN7MBMCL5JQ3PFUQS7TMX5AH4EEKOBJVDUF4TCV6WERATKFLQF4MQUPZTA",
            "BFRTECKTOOE7A5LHCF3TTEOH2A7BW46IYT2SX5VP6ANKEXHZYJY77SJTVM",
            "47YPQTIGQEO7T4Y4RWDYWEKV6RTR2UNBQXBABEEGM72ESWDQNCQ52OPASU"
        ])
        mn = (
            "auction inquiry lava second expand liberty glass involve ginger i"
            "llness length room item discover ahead table doctor term tackle c"
            "ement bonus profit right above catch")

        sk = mnemonic.to_private_key(mn)
        sender = "RWJLJCMQAFZ2ATP2INM2GZTKNL6OULCCUBO5TQPXH3V2KR4AG7U5UA5JNM"
        rcv = "PNWOET7LLOWMBMLE4KOCELCX6X3D3Q4H2Q4QJASYIEOF7YIPPQBG3YQ5YI"
        gh = "/rNsORAUOQDD2lVCyhg2sA/S+BlZElfNI/YEL5jINp0="
        close = "IDUTJEUIEVSMXTU4LGTJWZ2UE2E6TIODUKU6UW3FU3UKIQQ77RLUBBBFLA"

        sp = transaction.SuggestedParams(0, 62229, 63229, gh, "devnet-v38.0")
        txn = transaction.PaymentTxn(
            sender, sp, rcv, 1000, note=base64.b64decode("RSYiABhShvs="),
            close_remainder_to=close)

        mtx = transaction.MultisigTransaction(txn, msig)
        mtx.sign(sk)
        golden = (
            "gqRtc2lng6ZzdWJzaWeTgqJwa8QgG37AsEvqYbeWkJfmy/QH4QinBTUdC8mKvrEiC"
            "airgXihc8RAuLAFE0oma0skOoAmOzEwfPuLYpEWl4LINtsiLrUqWQkDxh4WHb29//"
            "YCpj4MFbiSgD2jKYt0XKRD86zKCF4RDYGicGvEIAljMglTc4nwdWcRdzmRx9A+G3P"
            "IxPUr9q/wGqJc+cJxgaJwa8Qg5/D4TQaBHfnzHI2HixFV9GcdUaGFwgCQhmf0SVhw"
            "aKGjdGhyAqF2AaN0eG6Lo2FtdM0D6KVjbG9zZcQgQOk0koglZMvOnFmmm2dUJonpo"
            "cOiqepbZabopEIf/FejZmVlzQPoomZ2zfMVo2dlbqxkZXZuZXQtdjM4LjCiZ2jEIP"
            "6zbDkQFDkAw9pVQsoYNrAP0vgZWRJXzSP2BC+YyDadomx2zfb9pG5vdGXECEUmIgA"
            "YUob7o3JjdsQge2ziT+tbrMCxZOKcIixX9fY9w4fUOQSCWEEcX+EPfAKjc25kxCCN"
            "krSJkAFzoE36Q1mjZmpq/OosQqBd2cH3PuulR4A36aR0eXBlo3BheQ==")
        self.assertEqual(golden, encoding.msgpack_encode(mtx))

        mtx_2 = transaction.MultisigTransaction(txn,
                                                msig.get_multisig_account())
        mn2 = (
            "since during average anxiety protect cherry club long lawsuit loa"
            "n expand embark forum theory winter park twenty ball kangaroo cra"
            "m burst board host ability left")
        sk2 = mnemonic.to_private_key(mn2)
        mtx_2.sign(sk2)

        mtx_final = transaction.MultisigTransaction.merge([mtx, mtx_2])

        golden2 = (
            "gqRtc2lng6ZzdWJzaWeTgqJwa8QgG37AsEvqYbeWkJfmy/QH4QinBTUdC8mKvrEiC"
            "airgXihc8RAuLAFE0oma0skOoAmOzEwfPuLYpEWl4LINtsiLrUqWQkDxh4WHb29//"
            "YCpj4MFbiSgD2jKYt0XKRD86zKCF4RDYKicGvEIAljMglTc4nwdWcRdzmRx9A+G3P"
            "IxPUr9q/wGqJc+cJxoXPEQBAhuyRjsOrnHp3s/xI+iMKiL7QPsh8iJZ22YOJJP0aF"
            "UwedMr+a6wfdBXk1OefyrAN1wqJ9rq6O+DrWV1fH0ASBonBrxCDn8PhNBoEd+fMcj"
            "YeLEVX0Zx1RoYXCAJCGZ/RJWHBooaN0aHICoXYBo3R4boujYW10zQPopWNsb3NlxC"
            "BA6TSSiCVky86cWaabZ1Qmiemhw6Kp6ltlpuikQh/8V6NmZWXNA+iiZnbN8xWjZ2V"
            "urGRldm5ldC12MzguMKJnaMQg/rNsORAUOQDD2lVCyhg2sA/S+BlZElfNI/YEL5jI"
            "Np2ibHbN9v2kbm90ZcQIRSYiABhShvujcmN2xCB7bOJP61uswLFk4pwiLFf19j3Dh"
            "9Q5BIJYQRxf4Q98AqNzbmTEII2StImQAXOgTfpDWaNmamr86ixCoF3Zwfc+66VHgD"
            "fppHR5cGWjcGF5")
        self.assertEqual(golden2, encoding.msgpack_encode(mtx_final))

    def test_sign(self):
        msig = transaction.Multisig(1, 2, [
            "DN7MBMCL5JQ3PFUQS7TMX5AH4EEKOBJVDUF4TCV6WERATKFLQF4MQUPZTA",
            "BFRTECKTOOE7A5LHCF3TTEOH2A7BW46IYT2SX5VP6ANKEXHZYJY77SJTVM",
            "47YPQTIGQEO7T4Y4RWDYWEKV6RTR2UNBQXBABEEGM72ESWDQNCQ52OPASU"
        ])
        mn = (
            "advice pudding treat near rule blouse same whisper inner electric"
            " quit surface sunny dismiss leader blood seat clown cost exist ho"
            "spital century reform able sponsor")
        sk = mnemonic.to_private_key(mn)

        rcv = "PNWOET7LLOWMBMLE4KOCELCX6X3D3Q4H2Q4QJASYIEOF7YIPPQBG3YQ5YI"
        gh = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
        close = "IDUTJEUIEVSMXTU4LGTJWZ2UE2E6TIODUKU6UW3FU3UKIQQ77RLUBBBFLA"
        sp = transaction.SuggestedParams(4, 12466, 13466, gh, "devnet-v33.0")
        txn = transaction.PaymentTxn(
            msig.address(), sp, rcv, 1000,
            note=base64.b64decode("X4Bl4wQ9rCo="), close_remainder_to=close)
        mtx = transaction.MultisigTransaction(txn, msig)
        mtx.sign(sk)
        golden = (
            "gqRtc2lng6ZzdWJzaWeTgaJwa8QgG37AsEvqYbeWkJfmy/QH4QinBTUdC8mKvrEiC"
            "airgXiBonBrxCAJYzIJU3OJ8HVnEXc5kcfQPhtzyMT1K/av8BqiXPnCcYKicGvEIO"
            "fw+E0GgR358xyNh4sRVfRnHVGhhcIAkIZn9ElYcGihoXPEQF6nXZ7CgInd1h7NVsp"
            "IPFZNhkPL+vGFpTNwH3Eh9gwPM8pf1EPTHfPvjf14sS7xN7mTK+wrz7Odhp4rdWBN"
            "UASjdGhyAqF2AaN0eG6Lo2FtdM0D6KVjbG9zZcQgQOk0koglZMvOnFmmm2dUJonpo"
            "cOiqepbZabopEIf/FejZmVlzQSYomZ2zTCyo2dlbqxkZXZuZXQtdjMzLjCiZ2jEIC"
            "YLIAmgk6iGi3lYci+l5Ubt5+0X5NhcTHivsEUmkO3Somx2zTSapG5vdGXECF+AZeM"
            "EPawqo3JjdsQge2ziT+tbrMCxZOKcIixX9fY9w4fUOQSCWEEcX+EPfAKjc25kxCCN"
            "krSJkAFzoE36Q1mjZmpq/OosQqBd2cH3PuulR4A36aR0eXBlo3BheQ==")
        self.assertEqual(golden, encoding.msgpack_encode(mtx))
        txid_golden = "TDIO6RJWJIVDDJZELMSX5CPJW7MUNM3QR4YAHYAKHF3W2CFRTI7A"
        self.assertEqual(txn.get_txid(), txid_golden)

    def test_msig_address(self):
        msig = transaction.Multisig(1, 2, [
            "XMHLMNAVJIMAW2RHJXLXKKK4G3J3U6VONNO3BTAQYVDC3MHTGDP3J5OCRU",
            "HTNOX33OCQI2JCOLZ2IRM3BC2WZ6JUILSLEORBPFI6W7GU5Q4ZW6LINHLA",
            "E6JSNTY4PVCY3IRZ6XEDHEO6VIHCQ5KGXCIQKFQCMB2N6HXRY4IB43VSHI"])
        golden = "UCE2U2JC4O4ZR6W763GUQCG57HQCDZEUJY4J5I6VYY4HQZUJDF7AKZO5GM"
        self.assertEqual(msig.address(), golden)

        msig2 = transaction.Multisig(1, 2, [
            "DN7MBMCL5JQ3PFUQS7TMX5AH4EEKOBJVDUF4TCV6WERATKFLQF4MQUPZTA",
            "BFRTECKTOOE7A5LHCF3TTEOH2A7BW46IYT2SX5VP6ANKEXHZYJY77SJTVM",
            "47YPQTIGQEO7T4Y4RWDYWEKV6RTR2UNBQXBABEEGM72ESWDQNCQ52OPASU"])
        golden = "RWJLJCMQAFZ2ATP2INM2GZTKNL6OULCCUBO5TQPXH3V2KR4AG7U5UA5JNM"
        self.assertEqual(msig2.address(), golden)

    def test_errors(self):

        # get random private key
        private_key_1, account_1 = account.generate_account()
        _, account_2 = account.generate_account()
        private_key_3, account_3 = account.generate_account()

        # create transaction
        gh = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
        sp = transaction.SuggestedParams(3, 1234, 1334, gh)
        txn = transaction.PaymentTxn(account_2, sp, account_2, 1000)

        # create multisig address with invalid version
        msig = transaction.Multisig(2, 2, [account_1, account_2])
        self.assertRaises(error.UnknownMsigVersionError, msig.validate)

        # change it to have invalid threshold
        msig.version = 1
        msig.threshold = 3
        self.assertRaises(error.InvalidThresholdError, msig.validate)

        # try to sign multisig transaction
        msig.threshold = 2
        mtx = transaction.MultisigTransaction(txn, msig)
        self.assertRaises(error.BadTxnSenderError,
                          mtx.sign, private_key_1)

        # change sender address to be correct
        txn.sender = msig.address()
        mtx = transaction.MultisigTransaction(txn, msig)

        # try to sign with incorrect private key
        self.assertRaises(error.InvalidSecretKeyError,
                          mtx.sign, private_key_3)

        # create another multisig with different address
        msig_2 = transaction.Multisig(1, 2, [account_2, account_3])

        # try to merge with different addresses
        mtx_2 = transaction.MultisigTransaction(txn, msig_2)
        self.assertRaises(error.MergeKeysMismatchError,
                          transaction.MultisigTransaction.merge,
                          [mtx, mtx_2])

        # create another multisig with same address
        msig_3 = msig_2.get_multisig_account()

        # add mismatched signatures
        msig_2.subsigs[0].signature = "sig2"
        msig_3.subsigs[0].signature = "sig3"

        # try to merge
        self.assertRaises(error.DuplicateSigMismatchError,
                          transaction.MultisigTransaction.merge,
                          [transaction.MultisigTransaction(txn, msig_2),
                           transaction.MultisigTransaction(txn, msig_3)])


class TestMsgpack(unittest.TestCase):
    def test_bid(self):
        bid = (
            "gqFigqNiaWSGo2FpZAGjYXVjxCCokNFWl9DCqHrP9trjPICAMGOaRoX/OR+M6tHWh"
            "fUBkKZiaWRkZXLEIP1rCXe2x5+exPBfU3CZwGPMY8mzwvglET+QtgfCPdCmo2N1cs"
            "8AAADN9kTOAKJpZM5JeDcCpXByaWNlzQMgo3NpZ8RAiR06J4suAixy13BKHlw4VrO"
            "RKzLT5CJr9n3YSj0Ao6byV23JHGU0yPf7u9/o4ECw4Xy9hc9pWopLW97xKXRfA6F0"
            "oWI=")
        self.assertEqual(bid, encoding.msgpack_encode(
                         encoding.msgpack_decode(bid)))

    def test_signed_txn(self):
        stxn = (
            "gqNzaWfEQGdpjnStb70k2iXzOlu+RSMgCYLe25wkUfbgRsXs7jx6rbW61ivCs6/zG"
            "s3gZAZf4L2XAQak7OjMh3lw9MTCIQijdHhuiaNhbXTOAAGGoKNmZWXNA+iiZnbNcl"
            "+jZ2Vuq25ldHdvcmstdjM4omdoxCBN/+nfiNPXLbuigk8M/TXsMUfMK7dV//xB1wk"
            "oOhNu9qJsds1yw6NyY3bEIPRUuVDPVUFC7Jk3+xDjHJfwWFDp+Wjy+Hx3cwL9ncVY"
            "o3NuZMQgGC5kQiOIPooA8mrvoHRyFtk27F/PPN08bAufGhnp0BGkdHlwZaNwYXk=")
        self.assertEqual(stxn, encoding.msgpack_encode(
                         encoding.msgpack_decode(stxn)))

    def test_payment_txn(self):
        paytxn = (
            "iaNhbXTOAAGGoKNmZWXNA+iiZnbNcq2jZ2Vuq25ldHdvcmstdjM4omdoxCBN/+nfi"
            "NPXLbuigk8M/TXsMUfMK7dV//xB1wkoOhNu9qJsds1zEaNyY3bEIAZ2cvp4J0OiBy"
            "5eAHIX/njaRko955rEdN4AUNEl4rxTo3NuZMQgGC5kQiOIPooA8mrvoHRyFtk27F/"
            "PPN08bAufGhnp0BGkdHlwZaNwYXk=")
        self.assertEqual(paytxn, encoding.msgpack_encode(
                         encoding.msgpack_decode(paytxn)))

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
            "Xo/AiI6kdHlwZaNwYXk=")
        self.assertEqual(msigtxn, encoding.msgpack_encode(
                         encoding.msgpack_decode(msigtxn)))

    def test_keyreg_txn_online(self):
        keyregtxn = (
            "jKNmZWXNA+iiZnbNcoqjZ2Vuq25ldHdvcmstdjM4omdoxCBN/+nfiNPXLbuigk8M/"
            "TXsMUfMK7dV//xB1wkoOhNu9qJsds1y7qZzZWxrZXnEIBguZEIjiD6KAPJq76B0ch"
            "bZNuxfzzzdPGwLnxoZ6dARo3NuZMQgGC5kQiOIPooA8mrvoHRyFtk27F/PPN08bAu"
            "fGhnp0BGkdHlwZaZrZXlyZWendm90ZWZzdM1yiqZ2b3Rla2TNMDmndm90ZWtlecQg"
            "GC5kQiOIPooA8mrvoHRyFtk27F/PPN08bAufGhnp0BGndm90ZWxzdM1y7g==")
        self.assertEqual(keyregtxn, encoding.msgpack_encode(
                         encoding.msgpack_decode(keyregtxn)))

    def test_keyreg_txn_offline(self):
        keyregtxn = (
            "hqNmZWXNA+iiZnbOALutq6JnaMQgSGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/c"
            "OUJOiKibHbOALuxk6NzbmTEIAn70nYsCPhsWua/bdenqQHeZnXXUOB+jFx2mGR9tu"
            "H9pHR5cGWma2V5cmVn")
        # using future_msgpack_decode instead of msgpack_decode
        # because non-future transactions do not support offline keyreg
        self.assertEqual(keyregtxn, encoding.msgpack_encode(
                         encoding.future_msgpack_decode(keyregtxn)))

    def test_keyreg_txn_nonpart(self):
        keyregtxn = (
            "h6NmZWXNA+iiZnbOALutq6JnaMQgSGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/c"
            "OUJOiKibHbOALuxk6dub25wYXJ0w6NzbmTEIAn70nYsCPhsWua/bdenqQHeZnXXUO"
            "B+jFx2mGR9tuH9pHR5cGWma2V5cmVn")
        # using future_msgpack_decode instead of msgpack_decode
        # because non-future transactions do not support nonpart keyreg
        self.assertEqual(keyregtxn, encoding.msgpack_encode(
                         encoding.future_msgpack_decode(keyregtxn)))

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
            "fbbh/aR0eXBlpGFjZmc=")
        self.assertEqual(golden, encoding.msgpack_encode(
                         encoding.msgpack_decode(golden)))

    def test_asset_config(self):
        assettxn = (
            "gqNzaWfEQBBkfw5n6UevuIMDo2lHyU4dS80JCCQ/vTRUcTx5m0ivX68zTKyuVRrHa"
            "TbxbRRc3YpJ4zeVEnC9Fiw3Wf4REwejdHhuiKRhcGFyhKFjxCAJ+9J2LAj4bFrmv2"
            "3Xp6kB3mZ111Dgfoxcdphkfbbh/aFmxCAJ+9J2LAj4bFrmv23Xp6kB3mZ111Dgfox"
            "cdphkfbbh/aFtxCAJ+9J2LAj4bFrmv23Xp6kB3mZ111Dgfoxcdphkfbbh/aFyxCAJ"
            "+9J2LAj4bFrmv23Xp6kB3mZ111Dgfoxcdphkfbbh/aRjYWlkzQTSo2ZlZc0NSKJmd"
            "s4ABOwPomdoxCBIY7UYpLPITsgQ8i1PEIHLD3HwWaesIN7GL39w5Qk6IqJsds4ABO"
            "/3o3NuZMQgCfvSdiwI+Gxa5r9t16epAd5mdddQ4H6MXHaYZH224f2kdHlwZaRhY2Z"
            "n")
        self.assertEqual(assettxn, encoding.msgpack_encode(
                         encoding.msgpack_decode(assettxn)))

    def test_asset_config_with_decimal(self):
        assettxn = (
            "gqNzaWfEQBBkfw5n6UevuIMDo2lHyU4dS80JCCQ/vTRUcTx5m0ivX68zTKyuVRrHa"
            "TbxbRRc3YpJ4zeVEnC9Fiw3Wf4REwejdHhuiKRhcGFyhaFjxCAJ+9J2LAj4bFrmv2"
            "3Xp6kB3mZ111Dgfoxcdphkfbbh/aJkYwyhZsQgCfvSdiwI+Gxa5r9t16epAd5mddd"
            "Q4H6MXHaYZH224f2hbcQgCfvSdiwI+Gxa5r9t16epAd5mdddQ4H6MXHaYZH224f2h"
            "csQgCfvSdiwI+Gxa5r9t16epAd5mdddQ4H6MXHaYZH224f2kY2FpZM0E0qNmZWXND"
            "UiiZnbOAATsD6JnaMQgSGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiKibH"
            "bOAATv96NzbmTEIAn70nYsCPhsWua/bdenqQHeZnXXUOB+jFx2mGR9tuH9pHR5cGW"
            "kYWNmZw==")
        self.assertEqual(assettxn, encoding.msgpack_encode(
                         encoding.msgpack_decode(assettxn)))

    def test_asset_destroy(self):
        assettxn = (
            "gqNzaWfEQBSP7HtzD/Lvn4aVvaNpeR4T93dQgo4LvywEwcZgDEoc/WVl3aKsZGcZk"
            "cRFoiWk8AidhfOZzZYutckkccB8RgGjdHhuh6RjYWlkAaNmZWXNB1iiZnbOAATsD6"
            "JnaMQgSGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiKibHbOAATv96NzbmT"
            "EIAn70nYsCPhsWua/bdenqQHeZnXXUOB+jFx2mGR9tuH9pHR5cGWkYWNmZw==")
        self.assertEqual(assettxn, encoding.msgpack_encode(
                         encoding.msgpack_decode(assettxn)))

    def test_asset_freeze(self):
        assettxn = (
            "gqNzaWfEQAhru5V2Xvr19s4pGnI0aslqwY4lA2skzpYtDTAN9DKSH5+qsfQQhm4oq"
            "+9VHVj7e1rQC49S28vQZmzDTVnYDQGjdHhuiaRhZnJ6w6RmYWRkxCAJ+9J2LAj4bF"
            "rmv23Xp6kB3mZ111Dgfoxcdphkfbbh/aRmYWlkAaNmZWXNCRqiZnbOAATsD6JnaMQ"
            "gSGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiKibHbOAATv+KNzbmTEIAn7"
            "0nYsCPhsWua/bdenqQHeZnXXUOB+jFx2mGR9tuH9pHR5cGWkYWZyeg==")
        self.assertEqual(assettxn, encoding.msgpack_encode(
                         encoding.msgpack_decode(assettxn)))

    def test_asset_transfer(self):
        assettxn = (
            "gqNzaWfEQNkEs3WdfFq6IQKJdF1n0/hbV9waLsvojy9pM1T4fvwfMNdjGQDy+Lees"
            "uQUfQVTneJD4VfMP7zKx4OUlItbrwSjdHhuiqRhYW10AaZhY2xvc2XEIAn70nYsCP"
            "hsWua/bdenqQHeZnXXUOB+jFx2mGR9tuH9pGFyY3bEIAn70nYsCPhsWua/bdenqQH"
            "eZnXXUOB+jFx2mGR9tuH9o2ZlZc0KvqJmds4ABOwPomdoxCBIY7UYpLPITsgQ8i1P"
            "EIHLD3HwWaesIN7GL39w5Qk6IqJsds4ABO/4o3NuZMQgCfvSdiwI+Gxa5r9t16epA"
            "d5mdddQ4H6MXHaYZH224f2kdHlwZaVheGZlcqR4YWlkAQ==")
        self.assertEqual(assettxn, encoding.msgpack_encode(
                         encoding.msgpack_decode(assettxn)))

    def test_asset_accept(self):
        assettxn = (
            "gqNzaWfEQJ7q2rOT8Sb/wB0F87ld+1zMprxVlYqbUbe+oz0WM63FctIi+K9eYFSqT"
            "26XBZ4Rr3+VTJpBE+JLKs8nctl9hgijdHhuiKRhcmN2xCAJ+9J2LAj4bFrmv23Xp6"
            "kB3mZ111Dgfoxcdphkfbbh/aNmZWXNCOiiZnbOAATsD6JnaMQgSGO1GKSzyE7IEPI"
            "tTxCByw9x8FmnrCDexi9/cOUJOiKibHbOAATv96NzbmTEIAn70nYsCPhsWua/bden"
            "qQHeZnXXUOB+jFx2mGR9tuH9pHR5cGWlYXhmZXKkeGFpZAE=")
        self.assertEqual(assettxn, encoding.msgpack_encode(
                         encoding.msgpack_decode(assettxn)))

    def test_asset_revoke(self):
        assettxn = (
            "gqNzaWfEQHsgfEAmEHUxLLLR9s+Y/yq5WeoGo/jAArCbany+7ZYwExMySzAhmV7M7"
            "S8+LBtJalB4EhzEUMKmt3kNKk6+vAWjdHhuiqRhYW10AaRhcmN2xCAJ+9J2LAj4bF"
            "rmv23Xp6kB3mZ111Dgfoxcdphkfbbh/aRhc25kxCAJ+9J2LAj4bFrmv23Xp6kB3mZ"
            "111Dgfoxcdphkfbbh/aNmZWXNCqqiZnbOAATsD6JnaMQgSGO1GKSzyE7IEPItTxCB"
            "yw9x8FmnrCDexi9/cOUJOiKibHbOAATv96NzbmTEIAn70nYsCPhsWua/bdenqQHeZ"
            "nXXUOB+jFx2mGR9tuH9pHR5cGWlYXhmZXKkeGFpZAE=")
        self.assertEqual(assettxn, encoding.msgpack_encode(
                         encoding.msgpack_decode(assettxn)))


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
        intarray[0] = (intarray[0]+1) % 256
        changed_message = bytes(intarray)
        self.assertFalse(util.verify_bytes(changed_message, signature, pk))


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
            b"\x32\x33\x02\x01\x02")
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

        self.assertTrue(logic.check_program(program, ['a' * 10]))

        # too long arg
        with self.assertRaises(error.InvalidProgram):
            logic.check_program(program, ['a' * 1000])

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
            programv=v+program
            with self.assertRaises(error.InvalidProgram):
                logic.check_program(programv, [])
        
        versions = [b"\x04"]
        for v in versions:
            programv=v+program
            self.assertTrue(logic.check_program(programv, None))

    def test_check_program_teal_2(self):
        # check TEAL v2 opcodes
        self.assertIsNotNone(logic.spec, "Must be called after any of logic.check_program")
        self.assertTrue(logic.spec['EvalMaxVersion'] >= 2)
        self.assertTrue(logic.spec['LogicSigVersion'] >= 2)

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
        self.assertIsNotNone(logic.spec, "Must be called after any of logic.check_program")
        self.assertTrue(logic.spec['EvalMaxVersion'] >= 3)
        self.assertTrue(logic.spec['LogicSigVersion'] >= 3)

        # min_balance
        program = b"\x03\x20\x01\x00\x22\x78" # int 0; min_balance
        self.assertTrue(logic.check_program(program, None))

        # pushbytes
        program = b"\x03\x20\x01\x00\x22\x80\x02\x68\x69\x48" # int 0; pushbytes "hi"; pop
        self.assertTrue(logic.check_program(program, None))

        # pushint
        program = b"\x03\x20\x01\x00\x22\x81\x01\x48" # int 0; pushint 1; pop
        self.assertTrue(logic.check_program(program, None))

        # swap
        program = b"\x03\x20\x02\x00\x01\x22\x23\x4c\x48" # int 0; int 1; swap; pop
        self.assertTrue(logic.check_program(program, None))

    def test_teal_sign(self):
        """test tealsign"""
        data = base64.b64decode("Ux8jntyBJQarjKGF8A==")
        seed = base64.b64decode("5Pf7eGMA52qfMT4R4/vYCt7con/7U3yejkdXkrcb26Q=")
        program = base64.b64decode("ASABASI=")
        addr = "6Z3C3LDVWGMX23BMSYMANACQOSINPFIRF77H7N3AWJZYV6OH6GWTJKVMXY"

        key = SigningKey(seed)
        verify_key = key.verify_key
        private_key = base64.b64encode(key.encode() + verify_key.encode()).decode()
        sig1 = logic.teal_sign(private_key, data, addr)
        sig2 = logic.teal_sign_from_program(private_key, data, program)
        self.assertEqual(sig1, sig2)

        msg = constants.logic_data_prefix + encoding.decode_address(addr) + data
        res = verify_key.verify(msg, sig1)
        self.assertIsNotNone(res)

    def test_check_program_teal_4(self):
        # check TEAL v4 opcodes
        self.assertIsNotNone(logic.spec, "Must be called after any of logic.check_program")
        self.assertTrue(logic.spec['EvalMaxVersion'] >= 4)

        # divmodw
        program = b"\x04\x20\x03\x01\x00\x02\x22\x81\xd0\x0f\x23\x24\x1f" # int 1; pushint 2000; int 0; int 2; divmodw
        self.assertTrue(logic.check_program(program, None))

        # gloads i
        program = b"\x04\x20\x01\x00\x22\x3b\x00" # int 0; gloads 0
        self.assertTrue(logic.check_program(program, None))
        
        # callsub
        program = b"\x04\x20\x02\x01\x02\x22\x88\x00\x02\x23\x12\x49" # int 1; callsub double; int 2; ==; double: dup;
        self.assertTrue(logic.check_program(program, None))

        # b>=
        program = b"\x04\x26\x02\x01\x11\x01\x10\x28\x29\xa7" # byte 0x11; byte 0x10; b>=
        self.assertTrue(logic.check_program(program, None))

        # b^
        program = b"\x04\x26\x03\x01\x11\x01\x10\x01\x01\x28\x29\xad\x2a\x12" # byte 0x11; byte 0x10; b>=
        self.assertTrue(logic.check_program(program, None))

        # callsub, retsub
        program = b"\x04\x20\x02\x01\x02\x22\x88\x00\x03\x23\x12\x43\x49\x08\x89" # int 1; callsub double; int 2; ==; return; double: dup; +; retsub;
        self.assertTrue(logic.check_program(program, None))

        # loop
        program = b"\x04\x20\x04\x01\x02\x0a\x10\x22\x23\x0b\x49\x24\x0c\x40\xff\xf8\x25\x12" # int 1; loop: int 2; *; dup; int 10; <; bnz loop; int 16; ==
        self.assertTrue(logic.check_program(program, None))

class TestLogicSig(unittest.TestCase):
    def test_basic(self):
        with self.assertRaises(error.InvalidProgram):
            lsig = transaction.LogicSig(None)

        with self.assertRaises(error.InvalidProgram):
            lsig = transaction.LogicSig(b"")

        program = b"\x01\x20\x01\x01\x22"  # int 1
        program_hash = (
            "6Z3C3LDVWGMX23BMSYMANACQOSINPFIRF77H7N3AWJZYV6OH6GWTJKVMXY")
        public_key = encoding.decode_address(program_hash)

        lsig = transaction.LogicSig(program)
        self.assertEqual(lsig.logic, program)
        self.assertEqual(lsig.args, None)
        self.assertEqual(lsig.sig, None)
        self.assertEqual(lsig.msig, None)
        verified = lsig.verify(public_key)
        self.assertTrue(verified)
        self.assertEqual(lsig.address(), program_hash)

        args = [
            b"\x01\x02\x03",
            b"\x04\x05\x06",
        ]
        lsig = transaction.LogicSig(program, args)
        self.assertEqual(lsig.logic, program)
        self.assertEqual(lsig.args, args)
        self.assertEqual(lsig.sig, None)
        self.assertEqual(lsig.msig, None)
        verified = lsig.verify(public_key)
        self.assertTrue(verified)

        # check serialization
        encoded = encoding.msgpack_encode(lsig)
        decoded = encoding.msgpack_decode(encoded)
        self.assertEqual(decoded, lsig)
        verified = lsig.verify(public_key)
        self.assertTrue(verified)

        # check signature verification on modified program
        program = b"\x01\x20\x01\x03\x22"
        lsig = transaction.LogicSig(program)
        self.assertEqual(lsig.logic, program)
        verified = lsig.verify(public_key)
        self.assertFalse(verified)
        self.assertNotEqual(lsig.address(), program_hash)

        # check invalid program fails
        program = b"\x00\x20\x01\x03\x22"
        lsig = transaction.LogicSig(program)
        verified = lsig.verify(public_key)
        self.assertFalse(verified)

    def test_signature(self):
        private_key, address = account.generate_account()
        public_key = encoding.decode_address(address)
        program = b"\x01\x20\x01\x01\x22"  # int 1
        lsig = transaction.LogicSig(program)
        lsig.sign(private_key)
        self.assertEqual(lsig.logic, program)
        self.assertEqual(lsig.args, None)
        self.assertEqual(lsig.msig, None)
        self.assertNotEqual(lsig.sig, None)

        verified = lsig.verify(public_key)
        self.assertTrue(verified)

        # check serialization
        encoded = encoding.msgpack_encode(lsig)
        decoded = encoding.msgpack_decode(encoded)
        self.assertEqual(decoded, lsig)
        verified = lsig.verify(public_key)
        self.assertTrue(verified)

    def test_multisig(self):
        private_key, _ = account.generate_account()
        private_key_1, account_1 = account.generate_account()
        private_key_2, account_2 = account.generate_account()

        # create multisig address with invalid version
        msig = transaction.Multisig(1, 2, [account_1, account_2])
        program = b"\x01\x20\x01\x01\x22"  # int 1
        lsig = transaction.LogicSig(program)
        lsig.sign(private_key_1, msig)
        self.assertEqual(lsig.logic, program)
        self.assertEqual(lsig.args, None)
        self.assertEqual(lsig.sig, None)
        self.assertNotEqual(lsig.msig, None)

        sender_addr = msig.address()
        public_key = encoding.decode_address(sender_addr)
        verified = lsig.verify(public_key)
        self.assertFalse(verified)       # not enough signatures

        with self.assertRaises(error.InvalidSecretKeyError):
            lsig.append_to_multisig(private_key)

        lsig.append_to_multisig(private_key_2)
        verified = lsig.verify(public_key)
        self.assertTrue(verified)

        # combine sig and multisig, ensure it fails
        lsigf = transaction.LogicSig(program)
        lsigf.sign(private_key)
        lsig.sig = lsigf.sig
        verified = lsig.verify(public_key)
        self.assertFalse(verified)

        # remove, ensure it still works
        lsig.sig = None
        verified = lsig.verify(public_key)
        self.assertTrue(verified)

        # check serialization
        encoded = encoding.msgpack_encode(lsig)
        decoded = encoding.msgpack_decode(encoded)
        self.assertEqual(decoded, lsig)
        verified = lsig.verify(public_key)
        self.assertTrue(verified)

    def test_transaction(self):
        fromAddress = (
            "47YPQTIGQEO7T4Y4RWDYWEKV6RTR2UNBQXBABEEGM72ESWDQNCQ52OPASU")
        toAddress = (
            "PNWOET7LLOWMBMLE4KOCELCX6X3D3Q4H2Q4QJASYIEOF7YIPPQBG3YQ5YI")
        mn = (
            "advice pudding treat near rule blouse same whisper inner electric"
            " quit surface sunny dismiss leader blood seat clown cost exist ho"
            "spital century reform able sponsor")
        fee = 1000
        amount = 2000
        firstRound = 2063137
        genesisID = "devnet-v1.0"

        genesisHash = "sC3P7e2SdbqKJK0tbiCdK9tdSpbe6XeCGKdoNzmlj0E="
        note = base64.b64decode("8xMCTuLQ810=")

        sp = transaction.SuggestedParams(
            fee, firstRound, firstRound+1000, genesisHash, genesisID,
            flat_fee=True)
        tx = transaction.PaymentTxn(
            fromAddress, sp, toAddress, amount,
            note=note
        )

        golden = (
            "gqRsc2lng6NhcmeSxAMxMjPEAzQ1NqFsxAUBIAEBIqNzaWfEQE6HXaI5K0lcq50o/"
            "y3bWOYsyw9TLi/oorZB4xaNdn1Z14351u2f6JTON478fl+JhIP4HNRRAIh/I8EWXB"
            "PpJQ2jdHhuiqNhbXTNB9CjZmVlzQPoomZ2zgAfeyGjZ2Vuq2Rldm5ldC12MS4womd"
            "oxCCwLc/t7ZJ1uookrS1uIJ0r211Klt7pd4IYp2g3OaWPQaJsds4AH38JpG5vdGXE"
            "CPMTAk7i0PNdo3JjdsQge2ziT+tbrMCxZOKcIixX9fY9w4fUOQSCWEEcX+EPfAKjc"
            "25kxCDn8PhNBoEd+fMcjYeLEVX0Zx1RoYXCAJCGZ/RJWHBooaR0eXBlo3BheQ=="
        )

        program = b"\x01\x20\x01\x01\x22"  # int 1
        args = [
            b"123",
            b"456"
        ]
        sk = mnemonic.to_private_key(mn)
        lsig = transaction.LogicSig(program, args)
        lsig.sign(sk)
        lstx = transaction.LogicSigTransaction(tx, lsig)
        verified = lstx.verify()
        self.assertTrue(verified)

        golden_decoded = encoding.msgpack_decode(golden)
        self.assertEqual(lstx, golden_decoded)


class TestTemplate(unittest.TestCase):
    def test_split(self):
        addr1 = "WO3QIJ6T4DZHBX5PWJH26JLHFSRT7W7M2DJOULPXDTUS6TUX7ZRIO4KDFY"
        addr2 = "W6UUUSEAOGLBHT7VFT4H2SDATKKSG6ZBUIJXTZMSLW36YS44FRP5NVAU7U"
        addr3 = "XCIBIN7RT4ZXGBMVAMU3QS6L5EKB7XGROC5EPCNHHYXUIBAA5Q6C5Y7NEU"
        s = template.Split(addr1, addr2, addr3, 30,
                           100, 123456, 10000, 5000000)
        golden = (
            "ASAIAcCWsQICAMDEB2QekE4mAyCztwQn0+DycN+vsk+vJWcsoz/b7NDS6i33HOkvT"
            "pf+YiC3qUpIgHGWE8/1LPh9SGCalSN7IaITeeWSXbfsS5wsXyC4kBQ38Z8zcwWVAy"
            "m4S8vpFB/c0XC6R4mnPi9EBADsPDEQIhIxASMMEDIEJBJAABkxCSgSMQcyAxIQMQg"
            "lEhAxAiEEDRAiQAAuMwAAMwEAEjEJMgMSEDMABykSEDMBByoSEDMACCEFCzMBCCEG"
            "CxIQMwAIIQcPEBA=")
        golden_addr = (
            "HDY7A4VHBWQWQZJBEMASFOUZKBNGWBMJEMUXAGZ4SPIRQ6C24MJHUZKFGY")
        self.assertEqual(s.get_program(), base64.b64decode(golden))
        self.assertEqual(s.get_address(), golden_addr)
        sp = transaction.SuggestedParams(
            10000, 1, 100, "f4OxZX/x/FO5LcGBSKHWXfwtSx+j1ncoSt3SABJtkGk=")
        txns = s.get_split_funds_transaction(
            s.get_program(), 1300000, sp)
        golden_txns = base64.b64decode(
            "gqRsc2lngaFsxM4BIAgBwJaxAgIAwMQHZB6QTiYDILO3BCfT4PJw36+yT68lZyyjP"
            "9vs0NLqLfcc6S9Ol/5iILepSkiAcZYTz/Us+H1IYJqVI3shohN55ZJdt+xLnCxfIL"
            "iQFDfxnzNzBZUDKbhLy+kUH9zRcLpHiac+L0QEAOw8MRAiEjEBIwwQMgQkEkAAGTE"
            "JKBIxBzIDEhAxCCUSEDECIQQNECJAAC4zAAAzAQASMQkyAxIQMwAHKRIQMwEHKhIQ"
            "MwAIIQULMwEIIQYLEhAzAAghBw8QEKN0eG6Jo2FtdM4ABJPgo2ZlZc4AId/gomZ2A"
            "aJnaMQgf4OxZX/x/FO5LcGBSKHWXfwtSx+j1ncoSt3SABJtkGmjZ3JwxCBLA74bTV"
            "35FJNL1h0K9ZbRU24b4M1JRkD1YTogvvDXbqJsdmSjcmN2xCC3qUpIgHGWE8/1LPh"
            "9SGCalSN7IaITeeWSXbfsS5wsX6NzbmTEIDjx8HKnDaFoZSEjASK6mVBaawWJIylw"
            "GzyT0Rh4WuMSpHR5cGWjcGF5gqRsc2lngaFsxM4BIAgBwJaxAgIAwMQHZB6QTiYDI"
            "LO3BCfT4PJw36+yT68lZyyjP9vs0NLqLfcc6S9Ol/5iILepSkiAcZYTz/Us+H1IYJ"
            "qVI3shohN55ZJdt+xLnCxfILiQFDfxnzNzBZUDKbhLy+kUH9zRcLpHiac+L0QEAOw"
            "8MRAiEjEBIwwQMgQkEkAAGTEJKBIxBzIDEhAxCCUSEDECIQQNECJAAC4zAAAzAQAS"
            "MQkyAxIQMwAHKRIQMwEHKhIQMwAIIQULMwEIIQYLEhAzAAghBw8QEKN0eG6Jo2Ftd"
            "M4AD0JAo2ZlZc4AId/gomZ2AaJnaMQgf4OxZX/x/FO5LcGBSKHWXfwtSx+j1ncoSt"
            "3SABJtkGmjZ3JwxCBLA74bTV35FJNL1h0K9ZbRU24b4M1JRkD1YTogvvDXbqJsdmS"
            "jcmN2xCC4kBQ38Z8zcwWVAym4S8vpFB/c0XC6R4mnPi9EBADsPKNzbmTEIDjx8HKn"
            "DaFoZSEjASK6mVBaawWJIylwGzyT0Rh4WuMSpHR5cGWjcGF5")
        encoded_txns = b''
        for txn in txns:
            encoded_txns += base64.b64decode(encoding.msgpack_encode(txn))
        self.assertEqual(encoded_txns, golden_txns)

    def test_HTLC(self):
        addr1 = "726KBOYUJJNE5J5UHCSGQGWIBZWKCBN4WYD7YVSTEXEVNFPWUIJ7TAEOPM"
        addr2 = "42NJMHTPFVPXVSDGA6JGKUV6TARV5UZTMPFIREMLXHETRKIVW34QFSDFRE"
        preimage = "cHJlaW1hZ2U="
        hash_image = "EHZhE08h/HwCIj1Qq56zYAvD/8NxJCOh5Hux+anb9V8="
        s = template.HTLC(addr1, addr2, "sha256", hash_image, 600000, 1000)
        golden_addr = (
            "FBZIR3RWVT2BTGVOG25H3VAOLVD54RTCRNRLQCCJJO6SVSCT5IVDYKNCSU")

        golden = (
            "ASAE6AcBAMDPJCYDIOaalh5vLV96yGYHkmVSvpgjXtMzY8qIkYu5yTipFbb5IBB2Y"
            "RNPIfx8AiI9UKues2ALw//DcSQjoeR7sfmp2/VfIP68oLsUSlpOp7Q4pGgayA5soQ"
            "W8tgf8VlMlyVaV9qITMQEiDjEQIxIQMQcyAxIQMQgkEhAxCSgSLQEpEhAxCSoSMQI"
            "lDRAREA==")
        p = s.get_program()
        self.assertEqual(p, base64.b64decode(golden))
        self.assertEqual(s.get_address(), golden_addr)
        golden_ltxn = (
            "gqRsc2lngqNhcmeRxAhwcmVpbWFnZaFsxJcBIAToBwEAwM8kJgMg5pqWHm8tX3rIZ"
            "geSZVK+mCNe0zNjyoiRi7nJOKkVtvkgEHZhE08h/HwCIj1Qq56zYAvD/8NxJCOh5H"
            "ux+anb9V8g/ryguxRKWk6ntDikaBrIDmyhBby2B/xWUyXJVpX2ohMxASIOMRAjEhA"
            "xBzIDEhAxCCQSEDEJKBItASkSEDEJKhIxAiUNEBEQo3R4boelY2xvc2XEIOaalh5v"
            "LV96yGYHkmVSvpgjXtMzY8qIkYu5yTipFbb5o2ZlZc0D6KJmdgGiZ2jEIH+DsWV/8"
            "fxTuS3BgUih1l38LUsfo9Z3KErd0gASbZBpomx2ZKNzbmTEIChyiO42rPQZmq42un"
            "3UDl1H3kZii2K4CElLvSrIU+oqpHR5cGWjcGF5")
        sp = transaction.SuggestedParams(
            0, 1, 100, "f4OxZX/x/FO5LcGBSKHWXfwtSx+j1ncoSt3SABJtkGk=")
        ltxn = template.HTLC.get_transaction(p, preimage, sp)
        self.assertEqual(golden_ltxn, encoding.msgpack_encode(ltxn))

    def test_dynamic_fee(self):
        addr1 = "726KBOYUJJNE5J5UHCSGQGWIBZWKCBN4WYD7YVSTEXEVNFPWUIJ7TAEOPM"
        addr2 = "42NJMHTPFVPXVSDGA6JGKUV6TARV5UZTMPFIREMLXHETRKIVW34QFSDFRE"
        sp = transaction.SuggestedParams(
            0, 12345, 12346, "f4OxZX/x/FO5LcGBSKHWXfwtSx+j1ncoSt3SABJtkGk=")

        s = template.DynamicFee(addr1, 5000, sp, addr2)
        s.lease_value = base64.b64decode(
            "f4OxZX/x/FO5LcGBSKHWXfwtSx+j1ncoSt3SABJtkGk=")

        golden_addr = (
            "GCI4WWDIWUFATVPOQ372OZYG52EULPUZKI7Y34MXK3ZJKIBZXHD2H5C5TI")

        golden = (
            "ASAFAgGIJ7lgumAmAyD+vKC7FEpaTqe0OKRoGsgObKEFvLYH/FZTJclWlfaiEyDmm"
            "pYeby1feshmB5JlUr6YI17TM2PKiJGLuck4qRW2+SB/g7Flf/H8U7ktwYFIodZd/C"
            "1LH6PWdyhK3dIAEm2QaTIEIhIzABAjEhAzAAcxABIQMwAIMQESEDEWIxIQMRAjEhA"
            "xBygSEDEJKRIQMQgkEhAxAiUSEDEEIQQSEDEGKhIQ")
        p = s.get_program()
        self.assertEqual(p, base64.b64decode(golden))
        self.assertEqual(s.get_address(), golden_addr)
        sk = (
            "cv8E0Ln24FSkwDgGeuXKStOTGcze5u8yldpXxgrBxumFPYdMJymqcGoxdDeyuM8t6"
            "Kxixfq0PJCyJP71uhYT7w==")
        txn, lsig = s.sign_dynamic_fee(sk)

        golden_txn = (
            "iqNhbXTNE4ilY2xvc2XEIOaalh5vLV96yGYHkmVSvpgjXtMzY8qIkYu5yTipFbb5"
            "o2ZlZc0D6KJmds0wOaJnaMQgf4OxZX/x/FO5LcGBSKHWXfwtSx+j1ncoSt3SABJtk"
            "GmibHbNMDqibHjEIH+DsWV/8fxTuS3BgUih1l38LUsfo9Z3KErd0gASbZBpo3Jjds"
            "Qg/ryguxRKWk6ntDikaBrIDmyhBby2B/xWUyXJVpX2ohOjc25kxCCFPYdMJymqcGo"
            "xdDeyuM8t6Kxixfq0PJCyJP71uhYT76R0eXBlo3BheQ==")
        golden_lsig = (
            "gqFsxLEBIAUCAYgnuWC6YCYDIP68oLsUSlpOp7Q4pGgayA5soQW8tgf8VlMlyVaV9"
            "qITIOaalh5vLV96yGYHkmVSvpgjXtMzY8qIkYu5yTipFbb5IH+DsWV/8fxTuS3BgU"
            "ih1l38LUsfo9Z3KErd0gASbZBpMgQiEjMAECMSEDMABzEAEhAzAAgxARIQMRYjEhA"
            "xECMSEDEHKBIQMQkpEhAxCCQSEDECJRIQMQQhBBIQMQYqEhCjc2lnxEAhLNdfdDp9"
            "Wbi0YwsEQCpP7TVHbHG7y41F4MoESNW/vL1guS+5Wj4f5V9fmM63/VKTSMFidHOSw"
            "m5o+pbV5lYH")
        self.assertEqual(golden_txn, encoding.msgpack_encode(txn))
        self.assertEqual(golden_lsig, encoding.msgpack_encode(lsig))

        sk_2 = (
            "2qjz96Vj9M6YOqtNlfJUOKac13EHCXyDty94ozCjuwwriI+jzFgStFx9E6kEk1l4+"
            "lFsW4Te2PY1KV8kNcccRg==")
        txns = s.get_transactions(txn, lsig, sk_2, 1234)

        golden_txns = (
            "gqNzaWfEQJBNVry9qdpnco+uQzwFicUWHteYUIxwDkdHqY5Qw2Q8Fc2StrQUgN+2k"
            "8q4rC0LKrTMJQnE+mLWhZgMMJvq3QCjdHhuiqNhbXTOAAWq6qNmZWXOAATzvqJmds"
            "0wOaJnaMQgf4OxZX/x/FO5LcGBSKHWXfwtSx+j1ncoSt3SABJtkGmjZ3JwxCCCVfq"
            "hCinRBXKMIq9eSrJQIXZ+7iXUTig91oGd/mZEAqJsds0wOqJseMQgf4OxZX/x/FO5"
            "LcGBSKHWXfwtSx+j1ncoSt3SABJtkGmjcmN2xCCFPYdMJymqcGoxdDeyuM8t6Kxix"
            "fq0PJCyJP71uhYT76NzbmTEICuIj6PMWBK0XH0TqQSTWXj6UWxbhN7Y9jUpXyQ1xx"
            "xGpHR5cGWjcGF5gqRsc2lngqFsxLEBIAUCAYgnuWC6YCYDIP68oLsUSlpOp7Q4pGg"
            "ayA5soQW8tgf8VlMlyVaV9qITIOaalh5vLV96yGYHkmVSvpgjXtMzY8qIkYu5yTip"
            "Fbb5IH+DsWV/8fxTuS3BgUih1l38LUsfo9Z3KErd0gASbZBpMgQiEjMAECMSEDMAB"
            "zEAEhAzAAgxARIQMRYjEhAxECMSEDEHKBIQMQkpEhAxCCQSEDECJRIQMQQhBBIQMQ"
            "YqEhCjc2lnxEAhLNdfdDp9Wbi0YwsEQCpP7TVHbHG7y41F4MoESNW/vL1guS+5Wj4"
            "f5V9fmM63/VKTSMFidHOSwm5o+pbV5lYHo3R4boujYW10zROIpWNsb3NlxCDmmpYe"
            "by1feshmB5JlUr6YI17TM2PKiJGLuck4qRW2+aNmZWXOAAWq6qJmds0wOaJnaMQgf"
            "4OxZX/x/FO5LcGBSKHWXfwtSx+j1ncoSt3SABJtkGmjZ3JwxCCCVfqhCinRBXKMIq"
            "9eSrJQIXZ+7iXUTig91oGd/mZEAqJsds0wOqJseMQgf4OxZX/x/FO5LcGBSKHWXfw"
            "tSx+j1ncoSt3SABJtkGmjcmN2xCD+vKC7FEpaTqe0OKRoGsgObKEFvLYH/FZTJclW"
            "lfaiE6NzbmTEIIU9h0wnKapwajF0N7K4zy3orGLF+rQ8kLIk/vW6FhPvpHR5cGWjc"
            "GF5")

        actual = (base64.b64decode(encoding.msgpack_encode(txns[0])) +
                  base64.b64decode(encoding.msgpack_encode(txns[1])))
        self.assertEqual(golden_txns, base64.b64encode(actual).decode())

    def test_periodic_payment(self):
        addr = "SKXZDBHECM6AS73GVPGJHMIRDMJKEAN5TUGMUPSKJCQ44E6M6TC2H2UJ3I"
        s = template.PeriodicPayment(addr, 500000, 95, 100, 1000, 2445756)
        s.lease_value = base64.b64decode(
            "AQIDBAUGBwgBAgMEBQYHCAECAwQFBgcIAQIDBAUGBwg=")

        golden_addr = (
            "JMS3K4LSHPULANJIVQBTEDP5PZK6HHMDQS4OKHIMHUZZ6OILYO3FVQW7IY")

        golden = (
            "ASAHAegHZABfoMIevKOVASYCIAECAwQFBgcIAQIDBAUGBwgBAgMEBQYHCAECAwQFB"
            "gcIIJKvkYTkEzwJf2arzJOxERsSogG9nQzKPkpIoc4TzPTFMRAiEjEBIw4QMQIkGC"
            "USEDEEIQQxAggSEDEGKBIQMQkyAxIxBykSEDEIIQUSEDEJKRIxBzIDEhAxAiEGDRA"
            "xCCUSEBEQ")
        p = s.get_program()
        self.assertEqual(p, base64.b64decode(golden))
        self.assertEqual(s.get_address(), golden_addr)
        gh = "f4OxZX/x/FO5LcGBSKHWXfwtSx+j1ncoSt3SABJtkGk="
        sp = transaction.SuggestedParams(0, 1200, None, gh)

        ltxn = s.get_withdrawal_transaction(p, sp)
        golden_ltxn = (
            "gqRsc2lngaFsxJkBIAcB6AdkAF+gwh68o5UBJgIgAQIDBAUGBwgBAgMEBQYHCAECA"
            "wQFBgcIAQIDBAUGBwggkq+RhOQTPAl/ZqvMk7ERGxKiAb2dDMo+SkihzhPM9MUxEC"
            "ISMQEjDhAxAiQYJRIQMQQhBDECCBIQMQYoEhAxCTIDEjEHKRIQMQghBRIQMQkpEjE"
            "HMgMSEDECIQYNEDEIJRIQERCjdHhuiaNhbXTOAAehIKNmZWXNA+iiZnbNBLCiZ2jE"
            "IH+DsWV/8fxTuS3BgUih1l38LUsfo9Z3KErd0gASbZBpomx2zQUPomx4xCABAgMEB"
            "QYHCAECAwQFBgcIAQIDBAUGBwgBAgMEBQYHCKNyY3bEIJKvkYTkEzwJf2arzJOxER"
            "sSogG9nQzKPkpIoc4TzPTFo3NuZMQgSyW1cXI76LA1KKwDMg39flXjnYOEuOUdDD0"
            "znzkLw7akdHlwZaNwYXk=")
        self.assertEqual(golden_ltxn, encoding.msgpack_encode(ltxn))

    def test_limit_order_a(self):
        addr = "726KBOYUJJNE5J5UHCSGQGWIBZWKCBN4WYD7YVSTEXEVNFPWUIJ7TAEOPM"
        s = template.LimitOrder(addr, 12345, 30, 100, 123456, 5000000, 10000)

        golden_addr = (
            "LXQWT2XLIVNFS54VTLR63UY5K6AMIEWI7YTVE6LB4RWZDBZKH22ZO3S36I")

        golden = (
            "ASAKAAHAlrECApBOBLlgZB7AxAcmASD+vKC7FEpaTqe0OKRoGsgObKEFvLYH/FZTJ"
            "clWlfaiEzEWIhIxECMSEDEBJA4QMgQjEkAAVTIEJRIxCCEEDRAxCTIDEhAzARAhBR"
            "IQMwERIQYSEDMBFCgSEDMBEzIDEhAzARIhBx01AjUBMQghCB01BDUDNAE0Aw1AACQ"
            "0ATQDEjQCNAQPEEAAFgAxCSgSMQIhCQ0QMQcyAxIQMQgiEhAQ")
        p = s.get_program()

        self.assertEqual(p, base64.b64decode(golden))
        self.assertEqual(s.get_address(), golden_addr)

        sk = (
            "DTKVj7KMON3GSWBwMX9McQHtaDDi8SDEBi0bt4rOxlHNRahLa0zVG+25BDIaHB1dS"
            "oIHIsUQ8FFcdnCdKoG+Bg==")
        gh = "f4OxZX/x/FO5LcGBSKHWXfwtSx+j1ncoSt3SABJtkGk="
        sp = transaction.SuggestedParams(10, 1234, 2234, gh)
        [stx_1, stx_2] = s.get_swap_assets_transactions(
            p, 3000, 10000, sk, sp)
        golden_txn_1 = (
            "gqRsc2lngaFsxLcBIAoAAcCWsQICkE4EuWBkHsDEByYBIP68oLsUSlpOp7Q4pGgay"
            "A5soQW8tgf8VlMlyVaV9qITMRYiEjEQIxIQMQEkDhAyBCMSQABVMgQlEjEIIQQNED"
            "EJMgMSEDMBECEFEhAzAREhBhIQMwEUKBIQMwETMgMSEDMBEiEHHTUCNQExCCEIHTU"
            "ENQM0ATQDDUAAJDQBNAMSNAI0BA8QQAAWADEJKBIxAiEJDRAxBzIDEhAxCCISEBCj"
            "dHhuiaNhbXTNJxCjZmVlzQisomZ2zQTSomdoxCB/g7Flf/H8U7ktwYFIodZd/C1LH"
            "6PWdyhK3dIAEm2QaaNncnDEIKz368WOGpdE/Ww0L8wUu5Ly2u2bpG3ZSMKCJvcvGA"
            "pTomx2zQi6o3JjdsQgzUWoS2tM1RvtuQQyGhwdXUqCByLFEPBRXHZwnSqBvgajc25"
            "kxCBd4Wnq60VaWXeVmuPt0x1XgMQSyP4nUnlh5G2Rhyo+taR0eXBlo3BheQ==")
        golden_txn_2 = (
            "gqNzaWfEQKXv8Z6OUDNmiZ5phpoQJHmfKyBal4gBZLPYsByYnlXCAlXMBeVFG5CLP"
            "1k5L6BPyEG2/XIbjbyM0CGG55CxxAKjdHhuiqRhYW10zQu4pGFyY3bEIP68oLsUSl"
            "pOp7Q4pGgayA5soQW8tgf8VlMlyVaV9qITo2ZlZc0JJKJmds0E0qJnaMQgf4OxZX/"
            "x/FO5LcGBSKHWXfwtSx+j1ncoSt3SABJtkGmjZ3JwxCCs9+vFjhqXRP1sNC/MFLuS"
            "8trtm6Rt2UjCgib3LxgKU6Jsds0IuqNzbmTEIM1FqEtrTNUb7bkEMhocHV1Kggcix"
            "RDwUVx2cJ0qgb4GpHR5cGWlYXhmZXKkeGFpZM0wOQ==")

        self.assertEqual(encoding.msgpack_encode(stx_1), golden_txn_1)
        self.assertEqual(encoding.msgpack_encode(stx_2), golden_txn_2)


class TestDryrun(dryrun.DryrunTestCaseMixin, unittest.TestCase):
    def setUp(self):
        self.mock_response = dict(error=None, txns=[])

        self.algo_client = Mock()
        self.algo_client.dryrun = Mock()
        def response(dr):
            return self.mock_response
        self.algo_client.dryrun.side_effect = response

    def test_create_request(self):
        helper = dryrun.Helper
        with self.assertRaises(TypeError):
            helper.build_dryrun_request(10)

        drr = helper.build_dryrun_request("int 1")
        self.assertEqual(len(drr.txns), 1)
        self.assertEqual(len(drr.sources), 1)
        self.assertEqual(drr.sources[0].txn_index, 0)
        self.assertEqual(drr.sources[0].field_name, "lsig")
        self.assertIsInstance(drr.txns[0], transaction.LogicSigTransaction)
        self.assertIsInstance(drr.txns[0].transaction, transaction.Transaction)

        drr = helper.build_dryrun_request("int 1", lsig=dict(args=[b"123", b"456"]))
        self.assertEqual(len(drr.txns), 1)
        self.assertEqual(len(drr.sources), 1)
        self.assertEqual(drr.sources[0].txn_index, 0)
        self.assertEqual(drr.sources[0].field_name, "lsig")
        self.assertIsInstance(drr.txns[0], transaction.LogicSigTransaction)
        self.assertIsInstance(drr.txns[0].transaction, transaction.Transaction)
        self.assertEqual(drr.txns[0].lsig.args, [b"123", b"456"])

        drr = helper.build_dryrun_request(b"\x02")
        self.assertEqual(len(drr.txns), 1)
        self.assertEqual(len(drr.sources), 0)
        self.assertIsInstance(drr.txns[0], transaction.LogicSigTransaction)
        self.assertIsInstance(drr.txns[0].transaction, transaction.Transaction)
        self.assertEqual(drr.txns[0].lsig.logic, b"\x02")

        drr = helper.build_dryrun_request(b"\x02", lsig=dict(args=[b"123", b"456"]))
        self.assertEqual(len(drr.txns), 1)
        self.assertEqual(len(drr.sources), 0)
        self.assertIsInstance(drr.txns[0], transaction.LogicSigTransaction)
        self.assertIsInstance(drr.txns[0].transaction, transaction.Transaction)
        self.assertEqual(drr.txns[0].lsig.logic, b"\x02")
        self.assertEqual(drr.txns[0].lsig.args, [b"123", b"456"])

        with self.assertRaises(TypeError):
            drr = helper.build_dryrun_request(b"\x02", lsig=dict(testkey=1))

        drr = helper.build_dryrun_request("int 1", app=dict())
        self.assertEqual(len(drr.txns), 1)
        self.assertEqual(len(drr.sources), 1)
        self.assertEqual(len(drr.apps), 1)
        self.assertEqual(drr.apps[0].id, drr.sources[0].app_index)
        self.assertNotEqual(drr.sources[0].app_index, 0)
        self.assertEqual(drr.sources[0].txn_index, 0)
        self.assertEqual(drr.sources[0].field_name, "approv")
        self.assertIsInstance(drr.txns[0], transaction.SignedTransaction)
        self.assertIsInstance(drr.txns[0].transaction, transaction.ApplicationCallTxn)
        self.assertEqual(drr.txns[0].transaction.index, 0)

        drr = helper.build_dryrun_request("int 1", app=dict(app_idx=None))
        self.assertEqual(len(drr.txns), 1)
        self.assertEqual(len(drr.sources), 1)
        self.assertEqual(len(drr.apps), 1)
        self.assertEqual(drr.apps[0].id, drr.sources[0].app_index)
        self.assertNotEqual(drr.sources[0].app_index, 0)
        self.assertEqual(drr.sources[0].txn_index, 0)
        self.assertEqual(drr.sources[0].field_name, "approv")
        self.assertIsInstance(drr.txns[0], transaction.SignedTransaction)
        self.assertIsInstance(drr.txns[0].transaction, transaction.ApplicationCallTxn)
        self.assertEqual(drr.txns[0].transaction.index, 0)

        drr = helper.build_dryrun_request("int 1", app=dict(app_idx=0))
        self.assertEqual(len(drr.txns), 1)
        self.assertEqual(len(drr.sources), 1)
        self.assertEqual(len(drr.apps), 1)
        self.assertEqual(drr.apps[0].id, drr.sources[0].app_index)
        self.assertNotEqual(drr.sources[0].app_index, 0)
        self.assertEqual(drr.sources[0].txn_index, 0)
        self.assertEqual(drr.sources[0].field_name, "approv")
        self.assertIsInstance(drr.txns[0], transaction.SignedTransaction)
        self.assertIsInstance(drr.txns[0].transaction, transaction.ApplicationCallTxn)
        self.assertEqual(drr.txns[0].transaction.index, 0)

        drr = helper.build_dryrun_request("int 1", app=dict(app_idx=1))
        self.assertEqual(len(drr.txns), 1)
        self.assertEqual(len(drr.sources), 1)
        self.assertEqual(len(drr.apps), 1)
        self.assertEqual(drr.apps[0].id, drr.sources[0].app_index)
        self.assertEqual(drr.sources[0].app_index, 1)
        self.assertEqual(drr.sources[0].txn_index, 0)
        self.assertEqual(drr.sources[0].field_name, "approv")
        self.assertIsInstance(drr.txns[0], transaction.SignedTransaction)
        self.assertIsInstance(drr.txns[0].transaction, transaction.ApplicationCallTxn)
        self.assertEqual(drr.txns[0].transaction.index, 1)

        drr = helper.build_dryrun_request("int 1", app=dict(app_idx=1, on_complete=0))
        self.assertEqual(drr.sources[0].field_name, "approv")

        drr = helper.build_dryrun_request("int 1", app=dict(on_complete=transaction.OnComplete.ClearStateOC))
        self.assertEqual(len(drr.txns), 1)
        self.assertEqual(len(drr.sources), 1)
        self.assertEqual(len(drr.apps), 1)
        self.assertEqual(drr.sources[0].txn_index, 0)
        self.assertEqual(drr.sources[0].field_name, "clearp")
        self.assertIsInstance(drr.txns[0], transaction.SignedTransaction)
        self.assertIsInstance(drr.txns[0].transaction, transaction.ApplicationCallTxn)

        drr = helper.build_dryrun_request(b"\x02", app=dict())
        self.assertEqual(len(drr.txns), 1)
        self.assertEqual(len(drr.sources), 0)
        self.assertEqual(len(drr.apps), 1)
        self.assertEqual(drr.apps[0].params.approval_program, b"\x02")
        self.assertIsInstance(drr.txns[0], transaction.SignedTransaction)
        self.assertIsInstance(drr.txns[0].transaction, transaction.ApplicationCallTxn)

        drr = helper.build_dryrun_request(b"\x02", app=dict(on_complete=0))
        self.assertEqual(len(drr.txns), 1)
        self.assertEqual(len(drr.sources), 0)
        self.assertEqual(len(drr.apps), 1)
        self.assertEqual(drr.apps[0].params.approval_program, b"\x02")
        self.assertIsNone(drr.apps[0].params.clear_state_program)
        self.assertIsInstance(drr.txns[0], transaction.SignedTransaction)
        self.assertIsInstance(drr.txns[0].transaction, transaction.ApplicationCallTxn)

        drr = helper.build_dryrun_request(b"\x02", app=dict(on_complete=transaction.OnComplete.ClearStateOC))
        self.assertEqual(len(drr.txns), 1)
        self.assertEqual(len(drr.sources), 0)
        self.assertEqual(len(drr.apps), 1)
        self.assertIsNone(drr.apps[0].params.approval_program)
        self.assertEqual(drr.apps[0].params.clear_state_program, b"\x02")
        self.assertIsInstance(drr.txns[0], transaction.SignedTransaction)
        self.assertIsInstance(drr.txns[0].transaction, transaction.ApplicationCallTxn)

        with self.assertRaises(TypeError):
            drr = helper.build_dryrun_request(b"\x02", app=dict(testkey=1))


    def test_pass_reject(self):
        self.mock_response = dict(error=None, txns=[{"logic-sig-messages": ["PASS"]}])
        self.assertPass("int 1")
        with self.assertRaises(AssertionError):
            self.assertReject("int 1")

        self.mock_response = dict(error=None, txns=[{"app-call-messages": ["PASS"]}])
        self.assertPass("int 1", app=dict(on_complete=0))
        with self.assertRaises(AssertionError):
            self.assertReject("int 1")

        self.assertPass(self.mock_response)
        with self.assertRaises(AssertionError):
            self.assertReject(self.mock_response)

        self.mock_response = dict(error=None, txns=[{"logic-sig-messages": ["REJECT"]}])
        self.assertReject("int 1")
        with self.assertRaises(AssertionError):
            self.assertPass("int 1")

        self.assertReject(self.mock_response)
        with self.assertRaises(AssertionError):
            self.assertPass(self.mock_response)

        self.mock_response = dict(error=None, txns=[{"app-call-messages": ["PASS"]}])
        self.assertPass(self.mock_response, txn_index=0)
        with self.assertRaises(AssertionError):
            self.assertReject(self.mock_response, txn_index=0)

        with self.assertRaisesRegex(AssertionError, r"out of range \[0, 1\)"):
            self.assertPass(self.mock_response, txn_index=1)

        with self.assertRaisesRegex(AssertionError, r"out of range \[0, 1\)"):
            self.assertReject(self.mock_response, txn_index=1)

        self.mock_response = dict(
            error=None,
            txns=[{"app-call-messages": ["PASS"]}, {"app-call-messages": ["PASS"]}]
        )
        self.assertPass(self.mock_response, txn_index=0)
        self.assertPass(self.mock_response, txn_index=1)
        self.assertPass(self.mock_response)

        self.mock_response = dict(
            error=None,
            txns=[{"app-call-messages": ["PASS"]}, {"app-call-messages": ["REJECT"]}]
        )
        self.assertPass(self.mock_response, txn_index=0)
        with self.assertRaises(AssertionError):
            self.assertPass(self.mock_response, txn_index=1)
        with self.assertRaises(AssertionError):
            self.assertPass(self.mock_response)

        with self.assertRaises(AssertionError):
            self.assertReject(self.mock_response, txn_index=0)
        self.assertReject(self.mock_response, txn_index=1)
        self.assertReject(self.mock_response)

        self.mock_response = dict(
            error=None,
            txns=[{"app-call-messages": ["REJECT"]}, {"app-call-messages": ["REJECT"]}]
        )
        with self.assertRaises(AssertionError):
            self.assertPass(self.mock_response)
        with self.assertRaises(AssertionError):
            self.assertPass(self.mock_response, txn_index=0)
        with self.assertRaises(AssertionError):
            self.assertPass(self.mock_response, txn_index=1)

        self.assertReject(self.mock_response)
        self.assertReject(self.mock_response, txn_index=0)
        self.assertReject(self.mock_response, txn_index=1)

    def test_no_error(self):
        self.mock_response = dict(error=None, txns=None)
        self.assertNoError("int 1")

        self.mock_response = dict(error="", txns=None)
        self.assertNoError("int 1")

        self.mock_response = dict(error="Dryrun Source[0]: :3 + arg 0 wanted type uint64", txns=None)
        with self.assertRaises(AssertionError):
            self.assertNoError("byte 0x10\nint 1\n+")

        self.mock_response = dict(error="", txns=[{"logic-sig-trace": [{"line":1}]}])
        self.assertNoError("int 1")
        with self.assertRaises(AssertionError):
            self.assertError("int 1")

        self.mock_response = dict(error="", txns=[{"app-call-trace": [{"line":1}]}])
        self.assertNoError("int 1")
        with self.assertRaises(AssertionError):
            self.assertError("int 1")

        self.mock_response = dict(error="", txns=[
            {"logic-sig-trace": [{"line":1}, {"error": "test", "line":2}]}
        ])
        self.assertError("int 1", "logic 0 failed")
        with self.assertRaises(AssertionError):
            self.assertNoError("int 1")

        self.mock_response = dict(error="", txns=[
            {"app-call-trace": [{"line":1}, {"error": "test", "line":2}]}
        ])

        self.assertError("int 1", "app 0 failed")
        with self.assertRaises(AssertionError):
            self.assertNoError("int 1")

        self.assertError("int 1", txn_index=0)

        self.mock_response = dict(error="", txns=[
            {"app-call-trace": [{"line":1}, {"error": "test1", "line":2}]},
            {"logic-sig-trace": [{"line":1}, {"error": "test2", "line":2}]}
        ])
        self.assertError("int 1", txn_index=0)
        self.assertError("int 1", txn_index=1)
        self.assertError("int 1")

        with self.assertRaises(AssertionError):
            self.assertNoError("int 1")
        with self.assertRaises(AssertionError):
            self.assertNoError("int 1", txn_index=0)
        with self.assertRaises(AssertionError):
            self.assertNoError("int 1", txn_index=1)

        self.mock_response = dict(error="", txns=[
            {"app-call-trace": [{"line":1}, {"line":2}]},
            {"logic-sig-trace": [{"line":1}, {"error": "test2", "line":2}]}
        ])
        self.assertNoError("int 1", txn_index=0)
        self.assertError("int 1", txn_index=1)
        self.assertError("int 1")

        with self.assertRaises(AssertionError):
            self.assertNoError("int 1")
        with self.assertRaises(AssertionError):
            self.assertNoError("int 1", txn_index=1)

    def test_global_state(self):
        txn_res1 = {
            "global-delta": [dict(
                key="test",
                value=dict(action=1, uint=2),
            )],
        }
        txn_res2 = {
            "global-delta": [dict(
                key="key",
                value=dict(action=1, uint=2),
            )],
        }
        self.mock_response = dict(
            error=None,
            txns=[txn_res1]
        )
        value = dict(key="test", value=dict(action=1, uint=2))
        self.assertGlobalStateContains("int 1", value, app=dict(on_complete=0))
        self.assertGlobalStateContains(self.mock_response, value, app=dict(on_complete=0))

        self.mock_response = dict(
            error=None,
            txns=[{
                "global-delta": [dict(
                    key="test",
                    value=dict(action=2, bytes="test"),
                )],
            }]
        )
        with self.assertRaises(AssertionError):
            self.assertGlobalStateContains("int 1", value)
        with self.assertRaises(AssertionError):
            self.assertGlobalStateContains(self.mock_response, value)

        self.mock_response = dict(
            error=None,
            txns=[txn_res2]
        )
        with self.assertRaises(AssertionError):
            self.assertGlobalStateContains("int 1", value)
        with self.assertRaises(AssertionError):
            self.assertGlobalStateContains(self.mock_response, value)

        self.mock_response = dict(
            error=None,
            txns=[txn_res1, txn_res1]
        )
        self.assertGlobalStateContains(self.mock_response, value)
        self.assertGlobalStateContains(self.mock_response, value, txn_index=0)
        self.assertGlobalStateContains(self.mock_response, value, txn_index=1)

        self.mock_response = dict(
            error=None,
            txns=[txn_res1, txn_res2]
        )
        self.assertGlobalStateContains(self.mock_response, value)
        self.assertGlobalStateContains(self.mock_response, value, txn_index=0)
        with self.assertRaises(AssertionError):
            self.assertGlobalStateContains(self.mock_response, value, txn_index=1)

        self.mock_response = dict(
            error=None,
            txns=[txn_res2, txn_res2]
        )
        with self.assertRaisesRegex(AssertionError, "not found in any of"):
            self.assertGlobalStateContains(self.mock_response, value)
        with self.assertRaises(AssertionError):
            self.assertGlobalStateContains(self.mock_response, value, txn_index=0)
        with self.assertRaises(AssertionError):
            self.assertGlobalStateContains(self.mock_response, value, txn_index=1)

    def test_local_state(self):
        txn_res1 = {
            "local-deltas": [dict(
                address="some_addr",
                delta=[dict(
                key="test",
                    value=dict(action=1, uint=2),
                )],
            )]
        }
        txn_res2 = {
            "local-deltas": [dict(
                address="some_addr",
                delta=[dict(
                key="key",
                    value=dict(action=1, uint=2),
                )],
            )]
        }
        self.mock_response = dict(
            error=None,
            txns=[txn_res1]
        )
        value = dict(key="test", value=dict(action=1, uint=2))
        self.assertLocalStateContains("int 1", "some_addr", value, app=dict(on_complete=0))

        with self.assertRaises(AssertionError):
            self.assertLocalStateContains("int 1", "other_addr", value, app=dict(on_complete=0))

        value = dict(key="test", value=dict(action=1, uint=3))
        with self.assertRaises(AssertionError):
            self.assertLocalStateContains("int 1", "other_addr", value, app=dict(on_complete=0))

        self.mock_response = dict(
            error=None,
            txns=[txn_res1, txn_res1]
        )
        value = dict(key="test", value=dict(action=1, uint=2))
        self.assertLocalStateContains(self.mock_response, "some_addr", value)
        self.assertLocalStateContains(self.mock_response, "some_addr", value, txn_index=0)
        self.assertLocalStateContains(self.mock_response, "some_addr", value, txn_index=1)

        self.mock_response = dict(
            error=None,
            txns=[txn_res2, txn_res1]
        )
        self.assertLocalStateContains(self.mock_response, "some_addr", value)
        with self.assertRaises(AssertionError):
            self.assertLocalStateContains(self.mock_response, "some_addr", value, txn_index=0)
        self.assertLocalStateContains(self.mock_response, "some_addr", value, txn_index=1)

        self.mock_response = dict(
            error=None,
            txns=[txn_res2, txn_res2]
        )
        with self.assertRaises(AssertionError):
            self.assertLocalStateContains(self.mock_response, "some_addr", value)
        with self.assertRaises(AssertionError):
            self.assertLocalStateContains(self.mock_response, "some_addr", value, txn_index=0)
        with self.assertRaises(AssertionError):
            self.assertLocalStateContains(self.mock_response, "some_addr", value, txn_index=1)


if __name__ == "__main__":
    to_run = [
        TestPaymentTransaction,
        TestAssetConfigConveniences,
        TestAssetTransferConveniences,
        TestApplicationTransactions,
        TestMnemonic,
        TestAddress,
        TestMultisig,
        TestMsgpack,
        TestSignBytes,
        TestLogic,
        TestLogicSig,
        TestTemplate,
        TestDryrun,
    ]
    loader = unittest.TestLoader()
    suites = [loader.loadTestsFromTestCase(test_class)
              for test_class in to_run]
    suite = unittest.TestSuite(suites)
    runner = unittest.TextTestRunner(verbosity=2)
    results = runner.run(suite)
