import base64
import json
from pathlib import Path

from nacl.signing import SigningKey

from algosdk import transaction, mnemonic, account
from algosdk.atomic_transaction_composer import (
    AccountTransactionSigner,
    sign_transaction_with_signer,
)
from algosdk.signer import Ed25519AlgorandSigner

from utils import get_algod_client, get_accounts


def compile_lsig(lsig_src_path: Path) -> str:
    algod_client = get_algod_client()
    # example: LSIG_COMPILE
    # read teal program
    data = open(lsig_src_path, "r").read()
    # compile teal program
    response = algod_client.compile(data)
    print("Response Result = ", response["result"])
    print("Response Hash = ", response["hash"])
    # example: LSIG_COMPILE
    return response["result"]


def get_lsig() -> transaction.LogicSigAccount:
    compiled_program = compile_lsig(Path("lsig") / "simple.teal")
    # example: LSIG_INIT
    program = base64.b64decode(compiled_program)
    lsig = transaction.LogicSigAccount(program)
    # example: LSIG_INIT
    return lsig


def lsig_args():
    compiled_program = compile_lsig()
    # example: LSIG_PASS_ARGS
    # string parameter
    arg_str = "my string"
    arg1 = arg_str.encode()
    lsig = transaction.LogicSigAccount(compiled_program, args=[arg1])
    # OR integer parameter
    arg1 = (123).to_bytes(8, "big")
    lsig = transaction.LogicSigAccount(compiled_program, args=[arg1])
    # example: LSIG_PASS_ARGS


def contract_account_example():
    algod_client = get_algod_client()

    # Seed the lsig account address so the
    # payment later works
    accts = get_accounts()
    seed_acct = accts.pop()
    lsig_args_path = Path("lsig") / "sample_arg.teal"
    compiled_program = compile_lsig(lsig_args_path)
    lsig = transaction.LogicSigAccount(base64.b64decode(compiled_program))
    ptxn = transaction.PaymentTxn(
        seed_acct.address,
        algod_client.suggested_params(),
        lsig.address(),
        10000000,
    )
    stxn = sign_transaction_with_signer(
        ptxn, AccountTransactionSigner(seed_acct.private_key)
    )
    txid = algod_client.send_transaction(stxn)
    transaction.wait_for_confirmation(algod_client, txid, 4)

    receiver = seed_acct.address

    # example: LSIG_SIGN_FULL
    # Create an algod client
    lsig_args_path = Path("lsig") / "sample_arg.teal"
    compiled_program = compile_lsig(lsig_args_path)
    program_binary = base64.b64decode(compiled_program)
    arg1 = (123).to_bytes(8, "big")
    lsig = transaction.LogicSigAccount(program_binary, args=[arg1])
    sender = lsig.address()
    # Get suggested parameters
    params = algod_client.suggested_params()
    # Build transaction
    amount = 10000
    # Create a transaction
    txn = transaction.PaymentTxn(sender, params, receiver, amount)
    # Create the LogicSigTransaction with contract account LogicSigAccount
    lstx = transaction.LogicSigTransaction(txn, lsig)

    # Send raw LogicSigTransaction to network
    txid = algod_client.send_transaction(lstx)
    print("Transaction ID: " + txid)
    # wait for confirmation
    confirmed_txn = transaction.wait_for_confirmation(algod_client, txid, 4)
    print(
        "Result confirmed in round: {}".format(
            confirmed_txn["confirmed-round"]
        )
    )
    # example: LSIG_SIGN_FULL


def delegate_lsig_example():
    algod_client = get_algod_client()
    accts = get_accounts()

    signer_acct = accts[0]
    receiver_acct = accts[1]

    # example: LSIG_DELEGATE_FULL
    lsig_args_path = Path("lsig") / "sample_arg.teal"
    compiled_program = compile_lsig(lsig_args_path)
    program_binary = base64.b64decode(compiled_program)
    arg1 = (123).to_bytes(8, "big")
    lsig = transaction.LogicSigAccount(program_binary, args=[arg1])

    def ed25519_signer_from_private_key(
        private_key: str,
    ) -> Ed25519AlgorandSigner:
        """Build a callback signer from a locally held private key.

        For production key management, construct Ed25519AlgorandSigner
        directly with a callback that calls your HSM or KMS instead.
        """
        raw = base64.b64decode(private_key)
        seed, public_key = raw[:32], raw[32:]

        def sign(data: bytes) -> bytes:
            return SigningKey(seed).sign(data).signature

        return Ed25519AlgorandSigner(public_key, sign)

    # Delegate the logic signature to the account using a callback signer
    lsig.sign_with_signer(
        ed25519_signer_from_private_key(signer_acct.private_key)
    )

    # Get suggested parameters
    params = algod_client.suggested_params()
    amount = 10000
    # Create a transaction where sender is the account that
    # is the delegating account
    txn = transaction.PaymentTxn(
        signer_acct.address, params, receiver_acct.address, amount
    )

    # Create the LogicSigTransaction with contract account LogicSigAccount
    lstx = transaction.LogicSigTransaction(txn, lsig)

    # Send raw LogicSigTransaction to network
    txid = algod_client.send_transaction(lstx)
    print("Transaction ID: " + txid)

    confirmed_txn = transaction.wait_for_confirmation(algod_client, txid, 4)
    print(
        "Result confirmed in round: {}".format(
            confirmed_txn["confirmed-round"]
        )
    )
    # example: LSIG_DELEGATE_FULL


if __name__ == "__main__":
    contract_account_example()
    delegate_lsig_example()
