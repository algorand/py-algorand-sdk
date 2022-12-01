import base64
import json
import re
import time

import pytest
from behave import given, step, then, when

from algosdk import abi, atomic_transaction_composer, encoding, mnemonic
from algosdk.abi.contract import NetworkInfo
from algosdk.error import ABITypeError, AtomicTransactionComposerError
from algosdk.future import transaction
from tests.steps.other_v2_steps import read_program


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


# Takes in a tuple where first element is the encoding and second element is value.
# If there is only one element, then it is assumed to be an int.
def process_app_arg(sub_arg):
    if len(sub_arg) == 1:  # assume int
        return int(sub_arg[0])
    elif sub_arg[0] == "str":
        return bytes(sub_arg[1], "ascii")
    elif sub_arg[0] == "b64":
        return base64.decodebytes(sub_arg[1].encode())
    elif sub_arg[0] == "int":
        return int(sub_arg[1])
    elif sub_arg[0] == "addr":
        return encoding.decode_address(sub_arg[1])


def split_and_process_app_args(in_args):
    if not in_args:
        return []
    split_args = in_args.split(",")
    sub_args = [sub_arg.split(":") for sub_arg in split_args]
    app_args = []
    for sub_arg in sub_args:
        app_args.append(process_app_arg(sub_arg))
    return app_args


def split_and_process_boxes(box_str: str):
    boxes = []
    app_id = 0
    split_args = box_str.split(",")
    # Box strings alternate between the app ID and the encoded app arg.
    for token in split_args:
        try:
            app_id = int(token)
        except ValueError:
            sub_arg = token.split(":")
            sub_arg = process_app_arg(sub_arg)
            boxes.append((app_id, sub_arg))
    # Sanity check that input correctly alternates between int and str.
    assert len(boxes) == len(split_args) // 2
    return boxes


def composer_status_string_to_enum(status):
    if status == "BUILDING":
        return (
            atomic_transaction_composer.AtomicTransactionComposerStatus.BUILDING
        )
    elif status == "BUILT":
        return (
            atomic_transaction_composer.AtomicTransactionComposerStatus.BUILT
        )
    elif status == "SIGNED":
        return (
            atomic_transaction_composer.AtomicTransactionComposerStatus.SIGNED
        )
    elif status == "SUBMITTED":
        return (
            atomic_transaction_composer.AtomicTransactionComposerStatus.SUBMITTED
        )
    elif status == "COMMITTED":
        return (
            atomic_transaction_composer.AtomicTransactionComposerStatus.COMMITTED
        )
    else:
        raise NotImplementedError(
            "no AtomicTransactionComposerStatus enum for " + status
        )


def s512_256_uint64(witness):
    return int.from_bytes(encoding.checksum(witness)[:8], "big")


# Dev mode helper functions
def wait_for_transaction_processing_to_complete_in_dev_mode(
    millisecond_num=500,
):
    """
    wait_for_transaction_processing_to_complete_in_dev_mode is a Dev mode helper method that waits for a transaction to be processed and serves as a rough analog to `context.app_acl.status_after_block(last_round + 2)`.
     * <p>
     * Since Dev mode produces blocks on a per transaction basis, it's possible algod generates a block _before_ the corresponding SDK call to wait for a block.
     * Without _any_ wait, it's possible the SDK looks for the transaction before algod completes processing. The analogous problem may also exist in indexer. So, the method performs a local sleep to simulate waiting for a block.
    """
    time.sleep(millisecond_num / 1000)


# Dev mode helper step
@then(
    "I sleep for {millisecond_num} milliseconds for indexer to digest things down."
)
def wait_for_indexer_in_dev_mode(context, millisecond_num):
    wait_for_transaction_processing_to_complete_in_dev_mode(
        int(millisecond_num)
    )


@step(
    'I sign and submit the transaction, saving the txid. If there is an error it is "{error_string:MaybeString}".'
)
def sign_submit_save_txid_with_error(context, error_string):
    try:
        signed_app_transaction = context.app_transaction.sign(
            context.transient_sk
        )
        context.app_txid = context.app_acl.send_transaction(
            signed_app_transaction
        )
    except Exception as e:
        if not error_string or error_string not in str(e):
            raise RuntimeError(
                "error string "
                + error_string
                + " not in actual error "
                + str(e)
            )


@when("we make a GetApplicationByID call for applicationID {app_id}")
def application_info(context, app_id):
    context.response = context.acl.application_info(int(app_id))


@when(
    'we make a GetApplicationBoxByName call for applicationID {app_id} with encoded box name "{box_name}"'
)
def application_box_by_name(context, app_id, box_name):
    boxes = split_and_process_app_args(box_name)[0]
    context.response = context.acl.application_box_by_name(app_id, boxes)


