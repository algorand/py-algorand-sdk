import base64
import json
import re
import unittest

from behave import (
    given,
    when,
    then,
    step,
)


from algosdk import abi, atomic_transaction_composer, encoding, logic, mnemonic
from algosdk.abi.base_type import ABIType
from algosdk.abi.contract import NetworkInfo
from algosdk.encoding import checksum
from algosdk.error import AlgodHTTPError
from algosdk.future import transaction
from algosdk.testing.dryrun import DryrunTestCaseMixin
from algosdk.v2client.models import (
    DryrunRequest,
    DryrunSource,
    Account,
    ApplicationLocalState,
)

from step_utils import (
    fund_account_address,
    load_resource,
    operation_string_to_enum,
    read_program,
    split_and_process_app_args,
)


def transient_acct_app_builder(
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
    )


@when("we make a GetApplicationByID call for applicationID {app_id}")
def application_info(context, app_id):
    context.response = context.acl.application_info(int(app_id))


@given(
    'I build an application transaction with the transient account, the current application with method args, suggested params, operation "{operation}", approval-program "{approval_program:MaybeString}", clear-program "{clear_program:MaybeString}", global-bytes {global_bytes}, global-ints {global_ints}, local-bytes {local_bytes}, local-ints {local_ints}, foreign-apps "{foreign_apps:MaybeString}", foreign-assets "{foreign_assets:MaybeString}", app-accounts "{app_accounts:MaybeString}", extra-pages {extra_pages}'
)
def build_app_txn_with_transient_with_curr_meth_args(
    context,
    operation,
    approval_program,
    clear_program,
    global_bytes,
    global_ints,
    local_bytes,
    local_ints,
    foreign_apps,
    foreign_assets,
    app_accounts,
    extra_pages,
):
    transient_acct_app_builder(
        context,
        operation,
        approval_program,
        clear_program,
        global_bytes,
        global_ints,
        local_bytes,
        local_ints,
        ",".join(map(str, context.method_args)),
        foreign_apps,
        foreign_assets,
        app_accounts,
        extra_pages,
    )


@step(
    'I build an application transaction with the transient account, the current application, suggested params, operation "{operation}", approval-program "{approval_program:MaybeString}", clear-program "{clear_program:MaybeString}", global-bytes {global_bytes}, global-ints {global_ints}, local-bytes {local_bytes}, local-ints {local_ints}, app-args "{app_args:MaybeString}", foreign-apps "{foreign_apps:MaybeString}", foreign-assets "{foreign_assets:MaybeString}", app-accounts "{app_accounts:MaybeString}", extra-pages {extra_pages}'
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
):
    transient_acct_app_builder(
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
    )


@when(
    'I build an application transaction with operation "{operation:MaybeString}", application-id {application_id}, sender "{sender:MaybeString}", approval-program "{approval_program:MaybeString}", clear-program "{clear_program:MaybeString}", global-bytes {global_bytes}, global-ints {global_ints}, local-bytes {local_bytes}, local-ints {local_ints}, app-args "{app_args:MaybeString}", foreign-apps "{foreign_apps:MaybeString}", foreign-assets "{foreign_assets:MaybeString}", app-accounts "{app_accounts:MaybeString}", fee {fee}, first-valid {first_valid}, last-valid {last_valid}, genesis-hash "{genesis_hash:MaybeString}", extra-pages {extra_pages}'
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
    )


@given(
    "I fund the current application's address with {fund_amount} microalgos."
)
def fund_app_account(context, fund_amount):
    fund_account_address(
        context,
        logic.get_application_address(context.current_application_id),
        fund_amount,
    )


@when("we make a LookupApplications call with applicationID {app_id}")
def lookup_application(context, app_id):
    context.response = context.icl.applications(int(app_id))


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


@step("I wait for the transaction to be confirmed.")
def wait_for_app_txn_confirm(context):
    sp = context.app_acl.suggested_params()
    last_round = sp.first
    context.app_acl.status_after_block(last_round + 2)
    if hasattr(context, "acl"):
        assert "type" in context.acl.transaction_info(
            context.transient_pk, context.app_txid
        )
        assert "type" in context.acl.transaction_by_id(context.app_txid)
    else:
        transaction.wait_for_confirmation(
            context.app_acl, context.app_txid, 10
        )


