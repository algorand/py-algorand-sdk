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


    def test_serialize_assetconfig(self):
        address = "BH55E5RMBD4GYWXGX5W5PJ5JAHPGM5OXKDQH5DC4O2MGI7NW4H6VOE4CP4"
        gh = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
        txn = transaction.AssetConfigTxn(address, 10, 322575, 323575, gh,
                                         address, 1234, manager=address,
                                         reserve=address, freeze=address,
                                         clawback=address)
        golden = ("iKRhcGFyhKFjxCAJ+9J2LAj4bFrmv23Xp6kB3mZ111Dgfoxcdphkfbbh" +
                  "/aFmxCAJ+9J2LAj4bFrmv23Xp6kB3mZ111Dgfoxcdphkfbbh/aFtxCAJ" +
                  "+9J2LAj4bFrmv23Xp6kB3mZ111Dgfoxcdphkfbbh/aFyxCAJ+9J2LAj4" +
                  "bFrmv23Xp6kB3mZ111Dgfoxcdphkfbbh/aRjYWlkgqFjxCAJ+9J2LAj4" +
                  "bFrmv23Xp6kB3mZ111Dgfoxcdphkfbbh/aFpzQTSo2ZlZc0OzqJmds4A" +
                  "BOwPomdoxCBIY7UYpLPITsgQ8i1PEIHLD3HwWaesIN7GL39w5Qk6IqJs" +
                  "ds4ABO/3o3NuZMQgCfvSdiwI+Gxa5r9t16epAd5mdddQ4H6MXHaYZH22" +
                  "4f2kdHlwZaRhY2Zn")
        self.assertEqual(encoding.msgpack_encode(txn), golden)

    def test_serialize_assetfreeze(self):
        address = "BH55E5RMBD4GYWXGX5W5PJ5JAHPGM5OXKDQH5DC4O2MGI7NW4H6VOE4CP4"
        gh = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
        txn = transaction.AssetFreezeTxn(address, 10, 322575, 323575, gh,
                                                 address, 1234, address, True)
        golden = ("iaRmYWRkxCAJ+9J2LAj4bFrmv23Xp6kB3mZ111Dgfoxcdphkfbbh/aRmYW" +
                  "lkgqFjxCAJ+9J2LAj4bFrmv23Xp6kB3mZ111Dgfoxcdphkfbbh/aFpzQTS" +
                  "pGFmcnrDo2ZlZc0KtKJmds4ABOwPomdoxCBIY7UYpLPITsgQ8i1PEIHLD3" +
                  "HwWaesIN7GL39w5Qk6IqJsds4ABO/3o3NuZMQgCfvSdiwI+Gxa5r9t16ep" +
                  "Ad5mdddQ4H6MXHaYZH224f2kdHlwZaRhZnJ6")
        self.assertEqual(encoding.msgpack_encode(txn), golden)

    def test_deserialize_assetfreeze(self):
        address = "BH55E5RMBD4GYWXGX5W5PJ5JAHPGM5OXKDQH5DC4O2MGI7NW4H6VOE4CP4"
        gh = "SGO1GKSzyE7IEPItTxCByw9x8FmnrCDexi9/cOUJOiI="
        txn = transaction.AssetFreezeTxn(address, 10, 322575, 323575, gh,
                                                 address, 1234, address, True)
        golden = ("iaRmYWRkxCAJ+9J2LAj4bFrmv23Xp6kB3mZ111Dgfoxcdphkfbbh/aRmYW" +
                  "lkgqFjxCAJ+9J2LAj4bFrmv23Xp6kB3mZ111Dgfoxcdphkfbbh/aFpzQTS" +
                  "pGFmcnrDo2ZlZc0KtKJmds4ABOwPomdoxCBIY7UYpLPITsgQ8i1PEIHLD3" +
                  "HwWaesIN7GL39w5Qk6IqJsds4ABO/3o3NuZMQgCfvSdiwI+Gxa5r9t16ep" +
                  "Ad5mdddQ4H6MXHaYZH224f2kdHlwZaRhZnJ6")
        self.assertEqual(txn, encoding.msgpack_decode(golden))

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

        # goal clerk send dumps unsigned transaction as signed with empty signature in order to save tx type
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
            "QIdBlHI6BdrIijcmN2xCCj8AKs8kPYlx63ppj1w5410qkMRGZ9FYofNYPXxGpNL"
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

        # goal clerk group sets Group to every transaction and concatenate them in output file
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

        # goal clerk group sets Group to every transaction and concatenate them in output file
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

    def test_assetconfig_txn(self):
        actxn = ("iKRhcGFyhKFjxCAJ+9J2LAj4bFrmv23Xp6kB3mZ111Dgfoxcdphkfbbh" +
                 "/aFmxCAJ+9J2LAj4bFrmv23Xp6kB3mZ111Dgfoxcdphkfbbh/aFtxCAJ" +
                 "+9J2LAj4bFrmv23Xp6kB3mZ111Dgfoxcdphkfbbh/aFyxCAJ+9J2LAj4" +
                 "bFrmv23Xp6kB3mZ111Dgfoxcdphkfbbh/aRjYWlkgqFjxCAJ+9J2LAj4" +
                 "bFrmv23Xp6kB3mZ111Dgfoxcdphkfbbh/aFpzQTSo2ZlZc0OzqJmds4A" +
                 "BOwPomdoxCBIY7UYpLPITsgQ8i1PEIHLD3HwWaesIN7GL39w5Qk6IqJs" +
                 "ds4ABO/3o3NuZMQgCfvSdiwI+Gxa5r9t16epAd5mdddQ4H6MXHaYZH22" +
                 "4f2kdHlwZaRhY2Zn")
        self.assertEqual(actxn, encoding.msgpack_encode(
                         encoding.msgpack_decode(actxn)))


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


if __name__ == "__main__":
    to_run = [TestTransaction,
              TestMnemonic,
              TestAddress,
              TestMultisig,
              TestMsgpack,
              TestSignBytes]
    loader = unittest.TestLoader()
    suites = [loader.loadTestsFromTestCase(test_class)
              for test_class in to_run]
    suite = unittest.TestSuite(suites)
    runner = unittest.TextTestRunner(verbosity=2)
    results = runner.run(suite)