@when(
    "we make a GetApplicationBoxes call for applicationID {app_id} with max {max_results}"
)
def application_boxes(context, app_id, max_results):
    context.response = context.acl.application_boxes(
        app_id, limit=int(max_results)
    )


@when(
    'we make a LookupApplicationLogsByID call with applicationID {app_id} limit {limit} minRound {min_round} maxRound {max_round} nextToken "{next_token:MaybeString}" sender "{sender:MaybeString}" and txID "{txid:MaybeString}"'
)
def lookup_application_logs(
    context, app_id, limit, min_round, max_round, next_token, sender, txid
):
    context.response = context.icl.application_logs(
        int(app_id),
        limit=int(limit),
        min_round=int(min_round),
        max_round=int(max_round),
        next_page=next_token,
        sender_addr=sender,
        txid=txid,
    )


@when("we make a SearchForApplications call with applicationID {app_id}")
def search_application(context, app_id):
    context.response = context.icl.search_applications(int(app_id))


@when('we make a SearchForApplications call with creator "{creator}"')
def search_application2(context, creator):
    context.response = context.icl.search_applications(creator=creator)


@when(
    'we make a LookupApplicationBoxByIDandName call with applicationID {app_id} with encoded box name "{box_name}"'
)
def lookup_application_box(context, app_id, box_name):
    boxes = split_and_process_app_args(box_name)[0]
    context.response = context.icl.application_box_by_name(app_id, boxes)


@when(
    'we make a SearchForApplicationBoxes call with applicationID {app_id} with max {max_results} nextToken "{token:MaybeString}"'
)
def search_application_boxes(context, app_id, max_results, token):
    context.response = context.icl.application_boxes(
        app_id, limit=int(max_results), next_page=token
    )


@when("we make a LookupApplications call with applicationID {app_id}")
def lookup_application(context, app_id):
    context.response = context.icl.applications(int(app_id))


@when(
    'I build an application transaction with operation "{operation:MaybeString}", application-id {application_id}, sender "{sender:MaybeString}", approval-program "{approval_program:MaybeString}", clear-program "{clear_program:MaybeString}", global-bytes {global_bytes}, global-ints {global_ints}, local-bytes {local_bytes}, local-ints {local_ints}, app-args "{app_args:MaybeString}", foreign-apps "{foreign_apps:MaybeString}", foreign-assets "{foreign_assets:MaybeString}", app-accounts "{app_accounts:MaybeString}", fee {fee}, first-valid {first_valid}, last-valid {last_valid}, genesis-hash "{genesis_hash:MaybeString}", extra-pages {extra_pages}, boxes "{boxes:MaybeString}"'
)
def build_app_transaction(
    context,
    operation,
    application_id,
    sender,
    approval_program,
    clear_program,
    global_bytes,
    global_ints,
    local_bytes,
    local_ints,
    app_args,
    foreign_apps,
    foreign_assets,
    app_accounts,
    fee,
    first_valid,
    last_valid,
    genesis_hash,
    extra_pages,
    boxes,
):
    if operation == "none":
        operation = None
    else:
        operation = operation_string_to_enum(operation)
    if sender == "none":
        sender = None
    if approval_program == "none":
        approval_program = None
    elif approval_program:
        approval_program = read_program(context, approval_program)
    if clear_program == "none":
        clear_program = None
    elif clear_program:
        clear_program = read_program(context, clear_program)
    if app_args == "none":
        app_args = None
    elif app_args:
        app_args = split_and_process_app_args(app_args)
    if foreign_apps == "none":
        foreign_apps = None
    elif foreign_apps:
        foreign_apps = [int(app) for app in foreign_apps.split(",")]
    if foreign_assets == "none":
        foreign_assets = None
    elif foreign_assets:
        foreign_assets = [int(app) for app in foreign_assets.split(",")]
    if app_accounts == "none":
        app_accounts = None
    elif app_accounts:
        app_accounts = [
            account_pubkey for account_pubkey in app_accounts.split(",")
        ]
    if boxes == "none":
        boxes = None
    elif boxes:
        boxes = split_and_process_boxes(boxes)
    if genesis_hash == "none":
        genesis_hash = None
    local_schema = transaction.StateSchema(
        num_uints=int(local_ints), num_byte_slices=int(local_bytes)
    )
    global_schema = transaction.StateSchema(
        num_uints=int(global_ints), num_byte_slices=int(global_bytes)
    )
    sp = transaction.SuggestedParams(
        int(fee),
        int(first_valid),
        int(last_valid),
        genesis_hash,
        flat_fee=True,
    )
    context.transaction = transaction.ApplicationCallTxn(
        sender=sender,
        sp=sp,
        index=int(application_id),
        on_complete=operation,
        local_schema=local_schema,
        global_schema=global_schema,
        approval_program=approval_program,
        clear_program=clear_program,
        app_args=app_args,
        accounts=app_accounts,
        foreign_apps=foreign_apps,
        foreign_assets=foreign_assets,
        extra_pages=int(extra_pages),
        note=None,
        lease=None,
        rekey_to=None,
        boxes=boxes,
    )


