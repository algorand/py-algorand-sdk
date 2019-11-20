import base64
import copy
import unittest
import random
from algosdk import transaction
from algosdk import encoding
from algosdk import account
from algosdk import mnemonic
from algosdk import wordlist
from algosdk import error
from algosdk import constants
from algosdk import util
from algosdk import logic
from algosdk import template


class TestTransaction(unittest.TestCase):
    def test_min_txn_fee(self):
        address = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
        gh = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
        txn = transaction.PaymentTxn(address, 0, 1, 100, gh, address,
                                     1000, note=b'\x00')
        self.assertEqual(constants.min_txn_fee, txn.fee)

    def test_serialize(self):
        address = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
        gh = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
        txn = transaction.PaymentTxn(address, 3, 1, 100, gh, address,
                                     1000, note=bytes([1, 32, 200]))
        enc = encoding.msgpack_encode(txn)
        re_enc = encoding.msgpack_encode(encoding.msgpack_decode(enc))
        self.assertEqual(enc, re_enc)

    def test_serialize_zero_amt(self):
        address = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
        gh = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
        txn = transaction.PaymentTxn(address, 3, 1, 100, gh, address,
                                     0, note=bytes([1, 32, 200]))
        enc = encoding.msgpack_encode(txn)
        re_enc = encoding.msgpack_encode(encoding.msgpack_decode(enc))
        self.assertEqual(enc, re_enc)

    def test_serialize_gen(self):
        address = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
        gh = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
        txn = transaction.PaymentTxn(address, 3, 1, 100, gh, address,
                                     1000, gen="testnet-v1.0",
                                     close_remainder_to=address)
        enc = encoding.msgpack_encode(txn)
        re_enc = encoding.msgpack_encode(encoding.msgpack_decode(enc))
        self.assertEqual(enc, re_enc)

    def test_serialize_txgroup(self):
        address = "7ZUECA7HFLZTXENRV24SHLU4AVPUTMTTDUFUBNBD64C73F3UHRTHAIOF6Q"
        gh = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
        txn = transaction.PaymentTxn(address, 3, 1, 100, gh, address,
                                     1000, gen="testnet-v1.0",
                                     close_remainder_to=address)
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
        mn = ("advice pudding treat near rule blouse same whisper inner " +
              "electric quit surface sunny dismiss leader blood seat " +
              "clown cost exist hospital century reform able sponsor")
        gh = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
        address = "PNWOET7LLOWMBMLE4KOCELCX6X3D3Q4H2Q4QJASYIEOF7YIPPQBG3YQ5YI"
        close = "IDUTJEUIEVSMXTU4LGTJWZ2UE2E6TIODUKU6UW3FU3UKIQQ77RLUBBBFLA"
        sk = mnemonic.to_private_key(mn)
        pk = account.address_from_private_key(sk)
        txn = transaction.PaymentTxn(pk, 4, 12466, 13466, gh, address, 1000,
                                     note=base64.b64decode("6gAVR0Nsv5Y="),
                                     gen="devnet-v33.0",
                                     close_remainder_to=close)
        stx = txn.sign(sk)
        golden = ("gqNzaWfEQPhUAZ3xkDDcc8FvOVo6UinzmKBCqs0woYSfodlmBMfQvGbeU" +
                  "x3Srxy3dyJDzv7rLm26BRv9FnL2/AuT7NYfiAWjdHhui6NhbXTNA+ilY2" +
                  "xvc2XEIEDpNJKIJWTLzpxZpptnVCaJ6aHDoqnqW2Wm6KRCH/xXo2ZlZc0" +
                  "EmKJmds0wsqNnZW6sZGV2bmV0LXYzMy4womdoxCAmCyAJoJOohot5WHIv" +
                  "peVG7eftF+TYXEx4r7BFJpDt0qJsds00mqRub3RlxAjqABVHQ2y/lqNyY" +
                  "3bEIHts4k/rW6zAsWTinCIsV/X2PcOH1DkEglhBHF/hD3wCo3NuZMQg5/" +
                  "D4TQaBHfnzHI2HixFV9GcdUaGFwgCQhmf0SVhwaKGkdHlwZaNwYXk=")
        self.assertEqual(golden, encoding.msgpack_encode(stx))
        txid_golden = "5FJDJD5LMZC3EHUYYJNH5I23U4X6H2KXABNDGPIL557ZMJ33GZHQ"
        self.assertEqual(txn.get_txid(), txid_golden)

        # check group field serialization
        gid = transaction.calculate_group_id([txn])
        stx.group = gid
        enc = encoding.msgpack_encode(stx)
        re_enc = encoding.msgpack_encode(encoding.msgpack_decode(enc))
        self.assertEqual(enc, re_enc)

    def test_serialize_pay(self):
        mn = ("advice pudding treat near rule blouse same whisper inner elec" +
              "tric quit surface sunny dismiss leader blood seat clown cost " +
              "exist hospital century reform able sponsor")
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
        txn = transaction.PaymentTxn(pk, fee, first_round, last_round, gh, to,
                                     amount, close, note, gen)
        signed_txn = txn.sign(sk)

        golden = ("gqNzaWfEQPhUAZ3xkDDcc8FvOVo6UinzmKBCqs0woYSfodlmBMfQvGbeU" +
                  "x3Srxy3dyJDzv7rLm26BRv9FnL2/AuT7NYfiAWjdHhui6NhbXTNA+ilY2" +
                  "xvc2XEIEDpNJKIJWTLzpxZpptnVCaJ6aHDoqnqW2Wm6KRCH/xXo2ZlZc0" +
                  "EmKJmds0wsqNnZW6sZGV2bmV0LXYzMy4womdoxCAmCyAJoJOohot5WHIv" +
                  "peVG7eftF+TYXEx4r7BFJpDt0qJsds00mqRub3RlxAjqABVHQ2y/lqNyY" +
                  "3bEIHts4k/rW6zAsWTinCIsV/X2PcOH1DkEglhBHF/hD3wCo3NuZMQg5/" +
                  "D4TQaBHfnzHI2HixFV9GcdUaGFwgCQhmf0SVhwaKGkdHlwZaNwYXk=")

        self.assertEqual(golden, encoding.msgpack_encode(signed_txn))

    def test_serialize_pay_lease(self):
        mn = ("advice pudding treat near rule blouse same whisper inner elec" +
              "tric quit surface sunny dismiss leader blood seat clown cost " +
              "exist hospital century reform able sponsor")
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
        txn = transaction.PaymentTxn(pk, fee, first_round, last_round, gh, to,
                                     amount, close, note, gen, lease=lease)
        signed_txn = txn.sign(sk)

        golden = ("gqNzaWfEQOMmFSIKsZvpW0txwzhmbgQjxv6IyN7BbV5sZ2aNgFbVcrWUn" +
                  "qPpQQxfPhV/wdu9jzEPUU1jAujYtcNCxJ7ONgejdHhujKNhbXTNA+ilY2" +
                  "xvc2XEIEDpNJKIJWTLzpxZpptnVCaJ6aHDoqnqW2Wm6KRCH/xXo2ZlZc0" +
                  "FLKJmds0wsqNnZW6sZGV2bmV0LXYzMy4womdoxCAmCyAJoJOohot5WHIv" +
                  "peVG7eftF+TYXEx4r7BFJpDt0qJsds00mqJseMQgAQIDBAECAwQBAgMEA" +
                  "QIDBAECAwQBAgMEAQIDBAECAwSkbm90ZcQI6gAVR0Nsv5ajcmN2xCB7bO" +
                  "JP61uswLFk4pwiLFf19j3Dh9Q5BIJYQRxf4Q98AqNzbmTEIOfw+E0GgR3" +
                  "58xyNh4sRVfRnHVGhhcIAkIZn9ElYcGihpHR5cGWjcGF5")

        self.assertEqual(golden, encoding.msgpack_encode(signed_txn))

    def test_serialize_keyreg(self):
        mn = ("awful drop leaf tennis indoor begin mandate discover uncle se" +
              "ven only coil atom any hospital uncover make any climb actor " +
              "armed measure need above hundred")
        sk = mnemonic.to_private_key(mn)
        pk = mnemonic.to_public_key(mn)
        fee = 1000
        first_round = 322575
        last_round = 323575
        gh = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
        votepk = encoding.encode_address(base64.b64decode(
                            "Kv7QI7chi1y6axoy+t7wzAVpePqRq/rkjzWh/RMYyLo="))
        selpk = encoding.encode_address(base64.b64decode(
                            "bPgrv4YogPcdaUAxrt1QysYZTVyRAuUMD4zQmCu9llc="))
        votefirst = 10000
        votelast = 10111
        votedilution = 11

        txn = transaction.KeyregTxn(pk, fee, first_round, last_round, gh,
                                    votepk, selpk, votefirst, votelast,
                                    votedilution, flat_fee=True)
        signed_txn = txn.sign(sk)

        golden = ("gqNzaWfEQEA8ANbrvTRxU9c8v6WERcEPw7D/HacRgg4vICa61vEof60Ww" +
                  "tx6KJKDyvBuvViFeacLlngPY6vYCVP0DktTwQ2jdHhui6NmZWXNA+iiZn" +
                  "bOAATsD6JnaMQgSGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiK" +
                  "ibHbOAATv96ZzZWxrZXnEIGz4K7+GKID3HWlAMa7dUMrGGU1ckQLlDA+M" +
                  "0JgrvZZXo3NuZMQgCfvSdiwI+Gxa5r9t16epAd5mdddQ4H6MXHaYZH224" +
                  "f2kdHlwZaZrZXlyZWendm90ZWZzdM0nEKZ2b3Rla2QLp3ZvdGVrZXnEIC" +
                  "r+0CO3IYtcumsaMvre8MwFaXj6kav65I81of0TGMi6p3ZvdGVsc3TNJ38=")

        self.assertEqual(golden, encoding.msgpack_encode(signed_txn))

    def test_serialize_asset_create(self):
        mn = ("awful drop leaf tennis indoor begin mandate discover uncle se" +
              "ven only coil atom any hospital uncover make any climb actor " +
              "armed measure need above hundred")
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

        txn = transaction.AssetConfigTxn(pk, fee, first_round, last_round, gh,
                                         total=total, manager=pk, reserve=pk,
                                         freeze=pk, clawback=pk,
                                         unit_name=unitname,
                                         asset_name=assetname, url=url,
                                         metadata_hash=metadata,
                                         default_frozen=False)
        signed_txn = txn.sign(sk)
        golden = ("gqNzaWfEQEDd1OMRoQI/rzNlU4iiF50XQXmup3k5czI9hEsNqHT7K4Ksf" +
                  "mA/0DUVkbzOwtJdRsHS8trm3Arjpy9r7AXlbAujdHhuh6RhcGFyiaJhbc" +
                  "QgZkFDUE80blJnTzU1ajFuZEFLM1c2U2djNEFQa2N5RmiiYW6odGVzdGN" +
                  "vaW6iYXWnd2Vic2l0ZaFjxCAJ+9J2LAj4bFrmv23Xp6kB3mZ111Dgfoxc" +
                  "dphkfbbh/aFmxCAJ+9J2LAj4bFrmv23Xp6kB3mZ111Dgfoxcdphkfbbh/" +
                  "aFtxCAJ+9J2LAj4bFrmv23Xp6kB3mZ111Dgfoxcdphkfbbh/aFyxCAJ+9" +
                  "J2LAj4bFrmv23Xp6kB3mZ111Dgfoxcdphkfbbh/aF0ZKJ1bqN0c3SjZmV" +
                  "lzQ+0omZ2zgAE7A+iZ2jEIEhjtRiks8hOyBDyLU8QgcsPcfBZp6wg3sYv" +
                  "f3DlCToiomx2zgAE7/ejc25kxCAJ+9J2LAj4bFrmv23Xp6kB3mZ111Dgf" +
                  "oxcdphkfbbh/aR0eXBlpGFjZmc=")
        self.assertEqual(golden, encoding.msgpack_encode(signed_txn))

    def test_serialize_asset_config(self):
        mn = ("awful drop leaf tennis indoor begin mandate discover uncle se" +
              "ven only coil atom any hospital uncover make any climb actor " +
              "armed measure need above hundred")
        sk = mnemonic.to_private_key(mn)
        pk = mnemonic.to_public_key(mn)
        fee = 10
        first_round = 322575
        last_round = 323575
        gh = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
        index = 1234
        txn = transaction.AssetConfigTxn(pk, fee, first_round, last_round, gh,
                                         manager=pk, reserve=pk, freeze=pk,
                                         clawback=pk, index=index)
        signed_txn = txn.sign(sk)
        golden = ("gqNzaWfEQBBkfw5n6UevuIMDo2lHyU4dS80JCCQ/vTRUcTx5m0ivX68zT" +
                  "KyuVRrHaTbxbRRc3YpJ4zeVEnC9Fiw3Wf4REwejdHhuiKRhcGFyhKFjxC" +
                  "AJ+9J2LAj4bFrmv23Xp6kB3mZ111Dgfoxcdphkfbbh/aFmxCAJ+9J2LAj" +
                  "4bFrmv23Xp6kB3mZ111Dgfoxcdphkfbbh/aFtxCAJ+9J2LAj4bFrmv23X" +
                  "p6kB3mZ111Dgfoxcdphkfbbh/aFyxCAJ+9J2LAj4bFrmv23Xp6kB3mZ11" +
                  "1Dgfoxcdphkfbbh/aRjYWlkzQTSo2ZlZc0NSKJmds4ABOwPomdoxCBIY7" +
                  "UYpLPITsgQ8i1PEIHLD3HwWaesIN7GL39w5Qk6IqJsds4ABO/3o3NuZMQ" +
                  "gCfvSdiwI+Gxa5r9t16epAd5mdddQ4H6MXHaYZH224f2kdHlwZaRhY2Zn")

        self.assertEqual(golden, encoding.msgpack_encode(signed_txn))

    def test_serialize_asset_destroy(self):
        mn = ("awful drop leaf tennis indoor begin mandate discover uncle se" +
              "ven only coil atom any hospital uncover make any climb actor " +
              "armed measure need above hundred")
        sk = mnemonic.to_private_key(mn)
        pk = mnemonic.to_public_key(mn)
        fee = 10
        first_round = 322575
        last_round = 323575
        gh = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
        index = 1
        txn = transaction.AssetConfigTxn(pk, fee, first_round, last_round, gh,
                                         index=index)
        signed_txn = txn.sign(sk)
        golden = ("gqNzaWfEQBSP7HtzD/Lvn4aVvaNpeR4T93dQgo4LvywEwcZgDEoc/WVl3" +
                  "aKsZGcZkcRFoiWk8AidhfOZzZYutckkccB8RgGjdHhuh6RjYWlkAaNmZW" +
                  "XNB1iiZnbOAATsD6JnaMQgSGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9" +
                  "/cOUJOiKibHbOAATv96NzbmTEIAn70nYsCPhsWua/bdenqQHeZnXXUOB+" +
                  "jFx2mGR9tuH9pHR5cGWkYWNmZw==")
        self.assertEqual(golden, encoding.msgpack_encode(signed_txn))

    def test_serialize_asset_freeze(self):
        mn = ("awful drop leaf tennis indoor begin mandate discover uncle se" +
              "ven only coil atom any hospital uncover make any climb actor " +
              "armed measure need above hundred")
        sk = mnemonic.to_private_key(mn)
        pk = mnemonic.to_public_key(mn)
        fee = 10
        first_round = 322575
        last_round = 323576
        gh = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
        index = 1
        target = "BH55E5RMBD4GYWXGX5W5PJ5JAHPGM5OXKDQH5DC4O2MGI7NW4H6VOE4CP4"
        txn = transaction.AssetFreezeTxn(pk, fee, first_round, last_round, gh,
                                         index=index, target=target,
                                         new_freeze_state=True)
        signed_txn = txn.sign(sk)
        golden = ("gqNzaWfEQAhru5V2Xvr19s4pGnI0aslqwY4lA2skzpYtDTAN9DKSH5+qs" +
                  "fQQhm4oq+9VHVj7e1rQC49S28vQZmzDTVnYDQGjdHhuiaRhZnJ6w6RmYW" +
                  "RkxCAJ+9J2LAj4bFrmv23Xp6kB3mZ111Dgfoxcdphkfbbh/aRmYWlkAaN" +
                  "mZWXNCRqiZnbOAATsD6JnaMQgSGO1GKSzyE7IEPItTxCByw9x8FmnrCDe" +
                  "xi9/cOUJOiKibHbOAATv+KNzbmTEIAn70nYsCPhsWua/bdenqQHeZnXXU" +
                  "OB+jFx2mGR9tuH9pHR5cGWkYWZyeg==")
        self.assertEqual(golden, encoding.msgpack_encode(signed_txn))

    def test_serialize_asset_transfer(self):
        mn = ("awful drop leaf tennis indoor begin mandate discover uncle se" +
              "ven only coil atom any hospital uncover make any climb actor " +
              "armed measure need above hundred")
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
        txn = transaction.AssetTransferTxn(pk, fee, first_round, last_round,
                                           gh, to, amount, index, close)
        signed_txn = txn.sign(sk)
        golden = ("gqNzaWfEQNkEs3WdfFq6IQKJdF1n0/hbV9waLsvojy9pM1T4fvwfMNdjG" +
                  "QDy+LeesuQUfQVTneJD4VfMP7zKx4OUlItbrwSjdHhuiqRhYW10AaZhY2" +
                  "xvc2XEIAn70nYsCPhsWua/bdenqQHeZnXXUOB+jFx2mGR9tuH9pGFyY3b" +
                  "EIAn70nYsCPhsWua/bdenqQHeZnXXUOB+jFx2mGR9tuH9o2ZlZc0KvqJm" +
                  "ds4ABOwPomdoxCBIY7UYpLPITsgQ8i1PEIHLD3HwWaesIN7GL39w5Qk6I" +
                  "qJsds4ABO/4o3NuZMQgCfvSdiwI+Gxa5r9t16epAd5mdddQ4H6MXHaYZH" +
                  "224f2kdHlwZaVheGZlcqR4YWlkAQ==")
        self.assertEqual(golden, encoding.msgpack_encode(signed_txn))

    def test_serialize_asset_accept(self):
        mn = ("awful drop leaf tennis indoor begin mandate discover uncle se" +
              "ven only coil atom any hospital uncover make any climb actor " +
              "armed measure need above hundred")
        sk = mnemonic.to_private_key(mn)
        pk = mnemonic.to_public_key(mn)
        fee = 10
        first_round = 322575
        last_round = 323575
        gh = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
        index = 1
        amount = 0
        to = "BH55E5RMBD4GYWXGX5W5PJ5JAHPGM5OXKDQH5DC4O2MGI7NW4H6VOE4CP4"
        txn = transaction.AssetTransferTxn(pk, fee, first_round, last_round,
                                           gh, to, amount, index)
        signed_txn = txn.sign(sk)
        golden = ("gqNzaWfEQJ7q2rOT8Sb/wB0F87ld+1zMprxVlYqbUbe+oz0WM63FctIi+" +
                  "K9eYFSqT26XBZ4Rr3+VTJpBE+JLKs8nctl9hgijdHhuiKRhcmN2xCAJ+9" +
                  "J2LAj4bFrmv23Xp6kB3mZ111Dgfoxcdphkfbbh/aNmZWXNCOiiZnbOAAT" +
                  "sD6JnaMQgSGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiKibHbO" +
                  "AATv96NzbmTEIAn70nYsCPhsWua/bdenqQHeZnXXUOB+jFx2mGR9tuH9p" +
                  "HR5cGWlYXhmZXKkeGFpZAE=")
        self.assertEqual(golden, encoding.msgpack_encode(signed_txn))

    def test_serialize_asset_revoke(self):
        mn = ("awful drop leaf tennis indoor begin mandate discover uncle se" +
              "ven only coil atom any hospital uncover make any climb actor " +
              "armed measure need above hundred")
        sk = mnemonic.to_private_key(mn)
        pk = mnemonic.to_public_key(mn)
        fee = 10
        first_round = 322575
        last_round = 323575
        gh = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
        index = 1
        amount = 1
        to = "BH55E5RMBD4GYWXGX5W5PJ5JAHPGM5OXKDQH5DC4O2MGI7NW4H6VOE4CP4"
        txn = transaction.AssetTransferTxn(pk, fee, first_round, last_round,
                                           gh, to, amount, index,
                                           revocation_target=to)
        signed_txn = txn.sign(sk)
        golden = ("gqNzaWfEQHsgfEAmEHUxLLLR9s+Y/yq5WeoGo/jAArCbany+7ZYwExMyS" +
                  "zAhmV7M7S8+LBtJalB4EhzEUMKmt3kNKk6+vAWjdHhuiqRhYW10AaRhcm" +
                  "N2xCAJ+9J2LAj4bFrmv23Xp6kB3mZ111Dgfoxcdphkfbbh/aRhc25kxCA" +
                  "J+9J2LAj4bFrmv23Xp6kB3mZ111Dgfoxcdphkfbbh/aNmZWXNCqqiZnbO" +
                  "AATsD6JnaMQgSGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiKib" +
                  "HbOAATv96NzbmTEIAn70nYsCPhsWua/bdenqQHeZnXXUOB+jFx2mGR9tu" +
                  "H9pHR5cGWlYXhmZXKkeGFpZAE=")
        self.assertEqual(golden, encoding.msgpack_encode(signed_txn))

    def test_group_id(self):
        address = "UPYAFLHSIPMJOHVXU2MPLQ46GXJKSDCEMZ6RLCQ7GWB5PRDKJUWKKXECXI"
        fromAddress, toAddress = address, address
        fee = 1000
        amount = 2000
        genesisID = "devnet-v1.0"
        genesisHash = "sC3P7e2SdbqKJK0tbiCdK9tdSpbe6XeCGKdoNzmlj0E="

        firstRound1 = 710399
        note1 = base64.b64decode("wRKw5cJ0CMo=")

        tx1 = transaction.PaymentTxn(
            fromAddress, fee, firstRound1, firstRound1 + 1000,
            genesisHash, toAddress, amount,
            note=note1, gen=genesisID, flat_fee=True
        )

        firstRound2 = 710515
        note2 = base64.b64decode("dBlHI6BdrIg=")
        tx2 = transaction.PaymentTxn(
            fromAddress, fee, firstRound2, firstRound2 + 1000,
            genesisHash, toAddress, amount,
            note=note2, gen=genesisID, flat_fee=True
        )

        # goal clerk send dumps unsigned transaction as signed with empty
        # signature in order to save tx type
        stx1 = transaction.SignedTransaction(tx1, None)
        stx2 = transaction.SignedTransaction(tx2, None)

        goldenTx1 = (
            "gaN0eG6Ko2FtdM0H0KNmZWXNA+iiZnbOAArW/6NnZW6rZGV2bmV0LXYxLjCiZ2j" +
            "EILAtz+3tknW6iiStLW4gnSvbXUqW3ul3ghinaDc5pY9Bomx2zgAK2uekbm90Zc" +
            "QIwRKw5cJ0CMqjcmN2xCCj8AKs8kPYlx63ppj1w5410qkMRGZ9FYofNYPXxGpNL" +
            "KNzbmTEIKPwAqzyQ9iXHremmPXDnjXSqQxEZn0Vih81g9fEak0spHR5cGWjcGF5"
        )
        goldenTx2 = (
            "gaN0eG6Ko2FtdM0H0KNmZWXNA+iiZnbOAArXc6NnZW6rZGV2bmV0LXYxLjCiZ2j" +
            "EILAtz+3tknW6iiStLW4gnSvbXUqW3ul3ghinaDc5pY9Bomx2zgAK21ukbm90Zc" +
            "QIdBlHI6BdrIijcmN2xCCj8AKs8kPYlx63ppj1w5410qkMRGZ9FYofNYPXxGpNL" +
            "KNzbmTEIKPwAqzyQ9iXHremmPXDnjXSqQxEZn0Vih81g9fEak0spHR5cGWjcGF5"
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
            "gaN0eG6Lo2FtdM0H0KNmZWXNA+iiZnbOAArW/6NnZW6rZGV2bmV0LXYxLjCiZ2j" +
            "EILAtz+3tknW6iiStLW4gnSvbXUqW3ul3ghinaDc5pY9Bo2dycMQgLiQ9OBup9H" +
            "/bZLSfQUH2S6iHUM6FQ3PLuv9FNKyt09SibHbOAAra56Rub3RlxAjBErDlwnQIy" +
            "qNyY3bEIKPwAqzyQ9iXHremmPXDnjXSqQxEZn0Vih81g9fEak0so3NuZMQgo/AC" +
            "rPJD2Jcet6aY9cOeNdKpDERmfRWKHzWD18RqTSykdHlwZaNwYXmBo3R4boujYW1" +
            "0zQfQo2ZlZc0D6KJmds4ACtdzo2dlbqtkZXZuZXQtdjEuMKJnaMQgsC3P7e2Sdb" +
            "qKJK0tbiCdK9tdSpbe6XeCGKdoNzmlj0GjZ3JwxCAuJD04G6n0f9tktJ9BQfZLq" +
            "IdQzoVDc8u6/0U0rK3T1KJsds4ACttbpG5vdGXECHQZRyOgXayIo3JjdsQgo/AC" +
            "rPJD2Jcet6aY9cOeNdKpDERmfRWKHzWD18RqTSyjc25kxCCj8AKs8kPYlx63ppj" +
            "1w5410qkMRGZ9FYofNYPXxGpNLKR0eXBlo3BheQ=="
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


class TestMnemonic(unittest.TestCase):
    def test_mnemonic_private_key(self):
        priv_key, address = account.generate_account()
        mn = mnemonic.from_private_key(priv_key)
        self.assertEqual(len(mn.split(" ")), constants.mnemonic_len)
        self.assertEqual(priv_key, mnemonic.to_private_key(mn))

    def test_zero_mnemonic(self):
        zero_bytes = bytes([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        expected_mnemonic = ("abandon abandon abandon abandon abandon " +
                             "abandon abandon abandon abandon abandon " +
                             "abandon abandon abandon abandon abandon " +
                             "abandon abandon abandon abandon abandon " +
                             "abandon abandon abandon abandon invest")
        result = mnemonic._from_key(zero_bytes)
        self.assertEqual(expected_mnemonic, result)
        result = mnemonic._to_key(result)
        self.assertEqual(zero_bytes, result)

    def test_wrong_checksum(self):
        mn = ("abandon abandon abandon abandon abandon abandon abandon " +
              "abandon abandon abandon abandon abandon abandon abandon " +
              "abandon abandon abandon abandon abandon abandon abandon " +
              "abandon abandon abandon abandon")
        self.assertRaises(error.WrongChecksumError, mnemonic._to_key, mn)

    def test_word_not_in_list(self):
        mn = ("abandon abandon abandon abandon abandon abandon abandon " +
              "abandon abandon abandon abandon abandon abandon abandon " +
              "abandon abandon abandon venues abandon abandon abandon " +
              "abandon abandon abandon invest")
        self.assertRaises(ValueError, mnemonic._to_key, mn)

    def test_wordlist(self):
        result = mnemonic._checksum(bytes(wordlist.word_list_raw(), "utf-8"))
        self.assertEqual(result, "venue")

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
        mn = ("auction inquiry lava second expand liberty glass involve " +
              "ginger illness length room item discover ahead table doctor " +
              "term tackle cement bonus profit right above catch")

        sk = mnemonic.to_private_key(mn)
        sender = "RWJLJCMQAFZ2ATP2INM2GZTKNL6OULCCUBO5TQPXH3V2KR4AG7U5UA5JNM"
        rcv = "PNWOET7LLOWMBMLE4KOCELCX6X3D3Q4H2Q4QJASYIEOF7YIPPQBG3YQ5YI"
        gh = "/rNsORAUOQDD2lVCyhg2sA/S+BlZElfNI/YEL5jINp0="
        close = "IDUTJEUIEVSMXTU4LGTJWZ2UE2E6TIODUKU6UW3FU3UKIQQ77RLUBBBFLA"
        txn = transaction.PaymentTxn(sender, 0, 62229, 63229, gh, rcv, 1000,
                                     note=base64.b64decode("RSYiABhShvs="),
                                     gen="devnet-v38.0",
                                     close_remainder_to=close)

        mtx = transaction.MultisigTransaction(txn, msig)
        mtx.sign(sk)
        golden = ("gqRtc2lng6ZzdWJzaWeTgqJwa8QgG37AsEvqYbeWkJfmy/QH4QinBTUdC" +
                  "8mKvrEiCairgXihc8RAuLAFE0oma0skOoAmOzEwfPuLYpEWl4LINtsiLr" +
                  "UqWQkDxh4WHb29//YCpj4MFbiSgD2jKYt0XKRD86zKCF4RDYGicGvEIAl" +
                  "jMglTc4nwdWcRdzmRx9A+G3PIxPUr9q/wGqJc+cJxgaJwa8Qg5/D4TQaB" +
                  "HfnzHI2HixFV9GcdUaGFwgCQhmf0SVhwaKGjdGhyAqF2AaN0eG6Lo2Ftd" +
                  "M0D6KVjbG9zZcQgQOk0koglZMvOnFmmm2dUJonpocOiqepbZabopEIf/F" +
                  "ejZmVlzQPoomZ2zfMVo2dlbqxkZXZuZXQtdjM4LjCiZ2jEIP6zbDkQFDk" +
                  "Aw9pVQsoYNrAP0vgZWRJXzSP2BC+YyDadomx2zfb9pG5vdGXECEUmIgAY" +
                  "Uob7o3JjdsQge2ziT+tbrMCxZOKcIixX9fY9w4fUOQSCWEEcX+EPfAKjc" +
                  "25kxCCNkrSJkAFzoE36Q1mjZmpq/OosQqBd2cH3PuulR4A36aR0eXBlo3" +
                  "BheQ==")
        self.assertEqual(golden, encoding.msgpack_encode(mtx))

        mtx_2 = transaction.MultisigTransaction(txn,
                                                msig.get_multisig_account())
        mn2 = ("since during average anxiety protect cherry club long " +
               "lawsuit loan expand embark forum theory winter park twenty " +
               "ball kangaroo cram burst board host ability left")
        sk2 = mnemonic.to_private_key(mn2)
        mtx_2.sign(sk2)

        mtx_final = transaction.MultisigTransaction.merge([mtx, mtx_2])

        golden2 = ("gqRtc2lng6ZzdWJzaWeTgqJwa8QgG37AsEvqYbeWkJfmy/QH4QinBTUd" +
                   "C8mKvrEiCairgXihc8RAuLAFE0oma0skOoAmOzEwfPuLYpEWl4LINtsi" +
                   "LrUqWQkDxh4WHb29//YCpj4MFbiSgD2jKYt0XKRD86zKCF4RDYKicGvE" +
                   "IAljMglTc4nwdWcRdzmRx9A+G3PIxPUr9q/wGqJc+cJxoXPEQBAhuyRj" +
                   "sOrnHp3s/xI+iMKiL7QPsh8iJZ22YOJJP0aFUwedMr+a6wfdBXk1Oefy" +
                   "rAN1wqJ9rq6O+DrWV1fH0ASBonBrxCDn8PhNBoEd+fMcjYeLEVX0Zx1R" +
                   "oYXCAJCGZ/RJWHBooaN0aHICoXYBo3R4boujYW10zQPopWNsb3NlxCBA" +
                   "6TSSiCVky86cWaabZ1Qmiemhw6Kp6ltlpuikQh/8V6NmZWXNA+iiZnbN" +
                   "8xWjZ2VurGRldm5ldC12MzguMKJnaMQg/rNsORAUOQDD2lVCyhg2sA/S" +
                   "+BlZElfNI/YEL5jINp2ibHbN9v2kbm90ZcQIRSYiABhShvujcmN2xCB7" +
                   "bOJP61uswLFk4pwiLFf19j3Dh9Q5BIJYQRxf4Q98AqNzbmTEII2StImQ" +
                   "AXOgTfpDWaNmamr86ixCoF3Zwfc+66VHgDfppHR5cGWjcGF5")
        self.assertEqual(golden2, encoding.msgpack_encode(mtx_final))

    def test_sign(self):
        msig = transaction.Multisig(1, 2, [
            "DN7MBMCL5JQ3PFUQS7TMX5AH4EEKOBJVDUF4TCV6WERATKFLQF4MQUPZTA",
            "BFRTECKTOOE7A5LHCF3TTEOH2A7BW46IYT2SX5VP6ANKEXHZYJY77SJTVM",
            "47YPQTIGQEO7T4Y4RWDYWEKV6RTR2UNBQXBABEEGM72ESWDQNCQ52OPASU"
        ])
        mn = ("advice pudding treat near rule blouse same whisper inner " +
              "electric quit surface sunny dismiss leader blood seat clown " +
              "cost exist hospital century reform able sponsor")
        sk = mnemonic.to_private_key(mn)

        rcv = "PNWOET7LLOWMBMLE4KOCELCX6X3D3Q4H2Q4QJASYIEOF7YIPPQBG3YQ5YI"
        gh = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
        close = "IDUTJEUIEVSMXTU4LGTJWZ2UE2E6TIODUKU6UW3FU3UKIQQ77RLUBBBFLA"
        txn = transaction.PaymentTxn(msig.address(), 4, 12466, 13466, gh,
                                     rcv, 1000,
                                     note=base64.b64decode("X4Bl4wQ9rCo="),
                                     gen="devnet-v33.0",
                                     close_remainder_to=close)
        mtx = transaction.MultisigTransaction(txn, msig)
        mtx.sign(sk)
        golden = ("gqRtc2lng6ZzdWJzaWeTgaJwa8QgG37AsEvqYbeWkJfmy/QH4QinBTUdC" +
                  "8mKvrEiCairgXiBonBrxCAJYzIJU3OJ8HVnEXc5kcfQPhtzyMT1K/av8B" +
                  "qiXPnCcYKicGvEIOfw+E0GgR358xyNh4sRVfRnHVGhhcIAkIZn9ElYcGi" +
                  "hoXPEQF6nXZ7CgInd1h7NVspIPFZNhkPL+vGFpTNwH3Eh9gwPM8pf1EPT" +
                  "HfPvjf14sS7xN7mTK+wrz7Odhp4rdWBNUASjdGhyAqF2AaN0eG6Lo2Ftd" +
                  "M0D6KVjbG9zZcQgQOk0koglZMvOnFmmm2dUJonpocOiqepbZabopEIf/F" +
                  "ejZmVlzQSYomZ2zTCyo2dlbqxkZXZuZXQtdjMzLjCiZ2jEICYLIAmgk6i" +
                  "Gi3lYci+l5Ubt5+0X5NhcTHivsEUmkO3Somx2zTSapG5vdGXECF+AZeME" +
                  "Pawqo3JjdsQge2ziT+tbrMCxZOKcIixX9fY9w4fUOQSCWEEcX+EPfAKjc" +
                  "25kxCCNkrSJkAFzoE36Q1mjZmpq/OosQqBd2cH3PuulR4A36aR0eXBlo3" +
                  "BheQ==")
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
        private_key_2, account_2 = account.generate_account()
        private_key_3, account_3 = account.generate_account()

        # create transaction
        gh = "JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI="
        txn = transaction.PaymentTxn(account_2, 3, 1234, 1334,
                                     gh, account_2, 1000)

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
        bid = ("gqFigqNiaWSGo2FpZAGjYXVjxCCokNFWl9DCqHrP9trjPICAMGOaRoX/OR+" +
               "M6tHWhfUBkKZiaWRkZXLEIP1rCXe2x5+exPBfU3CZwGPMY8mzwvglET+Qtg" +
               "fCPdCmo2N1cs8AAADN9kTOAKJpZM5JeDcCpXByaWNlzQMgo3NpZ8RAiR06J" +
               "4suAixy13BKHlw4VrORKzLT5CJr9n3YSj0Ao6byV23JHGU0yPf7u9/o4ECw" +
               "4Xy9hc9pWopLW97xKXRfA6F0oWI=")
        self.assertEqual(bid, encoding.msgpack_encode(
                         encoding.msgpack_decode(bid)))

    def test_signed_txn(self):
        stxn = ("gqNzaWfEQGdpjnStb70k2iXzOlu+RSMgCYLe25wkUfbgRsXs7jx6rbW61i" +
                "vCs6/zGs3gZAZf4L2XAQak7OjMh3lw9MTCIQijdHhuiaNhbXTOAAGGoKNm" +
                "ZWXNA+iiZnbNcl+jZ2Vuq25ldHdvcmstdjM4omdoxCBN/+nfiNPXLbuigk" +
                "8M/TXsMUfMK7dV//xB1wkoOhNu9qJsds1yw6NyY3bEIPRUuVDPVUFC7Jk3" +
                "+xDjHJfwWFDp+Wjy+Hx3cwL9ncVYo3NuZMQgGC5kQiOIPooA8mrvoHRyFt" +
                "k27F/PPN08bAufGhnp0BGkdHlwZaNwYXk=")
        self.assertEqual(stxn, encoding.msgpack_encode(
                         encoding.msgpack_decode(stxn)))

    def test_payment_txn(self):
        paytxn = ("iaNhbXTOAAGGoKNmZWXNA+iiZnbNcq2jZ2Vuq25ldHdvcmstdjM4omdo" +
                  "xCBN/+nfiNPXLbuigk8M/TXsMUfMK7dV//xB1wkoOhNu9qJsds1zEaNy" +
                  "Y3bEIAZ2cvp4J0OiBy5eAHIX/njaRko955rEdN4AUNEl4rxTo3NuZMQg" +
                  "GC5kQiOIPooA8mrvoHRyFtk27F/PPN08bAufGhnp0BGkdHlwZaNwYXk=")
        self.assertEqual(paytxn, encoding.msgpack_encode(
                         encoding.msgpack_decode(paytxn)))

    def test_multisig_txn(self):
        msigtxn = ("gqRtc2lng6ZzdWJzaWeSgqJwa8Qg1ke3gkLuR0MUN/Ku0oyiRVIm9P1" +
                   "QFDaiEhT5vtfLmd+hc8RAIEbfnhccjWfYQFQp/P4aJjATFdgaDDpnhy" +
                   "JF0tU/37CO5I5hhoCvUCRH/A/6X94Ewz9YEtk5dANEGKQW+/WyAIKic" +
                   "GvEIKgAZfZ4iDC+UY/P5F3tgs5rqeyYt08LT0c/D78u0V7KoXPEQCxU" +
                   "kQgTVC9lLpKVzcZGKesSCQcZL9UjXTzrteADicvcca7KT3WP0crGgAf" +
                   "J3a17Na5cykJzFEn7pq2SHgwD/QujdGhyAqF2AaN0eG6Jo2FtdM0D6K" +
                   "NmZWXNA+iiZnbNexSjZ2Vuq25ldHdvcmstdjM4omdoxCBN/+nfiNPXL" +
                   "buigk8M/TXsMUfMK7dV//xB1wkoOhNu9qJsds17eKNyY3bEIBguZEIj" +
                   "iD6KAPJq76B0chbZNuxfzzzdPGwLnxoZ6dARo3NuZMQgpuIJvJzW8E4" +
                   "uxsQGCW0S3n1u340PbHTB2zhtXo/AiI6kdHlwZaNwYXk=")
        self.assertEqual(msigtxn, encoding.msgpack_encode(
                         encoding.msgpack_decode(msigtxn)))

    def test_keyreg_txn(self):
        keyregtxn = ("jKNmZWXNA+iiZnbNcoqjZ2Vuq25ldHdvcmstdjM4omdoxCBN/+nfi" +
                     "NPXLbuigk8M/TXsMUfMK7dV//xB1wkoOhNu9qJsds1y7qZzZWxrZX" +
                     "nEIBguZEIjiD6KAPJq76B0chbZNuxfzzzdPGwLnxoZ6dARo3NuZMQ" +
                     "gGC5kQiOIPooA8mrvoHRyFtk27F/PPN08bAufGhnp0BGkdHlwZaZr" +
                     "ZXlyZWendm90ZWZzdM1yiqZ2b3Rla2TNMDmndm90ZWtlecQgGC5kQ" +
                     "iOIPooA8mrvoHRyFtk27F/PPN08bAufGhnp0BGndm90ZWxzdM1y7g==")
        self.assertEqual(keyregtxn, encoding.msgpack_encode(
                         encoding.msgpack_decode(keyregtxn)))

    def test_asset_create(self):
        golden = ("gqNzaWfEQEDd1OMRoQI/rzNlU4iiF50XQXmup3k5czI9hEsNqHT7K4Ksf" +
                  "mA/0DUVkbzOwtJdRsHS8trm3Arjpy9r7AXlbAujdHhuh6RhcGFyiaJhbc" +
                  "QgZkFDUE80blJnTzU1ajFuZEFLM1c2U2djNEFQa2N5RmiiYW6odGVzdGN" +
                  "vaW6iYXWnd2Vic2l0ZaFjxCAJ+9J2LAj4bFrmv23Xp6kB3mZ111Dgfoxc" +
                  "dphkfbbh/aFmxCAJ+9J2LAj4bFrmv23Xp6kB3mZ111Dgfoxcdphkfbbh/" +
                  "aFtxCAJ+9J2LAj4bFrmv23Xp6kB3mZ111Dgfoxcdphkfbbh/aFyxCAJ+9" +
                  "J2LAj4bFrmv23Xp6kB3mZ111Dgfoxcdphkfbbh/aF0ZKJ1bqN0c3SjZmV" +
                  "lzQ+0omZ2zgAE7A+iZ2jEIEhjtRiks8hOyBDyLU8QgcsPcfBZp6wg3sYv" +
                  "f3DlCToiomx2zgAE7/ejc25kxCAJ+9J2LAj4bFrmv23Xp6kB3mZ111Dgf" +
                  "oxcdphkfbbh/aR0eXBlpGFjZmc=")
        self.assertEqual(golden, encoding.msgpack_encode(
                         encoding.msgpack_decode(golden)))

    def test_asset_config(self):
        assettxn = ("gqNzaWfEQBBkfw5n6UevuIMDo2lHyU4dS80JCCQ/vTRUcTx5m0ivX6" +
                    "8zTKyuVRrHaTbxbRRc3YpJ4zeVEnC9Fiw3Wf4REwejdHhuiKRhcGFy" +
                    "hKFjxCAJ+9J2LAj4bFrmv23Xp6kB3mZ111Dgfoxcdphkfbbh/aFmxC" +
                    "AJ+9J2LAj4bFrmv23Xp6kB3mZ111Dgfoxcdphkfbbh/aFtxCAJ+9J2" +
                    "LAj4bFrmv23Xp6kB3mZ111Dgfoxcdphkfbbh/aFyxCAJ+9J2LAj4bF" +
                    "rmv23Xp6kB3mZ111Dgfoxcdphkfbbh/aRjYWlkzQTSo2ZlZc0NSKJm" +
                    "ds4ABOwPomdoxCBIY7UYpLPITsgQ8i1PEIHLD3HwWaesIN7GL39w5Q" +
                    "k6IqJsds4ABO/3o3NuZMQgCfvSdiwI+Gxa5r9t16epAd5mdddQ4H6M" +
                    "XHaYZH224f2kdHlwZaRhY2Zn")
        self.assertEqual(assettxn, encoding.msgpack_encode(
                         encoding.msgpack_decode(assettxn)))

    def test_asset_destroy(self):
        assettxn = ("gqNzaWfEQBSP7HtzD/Lvn4aVvaNpeR4T93dQgo4LvywEwcZgDEoc/W" +
                    "Vl3aKsZGcZkcRFoiWk8AidhfOZzZYutckkccB8RgGjdHhuh6RjYWlk" +
                    "AaNmZWXNB1iiZnbOAATsD6JnaMQgSGO1GKSzyE7IEPItTxCByw9x8F" +
                    "mnrCDexi9/cOUJOiKibHbOAATv96NzbmTEIAn70nYsCPhsWua/bden" +
                    "qQHeZnXXUOB+jFx2mGR9tuH9pHR5cGWkYWNmZw==")
        self.assertEqual(assettxn, encoding.msgpack_encode(
                         encoding.msgpack_decode(assettxn)))

    def test_asset_freeze(self):
        assettxn = ("gqNzaWfEQAhru5V2Xvr19s4pGnI0aslqwY4lA2skzpYtDTAN9DKSH5" +
                    "+qsfQQhm4oq+9VHVj7e1rQC49S28vQZmzDTVnYDQGjdHhuiaRhZnJ6" +
                    "w6RmYWRkxCAJ+9J2LAj4bFrmv23Xp6kB3mZ111Dgfoxcdphkfbbh/a" +
                    "RmYWlkAaNmZWXNCRqiZnbOAATsD6JnaMQgSGO1GKSzyE7IEPItTxCB" +
                    "yw9x8FmnrCDexi9/cOUJOiKibHbOAATv+KNzbmTEIAn70nYsCPhsWu" +
                    "a/bdenqQHeZnXXUOB+jFx2mGR9tuH9pHR5cGWkYWZyeg==")
        self.assertEqual(assettxn, encoding.msgpack_encode(
                         encoding.msgpack_decode(assettxn)))

    def test_asset_transfer(self):
        assettxn = ("gqNzaWfEQNkEs3WdfFq6IQKJdF1n0/hbV9waLsvojy9pM1T4fvwfMN" +
                    "djGQDy+LeesuQUfQVTneJD4VfMP7zKx4OUlItbrwSjdHhuiqRhYW10" +
                    "AaZhY2xvc2XEIAn70nYsCPhsWua/bdenqQHeZnXXUOB+jFx2mGR9tu" +
                    "H9pGFyY3bEIAn70nYsCPhsWua/bdenqQHeZnXXUOB+jFx2mGR9tuH9" +
                    "o2ZlZc0KvqJmds4ABOwPomdoxCBIY7UYpLPITsgQ8i1PEIHLD3HwWa" +
                    "esIN7GL39w5Qk6IqJsds4ABO/4o3NuZMQgCfvSdiwI+Gxa5r9t16ep" +
                    "Ad5mdddQ4H6MXHaYZH224f2kdHlwZaVheGZlcqR4YWlkAQ==")
        self.assertEqual(assettxn, encoding.msgpack_encode(
                         encoding.msgpack_decode(assettxn)))

    def test_asset_accept(self):
        assettxn = ("gqNzaWfEQJ7q2rOT8Sb/wB0F87ld+1zMprxVlYqbUbe+oz0WM63Fct" +
                    "Ii+K9eYFSqT26XBZ4Rr3+VTJpBE+JLKs8nctl9hgijdHhuiKRhcmN2" +
                    "xCAJ+9J2LAj4bFrmv23Xp6kB3mZ111Dgfoxcdphkfbbh/aNmZWXNCO" +
                    "iiZnbOAATsD6JnaMQgSGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/" +
                    "cOUJOiKibHbOAATv96NzbmTEIAn70nYsCPhsWua/bdenqQHeZnXXUO" +
                    "B+jFx2mGR9tuH9pHR5cGWlYXhmZXKkeGFpZAE=")
        self.assertEqual(assettxn, encoding.msgpack_encode(
                         encoding.msgpack_decode(assettxn)))

    def test_asset_revoke(self):
        assettxn = ("gqNzaWfEQHsgfEAmEHUxLLLR9s+Y/yq5WeoGo/jAArCbany+7ZYwEx" +
                    "MySzAhmV7M7S8+LBtJalB4EhzEUMKmt3kNKk6+vAWjdHhuiqRhYW10" +
                    "AaRhcmN2xCAJ+9J2LAj4bFrmv23Xp6kB3mZ111Dgfoxcdphkfbbh/a" +
                    "Rhc25kxCAJ+9J2LAj4bFrmv23Xp6kB3mZ111Dgfoxcdphkfbbh/aNm" +
                    "ZWXNCqqiZnbOAATsD6JnaMQgSGO1GKSzyE7IEPItTxCByw9x8FmnrC" +
                    "Dexi9/cOUJOiKibHbOAATv96NzbmTEIAn70nYsCPhsWua/bdenqQHe" +
                    "ZnXXUOB+jFx2mGR9tuH9pHR5cGWlYXhmZXKkeGFpZAE=")
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
    def test_parse_uvariant(self):
        data = b"\x01"
        value, length = logic.parse_uvariant(data)
        self.assertEqual(length, 1)
        self.assertEqual(value, 1)

        data = b"\x7b"
        value, length = logic.parse_uvariant(data)
        self.assertEqual(length, 1)
        self.assertEqual(value, 123)

        data = b"\xc8\x03"
        value, length = logic.parse_uvariant(data)
        self.assertEqual(length, 2)
        self.assertEqual(value, 456)

    def test_parse_intcblock(self):
        data = b"\x20\x05\x00\x01\xc8\x03\x7b\x02"
        size = logic.check_int_const_block(data, 0)
        self.assertEqual(size, len(data))

    def test_parse_bytecblock(self):
        data = (b"\x26\x02\x0d\x31\x32\x33\x34\x35\x36\x37\x38\x39\x30\x31" +
                b"\x32\x33\x02\x01\x02")
        size = logic.check_byte_const_block(data, 0)
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

        # check 800x keccak256 fail
        program += b"\x02" * 800
        with self.assertRaises(error.InvalidProgram):
            logic.check_program(program, [])


class TestLogicSig(unittest.TestCase):
    def test_basic(self):
        with self.assertRaises(error.InvalidProgram):
            lsig = transaction.LogicSig(None)

        with self.assertRaises(error.InvalidProgram):
            lsig = transaction.LogicSig(b"")

        program = b"\x01\x20\x01\x01\x22"  # int 1
        program_hash = ("6Z3C3LDVWGMX23BMSYMANACQOSINP" +
                        "FIRF77H7N3AWJZYV6OH6GWTJKVMXY")
        public_key = encoding.decode_address(program_hash)

        lsig = transaction.LogicSig(program)
        self.assertEqual(lsig.logic, program)
        self.assertEqual(lsig.args, None)
        self.assertEqual(lsig.sig, None)
        self.assertEqual(lsig.msig, None)
        verifed = lsig.verify(public_key)
        self.assertTrue(verifed)
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
        verifed = lsig.verify(public_key)
        self.assertTrue(verifed)

        # check serialization
        encoded = encoding.msgpack_encode(lsig)
        decoded = encoding.msgpack_decode(encoded)
        self.assertEqual(decoded, lsig)
        verifed = lsig.verify(public_key)
        self.assertTrue(verifed)

        # check signature verification on modified program
        program = b"\x01\x20\x01\x03\x22"
        lsig = transaction.LogicSig(program)
        self.assertEqual(lsig.logic, program)
        verifed = lsig.verify(public_key)
        self.assertFalse(verifed)
        self.assertNotEqual(lsig.address(), program_hash)

        # check invalid program fails
        program = b"\x00\x20\x01\x03\x22"
        lsig = transaction.LogicSig(program)
        verifed = lsig.verify(public_key)
        self.assertFalse(verifed)

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

        verifed = lsig.verify(public_key)
        self.assertTrue(verifed)

        # check serialization
        encoded = encoding.msgpack_encode(lsig)
        decoded = encoding.msgpack_decode(encoded)
        self.assertEqual(decoded, lsig)
        verifed = lsig.verify(public_key)
        self.assertTrue(verifed)

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
        verifed = lsig.verify(public_key)
        self.assertFalse(verifed)       # not enough signatures

        with self.assertRaises(error.InvalidSecretKeyError):
            lsig.append_to_multisig(private_key)

        lsig.append_to_multisig(private_key_2)
        verifed = lsig.verify(public_key)
        self.assertTrue(verifed)

        # combine sig and multisig, ensure it fails
        lsigf = transaction.LogicSig(program)
        lsigf.sign(private_key)
        lsig.sig = lsigf.sig
        verifed = lsig.verify(public_key)
        self.assertFalse(verifed)

        # remove, ensure it still works
        lsig.sig = None
        verifed = lsig.verify(public_key)
        self.assertTrue(verifed)

        # check serialization
        encoded = encoding.msgpack_encode(lsig)
        decoded = encoding.msgpack_decode(encoded)
        self.assertEqual(decoded, lsig)
        verifed = lsig.verify(public_key)
        self.assertTrue(verifed)

    def test_transaction(self):
        fromAddress = ("47YPQTIGQEO7T4Y4RWDYWEKV6RTR2" +
                       "UNBQXBABEEGM72ESWDQNCQ52OPASU")
        toAddress = ("PNWOET7LLOWMBMLE4KOCELCX6X3D3" +
                     "Q4H2Q4QJASYIEOF7YIPPQBG3YQ5YI")
        mn = ("advice pudding treat near rule blouse same whisper inner " +
              "electric quit surface sunny dismiss leader blood seat " +
              "clown cost exist hospital century reform able sponsor")
        fee = 1000
        amount = 2000
        firstRound = 2063137
        genesisID = "devnet-v1.0"

        genesisHash = "sC3P7e2SdbqKJK0tbiCdK9tdSpbe6XeCGKdoNzmlj0E="
        note = base64.b64decode("8xMCTuLQ810=")

        tx = transaction.PaymentTxn(
            fromAddress, fee, firstRound, firstRound + 1000,
            genesisHash, toAddress, amount,
            note=note, gen=genesisID, flat_fee=True
        )

        golden = (
            "gqRsc2lng6NhcmeSxAMxMjPEAzQ1NqFsxAUBIAEBIqNzaWfEQE6HXaI5K0lcq5" +
            "0o/y3bWOYsyw9TLi/oorZB4xaNdn1Z14351u2f6JTON478fl+JhIP4HNRRAIh/" +
            "I8EWXBPpJQ2jdHhuiqNhbXTNB9CjZmVlzQPoomZ2zgAfeyGjZ2Vuq2Rldm5ldC" +
            "12MS4womdoxCCwLc/t7ZJ1uookrS1uIJ0r211Klt7pd4IYp2g3OaWPQaJsds4A" +
            "H38JpG5vdGXECPMTAk7i0PNdo3JjdsQge2ziT+tbrMCxZOKcIixX9fY9w4fUOQ" +
            "SCWEEcX+EPfAKjc25kxCDn8PhNBoEd+fMcjYeLEVX0Zx1RoYXCAJCGZ/RJWHBo" +
            "oaR0eXBlo3BheQ=="
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
        verifed = lstx.verify()
        self.assertTrue(verifed)

        golden_decoded = encoding.msgpack_decode(golden)
        self.assertEqual(lstx, golden_decoded)


class TestTemplate(unittest.TestCase):
    def test_split(self):
        addr1 = "WO3QIJ6T4DZHBX5PWJH26JLHFSRT7W7M2DJOULPXDTUS6TUX7ZRIO4KDFY"
        addr2 = "W6UUUSEAOGLBHT7VFT4H2SDATKKSG6ZBUIJXTZMSLW36YS44FRP5NVAU7U"
        addr3 = "XCIBIN7RT4ZXGBMVAMU3QS6L5EKB7XGROC5EPCNHHYXUIBAA5Q6C5Y7NEU"
        s = template.Split(addr1, addr2, addr3, 30, 100, 123456,
                           10000, 5000000)
        golden = ("ASAIAcCWsQICAMDEBx5kkE4mAyCztwQn0+DycN+vsk+vJWcsoz/b7NDS" +
                  "6i33HOkvTpf+YiC3qUpIgHGWE8/1LPh9SGCalSN7IaITeeWSXbfsS5ws" +
                  "XyC4kBQ38Z8zcwWVAym4S8vpFB/c0XC6R4mnPi9EBADsPDEQIhIxASMM" +
                  "EDIEJBJAABkxCSgSMQcyAxIQMQglEhAxAiEEDRAiQAAuMwAAMwEAEjEJ" +
                  "MgMSEDMABykSEDMBByoSEDMACCEFCzMBCCEGCxIQMwAIIQcPEBA=")
        golden_addr = ("KPYGWKTV7CKMPMTLQRNGMEQRSYTYD" +
                       "HUOFNV4UDSBDLC44CLIJPQWRTCPBU")
        self.assertEqual(s.get_program(), base64.b64decode(golden))
        self.assertEqual(s.get_address(), golden_addr)

    def test_HTLC(self):
        addr1 = "726KBOYUJJNE5J5UHCSGQGWIBZWKCBN4WYD7YVSTEXEVNFPWUIJ7TAEOPM"
        addr2 = "42NJMHTPFVPXVSDGA6JGKUV6TARV5UZTMPFIREMLXHETRKIVW34QFSDFRE"
        s = template.HTLC(addr1, addr2, "sha256",
                          "f4OxZX/x/FO5LcGBSKHWXfwtSx+j1ncoSt3SABJtkGk=",
                          600000, 1000)
        golden_addr = ("KNBD7ATNUVQ4NTLOI72EEUWBVMBNK" +
                       "MPHWVBCETERV2W7T2YO6CVMLJRBM4")

        golden = ("ASAE6AcBAMDPJCYDIOaalh5vLV96yGYHkmVSvpgjXtMzY8qIkYu5yTip" +
                  "Fbb5IH+DsWV/8fxTuS3BgUih1l38LUsfo9Z3KErd0gASbZBpIP68oLsU" +
                  "SlpOp7Q4pGgayA5soQW8tgf8VlMlyVaV9qITMQEiDjEQIxIQMQcyAxIQ" +
                  "MQgkEhAxCSgSLQEpEhAxCSoSMQIlDRAREA==")
        p = s.get_program()
        self.assertEqual(p, base64.b64decode(golden))
        self.assertEqual(s.get_address(), golden_addr)


if __name__ == "__main__":
    to_run = [
        TestTransaction,
        TestMnemonic,
        TestAddress,
        TestMultisig,
        TestMsgpack,
        TestSignBytes,
        TestLogic,
        TestLogicSig,
        TestTemplate
    ]
    loader = unittest.TestLoader()
    suites = [loader.loadTestsFromTestCase(test_class)
              for test_class in to_run]
    suite = unittest.TestSuite(suites)
    runner = unittest.TextTestRunner(verbosity=2)
    results = runner.run(suite)
