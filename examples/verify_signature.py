from algosdk.account import generate_account
from algosdk import encoding, transaction
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
from typing import List
import base64


def verify_signed_transaction(raw_stxn: List[bytes]):
    # example: OFFLINE_VERIFY_SIG
    # decode the signed transaction
    stxn = encoding.msgpack_decode(raw_stxn)
    if stxn.signature is None or len(stxn.signature) == 0:
        return False

    public_key = stxn.transaction.sender
    if stxn.authorizing_address is not None:
        public_key = stxn.authorizing_address

    # Create a VerifyKey from nacl using the 32 byte public key
    verify_key = VerifyKey(encoding.decode_address(public_key))

    # Generate the message that was signed with TX prefix
    prefixed_message = b"TX" + base64.b64decode(
        encoding.msgpack_encode(stxn.transaction)
    )

    try:
        # Verify the signature
        verify_key.verify(prefixed_message, base64.b64decode(stxn.signature))
        return True
    except BadSignatureError:
        return False
    # example: OFFLINE_VERIFY_SIG


def main():
    sk, addr = generate_account()
    sp = transaction.SuggestedParams(
        0, 1, 2, "nDtgfcrOMvfAaxYZSL+gCqA2ot5uBknFJuWE4pVFloo="
    )
    txn = transaction.PaymentTxn(addr, sp, addr, 0)
    stxn = txn.sign(sk)
    stxn_blob = encoding.msgpack_encode(stxn)
    print("Valid? ", verify_signed_transaction(stxn_blob))


if __name__ == "__main__":
    main()