@step(
    'I build an application transaction with the transient account, the current application, suggested params, operation "{operation}", approval-program "{approval_program:MaybeString}", clear-program "{clear_program:MaybeString}", global-bytes {global_bytes}, global-ints {global_ints}, local-bytes {local_bytes}, local-ints {local_ints}, app-args "{app_args:MaybeString}", foreign-apps "{foreign_apps:MaybeString}", foreign-assets "{foreign_assets:MaybeString}", app-accounts "{app_accounts:MaybeString}", extra-pages {extra_pages}, boxes "{boxes:MaybeString}"'
)
def build_app_txn_with_transient(
    context,
    operation,
    approval_program,
    clear_program,
    global_bytes,
    global_ints,
    local_bytes,
    local_ints,
    app_args,
    foreign_apps,
    foreign_assets,
    app_accounts,
    extra_pages,
    boxes,
):
    application_id = 0
    if operation == "none":
        operation = None
    else:
        if (
            hasattr(context, "current_application_id")
            and context.current_application_id
            and operation != "create"
        ):
            application_id = context.current_application_id
        operation = operation_string_to_enum(operation)
    if approval_program == "none":
        approval_program = None
    elif approval_program:
        approval_program = read_program(context, approval_program)
    if clear_program == "none":
        clear_program = None
    elif clear_program:
        clear_program = read_program(context, clear_program)
    local_schema = transaction.StateSchema(
        num_uints=int(local_ints), num_byte_slices=int(local_bytes)
    )
    global_schema = transaction.StateSchema(
        num_uints=int(global_ints), num_byte_slices=int(global_bytes)
    )
    if app_args == "none":
        app_args = None
    elif app_args:
        app_args = split_and_process_app_args(app_args)
    if foreign_apps == "none":
        foreign_apps = None
    elif foreign_apps:
        foreign_apps = [int(app) for app in foreign_apps.split(",")]
    if foreign_assets == "none":
        foreign_assets = None
    elif foreign_assets:
        foreign_assets = [int(asset) for asset in foreign_assets.split(",")]
    if app_accounts == "none":
        app_accounts = None
    elif app_accounts:
        app_accounts = [
            account_pubkey for account_pubkey in app_accounts.split(",")
        ]
    if boxes == "none":
        boxes = None
    elif boxes:
        boxes = split_and_process_boxes(boxes)

    sp = context.app_acl.suggested_params()

    context.app_transaction = transaction.ApplicationCallTxn(
        sender=context.transient_pk,
        sp=sp,
        index=int(application_id),
        on_complete=operation,
        local_schema=local_schema,
        global_schema=global_schema,
        approval_program=approval_program,
        clear_program=clear_program,
        app_args=app_args,
        accounts=app_accounts,
        foreign_apps=foreign_apps,
        foreign_assets=foreign_assets,
        extra_pages=int(extra_pages),
        note=None,
        lease=None,
        rekey_to=None,
        boxes=boxes,
    )


@given("I reset the array of application IDs to remember.")
def reset_appid_list(context):
    context.app_ids = []


@step("I remember the new application ID.")
def remember_app_id(context):
    if hasattr(context, "acl"):
        app_id = context.acl.pending_transaction_info(context.app_txid)[
            "txresults"
        ]["createdapp"]
    else:
        app_id = context.app_acl.pending_transaction_info(context.app_txid)[
            "application-index"
        ]

    context.current_application_id = app_id
    if not hasattr(context, "app_ids"):
        context.app_ids = []

    context.app_ids.append(app_id)


# TODO: this needs to be modified to use v2 only
@step("I wait for the transaction to be confirmed.")
def wait_for_app_txn_confirm(context):
    wait_for_transaction_processing_to_complete_in_dev_mode()
    transaction.wait_for_confirmation(context.app_acl, context.app_txid, 1)


@given("an application id {app_id}")
def set_app_id(context, app_id):
    context.current_application_id = app_id