@given("I remember the new application ID.")
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


@then(
    "I get the application info for the current application, and its account matches the app id's hash"
)
def assert_app_account_is_the_hash(context):
    app_id = context.current_application_id
    app_info = context.app_acl.application_info(app_id)
    assert app_info["application-account"] == logic.get_application_address(
        app_id
    )


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


@when('I compile a teal program "{program}"')
def compile_step(context, program):
    data = load_resource(program)
    source = data.decode("utf-8")

    try:
        context.response = context.app_acl.compile(source)
        context.status = 200
    except AlgodHTTPError as ex:
        context.status = ex.code
        context.response = dict(result="", hash="")


@then(
    'it is compiled with {status} and "{result:MaybeString}" and "{hash:MaybeString}"'
)
def compile_check_step(context, status, result, hash):
    assert context.status == int(status)
    assert context.response["result"] == result
    assert context.response["hash"] == hash


@then(
    'base64 decoding the response is the same as the binary "{binary:MaybeString}"'
)
def b64decode_compiled_teal_step(context, binary):
    binary = load_resource(binary)
    response_result = context.response["result"]
    assert base64.b64decode(response_result.encode()) == binary


@when('I dryrun a "{kind}" program "{program}"')
def dryrun_step(context, kind, program):
    data = load_resource(program)
    sp = transaction.SuggestedParams(
        int(1000), int(1), int(100), "", flat_fee=True
    )
    zero_addr = encoding.encode_address(bytes(32))
    txn = transaction.Transaction(zero_addr, sp, None, None, "pay", None)
    sources = []

    if kind == "compiled":
        lsig = transaction.LogicSig(data)
        txns = [transaction.LogicSigTransaction(txn, lsig)]
    elif kind == "source":
        txns = [transaction.SignedTransaction(txn, None)]
        sources = [DryrunSource(field_name="lsig", source=data, txn_index=0)]
    else:
        assert False, f"kind {kind} not in (source, compiled)"

    drr = DryrunRequest(txns=txns, sources=sources)
    context.response = context.app_acl.dryrun(drr)


@then('I get execution result "{result}"')
def dryrun_check_step(context, result):
    ddr = context.response
    assert len(ddr["txns"]) > 0

    res = ddr["txns"][0]
    if (
        res["logic-sig-messages"] is not None
        and len(res["logic-sig-messages"]) > 0
    ):
        msgs = res["logic-sig-messages"]
    elif (
        res["app-call-messages"] is not None
        and len(res["app-call-messages"]) > 0
    ):
        msgs = res["app-call-messages"]

    assert len(msgs) > 0
    assert msgs[-1] == result


@when("we make any Dryrun call")
def dryrun_any_call_step(context):
    context.response = context.acl.dryrun(DryrunRequest())


@then(
    'the parsed Dryrun Response should have global delta "{creator}" with {action}'
)
def dryrun_parsed_response(context, creator, action):
    ddr = context.response
    assert len(ddr["txns"]) > 0

    delta = ddr["txns"][0]["global-delta"]
    assert len(delta) > 0
    assert delta[0]["key"] == creator
    assert delta[0]["value"]["action"] == int(action)


@given('dryrun test case with "{program}" of type "{kind}"')
def dryrun_test_case_step(context, program, kind):
    if kind not in set(["lsig", "approv", "clearp"]):
        assert False, f"kind {kind} not in (lsig, approv, clearp)"

    prog = load_resource(program)
    # check if source
    if prog[0] > 0x20:
        prog = prog.decode("utf-8")

    context.dryrun_case_program = prog
    context.dryrun_case_kind = kind


@then('status assert of "{status}" is succeed')
def dryrun_test_case_status_assert_step(context, status):
    class TestCase(DryrunTestCaseMixin, unittest.TestCase):
        """Mock TestCase to test"""

    ts = TestCase()
    ts.algo_client = context.app_acl

    lsig = None
    app = None
    if context.dryrun_case_kind == "lsig":
        lsig = dict()
    if context.dryrun_case_kind == "approv":
        app = dict()
    elif context.dryrun_case_kind == "clearp":
        app = dict(on_complete=transaction.OnComplete.ClearStateOC)

    if status == "PASS":
        ts.assertPass(context.dryrun_case_program, lsig=lsig, app=app)
    else:
        ts.assertReject(context.dryrun_case_program, lsig=lsig, app=app)


