from datetime import datetime

from algosdk import (
    account,
    auction,
    encoding,
    kmd,
    wallet,
)
from algosdk.future import transaction
from behave import given, then, when

token = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
algod_port = 60000
kmd_port = 60001


@when("I create a wallet")
def create_wallet(context):
    context.wallet_name = "Walletpy"
    context.wallet_pswd = ""
    context.wallet_id = context.kcl.create_wallet(
        context.wallet_name, context.wallet_pswd
    )["id"]


@then("the wallet should exist")
def wallet_exist(context):
    wallets = context.kcl.list_wallets()
    wallet_names = [w["name"] for w in wallets]
    assert context.wallet_name in wallet_names


@when("I get the wallet handle")
def get_handle(context):
    context.handle = context.kcl.init_wallet_handle(
        context.wallet_id, context.wallet_pswd
    )


@then("I can get the master derivation key")
def get_mdk(context):
    mdk = context.kcl.export_master_derivation_key(
        context.handle, context.wallet_pswd
    )
    assert mdk


@when("I rename the wallet")
def rename_wallet(context):
    context.wallet_name = "Walletpy_new"
    context.kcl.rename_wallet(
        context.wallet_id, context.wallet_pswd, context.wallet_name
    )


@then("I can still get the wallet information with the same handle")
def get_wallet_info(context):
    info = context.kcl.get_wallet(context.handle)
    assert info


@when("I renew the wallet handle")
def renew_handle(context):
    if not hasattr(context, "handle"):
        context.handle = context.kcl.init_wallet_handle(
            context.wallet_id, context.wallet_pswd
        )
    context.kcl.renew_wallet_handle(context.handle)


@when("I release the wallet handle")
def release_handle(context):
    context.kcl.release_wallet_handle(context.handle)


@then("the wallet handle should not work")
def try_handle(context):
    try:
        context.renew_wallet_handle(context.handle)
        context.error = False
    except:
        context.error = True
    assert context.error


@given('multisig addresses "{addresses}"')
def msig_addresses(context, addresses):
    addresses = addresses.split(" ")
    context.msig = transaction.Multisig(1, 2, addresses)


@then("v1 should be in the versions")
def v1_in_versions(context):
    assert "v1" in context.versions


@when("I get versions with kmd")
def kcl_v(context):
    context.versions = context.kcl.versions()


@when("I import the multisig")
def import_msig(context):
    context.wallet.import_multisig(context.msig)


@then("the multisig should be in the wallet")
def msig_in_wallet(context):
    msigs = context.wallet.list_multisig()
    assert context.msig.address() in msigs


@when("I export the multisig")
def exp_msig(context):
    context.exp = context.wallet.export_multisig(context.msig.address())


@then("the multisig should equal the exported multisig")
def msig_eq(context):
    assert encoding.msgpack_encode(context.msig) == encoding.msgpack_encode(
        context.exp
    )


@when("I delete the multisig")
def delete_msig(context):
    context.wallet.delete_multisig(context.msig.address())


@then("the multisig should not be in the wallet")
def msig_not_in_wallet(context):
    msigs = context.wallet.list_multisig()
    assert context.msig.address() not in msigs


@when("I generate a key using kmd")
def gen_key_kmd(context):
    context.pk = context.wallet.generate_key()


@then("the key should be in the wallet")
def key_in_wallet(context):
    keys = context.wallet.list_keys()
    assert context.pk in keys


@when("I delete the key")
def delete_key(context):
    context.wallet.delete_key(context.pk)


@then("the key should not be in the wallet")
def key_not_in_wallet(context):
    keys = context.wallet.list_keys()
    assert context.pk not in keys


@when("I generate a key")
def gen_key(context):
    context.sk, context.pk = account.generate_account()
    context.old = context.pk


@when("I import the key")
def import_key(context):
    context.wallet.import_key(context.sk)


@then("the private key should be equal to the exported private key")
def sk_eq_export(context):
    exp = context.wallet.export_key(context.pk)
    assert context.sk == exp
    context.wallet.delete_key(context.pk)


@given("a kmd client")
def kmd_client(context):
    kmd_address = "http://localhost:" + str(kmd_port)
    context.kcl = kmd.KMDClient(token, kmd_address)


@given("wallet information")
def wallet_info(context):
    context.wallet_name = "unencrypted-default-wallet"
    context.wallet_pswd = ""
    context.wallet = wallet.Wallet(
        context.wallet_name, context.wallet_pswd, context.kcl
    )
    context.wallet_id = context.wallet.id
    context.accounts = context.wallet.list_keys()


@when("I create a bid")
def create_bid(context):
    context.sk, pk = account.generate_account()
    context.bid = auction.Bid(pk, 1, 2, 3, pk, 4)


@when("I encode and decode the bid")
def enc_dec_bid(context):
    context.bid = encoding.msgpack_decode(encoding.msgpack_encode(context.bid))


@then("the bid should still be the same")
def check_bid(context):
    assert context.sbid == context.old


@when("I sign the bid")
def sign_bid(context):
    context.sbid = context.bid.sign(context.sk)
    context.old = context.bid.sign(context.sk)