@step(
    'The transient account should have the created app "{app_created_bool_as_string:MaybeString}" and total schema byte-slices {byte_slices} and uints {uints}, the application "{application_state:MaybeString}" state contains key "{state_key:MaybeString}" with value "{state_value:MaybeString}"'
)
def verify_app_txn(
    context,
    app_created_bool_as_string,
    byte_slices,
    uints,
    application_state,
    state_key,
    state_value,
):
    account_info = context.app_acl.account_info(context.transient_pk)
    app_total_schema = account_info["apps-total-schema"]
    assert app_total_schema["num-byte-slice"] == int(byte_slices)
    assert app_total_schema["num-uint"] == int(uints)

    app_created = app_created_bool_as_string == "true"
    created_apps = account_info["created-apps"]
    # If we don't expect the app to exist, verify that it isn't there and exit.
    if not app_created:
        for app in created_apps:
            assert app["id"] != context.current_application_id
        return

    found_app = False
    for app in created_apps:
        found_app = found_app or app["id"] == context.current_application_id
    assert found_app

    # If there is no key to check, we're done.
    if state_key is None or state_key == "":
        return

    found_value_for_key = False
    key_values = list()
    if application_state == "local":
        counter = 0
        for local_state in account_info["apps-local-state"]:
            if local_state["id"] == context.current_application_id:
                key_values = local_state["key-value"]
                counter = counter + 1
        assert counter == 1
    elif application_state == "global":
        counter = 0
        for created_app in account_info["created-apps"]:
            if created_app["id"] == context.current_application_id:
                key_values = created_app["params"]["global-state"]
                counter = counter + 1
        assert counter == 1
    else:
        raise NotImplementedError(
            'test does not understand application state "'
            + application_state
            + '"'
        )

    assert len(key_values) > 0

    for key_value in key_values:
        found_key = key_value["key"]
        if found_key == state_key:
            found_value_for_key = True
            found_value = key_value["value"]
            if found_value["type"] == 1:
                assert found_value["bytes"] == state_value
            elif found_value["type"] == 0:
                assert found_value["uint"] == int(state_value)
    assert found_value_for_key


@given("a new AtomicTransactionComposer")
def create_atomic_transaction_composer(context):
    context.atomic_transaction_composer = (
        atomic_transaction_composer.AtomicTransactionComposer()
    )


@step('I create the Method object from method signature "{method_signature}"')
def build_abi_method(context, method_signature):
    context.abi_method = abi.Method.from_signature(method_signature)


@step("I make a transaction signer for the {account_type} account.")
def create_transaction_signer(context, account_type):
    if account_type == "transient":
        private_key = context.transient_sk
    elif account_type == "signing":
        private_key = mnemonic.to_private_key(context.signing_mnemonic)
    else:
        raise NotImplementedError(
            "cannot make transaction signer for " + account_type
        )
    context.transaction_signer = (
        atomic_transaction_composer.AccountTransactionSigner(private_key)
    )


@step("I create a transaction with signer with the current transaction.")
def create_transaction_with_signer(context):
    context.transaction_with_signer = (
        atomic_transaction_composer.TransactionWithSigner(
            context.transaction, context.transaction_signer
        )
    )


@when("I add the current transaction with signer to the composer.")
def add_transaction_to_composer(context):
    context.atomic_transaction_composer.add_transaction(
        context.transaction_with_signer
    )


def process_abi_args(context, method, arg_tokens):
    method_args = []
    for arg_index, arg_token in enumerate(arg_tokens):
        if arg_index >= len(method.args):
            method_args.append(arg_token)
            continue

        arg = method.args[arg_index]
        if isinstance(arg.type, abi.ABIType):
            method_arg = arg.type.decode(base64.b64decode(arg_token))
            method_args.append(method_arg)
        elif arg.type == abi.ABIReferenceType.ACCOUNT:
            method_arg = abi.AddressType().decode(base64.b64decode(arg_token))
            method_args.append(method_arg)
        elif (
            arg.type == abi.ABIReferenceType.APPLICATION
            or arg.type == abi.ABIReferenceType.ASSET
        ):
            parts = arg_token.split(":")
            if len(parts) == 2 and parts[0] == "ctxAppIdx":
                method_arg = context.app_ids[int(parts[1])]
            else:
                method_arg = abi.UintType(64).decode(
                    base64.b64decode(arg_token)
                )
            method_args.append(method_arg)
        else:
            # Append the transaction signer as is
            method_args.append(arg_token)
    return method_args


@step("I create a new method arguments array.")
def create_abi_method_args(context):
    context.method_args = []


@step(
    "I append the current transaction with signer to the method arguments array."
)
def append_txn_to_method_args(context):
    context.method_args.append(context.transaction_with_signer)


@step(
    'I append the encoded arguments "{method_args:MaybeString}" to the method arguments array.'
)
def append_app_args_to_method_args(context, method_args):
    # Returns a list of ABI method arguments
    app_args = method_args.split(",") if method_args else []
    context.method_args += app_args


@given('I add the nonce "{nonce}"')
def add_nonce(context, nonce):
    context.nonce = nonce


