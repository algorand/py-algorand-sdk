import base64
import unittest

from algosdk import account, encoding, error, mnemonic
from algosdk.future import transaction


class TestLogicSig(unittest.TestCase):
    def test_basic(self):
        with self.assertRaises(error.InvalidProgram):
            lsig = transaction.LogicSig(None)

        with self.assertRaises(error.InvalidProgram):
            lsig = transaction.LogicSig(b"")

        program = b"\x01\x20\x01\x01\x22"  # int 1
        program_hash = (
            "6Z3C3LDVWGMX23BMSYMANACQOSINPFIRF77H7N3AWJZYV6OH6GWTJKVMXY"
        )
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
        self.assertFalse(verified)  # not enough signatures

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
            "47YPQTIGQEO7T4Y4RWDYWEKV6RTR2UNBQXBABEEGM72ESWDQNCQ52OPASU"
        )
        toAddress = (
            "PNWOET7LLOWMBMLE4KOCELCX6X3D3Q4H2Q4QJASYIEOF7YIPPQBG3YQ5YI"
        )
        mn = (
            "advice pudding treat near rule blouse same whisper inner electric"
            " quit surface sunny dismiss leader blood seat clown cost exist ho"
            "spital century reform able sponsor"
        )
        fee = 1000
        amount = 2000
        firstRound = 2063137
        genesisID = "devnet-v1.0"

        genesisHash = "sC3P7e2SdbqKJK0tbiCdK9tdSpbe6XeCGKdoNzmlj0E="
        note = base64.b64decode("8xMCTuLQ810=")

        sp = transaction.SuggestedParams(
            fee,
            firstRound,
            firstRound + 1000,
            genesisHash,
            genesisID,
            flat_fee=True,
        )
        tx = transaction.PaymentTxn(
            fromAddress, sp, toAddress, amount, note=note
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
        args = [b"123", b"456"]
        sk = mnemonic.to_private_key(mn)
        lsig = transaction.LogicSig(program, args)
        lsig.sign(sk)
        lstx = transaction.LogicSigTransaction(tx, lsig)
        verified = lstx.verify()
        self.assertTrue(verified)

        golden_decoded = encoding.msgpack_decode(golden)
        self.assertEqual(lstx, golden_decoded)


sampleMnemonic1 = "auction inquiry lava second expand liberty glass involve ginger illness length room item discover ahead table doctor term tackle cement bonus profit right above catch"
sampleMnemonic2 = "since during average anxiety protect cherry club long lawsuit loan expand embark forum theory winter park twenty ball kangaroo cram burst board host ability left"
sampleMnemonic3 = "advice pudding treat near rule blouse same whisper inner electric quit surface sunny dismiss leader blood seat clown cost exist hospital century reform able sponsor"

sampleAccount1 = mnemonic.to_private_key(sampleMnemonic1)
sampleAccount2 = mnemonic.to_private_key(sampleMnemonic2)
sampleAccount3 = mnemonic.to_private_key(sampleMnemonic3)

sampleMsig = transaction.Multisig(
    1,
    2,
    [
        "DN7MBMCL5JQ3PFUQS7TMX5AH4EEKOBJVDUF4TCV6WERATKFLQF4MQUPZTA",
        "BFRTECKTOOE7A5LHCF3TTEOH2A7BW46IYT2SX5VP6ANKEXHZYJY77SJTVM",
        "47YPQTIGQEO7T4Y4RWDYWEKV6RTR2UNBQXBABEEGM72ESWDQNCQ52OPASU",
    ],
)


class TestLogicSigAccount(unittest.TestCase):
    def test_create_no_args(self):
        program = b"\x01\x20\x01\x01\x22"  # int 1

        lsigAccount = transaction.LogicSigAccount(program)

        self.assertEqual(lsigAccount.lsig.logic, program)
        self.assertEqual(lsigAccount.lsig.args, None)
        self.assertEqual(lsigAccount.lsig.sig, None)
        self.assertEqual(lsigAccount.lsig.msig, None)
        self.assertEqual(lsigAccount.sigkey, None)

        # check serialization
        encoded = encoding.msgpack_encode(lsigAccount)
        expectedEncoded = "gaRsc2lngaFsxAUBIAEBIg=="
        self.assertEqual(encoded, expectedEncoded)

        decoded = encoding.future_msgpack_decode(encoded)
        self.assertEqual(decoded, lsigAccount)

    def test_create_with_args(self):
        program = b"\x01\x20\x01\x01\x22"  # int 1
        args = [b"\x01", b"\x02\x03"]

        lsigAccount = transaction.LogicSigAccount(program, args)

        self.assertEqual(lsigAccount.lsig.logic, program)
        self.assertEqual(lsigAccount.lsig.args, args)
        self.assertEqual(lsigAccount.lsig.sig, None)
        self.assertEqual(lsigAccount.lsig.msig, None)
        self.assertEqual(lsigAccount.sigkey, None)

        # check serialization
        encoded = encoding.msgpack_encode(lsigAccount)
        expectedEncoded = "gaRsc2lngqNhcmeSxAEBxAICA6FsxAUBIAEBIg=="
        self.assertEqual(encoded, expectedEncoded)

        decoded = encoding.future_msgpack_decode(encoded)
        self.assertEqual(decoded, lsigAccount)

    def test_sign(self):
        program = b"\x01\x20\x01\x01\x22"  # int 1
        args = [b"\x01", b"\x02\x03"]

        lsigAccount = transaction.LogicSigAccount(program, args)
        lsigAccount.sign(sampleAccount1)

        expectedSig = "SRO4BdGefywQgPYzfhhUp87q7hDdvRNlhL+Tt18wYxWRyiMM7e8j0XQbUp2w/+83VNZG9LVh/Iu8LXtOY1y9Ag=="
        expectedSigKey = encoding.decode_address(
            account.address_from_private_key(sampleAccount1)
        )

        self.assertEqual(lsigAccount.lsig.logic, program)
        self.assertEqual(lsigAccount.lsig.args, args)
        self.assertEqual(lsigAccount.lsig.sig, expectedSig)
        self.assertEqual(lsigAccount.lsig.msig, None)
        self.assertEqual(lsigAccount.sigkey, expectedSigKey)

        # check serialization
        encoded = encoding.msgpack_encode(lsigAccount)
        expectedEncoded = "gqRsc2lng6NhcmeSxAEBxAICA6FsxAUBIAEBIqNzaWfEQEkTuAXRnn8sEID2M34YVKfO6u4Q3b0TZYS/k7dfMGMVkcojDO3vI9F0G1KdsP/vN1TWRvS1YfyLvC17TmNcvQKmc2lna2V5xCAbfsCwS+pht5aQl+bL9AfhCKcFNR0LyYq+sSIJqKuBeA=="
        self.assertEqual(encoded, expectedEncoded)

        decoded = encoding.future_msgpack_decode(encoded)
        self.assertEqual(decoded, lsigAccount)

    def test_sign_multisig(self):
        program = b"\x01\x20\x01\x01\x22"  # int 1
        args = [b"\x01", b"\x02\x03"]

        lsigAccount = transaction.LogicSigAccount(program, args)
        lsigAccount.sign_multisig(sampleMsig, sampleAccount1)

        expectedSig = base64.b64decode(
            "SRO4BdGefywQgPYzfhhUp87q7hDdvRNlhL+Tt18wYxWRyiMM7e8j0XQbUp2w/+83VNZG9LVh/Iu8LXtOY1y9Ag=="
        )
        expectedMsig = encoding.future_msgpack_decode(
            encoding.msgpack_encode(sampleMsig)
        )
        expectedMsig.subsigs[0].signature = expectedSig

        self.assertEqual(lsigAccount.lsig.logic, program)
        self.assertEqual(lsigAccount.lsig.args, args)
        self.assertEqual(lsigAccount.lsig.sig, None)
        self.assertEqual(lsigAccount.lsig.msig, expectedMsig)
        self.assertEqual(lsigAccount.sigkey, None)

        # check serialization
        encoded = encoding.msgpack_encode(lsigAccount)
        expectedEncoded = "gaRsc2lng6NhcmeSxAEBxAICA6FsxAUBIAEBIqRtc2lng6ZzdWJzaWeTgqJwa8QgG37AsEvqYbeWkJfmy/QH4QinBTUdC8mKvrEiCairgXihc8RASRO4BdGefywQgPYzfhhUp87q7hDdvRNlhL+Tt18wYxWRyiMM7e8j0XQbUp2w/+83VNZG9LVh/Iu8LXtOY1y9AoGicGvEIAljMglTc4nwdWcRdzmRx9A+G3PIxPUr9q/wGqJc+cJxgaJwa8Qg5/D4TQaBHfnzHI2HixFV9GcdUaGFwgCQhmf0SVhwaKGjdGhyAqF2AQ=="
        self.assertEqual(encoded, expectedEncoded)

        decoded = encoding.future_msgpack_decode(encoded)
        self.assertEqual(decoded, lsigAccount)

    def test_append_to_multisig(self):
        program = b"\x01\x20\x01\x01\x22"  # int 1
        args = [b"\x01", b"\x02\x03"]

        msig1of3Encoded = "gaRsc2lng6NhcmeSxAEBxAICA6FsxAUBIAEBIqRtc2lng6ZzdWJzaWeTgqJwa8QgG37AsEvqYbeWkJfmy/QH4QinBTUdC8mKvrEiCairgXihc8RASRO4BdGefywQgPYzfhhUp87q7hDdvRNlhL+Tt18wYxWRyiMM7e8j0XQbUp2w/+83VNZG9LVh/Iu8LXtOY1y9AoGicGvEIAljMglTc4nwdWcRdzmRx9A+G3PIxPUr9q/wGqJc+cJxgaJwa8Qg5/D4TQaBHfnzHI2HixFV9GcdUaGFwgCQhmf0SVhwaKGjdGhyAqF2AQ=="
        lsigAccount = encoding.future_msgpack_decode(msig1of3Encoded)

        lsigAccount.append_to_multisig(sampleAccount2)

        expectedSig1 = base64.b64decode(
            "SRO4BdGefywQgPYzfhhUp87q7hDdvRNlhL+Tt18wYxWRyiMM7e8j0XQbUp2w/+83VNZG9LVh/Iu8LXtOY1y9Ag=="
        )
        expectedSig2 = base64.b64decode(
            "ZLxV2+2RokHUKrZg9+FKuZmaUrOxcVjO/D9P58siQRStqT1ehAUCChemaYMDIk6Go4tqNsVUviBQ/9PuqLMECQ=="
        )
        expectedMsig = encoding.future_msgpack_decode(
            encoding.msgpack_encode(sampleMsig)
        )
        expectedMsig.subsigs[0].signature = expectedSig1
        expectedMsig.subsigs[1].signature = expectedSig2

        self.assertEqual(lsigAccount.lsig.logic, program)
        self.assertEqual(lsigAccount.lsig.args, args)
        self.assertEqual(lsigAccount.lsig.sig, None)
        self.assertEqual(lsigAccount.lsig.msig, expectedMsig)
        self.assertEqual(lsigAccount.sigkey, None)

        # check serialization
        encoded = encoding.msgpack_encode(lsigAccount)
        expectedEncoded = "gaRsc2lng6NhcmeSxAEBxAICA6FsxAUBIAEBIqRtc2lng6ZzdWJzaWeTgqJwa8QgG37AsEvqYbeWkJfmy/QH4QinBTUdC8mKvrEiCairgXihc8RASRO4BdGefywQgPYzfhhUp87q7hDdvRNlhL+Tt18wYxWRyiMM7e8j0XQbUp2w/+83VNZG9LVh/Iu8LXtOY1y9AoKicGvEIAljMglTc4nwdWcRdzmRx9A+G3PIxPUr9q/wGqJc+cJxoXPEQGS8VdvtkaJB1Cq2YPfhSrmZmlKzsXFYzvw/T+fLIkEUrak9XoQFAgoXpmmDAyJOhqOLajbFVL4gUP/T7qizBAmBonBrxCDn8PhNBoEd+fMcjYeLEVX0Zx1RoYXCAJCGZ/RJWHBooaN0aHICoXYB"
        self.assertEqual(encoded, expectedEncoded)

        decoded = encoding.future_msgpack_decode(encoded)
        self.assertEqual(decoded, lsigAccount)

    def test_verify(self):
        escrowEncoded = "gaRsc2lngqNhcmeSxAEBxAICA6FsxAUBIAEBIg=="
        escrowLsigAccount = encoding.future_msgpack_decode(escrowEncoded)
        self.assertEqual(escrowLsigAccount.verify(), True)

        sigEncoded = "gqRsc2lng6NhcmeSxAEBxAICA6FsxAUBIAEBIqNzaWfEQEkTuAXRnn8sEID2M34YVKfO6u4Q3b0TZYS/k7dfMGMVkcojDO3vI9F0G1KdsP/vN1TWRvS1YfyLvC17TmNcvQKmc2lna2V5xCAbfsCwS+pht5aQl+bL9AfhCKcFNR0LyYq+sSIJqKuBeA=="
        sigLsigAccount = encoding.future_msgpack_decode(sigEncoded)
        self.assertEqual(sigLsigAccount.verify(), True)

        sigLsigAccount.lsig.sig = "AQ=="  # wrong length of bytes
        self.assertEqual(sigLsigAccount.verify(), False)

        sigLsigAccount.lsig.sig = 123  # wrong type (not bytes)
        self.assertEqual(sigLsigAccount.verify(), False)

        msigEncoded = "gaRsc2lng6NhcmeSxAEBxAICA6FsxAUBIAEBIqRtc2lng6ZzdWJzaWeTgqJwa8QgG37AsEvqYbeWkJfmy/QH4QinBTUdC8mKvrEiCairgXihc8RASRO4BdGefywQgPYzfhhUp87q7hDdvRNlhL+Tt18wYxWRyiMM7e8j0XQbUp2w/+83VNZG9LVh/Iu8LXtOY1y9AoKicGvEIAljMglTc4nwdWcRdzmRx9A+G3PIxPUr9q/wGqJc+cJxoXPEQGS8VdvtkaJB1Cq2YPfhSrmZmlKzsXFYzvw/T+fLIkEUrak9XoQFAgoXpmmDAyJOhqOLajbFVL4gUP/T7qizBAmBonBrxCDn8PhNBoEd+fMcjYeLEVX0Zx1RoYXCAJCGZ/RJWHBooaN0aHICoXYB"
        msigLsigAccount = encoding.future_msgpack_decode(msigEncoded)
        self.assertEqual(msigLsigAccount.verify(), True)

        msigLsigAccount.lsig.msig.subsigs[0].signature = None
        self.assertEqual(msigLsigAccount.verify(), False)

    def test_is_delegated(self):
        escrowEncoded = "gaRsc2lngqNhcmeSxAEBxAICA6FsxAUBIAEBIg=="
        escrowLsigAccount = encoding.future_msgpack_decode(escrowEncoded)
        self.assertEqual(escrowLsigAccount.is_delegated(), False)

        sigEncoded = "gqRsc2lng6NhcmeSxAEBxAICA6FsxAUBIAEBIqNzaWfEQEkTuAXRnn8sEID2M34YVKfO6u4Q3b0TZYS/k7dfMGMVkcojDO3vI9F0G1KdsP/vN1TWRvS1YfyLvC17TmNcvQKmc2lna2V5xCAbfsCwS+pht5aQl+bL9AfhCKcFNR0LyYq+sSIJqKuBeA=="
        sigLsigAccount = encoding.future_msgpack_decode(sigEncoded)
        self.assertEqual(sigLsigAccount.is_delegated(), True)

        msigEncoded = "gaRsc2lng6NhcmeSxAEBxAICA6FsxAUBIAEBIqRtc2lng6ZzdWJzaWeTgqJwa8QgG37AsEvqYbeWkJfmy/QH4QinBTUdC8mKvrEiCairgXihc8RASRO4BdGefywQgPYzfhhUp87q7hDdvRNlhL+Tt18wYxWRyiMM7e8j0XQbUp2w/+83VNZG9LVh/Iu8LXtOY1y9AoKicGvEIAljMglTc4nwdWcRdzmRx9A+G3PIxPUr9q/wGqJc+cJxoXPEQGS8VdvtkaJB1Cq2YPfhSrmZmlKzsXFYzvw/T+fLIkEUrak9XoQFAgoXpmmDAyJOhqOLajbFVL4gUP/T7qizBAmBonBrxCDn8PhNBoEd+fMcjYeLEVX0Zx1RoYXCAJCGZ/RJWHBooaN0aHICoXYB"
        msigLsigAccount = encoding.future_msgpack_decode(msigEncoded)
        self.assertEqual(msigLsigAccount.is_delegated(), True)

    def test_address(self):
        escrowEncoded = "gaRsc2lngqNhcmeSxAEBxAICA6FsxAUBIAEBIg=="
        escrowLsigAccount = encoding.future_msgpack_decode(escrowEncoded)
        escrowExpectedAddr = (
            "6Z3C3LDVWGMX23BMSYMANACQOSINPFIRF77H7N3AWJZYV6OH6GWTJKVMXY"
        )
        self.assertEqual(escrowLsigAccount.address(), escrowExpectedAddr)

        sigEncoded = "gqRsc2lng6NhcmeSxAEBxAICA6FsxAUBIAEBIqNzaWfEQEkTuAXRnn8sEID2M34YVKfO6u4Q3b0TZYS/k7dfMGMVkcojDO3vI9F0G1KdsP/vN1TWRvS1YfyLvC17TmNcvQKmc2lna2V5xCAbfsCwS+pht5aQl+bL9AfhCKcFNR0LyYq+sSIJqKuBeA=="
        sigLsigAccount = encoding.future_msgpack_decode(sigEncoded)
        sigExpectedAddr = (
            "DN7MBMCL5JQ3PFUQS7TMX5AH4EEKOBJVDUF4TCV6WERATKFLQF4MQUPZTA"
        )
        self.assertEqual(sigLsigAccount.address(), sigExpectedAddr)

        msigEncoded = "gaRsc2lng6NhcmeSxAEBxAICA6FsxAUBIAEBIqRtc2lng6ZzdWJzaWeTgqJwa8QgG37AsEvqYbeWkJfmy/QH4QinBTUdC8mKvrEiCairgXihc8RASRO4BdGefywQgPYzfhhUp87q7hDdvRNlhL+Tt18wYxWRyiMM7e8j0XQbUp2w/+83VNZG9LVh/Iu8LXtOY1y9AoKicGvEIAljMglTc4nwdWcRdzmRx9A+G3PIxPUr9q/wGqJc+cJxoXPEQGS8VdvtkaJB1Cq2YPfhSrmZmlKzsXFYzvw/T+fLIkEUrak9XoQFAgoXpmmDAyJOhqOLajbFVL4gUP/T7qizBAmBonBrxCDn8PhNBoEd+fMcjYeLEVX0Zx1RoYXCAJCGZ/RJWHBooaN0aHICoXYB"
        msigLsigAccount = encoding.future_msgpack_decode(msigEncoded)
        msigExpectedAddr = (
            "RWJLJCMQAFZ2ATP2INM2GZTKNL6OULCCUBO5TQPXH3V2KR4AG7U5UA5JNM"
        )
        self.assertEqual(msigLsigAccount.address(), msigExpectedAddr)


class TestLogicSigTransaction(unittest.TestCase):
    program = b"\x01\x20\x01\x01\x22"  # int 1
    args = [b"\x01", b"\x02\x03"]

    otherAddr = "WTDCE2FEYM2VB5MKNXKLRSRDTSPR2EFTIGVH4GRW4PHGD6747GFJTBGT2A"

    def _test_sign_txn(
        self, lsigObject, sender, expectedEncoded, expectedValid=True
    ):
        sp = transaction.SuggestedParams(
            fee=217000,
            flat_fee=True,
            first=972508,
            last=973508,
            gh="JgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dI=",
            gen="testnet-v31.0",
        )
        txn = transaction.PaymentTxn(
            sender,
            sp,
            TestLogicSigTransaction.otherAddr,
            5000,
            note=b"\xb4\x51\x79\x39\xfc\xfa\xd2\x71",
        )

        actual = transaction.LogicSigTransaction(txn, lsigObject)
        self.assertEqual(actual.verify(), expectedValid)

        if not expectedValid:
            return

        actualEncoded = encoding.msgpack_encode(actual)
        self.assertEqual(actualEncoded, expectedEncoded)

        decoded = encoding.future_msgpack_decode(actualEncoded)
        self.assertEqual(decoded, actual)

    def test_LogicSig_escrow(self):
        lsig = transaction.LogicSig(
            TestLogicSigTransaction.program, TestLogicSigTransaction.args
        )

        sender = lsig.address()
        expected = "gqRsc2lngqNhcmeSxAEBxAICA6FsxAUBIAEBIqN0eG6Ko2FtdM0TiKNmZWXOAANPqKJmds4ADtbco2dlbq10ZXN0bmV0LXYzMS4womdoxCAmCyAJoJOohot5WHIvpeVG7eftF+TYXEx4r7BFJpDt0qJsds4ADtrEpG5vdGXECLRReTn8+tJxo3JjdsQgtMYiaKTDNVD1im3UuMojnJ8dELNBqn4aNuPOYfv8+Yqjc25kxCD2di2sdbGZfWwslhgGgFB0kNeVES/+f7dgsnOK+cfxraR0eXBlo3BheQ=="
        self._test_sign_txn(lsig, sender, expected)

    def test_LogicSig_escrow_different_sender(self):
        lsig = transaction.LogicSig(
            TestLogicSigTransaction.program, TestLogicSigTransaction.args
        )

        sender = TestLogicSigTransaction.otherAddr
        expected = "g6Rsc2lngqNhcmeSxAEBxAICA6FsxAUBIAEBIqRzZ25yxCD2di2sdbGZfWwslhgGgFB0kNeVES/+f7dgsnOK+cfxraN0eG6Ko2FtdM0TiKNmZWXOAANPqKJmds4ADtbco2dlbq10ZXN0bmV0LXYzMS4womdoxCAmCyAJoJOohot5WHIvpeVG7eftF+TYXEx4r7BFJpDt0qJsds4ADtrEpG5vdGXECLRReTn8+tJxo3JjdsQgtMYiaKTDNVD1im3UuMojnJ8dELNBqn4aNuPOYfv8+Yqjc25kxCC0xiJopMM1UPWKbdS4yiOcnx0Qs0Gqfho2485h+/z5iqR0eXBlo3BheQ=="
        self._test_sign_txn(lsig, sender, expected)

    def test_LogicSig_single_delegated(self):
        sk = mnemonic.to_private_key(
            "olympic cricket tower model share zone grid twist sponsor avoid eight apology patient party success claim famous rapid donor pledge bomb mystery security ability often"
        )

        lsig = transaction.LogicSig(
            TestLogicSigTransaction.program, TestLogicSigTransaction.args
        )
        lsig.sign(sk)

        sender = account.address_from_private_key(sk)
        expected = "gqRsc2lng6NhcmeSxAEBxAICA6FsxAUBIAEBIqNzaWfEQD4FPTlN+xK8ZXmf6jGKe46iUYtVLIq+bNenZS3YsBh+IQUtuSRiiRblYXTNDxmsuWxFpCmRmREd5Hzk/BLszgKjdHhuiqNhbXTNE4ijZmVlzgADT6iiZnbOAA7W3KNnZW6tdGVzdG5ldC12MzEuMKJnaMQgJgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dKibHbOAA7axKRub3RlxAi0UXk5/PrScaNyY3bEILTGImikwzVQ9Ypt1LjKI5yfHRCzQap+GjbjzmH7/PmKo3NuZMQgXmdPHAru7DdxiY9hx2/10koZeT4skfoIUWJj44Vz6kKkdHlwZaNwYXk="
        self._test_sign_txn(lsig, sender, expected)

    def test_LogicSig_single_delegated_different_sender(self):
        sk = mnemonic.to_private_key(
            "olympic cricket tower model share zone grid twist sponsor avoid eight apology patient party success claim famous rapid donor pledge bomb mystery security ability often"
        )

        lsig = transaction.LogicSig(
            TestLogicSigTransaction.program, TestLogicSigTransaction.args
        )
        lsig.sign(sk)

        sender = TestLogicSigTransaction.otherAddr
        self._test_sign_txn(lsig, sender, None, False)

    def test_LogicSig_msig_delegated(self):
        lsig = transaction.LogicSig(
            TestLogicSigTransaction.program, TestLogicSigTransaction.args
        )
        lsig.sign(sampleAccount1, sampleMsig)
        lsig.append_to_multisig(sampleAccount2)

        sender = sampleMsig.address()
        expected = "gqRsc2lng6NhcmeSxAEBxAICA6FsxAUBIAEBIqRtc2lng6ZzdWJzaWeTgqJwa8QgG37AsEvqYbeWkJfmy/QH4QinBTUdC8mKvrEiCairgXihc8RASRO4BdGefywQgPYzfhhUp87q7hDdvRNlhL+Tt18wYxWRyiMM7e8j0XQbUp2w/+83VNZG9LVh/Iu8LXtOY1y9AoKicGvEIAljMglTc4nwdWcRdzmRx9A+G3PIxPUr9q/wGqJc+cJxoXPEQGS8VdvtkaJB1Cq2YPfhSrmZmlKzsXFYzvw/T+fLIkEUrak9XoQFAgoXpmmDAyJOhqOLajbFVL4gUP/T7qizBAmBonBrxCDn8PhNBoEd+fMcjYeLEVX0Zx1RoYXCAJCGZ/RJWHBooaN0aHICoXYBo3R4boqjYW10zROIo2ZlZc4AA0+oomZ2zgAO1tyjZ2VurXRlc3RuZXQtdjMxLjCiZ2jEICYLIAmgk6iGi3lYci+l5Ubt5+0X5NhcTHivsEUmkO3Somx2zgAO2sSkbm90ZcQItFF5Ofz60nGjcmN2xCC0xiJopMM1UPWKbdS4yiOcnx0Qs0Gqfho2485h+/z5iqNzbmTEII2StImQAXOgTfpDWaNmamr86ixCoF3Zwfc+66VHgDfppHR5cGWjcGF5"
        self._test_sign_txn(lsig, sender, expected)

    def test_LogicSig_msig_delegated_different_sender(self):
        lsig = transaction.LogicSig(
            TestLogicSigTransaction.program, TestLogicSigTransaction.args
        )
        lsig.sign(sampleAccount1, sampleMsig)
        lsig.append_to_multisig(sampleAccount2)

        sender = TestLogicSigTransaction.otherAddr
        expected = "g6Rsc2lng6NhcmeSxAEBxAICA6FsxAUBIAEBIqRtc2lng6ZzdWJzaWeTgqJwa8QgG37AsEvqYbeWkJfmy/QH4QinBTUdC8mKvrEiCairgXihc8RASRO4BdGefywQgPYzfhhUp87q7hDdvRNlhL+Tt18wYxWRyiMM7e8j0XQbUp2w/+83VNZG9LVh/Iu8LXtOY1y9AoKicGvEIAljMglTc4nwdWcRdzmRx9A+G3PIxPUr9q/wGqJc+cJxoXPEQGS8VdvtkaJB1Cq2YPfhSrmZmlKzsXFYzvw/T+fLIkEUrak9XoQFAgoXpmmDAyJOhqOLajbFVL4gUP/T7qizBAmBonBrxCDn8PhNBoEd+fMcjYeLEVX0Zx1RoYXCAJCGZ/RJWHBooaN0aHICoXYBpHNnbnLEII2StImQAXOgTfpDWaNmamr86ixCoF3Zwfc+66VHgDfpo3R4boqjYW10zROIo2ZlZc4AA0+oomZ2zgAO1tyjZ2VurXRlc3RuZXQtdjMxLjCiZ2jEICYLIAmgk6iGi3lYci+l5Ubt5+0X5NhcTHivsEUmkO3Somx2zgAO2sSkbm90ZcQItFF5Ofz60nGjcmN2xCC0xiJopMM1UPWKbdS4yiOcnx0Qs0Gqfho2485h+/z5iqNzbmTEILTGImikwzVQ9Ypt1LjKI5yfHRCzQap+GjbjzmH7/PmKpHR5cGWjcGF5"
        self._test_sign_txn(lsig, sender, expected)

    def test_LogicSigAccount_escrow(self):
        lsigAccount = transaction.LogicSigAccount(
            TestLogicSigTransaction.program, TestLogicSigTransaction.args
        )

        sender = lsigAccount.address()
        expected = "gqRsc2lngqNhcmeSxAEBxAICA6FsxAUBIAEBIqN0eG6Ko2FtdM0TiKNmZWXOAANPqKJmds4ADtbco2dlbq10ZXN0bmV0LXYzMS4womdoxCAmCyAJoJOohot5WHIvpeVG7eftF+TYXEx4r7BFJpDt0qJsds4ADtrEpG5vdGXECLRReTn8+tJxo3JjdsQgtMYiaKTDNVD1im3UuMojnJ8dELNBqn4aNuPOYfv8+Yqjc25kxCD2di2sdbGZfWwslhgGgFB0kNeVES/+f7dgsnOK+cfxraR0eXBlo3BheQ=="
        self._test_sign_txn(lsigAccount, sender, expected)

    def test_LogicSigAccount_escrow_different_sender(self):
        lsigAccount = transaction.LogicSigAccount(
            TestLogicSigTransaction.program, TestLogicSigTransaction.args
        )

        sender = TestLogicSigTransaction.otherAddr
        expected = "g6Rsc2lngqNhcmeSxAEBxAICA6FsxAUBIAEBIqRzZ25yxCD2di2sdbGZfWwslhgGgFB0kNeVES/+f7dgsnOK+cfxraN0eG6Ko2FtdM0TiKNmZWXOAANPqKJmds4ADtbco2dlbq10ZXN0bmV0LXYzMS4womdoxCAmCyAJoJOohot5WHIvpeVG7eftF+TYXEx4r7BFJpDt0qJsds4ADtrEpG5vdGXECLRReTn8+tJxo3JjdsQgtMYiaKTDNVD1im3UuMojnJ8dELNBqn4aNuPOYfv8+Yqjc25kxCC0xiJopMM1UPWKbdS4yiOcnx0Qs0Gqfho2485h+/z5iqR0eXBlo3BheQ=="
        self._test_sign_txn(lsigAccount, sender, expected)

    def test_LogicSigAccount_single_delegated(self):
        sk = mnemonic.to_private_key(
            "olympic cricket tower model share zone grid twist sponsor avoid eight apology patient party success claim famous rapid donor pledge bomb mystery security ability often"
        )

        lsigAccount = transaction.LogicSigAccount(
            TestLogicSigTransaction.program, TestLogicSigTransaction.args
        )
        lsigAccount.sign(sk)

        sender = account.address_from_private_key(sk)
        expected = "gqRsc2lng6NhcmeSxAEBxAICA6FsxAUBIAEBIqNzaWfEQD4FPTlN+xK8ZXmf6jGKe46iUYtVLIq+bNenZS3YsBh+IQUtuSRiiRblYXTNDxmsuWxFpCmRmREd5Hzk/BLszgKjdHhuiqNhbXTNE4ijZmVlzgADT6iiZnbOAA7W3KNnZW6tdGVzdG5ldC12MzEuMKJnaMQgJgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dKibHbOAA7axKRub3RlxAi0UXk5/PrScaNyY3bEILTGImikwzVQ9Ypt1LjKI5yfHRCzQap+GjbjzmH7/PmKo3NuZMQgXmdPHAru7DdxiY9hx2/10koZeT4skfoIUWJj44Vz6kKkdHlwZaNwYXk="
        self._test_sign_txn(lsigAccount, sender, expected)

    def test_LogicSigAccount_single_delegated_different_sender(self):
        sk = mnemonic.to_private_key(
            "olympic cricket tower model share zone grid twist sponsor avoid eight apology patient party success claim famous rapid donor pledge bomb mystery security ability often"
        )

        lsigAccount = transaction.LogicSigAccount(
            TestLogicSigTransaction.program, TestLogicSigTransaction.args
        )
        lsigAccount.sign(sk)

        sender = TestLogicSigTransaction.otherAddr
        expected = "g6Rsc2lng6NhcmeSxAEBxAICA6FsxAUBIAEBIqNzaWfEQD4FPTlN+xK8ZXmf6jGKe46iUYtVLIq+bNenZS3YsBh+IQUtuSRiiRblYXTNDxmsuWxFpCmRmREd5Hzk/BLszgKkc2ducsQgXmdPHAru7DdxiY9hx2/10koZeT4skfoIUWJj44Vz6kKjdHhuiqNhbXTNE4ijZmVlzgADT6iiZnbOAA7W3KNnZW6tdGVzdG5ldC12MzEuMKJnaMQgJgsgCaCTqIaLeVhyL6XlRu3n7Rfk2FxMeK+wRSaQ7dKibHbOAA7axKRub3RlxAi0UXk5/PrScaNyY3bEILTGImikwzVQ9Ypt1LjKI5yfHRCzQap+GjbjzmH7/PmKo3NuZMQgtMYiaKTDNVD1im3UuMojnJ8dELNBqn4aNuPOYfv8+YqkdHlwZaNwYXk="
        self._test_sign_txn(lsigAccount, sender, expected)

    def test_LogicSigAccount_msig_delegated(self):
        lsigAccount = transaction.LogicSigAccount(
            TestLogicSigTransaction.program, TestLogicSigTransaction.args
        )
        lsigAccount.sign_multisig(sampleMsig, sampleAccount1)
        lsigAccount.append_to_multisig(sampleAccount2)

        sender = sampleMsig.address()
        expected = "gqRsc2lng6NhcmeSxAEBxAICA6FsxAUBIAEBIqRtc2lng6ZzdWJzaWeTgqJwa8QgG37AsEvqYbeWkJfmy/QH4QinBTUdC8mKvrEiCairgXihc8RASRO4BdGefywQgPYzfhhUp87q7hDdvRNlhL+Tt18wYxWRyiMM7e8j0XQbUp2w/+83VNZG9LVh/Iu8LXtOY1y9AoKicGvEIAljMglTc4nwdWcRdzmRx9A+G3PIxPUr9q/wGqJc+cJxoXPEQGS8VdvtkaJB1Cq2YPfhSrmZmlKzsXFYzvw/T+fLIkEUrak9XoQFAgoXpmmDAyJOhqOLajbFVL4gUP/T7qizBAmBonBrxCDn8PhNBoEd+fMcjYeLEVX0Zx1RoYXCAJCGZ/RJWHBooaN0aHICoXYBo3R4boqjYW10zROIo2ZlZc4AA0+oomZ2zgAO1tyjZ2VurXRlc3RuZXQtdjMxLjCiZ2jEICYLIAmgk6iGi3lYci+l5Ubt5+0X5NhcTHivsEUmkO3Somx2zgAO2sSkbm90ZcQItFF5Ofz60nGjcmN2xCC0xiJopMM1UPWKbdS4yiOcnx0Qs0Gqfho2485h+/z5iqNzbmTEII2StImQAXOgTfpDWaNmamr86ixCoF3Zwfc+66VHgDfppHR5cGWjcGF5"
        self._test_sign_txn(lsigAccount, sender, expected)

    def test_LogicSigAccount_msig_delegated_different_sender(self):
        lsigAccount = transaction.LogicSigAccount(
            TestLogicSigTransaction.program, TestLogicSigTransaction.args
        )
        lsigAccount.sign_multisig(sampleMsig, sampleAccount1)
        lsigAccount.append_to_multisig(sampleAccount2)

        sender = TestLogicSigTransaction.otherAddr
        expected = "g6Rsc2lng6NhcmeSxAEBxAICA6FsxAUBIAEBIqRtc2lng6ZzdWJzaWeTgqJwa8QgG37AsEvqYbeWkJfmy/QH4QinBTUdC8mKvrEiCairgXihc8RASRO4BdGefywQgPYzfhhUp87q7hDdvRNlhL+Tt18wYxWRyiMM7e8j0XQbUp2w/+83VNZG9LVh/Iu8LXtOY1y9AoKicGvEIAljMglTc4nwdWcRdzmRx9A+G3PIxPUr9q/wGqJc+cJxoXPEQGS8VdvtkaJB1Cq2YPfhSrmZmlKzsXFYzvw/T+fLIkEUrak9XoQFAgoXpmmDAyJOhqOLajbFVL4gUP/T7qizBAmBonBrxCDn8PhNBoEd+fMcjYeLEVX0Zx1RoYXCAJCGZ/RJWHBooaN0aHICoXYBpHNnbnLEII2StImQAXOgTfpDWaNmamr86ixCoF3Zwfc+66VHgDfpo3R4boqjYW10zROIo2ZlZc4AA0+oomZ2zgAO1tyjZ2VurXRlc3RuZXQtdjMxLjCiZ2jEICYLIAmgk6iGi3lYci+l5Ubt5+0X5NhcTHivsEUmkO3Somx2zgAO2sSkbm90ZcQItFF5Ofz60nGjcmN2xCC0xiJopMM1UPWKbdS4yiOcnx0Qs0Gqfho2485h+/z5iqNzbmTEILTGImikwzVQ9Ypt1LjKI5yfHRCzQap+GjbjzmH7/PmKpHR5cGWjcGF5"
        self._test_sign_txn(lsigAccount, sender, expected)
