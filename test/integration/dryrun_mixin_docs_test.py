"""
Derived from: https://github.com/algorand/docs/blob/bbd379df193399f82686e9f6d5c2bcb9d676d2d7/docs/features/asc1/teal_test.md#basic-setup-and-simple-tests
"""
import base64
from tabulate import tabulate
import unittest

from algosdk.constants import PAYMENT_TXN, APPCALL_TXN
from algosdk.future import transaction
from algosdk.encoding import decode_address, checksum
from algosdk.v2client.models import (
    Account,
    Application,
    ApplicationLocalState,
    ApplicationParams,
    ApplicationStateSchema,
    TealKeyValue,
    TealValue,
)
from algosdk.testing.dryrun import DryrunTestCaseMixin, Helper as DryRunHelper

from x.testnet import get_algod


def b64_encode_hack(s, b=None):
    if not b:
        b = bytes(s, "utf-8")
    return base64.b64encode(b).decode("utf-8")


class ExampleTestCase(DryrunTestCaseMixin, unittest.TestCase):
    """The test harness consist of DryrunTestCaseMixin class that is supposed to be used as a mixin
    to unittest-based user-defined tests and Helper class with various utilities.

    DryrunTestCaseMixin provides helpers for testing both LogicSig and Application smart contracts.

    ## Basic asserts: to check if the program return true, false or does [not] err during compilation or execution:
    * assertPass
    * assertReject
    * assertError
    * assertNoError
    """

    def setUp(self):
        self.algo_client = get_algod()

    def test_simple(self):
        """ """
        self.assertPass("int 1")
        self.assertReject("int 0")
        self.assertNoError("int 0")
        self.assertError("byte 0", "1 error")

    def test_logic_sig(self):
        """Shows how to test logic sig with parameters

        This example demonstrates how to pass LogicSig parameters
            - they need to be a list of bytes items in args key of lsig parameter to any assert function.

        In general, specifying lsig non-None parameter forces to use LogicSig run mode.
        """
        source = """
arg 0
btoi
int 0x31
==
"""
        self.assertError(source, "cannot load arg[0]")
        self.assertReject(source)
        self.assertPass(source, lsig=dict(args=[b"1", b"2"]))

        drr = self.dryrun_request(source, lsig=dict(args=[b"\x31", b"2"]))
        self.assertPass(drr)

    def test_logic_sig_ex(self):
        """Shows how to use and examine raw dryrun response"""
        source = """
arg 0
btoi
int 0x31
==
"""
        drr = self.dryrun_request(source, lsig=dict(args=[b"\x31", b"2"]))
        self.assertPass(drr)

    def test_app_global_state(self):
        """Use voting app as example to check app initialization

        Note the app parameter in assert functions.
        It allows setting application-specific fields like OnCompletion, ApplicationID, ApplicationArgs, Accounts

        Two assertReject statements in the beginning on the test check prerequisites:
        1. application call in creation mode (app_idx = 0)
        2. number of required initialization parameters.

        Then dryrun_request helper is used to obtain execution result and written values with
        assertGlobalStateContains. Changes are reported as EvalDelta type with key, value, action, uint or bytes properties.
        bytes values are base64-encoded, and action is explained in the table below:

        | action | description     |
        |--------|-----------------|
        | 1      | set bytes value |
        | 2      | set uint value  |
        | 3      | delete value    |

        Having this information, `assertGlobalStateContains` validates that **Creator** global key is set to txn sender address,
        and all the **RegBegin**, **RegEnd**, **VoteBegin** and **VoteEnd** are properly initialized.
        """
        source = """#pragma version 2
int 0
txn ApplicationID
==
bz not_creation
byte "Creator"
txn Sender
app_global_put
txn NumAppArgs
int 4
==
bz failed
byte "RegBegin"
txna ApplicationArgs 0
btoi
app_global_put
byte "RegEnd"
txna ApplicationArgs 1
btoi
app_global_put
byte "VoteBegin"
txna ApplicationArgs 2
btoi
app_global_put
byte "VoteEnd"
txna ApplicationArgs 3
btoi
app_global_put
int 1
return
not_creation:
int 0
return
failed:
int 0
return
"""
        self.assertReject(source, app=dict(app_idx=0))
        self.assertReject(
            source,
            app=dict(
                app_idx=1,
                args=[b"\x01", b"\xFF", b"\x01\x00", b"\x01\xFF"],
            ),
        )
        self.assertPass(
            source,
            app=dict(
                app_idx=0,
                args=[b"\x01", b"\xFF", b"\x01\x00", b"\x01\xFF"],
            ),
        )

        sender = "42NJMHTPFVPXVSDGA6JGKUV6TARV5UZTMPFIREMLXHETRKIVW34QFSDFRE"
        drr = self.dryrun_request(
            source,
            sender=sender,
            app=dict(
                app_idx=0,
                args=[
                    (0x01).to_bytes(1, byteorder="big"),
                    (0xFF).to_bytes(1, byteorder="big"),
                    (0x0100).to_bytes(2, byteorder="big"),
                    (0x01FF).to_bytes(2, byteorder="big"),
                ],
            ),
        )
        self.assertPass(drr)

        value = dict(
            key=b64_encode_hack("Creator"),
            value=dict(
                action=1,
                bytes=b64_encode_hack("", decode_address(sender)),
            ),
        )
        self.assertGlobalStateContains(drr, value)

        value = dict(
            key=b64_encode_hack("RegBegin"),
            value=dict(action=2, uint=0x01),
        )
        self.assertGlobalStateContains(drr, value)

        value = dict(
            key=b64_encode_hack("RegEnd"), value=dict(action=2, uint=0xFF)
        )
        self.assertGlobalStateContains(drr, value)

        value = dict(
            key=b64_encode_hack("VoteBegin"),
            value=dict(action=2, uint=0x0100),
        )
        self.assertGlobalStateContains(drr, value)

        value = dict(
            key=b64_encode_hack("VoteEnd"),
            value=dict(action=2, uint=0x01FF),
        )
        self.assertGlobalStateContains(drr, value)

    def test_app_global_state_existing(self):
        """Use voting app as example to check app update

        Now let's test an application and check what does it write to the global state.
        Example below is an initialization prologue of voting app.
        """
        source = """#pragma version 2
int 0
txn ApplicationID
==
bz not_creation
// fail on creation in this test scenario
int 0
return
not_creation:
int UpdateApplication
txn OnCompletion
==
bz failed
byte "Creator"
app_global_get
txn Sender
==
bz failed
int 1
return
failed:
int 0"""
        sender = self.default_address()

        self.assertReject(source, app=dict(app_idx=0))
        self.assertReject(source, app=dict(app_idx=1))
        self.assertReject(source, app=dict(app_idx=1, accounts=[sender]))

        app = dict(
            app_idx=1,
            global_state=[
                TealKeyValue(
                    key=b64_encode_hack("Creator"),
                    value=TealValue(type=1, bytes=b""),
                )
            ],
        )
        self.assertReject(source, app=app)

        app["on_complete"] = transaction.OnComplete.UpdateApplicationOC
        self.assertReject(source, app=app)

        # TODO: get this one to pass as well
        # app["global_state"][0].value.bytes = decode_address(sender)
        # self.assertPass(source, app=app)

    def test_app_local_state(self):
        """Use voting app as example to check local state writes"""
        source = """#pragma version 2
txna ApplicationArgs 0
byte "vote"
==
bnz vote
int 0
return
vote:
global Round
byte "VoteBegin"
app_global_get
>=
global Round
byte "VoteEnd"
app_global_get
<=
&&
bz failed
int 0
txn ApplicationID
app_opted_in
bz failed
int 0
txn ApplicationID
byte "voted"
app_local_get_ex
bnz voted
//read existing vote candidate
txna ApplicationArgs 1
app_global_get
bnz increment_existing
pop
int 0
increment_existing:
int 1
+
store 1
txna ApplicationArgs 1
load 1
app_global_put
int 0 //sender
byte "voted"
txna ApplicationArgs 1
app_local_put
int 1
return
voted:
pop
int 1
return
failed:
int 0
return
"""
        drr = self.dryrun_request(source, app=dict(app_idx=1))
        self.assertReject(drr)
        self.assertError(drr, "invalid ApplicationArgs index 0")

        drr = self.dryrun_request(source, app=dict(app_idx=1, args=[b"vote"]))
        self.assertReject(drr)
        self.assertNoError(drr)

        sender = "42NJMHTPFVPXVSDGA6JGKUV6TARV5UZTMPFIREMLXHETRKIVW34QFSDFRE"
        creator = "DFPKC2SJP3OTFVJFMCD356YB7BOT4SJZTGWLIPPFEWL3ZABUFLTOY6ILYE"
        creator_data = Account(
            address=creator,
            status="Offline",
            created_apps=[
                Application(
                    id=1,
                    params=ApplicationParams(
                        global_state=[
                            TealKeyValue(
                                key=b64_encode_hack("VoteBegin"),
                                value=TealValue(type=2, uint=1),
                            ),
                            TealKeyValue(
                                key=b64_encode_hack("VoteEnd"),
                                value=TealValue(type=2, uint=1000),
                            ),
                        ]
                    ),
                ),
            ],
        )

        accounts = [creator_data]

        drr = self.dryrun_request(
            source,
            app=dict(
                app_idx=1,
                args=[b"vote"],
                round=3,
                creator=creator,
                accounts=accounts,
            ),
        )
        self.assertReject(drr)
        self.assertNoError(drr)

        sender_data = Account(
            address=sender,
            status="Offline",
            apps_local_state=[ApplicationLocalState(id=1)],
        )

        accounts = [creator_data, sender_data]
        drr = self.dryrun_request(
            source,
            sender=sender,
            app=dict(
                app_idx=1,
                creator=creator,
                args=[b"vote"],
                round=3,
                accounts=accounts,
            ),
        )
        self.assertError(drr, "invalid ApplicationArgs index 1")

        accounts = [creator_data, sender_data]
        drr = self.dryrun_request(
            source,
            sender=sender,
            app=dict(
                app_idx=1,
                creator=creator,
                args=[b"vote", "test"],
                round=3,
                accounts=accounts,
            ),
        )
        self.assertPass(drr)
        DryRunHelper.pprint(drr)

        value = dict(
            key=b64_encode_hack("voted"),
            value=DryRunHelper.build_bytes_delta_value("test"),
        )
        self.assertLocalStateContains(drr, sender, value)

        value = dict(key=b64_encode_hack("test"), value=dict(action=2, uint=1))
        self.assertGlobalStateContains(drr, value)

    def test_transactions(self):
        """Test app call and logic sig transactions interaction
        INTERESTING logic sig USE CASE

        Although examples above provide testing tools for "create and run" scenarios when
        testing single programs, sometimes transaction interactions also need to tested.
        In this example we consider how stateful application can __offload__ some computations
        to stateless logicsig program, and ensure the logic sig is the right one.

        Suppose our logic sig program computes the following hash:
            h(h(a1) + h(a2) + h(a3) + h(a4))
        where + is string concatenation, and then verifies it against some provided proof.

        Suppose our application approves only if the calculation is made correctly.
        To achieve this, create a txn group where:

        1. Txn 1 is an escrow logic sig txn with hash calculation approval program (see logic_source below).
        2. Txn 2 is app call txn with txn 1 checker (see app_source below).
          * Ensure txn 1 sender is know-ahead escrow address.
          * Ensure txn 1 Note field is set to proof that is needed to be confirmed.
        3. Input data a1, a2, a3, a4 are set as ApplicationArgs for txn 2 and accessed from txn 1
        (logic sig args can be used as well, since both the logic hash and the proof checked in the app call program).

        """
        logic_source = """#pragma version 2
gtxna 1 ApplicationArgs 0
sha512_256
gtxna 1 ApplicationArgs 1
sha512_256
concat
gtxna 1 ApplicationArgs 2
sha512_256
gtxna 1 ApplicationArgs 3
sha512_256
concat
concat
sha512_256
txn Note
==
"""
        # compile the logic sig program
        logic_compiled = self.algo_client.compile(logic_source)
        self.assertIn("hash", logic_compiled)
        self.assertIn("result", logic_compiled)
        logic = base64.b64decode(logic_compiled["result"])
        logic_hash = logic_compiled["hash"]

        # compute proof from parameters
        args = [b"this", b"is", b"a", b"test"]
        parts = []
        for arg in args:
            parts.append(checksum(arg))

        proof = checksum(b"".join(parts))

        # create and compile app call program
        app_source = f"""#pragma version 2
gtxn 0 Sender
addr {logic_hash}
==
gtxn 0 Note
byte {"0x" + proof.hex()}
==
&&
"""
        app_compiled = self.algo_client.compile(app_source)
        self.assertIn("result", app_compiled)
        app = base64.b64decode(app_compiled["result"])

        # create transactions
        txn1 = DryRunHelper.sample_txn(logic_hash, PAYMENT_TXN)
        txn1.note = proof
        logicsig = transaction.LogicSig(logic, None)
        stxn1 = transaction.LogicSigTransaction(txn1, logicsig)

        app_idx = 1
        txn2 = DryRunHelper.sample_txn(self.default_address(), APPCALL_TXN)
        txn2.index = app_idx
        txn2.app_args = args
        stxn2 = transaction.SignedTransaction(txn2, None)

        # create a balance record with the application
        # creator address is a random one
        creator = "DFPKC2SJP3OTFVJFMCD356YB7BOT4SJZTGWLIPPFEWL3ZABUFLTOY6ILYE"
        creator_data = Account(
            address=creator,
            status="Offline",
            created_apps=[
                Application(
                    id=1,
                    params=ApplicationParams(
                        approval_program=app,
                        local_state_schema=ApplicationStateSchema(64, 64),
                        global_state_schema=ApplicationStateSchema(64, 64),
                    ),
                )
            ],
        )

        drr = self.dryrun_request_from_txn(
            [stxn1, stxn2], app=dict(accounts=[creator_data])
        )
        self.assertPass(drr)

        # now check the verification logic
        # wrong creator
        txn1.sender = creator
        drr = self.dryrun_request_from_txn(
            [stxn1, stxn2], app=dict(accounts=[creator_data])
        )
        self.assertPass(drr, txn_index=0)
        self.assertReject(drr, txn_index=1)
        self.assertReject(drr)

        # wrong proof
        txn1.sender = logic_hash
        txn1.note = b"wrong"
        drr = self.dryrun_request_from_txn(
            [stxn1, stxn2], app=dict(accounts=[creator_data])
        )
        self.assertReject(drr, txn_index=0)
        self.assertReject(drr, txn_index=1)
        self.assertReject(drr)

    def test_factorial(self):
        """
        Shows how to test the same code as a logic sig or an app
        python -m unittest x.blackbox.dryrun_mixin_docs_test.ExampleTestCase.test_factorial
        """
        source = """#pragma version 6
{} 0
btoi
callsub oldfac_0
return

// oldfac
oldfac_0:
store 0
load 0
int 2
<
bnz oldfac_0_l2
load 0
load 0
int 1
-
load 0
swap
callsub oldfac_0
swap
store 0
*
b oldfac_0_l3
oldfac_0_l2:
int 1
oldfac_0_l3:
retsub"""

        def tb(i):
            return i.to_bytes(1, "big")

        lsig_src = source.format("arg")
        app_src = source.format("txna ApplicationArgs")

        max_arg_before_overflow = 20
        finalgood_args = None
        for i in range(max_arg_before_overflow):
            finalgood_args = {"args": [tb(i)]}
            lsig_dr = self.dryrun_request(lsig_src, lsig=finalgood_args)
            self.assertPass(lsig_dr, msg=f"i={i}")
            app_dr = self.dryrun_request(app_src, app=finalgood_args)
            self.assertPass(app_dr, msg=f"i={i}")

        print(f"n={1+max_arg_before_overflow} was TOO BIG:")
        toobig_args = {"args": [tb(1 + max_arg_before_overflow)]}
        self.assertError(lsig_src, "overflow", lsig=toobig_args)
        lsig_dr = self.dryrun_request(lsig_src, lsig=toobig_args)
        DryRunHelper.pprint(lsig_dr)

        self.assertError(app_src, "overflow", app=toobig_args)
        app_dr = self.dryrun_request(app_src, app=toobig_args)
        DryRunHelper.pprint(app_dr)

        print("\n" * 3, f"BUT...  n={1+max_arg_before_overflow} is JUST FINE:")
        lsig_dr = self.dryrun_request(lsig_src, lsig=finalgood_args)
        DryRunHelper.pprint(lsig_dr)

        app_dr = self.dryrun_request(app_src, app=finalgood_args)
        DryRunHelper.pprint(app_dr)

        print("FINISHED logic sig", "\n" * 3, "BEGIN app")

        print("HOW ABOUT costs?")

        def get_cost(i):
            return self.dryrun_request(app_src, app={"args": [tb(i)]})["txns"][
                0
            ]["cost"]

        print(
            tabulate(
                [(i, get_cost(i)) for i in range(45)], headers=["n", "Cost(n)"]
            ),
        )