def abi_method_adder(
    context,
    account_type,
    operation,
    create_when_calling=False,
    approval_program_path=None,
    clear_program_path=None,
    global_bytes=None,
    global_ints=None,
    local_bytes=None,
    local_ints=None,
    extra_pages=None,
    force_unique_transactions=False,
    exception_key="none",
):
    if account_type == "transient":
        sender = context.transient_pk
    elif account_type == "signing":
        sender = mnemonic.to_public_key(context.signing_mnemonic)
    else:
        raise NotImplementedError(
            "cannot make transaction signer for " + account_type
        )
    approval_program = clear_program = None
    global_schema = local_schema = None

    def int_if_given(given):
        return int(given) if given else 0

    local_schema = global_schema = None
    if create_when_calling:
        if approval_program_path:
            approval_program = read_program(context, approval_program_path)
        if clear_program_path:
            clear_program = read_program(context, clear_program_path)
        if local_ints or local_bytes:
            local_schema = transaction.StateSchema(
                num_uints=int_if_given(local_ints),
                num_byte_slices=int_if_given(local_bytes),
            )
        if global_ints or global_bytes:
            global_schema = transaction.StateSchema(
                num_uints=int_if_given(global_ints),
                num_byte_slices=int_if_given(global_bytes),
            )
        extra_pages = int_if_given(extra_pages)

    app_id = int(context.current_application_id)

    app_args = process_abi_args(
        context, context.abi_method, context.method_args
    )
    context.app_args = app_args
    note = None
    if force_unique_transactions:
        note = (
            b"I should be unique thanks to this nonce: "
            + context.nonce.encode()
        )

    try:
        context.atomic_transaction_composer.add_method_call(
            app_id=app_id,
            method=context.abi_method,
            sender=sender,
            sp=context.suggested_params,
            signer=context.transaction_signer,
            method_args=app_args,
            on_complete=operation_string_to_enum(operation),
            local_schema=local_schema,
            global_schema=global_schema,
            approval_program=approval_program,
            clear_program=clear_program,
            extra_pages=extra_pages,
            note=note,
        )
    except AtomicTransactionComposerError as atce:
        assert (
            exception_key != "none"
        ), f"cucumber step asserted that no exception resulted, but the following exception actually occurred: {atce}"

        arglen_exception = "argument_count_mismatch"
        known_exception_keys = [arglen_exception]
        assert (
            exception_key in known_exception_keys
        ), f"encountered exception key '{exception_key}' which is not in known set: {known_exception_keys}"

        if exception_key == arglen_exception:
            exception_msg = (
                "number of method arguments do not match the method signature"
            )
            assert exception_msg in str(
                atce
            ), f"expected argument count mismatch error such as '{exception_msg}' but got the following instead: {atce}"
        return

    assert (
        exception_key == "none"
    ), f"should have encountered an AtomicTransactionComposerError keyed by '{exception_key}', but no such exception has been detected"


@step(
    'I add a method call with the {account_type} account, the current application, suggested params, on complete "{operation}", current transaction signer, current method arguments; any resulting exception has key "{exception_key}".'
)
def add_abi_method_call_with_exception(
    context, account_type, operation, exception_key
):
    abi_method_adder(
        context,
        account_type,
        operation,
        exception_key=exception_key,
    )


@step(
    'I add a method call with the {account_type} account, the current application, suggested params, on complete "{operation}", current transaction signer, current method arguments.'
)
def add_abi_method_call(context, account_type, operation):
    abi_method_adder(
        context,
        account_type,
        operation,
    )


@when(
    'I add a method call with the {account_type} account, the current application, suggested params, on complete "{operation}", current transaction signer, current method arguments, approval-program "{approval_program_path:MaybeString}", clear-program "{clear_program_path:MaybeString}", global-bytes {global_bytes}, global-ints {global_ints}, local-bytes {local_bytes}, local-ints {local_ints}, extra-pages {extra_pages}.'
)
def add_abi_method_call_creation_with_allocs(
    context,
    account_type,
    operation,
    approval_program_path,
    clear_program_path,
    global_bytes,
    global_ints,
    local_bytes,
    local_ints,
    extra_pages,
):
    abi_method_adder(
        context,
        account_type,
        operation,
        True,
        approval_program_path,
        clear_program_path,
        global_bytes,
        global_ints,
        local_bytes,
        local_ints,
        extra_pages,
    )


@when(
    'I add a method call with the {account_type} account, the current application, suggested params, on complete "{operation}", current transaction signer, current method arguments, approval-program "{approval_program_path:MaybeString}", clear-program "{clear_program_path:MaybeString}".'
)
def add_abi_method_call_creation(
    context,
    account_type,
    operation,
    approval_program_path,
    clear_program_path,
):
    abi_method_adder(
        context,
        account_type,
        operation,
        True,
        approval_program_path,
        clear_program_path,
    )


@step(
    'I add a nonced method call with the {account_type} account, the current application, suggested params, on complete "{operation}", current transaction signer, current method arguments.'
)
def add_abi_method_call_nonced(context, account_type, operation):
    abi_method_adder(
        context,
        account_type,
        operation,
        force_unique_transactions=True,
    )


