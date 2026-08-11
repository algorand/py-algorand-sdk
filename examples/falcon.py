# Post-quantum signing with Falcon-1024.
import base64

from algosdk import account, constants, encoding, mnemonic, transaction
from algosdk.atomic_transaction_composer import (
    AccountTransactionSigner,
    AtomicTransactionComposer,
    LogicSigTransactionSigner,
    TransactionWithSigner,
    sign_transaction_with_signer,
)
from algosdk.signer import Falcon1024TransactionSigner
from algosdk.v2client import algod

from utils import get_algod_client, get_accounts

# The SDK is signature scheme agnostic and never bundles a post-quantum
# implementation, so the Falcon-1024 keypair comes from a separate package:
# `pip install temp-falcon` (0.4.0 or newer). It is not a dependency of the
# SDK, so this example skips itself wherever the package is missing
try:
    from temp_falcon import falcon1024
except ImportError:
    falcon1024 = None

# These words are public, so only ever use them on a private network
PQ_MNEMONIC = " ".join(["abandon"] * 24 + ["invest"])


def fund_account(
    algod_client: algod.AlgodClient, receiver: str, amount: int
) -> None:
    dispenser = get_accounts()[0]
    sp = algod_client.suggested_params()
    txn = transaction.PaymentTxn(dispenser.address, sp, receiver, amount)
    signed_txn = sign_transaction_with_signer(txn, dispenser.signer)
    txid = algod_client.send_transaction(signed_txn)
    transaction.wait_for_confirmation(algod_client, txid, 4)


def get_falcon_signer() -> Falcon1024TransactionSigner:
    # example: PQ_FALCON_KEYGEN
    # A 25 word post-quantum mnemonic seeds a Falcon-1024 keypair, the same
    # way a 25 word mnemonic seeds an ed25519 one. Key generation is
    # deterministic, so these words always produce this keypair. Signer
    # comes from the temp-falcon package, `pip install temp-falcon`
    seed = mnemonic.to_pq_seed(PQ_MNEMONIC, constants.falcon_1024_scheme)
    falcon = falcon1024.Signer.generate(seed)
    # example: PQ_FALCON_KEYGEN

    # example: PQ_FALCON_SIGNER
    # The SDK never sees the private key. It takes the public key plus a
    # callback that signs exact bytes, so the key can stay in a wallet, an
    # HSM or a remote service. The object below is at once the post-quantum
    # address, a TransactionSigner an atomic transaction composer accepts,
    # and the signer that delegates a logic signature
    falcon_signer = Falcon1024TransactionSigner(falcon.public_key, falcon.sign)

    # A Falcon-1024 public key is 1793 bytes, so the address commits to a
    # hash of the key plus a salt. Otherwise it behaves like any other
    # address: it can be funded, sent from, and rekeyed to
    print(f"Falcon-1024 address: {falcon_signer.address}")
    # example: PQ_FALCON_SIGNER
    return falcon_signer


