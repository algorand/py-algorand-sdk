import base64
from pathlib import Path
from typing import Union

from algosdk import encoding
from algosdk.future import transaction

import parse
from behave import register_type


########### TYPE REGISTRY ############


@parse.with_pattern(r".*")
def parse_string(text):
    return text


register_type(MaybeString=parse_string)


@parse.with_pattern(r"true|false")
def parse_bool(value):
    if value not in ("true", "false"):
        raise ValueError("Unknown value for include_all: {}".format(value))
    return value == "true"


register_type(MaybeBool=parse_bool)

########### GENERIC HELPERS ############


def load_resource(res, is_binary=True):
    """load data from features/resources"""
    path = Path(__file__).parent.parent / "features" / "resources" / res
    filemode = "rb" if is_binary else "r"
    with open(path, filemode) as fin:
        data = fin.read()
    return data


def read_program_binary(path):
    return bytearray(load_resource(path))


def read_program(context, path):
    """
    Assumes that have already added `context.app_acl` so need to have previously
    called one of the steps "Given an algod v2 client..."
    """
    if path.endswith(".teal"):
        assert hasattr(
            context, "app_acl"
        ), "Cannot compile teal program into binary because no algod v2 client has been provided in the context"

        teal = load_resource(path, is_binary=False)
        resp = context.app_acl.compile(teal)
        return base64.b64decode(resp["result"])

    return read_program_binary(path)


def operation_string_to_enum(operation):
    if operation == "call":
        return transaction.OnComplete.NoOpOC
    elif operation == "create":
        return transaction.OnComplete.NoOpOC
    elif operation == "noop":
        return transaction.OnComplete.NoOpOC
    elif operation == "update":
        return transaction.OnComplete.UpdateApplicationOC
    elif operation == "optin":
        return transaction.OnComplete.OptInOC
    elif operation == "delete":
        return transaction.OnComplete.DeleteApplicationOC
    elif operation == "clear":
        return transaction.OnComplete.ClearStateOC
    elif operation == "closeout":
        return transaction.OnComplete.CloseOutOC
    else:
        raise NotImplementedError(
            "no oncomplete enum for operation " + operation
        )


def split_and_process_app_args(in_args):
    split_args = in_args.split(",")
    sub_args = [sub_arg.split(":") for sub_arg in split_args]
    app_args = []
    for sub_arg in sub_args:
        if len(sub_arg) == 1:  # assume int
            app_args.append(int(sub_arg[0]))
        elif sub_arg[0] == "str":
            app_args.append(bytes(sub_arg[1], "ascii"))
        elif sub_arg[0] == "b64":
            app_args.append(base64.decodebytes(sub_arg[1].encode()))
        elif sub_arg[0] == "int":
            app_args.append(int(sub_arg[1]))
        elif sub_arg[0] == "addr":
            app_args.append(encoding.decode_address(sub_arg[1]))
    return app_args


########### STEP HELPERS ############


def fund_account_address(
    context, account_address: str, amount: Union[int, str]
):
    sp = context.app_acl.suggested_params()
    payment = transaction.PaymentTxn(
        context.accounts[0],
        sp,
        account_address,
        int(amount),
    )
    signed_payment = context.wallet.sign_transaction(payment)
    context.app_acl.send_transaction(signed_payment)
    transaction.wait_for_confirmation(context.app_acl, payment.get_txid(), 10)