@step(
    'I build the transaction group with the composer. If there is an error it is "{error_string:MaybeString}".'
)
def build_atomic_transaction_group(context, error_string):
    try:
        context.atomic_transaction_composer.build_group()
    except Exception as e:
        if not error_string:
            raise RuntimeError(f"Unexpected error for building composer {e}")
        elif error_string == "zero group size error":
            error_message = (
                "no transactions to build for AtomicTransactionComposer"
            )
            assert error_message in str(e)
        else:
            raise NotImplemented(
                f"Unknown error string for building composer: {error_string}"
            )


@then('The composer should have a status of "{status}".')
def check_atomic_transaction_composer_status(context, status):
    assert (
        context.atomic_transaction_composer.get_status()
        == composer_status_string_to_enum(status)
    )


@then("I gather signatures with the composer.")
def gather_signatures_composer(context):
    context.signed_transactions = (
        context.atomic_transaction_composer.gather_signatures()
    )


@then("I clone the composer.")
def clone_atomic_transaction_composer(context):
    context.atomic_transaction_composer = (
        context.atomic_transaction_composer.clone()
    )


@then("I execute the current transaction group with the composer.")
def execute_atomic_transaction_composer(context):
    context.atomic_transaction_composer_return = (
        context.atomic_transaction_composer.execute(context.app_acl, 10)
    )
    assert context.atomic_transaction_composer_return.confirmed_round > 0


@then('The app should have returned "{returns:MaybeString}".')
def check_atomic_transaction_composer_response(context, returns):
    if not returns:
        expected_tokens = []
        assert len(context.atomic_transaction_composer_return.abi_results) == 1
        result = context.atomic_transaction_composer_return.abi_results[0]
        assert result.return_value is None
        assert result.decode_error is None
    else:
        expected_tokens = returns.split(",")
        for i, expected in enumerate(expected_tokens):
            result = context.atomic_transaction_composer_return.abi_results[i]
            if not returns or not expected_tokens[i]:
                assert result.return_value is None
                assert result.decode_error is None
                continue
            expected_bytes = base64.b64decode(expected)
            expected_value = result.method.returns.type.decode(expected_bytes)

            assert expected_bytes == result.raw_value, "actual is {}".format(
                result.raw_value
            )
            assert (
                expected_value == result.return_value
            ), "actual is {}".format(result.return_value)
            assert result.decode_error is None


@then('The app should have returned ABI types "{abiTypes:MaybeString}".')
def check_atomic_transaction_composer_return_type(context, abiTypes):
    expected_tokens = abiTypes.split(":")
    results = context.atomic_transaction_composer_return.abi_results
    assert len(expected_tokens) == len(
        results
    ), f"surprisingly, we don't have the same number of expected results ({len(expected_tokens)}) as actual results ({len(results)})"
    for i, expected in enumerate(expected_tokens):
        result = results[i]
        assert result.decode_error is None

        if expected == "void":
            assert result.raw_value is None
            with pytest.raises(ABITypeError):
                abi.ABIType.from_string(expected)
            continue

        expected_type = abi.ABIType.from_string(expected)
        decoded_result = expected_type.decode(result.raw_value)
        result_round_trip = expected_type.encode(decoded_result)
        assert result_round_trip == result.raw_value


@when("I serialize the Method object into json")
def serialize_method_to_json(context):
    context.json_output = context.abi_method.dictify()


@when(
    'I create the Method object with name "{method_name}" method description "{method_desc}" first argument type "{first_arg_type}" first argument description "{first_arg_desc}" second argument type "{second_arg_type}" second argument description "{second_arg_desc}" and return type "{return_arg_type}"'
)
def create_method_from_test_with_arg_name_and_desc(
    context,
    method_name,
    method_desc,
    first_arg_type,
    first_arg_desc,
    second_arg_type,
    second_arg_desc,
    return_arg_type,
):
    context.abi_method = abi.Method(
        name=method_name,
        args=[
            abi.Argument(arg_type=first_arg_type, desc=first_arg_desc),
            abi.Argument(arg_type=second_arg_type, desc=second_arg_desc),
        ],
        returns=abi.Returns(return_arg_type),
        desc=method_desc,
    )


@when(
    'I create the Method object with name "{method_name}" first argument name "{first_arg_name}" first argument type "{first_arg_type}" second argument name "{second_arg_name}" second argument type "{second_arg_type}" and return type "{return_arg_type}"'
)
def create_method_from_test_with_arg_name(
    context,
    method_name,
    first_arg_name,
    first_arg_type,
    second_arg_name,
    second_arg_type,
    return_arg_type,
):
    context.abi_method = abi.Method(
        name=method_name,
        args=[
            abi.Argument(arg_type=first_arg_type, name=first_arg_name),
            abi.Argument(arg_type=second_arg_type, name=second_arg_name),
        ],
        returns=abi.Returns(return_arg_type),
    )