def falcon_example() -> None:
    if falcon1024 is None:
        print("temp-falcon is not installed, skipping falcon example")
        return

    algod_client = get_algod_client()

    # Only a node running the future consensus version understands the
    # post-quantum signature field, so skip instead of sending transactions
    # it is bound to reject. A node that cannot be reached raises here
    sp = algod_client.suggested_params()
    if sp.consensus_version != "future":
        print(
            f"node runs consensus version {sp.consensus_version}, which has"
            " no post-quantum support, skipping falcon example"
        )
        return

    falcon_signer = get_falcon_signer()

    # Verification only needs the public key, which is what a third party
    # checking these signatures would hold
    verifier = falcon1024.Verifier(falcon_signer.public_key)

    # Cover the minimum balance plus the fees paid below
    fund_account(algod_client, falcon_signer.address, 120_000)
    info = algod_client.account_info(falcon_signer.address)
    print(f"Falcon account balance: {info['amount']} microAlgos")

    # example: PQ_FALCON_PAYMENT
    sp = algod_client.suggested_params()
    # A Falcon-1024 public key and signature add about 3 kB to a transaction,
    # while the fee estimator sizes a transaction as if it carried an ed25519
    # signature. Set a flat fee so the fee does not rest on that estimate
    sp.flat_fee = True
    sp.fee = 3000

    # Send a 0 amount payment from the Falcon address to itself
    txn = transaction.PaymentTxn(
        falcon_signer.address, sp, falcon_signer.address, 0
    )

    # Falcon1024TransactionSigner is a TransactionSigner, so the composer
    # takes it wherever an account signer would go
    atc = AtomicTransactionComposer()
    atc.add_transaction(TransactionWithSigner(txn, falcon_signer))
    # example: PQ_FALCON_PAYMENT

    # example: PQ_FALCON_VERIFY_SIGNATURE
    # Signing yields a PQSignedTransaction holding a detached Falcon
    # signature over the transaction signing preimage, so anyone with the
    # public key can check it offline before the transaction is submitted
    signed_txn = atc.gather_signatures()[0]
    signature = signed_txn.pqsig.signature
    assert verifier.is_valid(
        txn.bytes_to_sign(), signature
    ), "the falcon signature does not match the transaction"

    # Falcon signatures are compressed, so their length varies
    print(f"Verified a {len(signature)} byte falcon signature")
    # example: PQ_FALCON_VERIFY_SIGNATURE

    result = atc.execute(algod_client, 4)
    print(f"Result confirmed in round: {result.confirmed_round}")

    # example: PQ_FALCON_DELEGATE_LSIG
    # A delegated program can spend from the Falcon account, so keep it
    # narrow. This one approves only transactions with a 0 amount field,
    # which by itself does not stop algos from moving: a real delegation
    # should also pin the transaction type, the receiver, the fee, and the
    # close and rekey fields
    teal = "#pragma version 12\ntxn Amount\nint 0\n=="
    program = base64.b64decode(algod_client.compile(teal)["result"])
    lsig = transaction.LogicSigAccount(program)

    # Delegating signs "PQProgram" + the post-quantum address + the program,
    # using the same raw signer that signs transactions
    lsig.sign_with_signer(falcon_signer)
    print(f"Logic signature delegated by: {lsig.address()}")

    # Consensus verifies that signature at submission. Rebuilding the
    # preimage here shows what it covers, and is a real check on the
    # signature bytes, which LogicSigAccount.verify does not perform for a
    # post-quantum signature
    program_preimage = (
        constants.pq_program_prefix
        + encoding.decode_address(falcon_signer.address)
        + program
    )
    assert verifier.is_valid(
        program_preimage, lsig.lsig.pqsig.signature
    ), "the delegated logic signature does not match the program"
    # example: PQ_FALCON_DELEGATE_LSIG

    # example: PQ_FALCON_LSIG_PAYMENT
    sp = algod_client.suggested_params()
    sp.flat_fee = True
    sp.fee = 3000

    # The delegating account is the sender: the program authorizes the spend,
    # so no transaction signature is needed. The note only keeps this payment
    # distinct from the identical one sent earlier
    lsig_txn = transaction.PaymentTxn(
        falcon_signer.address,
        sp,
        falcon_signer.address,
        0,
        note=b"delegated lsig payment",
    )

    # LogicSigTransactionSigner turns the delegated logic signature into a
    # TransactionSigner, which is how a logic signature joins a group
    lsig_atc = AtomicTransactionComposer()
    lsig_atc.add_transaction(
        TransactionWithSigner(lsig_txn, LogicSigTransactionSigner(lsig))
    )

    lsig_result = lsig_atc.execute(algod_client, 4)
    print(f"Result confirmed in round: {lsig_result.confirmed_round}")
    # example: PQ_FALCON_LSIG_PAYMENT

    # example: PQ_FALCON_REKEY
    # The same 25 word mnemonic also yields an ordinary ed25519 account
    private_key = mnemonic.to_private_key(PQ_MNEMONIC)
    ed25519_address = account.address_from_private_key(private_key)
    ed25519_signer = AccountTransactionSigner(private_key)
    fund_account(algod_client, ed25519_address, 120_000)

    # Rekeying hands authorization of that account to the Falcon address. The
    # account keeps its address, balance and assets, but from here on only
    # the Falcon key can sign for it, which is why an account that is already
    # rekeyed cannot send this transaction a second time
    if algod_client.account_info(ed25519_address).get("auth-addr") is None:
        sp = algod_client.suggested_params()
        rekey_txn = transaction.PaymentTxn(
            ed25519_address,
            sp,
            ed25519_address,
            0,
            rekey_to=falcon_signer.address,
        )
        signed_rekey = sign_transaction_with_signer(rekey_txn, ed25519_signer)
        txid = algod_client.send_transaction(signed_rekey)
        transaction.wait_for_confirmation(algod_client, txid, 4)

    auth_addr = algod_client.account_info(ed25519_address)["auth-addr"]
    assert auth_addr == falcon_signer.address, "the rekey did not take effect"
    print(f"{ed25519_address} is now authorized by {auth_addr}")
    # example: PQ_FALCON_REKEY

    # example: PQ_FALCON_REKEYED_PAYMENT
    sp = algod_client.suggested_params()
    sp.flat_fee = True
    sp.fee = 3000

    # The sender is the rekeyed ed25519 account while the Falcon key signs.
    # The signer records itself as the authorizing address of the signed
    # transaction, so the node knows which key to check
    rekeyed_txn = transaction.PaymentTxn(
        ed25519_address,
        sp,
        falcon_signer.address,
        0,
        note=b"rekeyed payment",
    )

    rekeyed_atc = AtomicTransactionComposer()
    rekeyed_atc.add_transaction(
        TransactionWithSigner(rekeyed_txn, falcon_signer)
    )

    rekeyed_result = rekeyed_atc.execute(algod_client, 4)
    print(f"Result confirmed in round: {rekeyed_result.confirmed_round}")
    # example: PQ_FALCON_REKEYED_PAYMENT

    # example: PQ_FALCON_REKEYED_LSIG_PAYMENT
    sp = algod_client.suggested_params()
    sp.flat_fee = True
    sp.fee = 3000

    # The delegated program spends from the rekeyed account too: the logic
    # signature was delegated by the Falcon address, which now authorizes
    # this account, so the same delegation covers both. The signer records
    # the Falcon address as the authorizing address of the signed
    # transaction, just as the transaction signer did above
    rekeyed_lsig_txn = transaction.PaymentTxn(
        ed25519_address,
        sp,
        falcon_signer.address,
        0,
        note=b"rekeyed delegated lsig payment",
    )

    rekeyed_lsig_atc = AtomicTransactionComposer()
    rekeyed_lsig_atc.add_transaction(
        TransactionWithSigner(
            rekeyed_lsig_txn, LogicSigTransactionSigner(lsig)
        )
    )

    rekeyed_lsig_result = rekeyed_lsig_atc.execute(algod_client, 4)
    print(f"Result confirmed in round: {rekeyed_lsig_result.confirmed_round}")
    # example: PQ_FALCON_REKEYED_LSIG_PAYMENT


if __name__ == "__main__":
    falcon_example()