def dryrun_test_case_global_state_assert_impl(
    context, key, value, action, raises
):
    class TestCase(DryrunTestCaseMixin, unittest.TestCase):
        """Mock TestCase to test"""

    ts = TestCase()
    ts.algo_client = context.app_acl

    action = int(action)

    val = dict(action=action)
    if action == 1:
        val["bytes"] = value
    elif action == 2:
        val["uint"] = int(value)

    on_complete = transaction.OnComplete.NoOpOC
    if context.dryrun_case_kind == "clearp":
        on_complete = transaction.OnComplete.ClearStateOC

    raised = False
    try:
        ts.assertGlobalStateContains(
            context.dryrun_case_program,
            dict(key=key, value=val),
            app=dict(on_complete=on_complete),
        )
    except AssertionError:
        raised = True

    if raises:
        ts.assertTrue(raised, "assertGlobalStateContains expected to raise")


@then('global delta assert with "{key}", "{value}" and {action} is succeed')
def dryrun_test_case_global_state_assert_step(context, key, value, action):
    dryrun_test_case_global_state_assert_impl(
        context, key, value, action, False
    )


@then('global delta assert with "{key}", "{value}" and {action} is failed')
def dryrun_test_case_global_state_assert_fail_step(
    context, key, value, action
):
    dryrun_test_case_global_state_assert_impl(
        context, key, value, action, True
    )


@then(
    'local delta assert for "{account}" of accounts {index} with "{key}", "{value}" and {action} is succeed'
)
def dryrun_test_case_local_state_assert_fail_step(
    context, account, index, key, value, action
):
    class TestCase(DryrunTestCaseMixin, unittest.TestCase):
        """Mock TestCase to test"""

    ts = TestCase()
    ts.algo_client = context.app_acl

    action = int(action)

    val = dict(action=action)
    if action == 1:
        val["bytes"] = value
    elif action == 2:
        val["uint"] = int(value)

    on_complete = transaction.OnComplete.NoOpOC
    if context.dryrun_case_kind == "clearp":
        on_complete = transaction.OnComplete.ClearStateOC

    app_idx = 1
    accounts = [
        Account(
            address=ts.default_address(),
            status="Offline",
            apps_local_state=[ApplicationLocalState(id=app_idx)],
        )
    ] * 2
    accounts[int(index)].address = account

    drr = ts.dryrun_request(
        context.dryrun_case_program,
        sender=accounts[0].address,
        app=dict(app_idx=app_idx, on_complete=on_complete, accounts=accounts),
    )

    ts.assertNoError(drr)
    ts.assertLocalStateContains(drr, account, dict(key=key, value=val))


@given("a new AtomicTransactionComposer")
def create_atomic_transaction_composer(context):
    context.atomic_transaction_composer = (
        atomic_transaction_composer.AtomicTransactionComposer()
    )
    context.method_list = []


@given("I make a transaction signer for the transient account.")
def create_transient_transaction_signer(context):
    private_key = context.transient_sk
    context.transaction_signer = (
        atomic_transaction_composer.AccountTransactionSigner(private_key)
    )


@when("I make a transaction signer for the {account_type} account.")
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