@when(
    'I create the Method object with name "{method_name}" first argument type "{first_arg_type}" second argument type "{second_arg_type}" and return type "{return_arg_type}"'
)
def create_method_from_test(
    context, method_name, first_arg_type, second_arg_type, return_arg_type
):
    context.abi_method = abi.Method(
        name=method_name,
        args=[abi.Argument(first_arg_type), abi.Argument(second_arg_type)],
        returns=abi.Returns(return_arg_type),
    )


@then("the deserialized json should equal the original Method object")
def deserialize_method_to_object(context):
    json_string = json.dumps(context.json_output)
    actual = abi.Method.from_json(json_string)
    assert actual == context.abi_method


@then("the txn count should be {txn_count}")
def check_method_txn_count(context, txn_count):
    assert context.abi_method.get_txn_calls() == int(txn_count)


@then('the method selector should be "{method_selector}"')
def check_method_selector(context, method_selector):
    assert context.abi_method.get_selector() == bytes.fromhex(method_selector)


@when(
    'I create an Interface object from the Method object with name "{interface_name}" and description "{description}"'
)
def create_interface_object(context, interface_name, description):
    context.abi_interface = abi.Interface(
        name=interface_name, desc=description, methods=[context.abi_method]
    )


@when("I serialize the Interface object into json")
def serialize_interface_to_json(context):
    context.json_output = context.abi_interface.dictify()


@then("the deserialized json should equal the original Interface object")
def deserialize_json_to_interface(context):
    actual = abi.Interface.undictify(context.json_output)
    assert actual == context.abi_interface


@when(
    'I create a Contract object from the Method object with name "{contract_name}" and description "{description}"'
)
def create_contract_object(context, contract_name, description):
    context.abi_contract = abi.Contract(
        name=contract_name, desc=description, methods=[context.abi_method]
    )


@when('I set the Contract\'s appID to {app_id} for the network "{network_id}"')
def set_contract_networks(context, app_id, network_id):
    if not context.abi_contract.networks:
        context.abi_contract.networks = {}
    context.abi_contract.networks[network_id] = NetworkInfo(int(app_id))


@when("I serialize the Contract object into json")
def serialize_contract_to_json(context):
    context.json_output = context.abi_contract.dictify()


@then("the deserialized json should equal the original Contract object")
def deserialize_json_to_contract(context):
    actual = abi.Contract.undictify(context.json_output)
    assert actual == context.abi_contract


@then(
    "The {result_index}th atomic result for randomInt({input}) proves correct"
)
def sha512_256_of_witness_mod_n_is_result(context, result_index, input):
    input = int(input)
    abi_type = abi.ABIType.from_string("(uint64,byte[17])")
    result = context.atomic_transaction_composer_return.abi_results[
        int(result_index)
    ]
    rand_int, witness = abi_type.decode(result.raw_value)
    witness = bytes(witness)
    x = s512_256_uint64(witness)
    quotient = x % input
    assert quotient == rand_int


@then(
    'The {result_index}th atomic result for randElement("{input}") proves correct'
)
def char_with_idx_sha512_256_of_witness_mod_n_is_result(
    context, result_index, input
):
    abi_type = abi.ABIType.from_string("(byte,byte[17])")
    result = context.atomic_transaction_composer_return.abi_results[
        int(result_index)
    ]
    rand_elt, witness = abi_type.decode(result.raw_value)
    witness = bytes(witness)
    x = s512_256_uint64(witness)
    quotient = x % len(input)
    assert input[quotient] == bytes([rand_elt]).decode()


@then(
    'The {result_index}th atomic result for "spin()" satisfies the regex "{regex}"'
)
def spin_results_satisfy(context, result_index, regex):
    abi_type = abi.ABIType.from_string("(byte[3],byte[17],byte[17],byte[17])")
    result = context.atomic_transaction_composer_return.abi_results[
        int(result_index)
    ]
    spin, _, _, _ = abi_type.decode(result.raw_value)
    spin = bytes(spin).decode()

    assert re.search(regex, spin), f"{spin} did not match the regex {regex}"


@when(
    'I append to my Method objects list in the case of a non-empty signature "{method:MaybeString}"'
)
def make_extra_method(context, method):
    if not hasattr(context, "methods"):
        context.methods = []

    if method != "":
        context.methods.append(abi.Method.from_signature(method))


@when("I create an Interface object from my Method objects list")
def create_interface_from_method(context):
    context.iface = abi.Interface("", context.methods)


@when("I create a Contract object from my Method objects list")
def create_contract_from_method(context):
    context.contract = abi.Contract("", context.methods)


@when('I get the method from the Interface by name "{name}"')
def get_interface_method_by_name(context, name):
    try:
        context.retrieved_method = context.iface.get_method_by_name(name)
    except KeyError as ke:
        context.error = str(ke)


@when('I get the method from the Contract by name "{name}"')
def get_contract_method_by_name(context, name):
    try:
        context.retrieved_method = context.contract.get_method_by_name(name)
    except KeyError as ke:
        context.error = str(ke)


@then(
    'the produced method signature should equal "{methodsig}". If there is an error it begins with "{error:MaybeString}"'
)
def check_found_method_or_error(context, methodsig, error: str = None):
    if hasattr(context, "retrieved_method"):
        assert error == ""
        assert methodsig == context.retrieved_method.get_signature()
    elif hasattr(context, "error"):
        assert error != ""
        assert error in context.error
    else:
        assert False, "Both retrieved method and error string are None"


@then(
    'according to "{from_client}", the contents of the box with name "{box_name}" in the current application should be "{box_value:MaybeString}". If there is an error it is "{error_string:MaybeString}".'
)
def check_box_contents(
    context,
    from_client,
    box_name,
    box_value: str = None,
    error_string: str = None,
):
    try:
        box_name = split_and_process_app_args(box_name)[0]
        if from_client == "algod":
            box_response = context.app_acl.application_box_by_name(
                context.current_application_id, box_name
            )
        elif from_client == "indexer":
            box_response = context.app_icl.application_box_by_name(
                context.current_application_id, box_name
            )
        else:
            assert False, f"expecting algod or indexer, got: {from_client}"

        actual_name = box_response["name"]
        actual_value = box_response["value"]
        assert box_name == base64.b64decode(actual_name)
        assert box_value == str(actual_value)
    except Exception as e:
        if not error_string or error_string not in str(e):
            raise RuntimeError(
                "error string "
                + error_string
                + " not in actual error "
                + str(e)
            )


@then(
    'according to "{from_client}", with {limit} being the parameter that limits results, the current application should have {expected_num} boxes.'
)
def check_box_num_by_limit(context, from_client, limit, expected_num: str):
    limit_int = int(limit)
    expected_num_int = int(expected_num)
    if from_client == "algod":
        box_response = context.app_acl.application_boxes(
            context.current_application_id, limit=limit_int
        )
    elif from_client == "indexer":
        box_response = context.app_icl.application_boxes(
            context.current_application_id, limit=limit_int
        )
    else:
        assert False, f"expecting algod or indexer, got: {from_client}"

    assert expected_num_int == len(
        box_response["boxes"]
    ), f"expected box num: {expected_num_int}, got {len(box_response['boxes'])}"


@then(
    'according to "{from_client}", the current application should have the following boxes "{box_names:MaybeString}".'
)
def check_all_boxes(context, from_client: str, box_names: str = None):
    expected_box_names = []
    if box_names:
        expected_box_names = [
            base64.b64decode(box_encoded)
            for box_encoded in box_names.split(":")
        ]
    if from_client == "algod":
        box_response = context.app_acl.application_boxes(
            context.current_application_id
        )
    elif from_client == "indexer":
        box_response = context.app_icl.application_boxes(
            context.current_application_id
        )
    else:
        assert False, f"expecting algod or indexer, got: {from_client}"

    actual_box_names = [
        base64.b64decode(box["name"]) for box in box_response["boxes"]
    ]

    # Check that length of lists are equal, then check for set equality.
    assert len(expected_box_names) == len(
        actual_box_names
    ), f"Expected box names array length does not match actual array length {len(expected_box_names)} != {len(actual_box_names)}"
    assert set(expected_box_names) == set(
        actual_box_names
    ), f"Expected box names array does not match actual array {expected_box_names} != {actual_box_names}"


@then(
    'according to indexer, with {limit} being the parameter that limits results, and "{next_page:MaybeString}" being the parameter that sets the next result, the current application should have the following boxes "{box_names:MaybeString}".'
)
def check_all_boxes_by_indexer(
    context, limit, next_page: str = None, box_names: str = None
):
    expected_box_names = []
    if box_names:
        expected_box_names = [
            base64.b64decode(box_encoded)
            for box_encoded in box_names.split(":")
        ]
    limit_int = int(limit)
    next_page = next_page if next_page else ""
    box_response = context.app_icl.application_boxes(
        context.current_application_id, limit=limit_int, next_page=next_page
    )

    actual_box_names = [
        base64.b64decode(box["name"]) for box in box_response["boxes"]
    ]

    # Check that length of lists are equal, then check for set equality.
    assert len(expected_box_names) == len(
        actual_box_names
    ), f"Expected box names array length does not match actual array length {len(expected_box_names)} != {len(actual_box_names)}"
    assert set(expected_box_names) == set(
        actual_box_names
    ), f"Expected box names array does not match actual array {expected_box_names} != {actual_box_names}"