@step('I create the Method object from method signature "{method_signature}"')
def build_abi_method(context, method_signature):
    context.abi_method = abi.Method.from_signature(method_signature)
    if not hasattr(context, "method_list"):
        context.method_list = []
    context.method_list.append(context.abi_method)


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
    for arg_index, arg in enumerate(method.args):
        # Skip arg if it does not have a type
        if isinstance(arg.type, abi.ABIType):
            method_arg = arg.type.decode(
                base64.b64decode(arg_tokens[arg_index])
            )
            method_args.append(method_arg)
        elif arg.type == abi.ABIReferenceType.ACCOUNT:
            method_arg = abi.AddressType().decode(
                base64.b64decode(arg_tokens[arg_index])
            )
            method_args.append(method_arg)
        elif (
            arg.type == abi.ABIReferenceType.APPLICATION
            or arg.type == abi.ABIReferenceType.ASSET
        ):
            parts = arg_tokens[arg_index].split(":")
            if len(parts) == 2 and parts[0] == "ctxAppIdx":
                method_arg = context.app_ids[int(parts[1])]
            else:
                method_arg = abi.UintType(64).decode(
                    base64.b64decode(arg_tokens[arg_index])
                )
            method_args.append(method_arg)
        else:
            # Append the transaction signer as is
            method_args.append(arg_tokens[arg_index])
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
    app_args = method_args.split(",")
    context.method_args += app_args


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
    note = None
    if force_unique_transactions:
        note = b"step number: " + context.step_number.to_bytes(8, "big")

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
            expected_value = context.method_list[i].returns.type.decode(
                expected_bytes
            )

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
    for i, expected in enumerate(expected_tokens):
        result = context.atomic_transaction_composer_return.abi_results[i]
        assert result.decode_error is None

        if not result or not expected_tokens[i]:
            assert result.return_value is None
            assert result.decode_error is None
            continue

        expected_type = ABIType.from_string(expected)
        decoded_result = expected_type.decode(result.raw_value)
        result_round_trip = expected_type.encode(decoded_result)
        assert result_round_trip == result.raw_value


@when("I serialize the Method object into json")
def serialize_method_to_json(context):
    context.json_output = context.abi_method.dictify()


@then(
    'the produced json should equal "{json_path}" loaded from "{json_directory}"'
)
def check_json_output_equals(context, json_path, json_directory):
    with open(
        "test/features/unit/" + json_directory + "/" + json_path, "rb"
    ) as f:
        loaded_response = json.load(f)
    assert context.json_output == loaded_response


@when(
    'I create the Method object with name "{method_name}" method description "{method_desc}" first argument type "{first_arg_type}" first argument description "{first_arg_desc}" second argument type "{second_arg_type}" second argument description "{second_arg_desc}" and return type "{return_arg_type}"'
)
def create_method_from_test_with_arg_name(
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
    'I can dig into the resulting atomic transaction execution tree with path "{path}"'
)
def digging_the_inner_txns(context, path):
    d = context.atomic_transaction_composer_return.tx_infos
    for i, p in enumerate(path.split(",")):
        idx = int(p)
        d = d["inner-txns"][idx] if i else d[idx]


@then(
    'I dig into the paths "{paths}" of the resulting atomic transaction tree I see group ids and they are all the same'
)
def same_groupids_for_paths(context, paths):
    paths = [[int(p) for p in path.split(",")] for path in paths.split(":")]
    grp = None
    for path in paths:
        d = context.atomic_transaction_composer_return.tx_infos
        for idx, p in enumerate(path):
            d = d["inner-txns"][p] if idx else d[idx]
            _grp = d["txn"]["txn"]["grp"]
        if not grp:
            grp = _grp
        else:
            assert grp == _grp, f"non-constant txn group hashes {_grp} v {grp}"


@then(
    'I can retrieve all inner transactions that were called from the atomic transaction with call graph "{callGraph}".'
)
def can_retrieve_all_inner_txns(context, callGraph):
    actual = context.atomic_transaction_composer_return.transactions_trace(
        quote="'"
    )
    assert actual == callGraph, f"expected: {callGraph} but got: {actual}"


def s512_256_uint64(witness):
    return int.from_bytes(checksum(witness)[:8], "big")


@then(
    "The {result_index}th atomic result for randomInt({input}) proves correct"
)
def sha512_256_of_witness_mod_n_is_result(context, result_index, input):
    input = int(input)
    abi_type = ABIType.from_string("(uint64,byte[17])")
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
    abi_type = ABIType.from_string("(byte,byte[17])")
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
    abi_type = ABIType.from_string("(byte[3],byte[17],byte[17],byte[17])")
    result = context.atomic_transaction_composer_return.abi_results[
        int(result_index)
    ]
    spin, _, _, _ = abi_type.decode(result.raw_value)
    spin = bytes(spin).decode()

    assert re.search(regex, spin), f"{spin} did not match the regex {regex}"
