# TEAL Blackbox Toolkit: Program Reporting and Testing via Dry Runs

**NOTE: to get math formulas to render here using Chrome, add the [xhub extension](https://chrome.google.com/webstore/detail/xhub/anidddebgkllnnnnjfkmjcaallemhjee/related) and reload**

## TLDR; Dry Run a Sequence of Inputs on Apps/LogicSigs, View Stats, and make Assertions on Behavior

### Trying out the new test

```sh
pytest x/blackbox/blackbox_test.py 
```

## Blackbox Testing Howto

### What is TEAL Blackbox Testing?

TEAL Blackbox Testing lets you treat your TEAL programs as black boxes that receive inputs and that produce outputs and other observable effects. You can create reports that summarize those effects,
and turn the _reports_ into _program invariant conjectures_ which you then check with _sequence assertions_.

### Why Blackbox Testing?

Here are some use cases:

* by allowing you to assert that certain invariants hold over a large set of inputs you gain greater confidence that your TEAL programs and AVM smart contracts work as designed
* when tweaking, refactoring or optimizing your TEAL source, ensure that no regressions have occured
* allows AVM developers to practice the art of TTDD (TEAL Test Driven Development)

## Simple TEAL Blackbox Toolkit Example: Program for $`x^2`$

Suppose you have a [TEAL program](https://github.com/algorand/py-algorand-sdk/blob/23c21170cfb19652d5da854e499dca47eabb20e8/x/blackbox/teal/lsig_square.teal) that purportedly computes $`x^2`$. You'd like to write some unit tests to validate that it computes what you think it should, and also make **assertions** regarding:

* the total program cost
* the contents at the stack's top at the end of execution
* the maximum height of the stack during execution
* the contents of the scratch variables at the end
* the contents of the final log message (this is especially useful for [ABI-compliant programs](https://developer.algorand.org/docs/get-details/dapps/smart-contracts/ABI/))
* the status of the program (**PASS**, **REJECT** or _erroring_)
* error conditions that are and are not encountered

Even better, before making fine-grained assertions you'd like to get a sense of what the program is doing on a large set of inputs so you can discover program invariants to assert. One recommended approach for solving this problem is to:

* start by making basic assertions and validate them using dry runs (see "**Basic Assertions**" section below)
* execute the program on a run-sequence of inputs and explore the results (see "**EDRA: Exploratory Dry Run Analysis**" section below)
* create invariants for the entire run-sequence and assert that the invariants hold (see "**Advanced: Asserting Invariants on a Dry Run Sequence**" section below)

### Dry Run Environment Setup

1. Start with a running local node and make note of Algod's port number (for our [standard sandbox](https://github.com/algorand/sandbox) this is `4001`)
2. Set the `ALGOD_PORT` value in [x/testnet.py](https://github.com/algorand/py-algorand-sdk/blob/5faf79ddb56327a0e036ff4e21a39b52535751ae/x/testnet.py#L6) to this port number. (The port is set to `60000` by default because [SDK-testing](https://github.com/algorand/algorand-sdk-testing) bootstraps with this setting on Circle and also to avoid conflicting locally with the typical sandbox setup)

### TEAL Program for Testing: Logic Sig v. App

3. Next, you'll need to figure out if your TEAL program should be a Logic Signature or an Application. Each of these program _modes_ has its merits, but I won't get into the pros/cons here. From a Blackbox Test's perspective, the main difference is how each receives its arguments from the program executor. Logic sigs rely on the [arg opcode](https://developer.algorand.org/docs/get-details/dapps/avm/teal/opcodes/#arg-n) while apps rely on [txna ApplicationArgs i](https://developer.algorand.org/docs/get-details/dapps/avm/teal/opcodes/#txna-f-i). In our $`x^2`$ **logic sig** example, you can see on [line 2](https://github.com/algorand/py-algorand-sdk/blob/23c21170cfb19652d5da854e499dca47eabb20e8/x/blackbox/teal/lsig_square.teal#L2) that the `arg` opcode is used. Because argument each opcode (`arg` versus `ApplicationArgs`) is exclusive to one mode, any program that takes input will execute succesfully in _one mode only_.
4. Save the TEAL program you want to test. You can inline them in your test or follow the approach of `x/blackbox/blackbox_test.py` and save in `x/blackbox/teal`

### The TEAL Blackbox Toolkit

The TEAL Blackbox Toolkit comes with the following utility classes:

* `DryRunExecutor` - facility to execute dry run's for apps and logic sigs
* `DryRunTransactionResult` - class encapsulating a single app or logic sig dry run transaction and for making assertions about the dry run
* `SequenceAssertion` - class for asserting invariants about a _sequence_ of dry run executions

### Basic Assertions

When executing a dry run using  `DryRunExecutor` you'll get back `DryRunTransactionResult` objects. Such objects have
**assertable properties** that can be used to validate the dry run.

4. Back to our $`x^2`$ example, assume you have a variable `teal` containing the TEAL source as a string. You can run the following:

```python
algod = get_algod()
x = 9
args = (x,)
dryrun_result = DryRunExecutor.dryrun_app(algod, teal, args)
assert dryrun_result.status() == "PASS"
assert dryrun_result.stack_stop() == x ** 2
```

Some of the main available _assertable properties_ are:

* `stack_top()`
* `last_log()`
* `cost()`
* `status()`
* `final_scratch()`
* `error()`
* `max_stack_height()`

See the [DryRunTransactionResult class comment](https://github.com/algorand/py-algorand-sdk/blob/b2a3366b7bc976e0610429c186b7968a7f1bbc76/algosdk/testing/teal_blackbox.py#L371) for more assertable properties and details.

### Printing out the Stack Trace for a Failing Assertion

The `DryRunTransactionResult.report()` method lets you print out
a handy report in the case of a failing assertion. Let's intentionally break the test case above by claiming that 
$`x^2 == x^3`$ for $`x=2`$ and print out this `report()` when our silly assertion fails:

```python
algod = get_algod()
x = 2
args = (x,)
dryrun_result = DryRunExecutor.dryrun_app(algod, teal, args)
assert dryrun_result.status() == "PASS", dryrun_result.report(args, f"expected PASS but got {dryrun_result.status()}")
assert dryrun_result.stack_stop() == x ** 3, f"expected {x ** 3} but got {dryrun_result.stack_stop()}"
```

If we run the test we'll get the following printout (this is for pytest, but other testing frameworks should be similar):
```sh
E               AssertionError: ===============
E               <<<<<<<<<<<expected 8 but got 4>>>>>>>>>>>>>
E               ===============
E               App Trace:
E                  step |   PC# |   L# | Teal              | Scratch   | Stack
E               --------+-------+------+-------------------+-----------+----------------------
E                     1 |     1 |    1 | #pragma version 6 |           | []
E                     2 |     2 |    2 | arg_0             |           | [0x0000000000000002]
E                     3 |     3 |    3 | btoi              |           | [2]
E                     4 |     7 |    6 | label1:           |           | [2]
E                     5 |     9 |    7 | store 0           | 0->2      | []
E                     6 |    11 |    8 | load 0            |           | [2]
E                     7 |    13 |    9 | pushint 2         |           | [2, 2]
E                     8 |    14 |   10 | exp               |           | [4]
E                     9 |     6 |    4 | callsub label1    |           | [4]
E                    10 |    15 |   11 | retsub            |           | [4]
E               ===============
E               MODE: Mode.Signature
E               TOTAL COST: None
E               ===============
E               FINAL MESSAGE: PASS
E               ===============
E               Messages: ['PASS']
E               Logs: []
E               ===============
E               -----BlackBoxResult(steps_executed=10)-----
E               TOTAL STEPS: 10
E               FINAL STACK: [4]
E               FINAL STACK TOP: 4
E               MAX STACK HEIGHT: 2
E               FINAL SCRATCH: {0: 2}
E               SLOTS USED: [0]
E               FINAL AS ROW: {'steps': 10, ' top_of_stack': 4, 'max_stack_height': 2, 's@000': 2}
E               ===============
E               Global Delta:
E               []
E               ===============
E               Local Delta:
E               []
E               ===============
E               TXN AS ROW: {' Run': 3, ' cost': None, ' final_log': None, ' final_message': 'PASS', ' Status': 'PASS', 'steps': 10, ' top_of_stack': 4, 'max_stack_height': 2, 's@000': 2, 'Arg_00': 2}
E               ===============
E               <<<<<<<<<<<expected 8 but got 4>>>>>>>>>>>>>
E               ===============
```

In particular, we can:

* Track the program execution by viewing its **App Trace**
  * 2 was assigned to **scratch slot #0** at step 5
  * the stack ended up with **4** on top
  * the run **PASS**'ed
* Read the message that was passed and explains in English what went wrong: `<<<<<<<<<<<expected 8 but got 4>>>>>>>>>>>>>`

### EDRA: Exploratory Dry Run Analysis

Let's expand our investigation from a single dry-run to to multiple runs or a **run sequence**. In other words, given a sequence of inputs, observe _assertable properties_ for the corresponding
executions, and conjecture some program invariants. To aid in the investigation 
we'll generate a report in CSV format (Comma Separated Values) where:

* columns represent _assertable properties_ of dry-runs, and
* rows represents dry-run executions for specific inputs

5. Back to our $`x^2`$ example, here's how to generate a report with 1 row for each of the inputs `0, 1, ... , 15`: 

```python
algod = get_algod()
inputs = [(x,) for x in range(16)]
dryrun_results = DryRunExecutor.dryrun_logicsig_on_sequence(algod, teal, inputs)
csv = DryRunTransactionResult.csv_report(inputs, dryrun_results)
print(csv)
```

Note: that each element in the `inputs` array `(x,)` is itself a tuple as `args` given to a dry run execution need to be `Iterable` (remember, that these will be passed to a TEAL program which may take one, several, or no inputs at all).
At this point, you'll be able to look at your [dry run sequence results](https://github.com/algorand/py-algorand-sdk/blob/1bc7b8fcf21401608cece65507c36d1f6dbad531/algosdk/testing/teal_blackbox.py#L713) and conduct some analysis. For the $`x^2`$ example if you load the CSV in Google sheets and reformat a bit it will look like:

<img width="465" alt="image" src="https://user-images.githubusercontent.com/291133/158812699-318169e2-487c-4dac-b97b-a9db8148b638.png">

Perusing the above, it looks right: 

* column `D` **Arg 00** has the input $`x`$ (it's the argument at index 0)
* column `A` contains the **Run** number
* column `E`  **top of stack** does indeed store $`x^2`$ at the end of the calculation
* column `B` **Status** of each runs **PASS**es _except for **Run 1** with **Arg 00** = 0_. (The first run **REJECT**s because $`0^2 = 0`$ and TEAL programs reject when the top of the stack is 0)
* column `G` shows scratch slot **s@000** which stores the value of $`x`$ (except for the case $`x = 0`$ in which appears empty; in fact, slots always default to the zero value and an **<a name="0val-artifact">artifact</a>** of dry-runs is that they do not report when 0-values get stored into previously empty slots as no state change actually occurs)
* column `F` **max stack height** is always 2. The final obervation makes sense because there is no branching or looping in the program.

6. We can re-cast these observed effects in `Columns E, B, G, F` as **program invariant conjectures** written in Python as follows:

* `dryrun_result.stack_top() == x ** 2`
* `dryrun_result.max_stack_height() == 2`
* `dryrun_result.status() == ("REJECT" if x == 0 else "PASS")`
* `dryrun_result.final_scratch() == ({} if x == 0 else {0: x})`


### Advanced: Asserting Invariants on a Dry Run Sequence

The final and most advanced topic of this Howto is to turn _program invariant conjections_ into
**sequence assertions**. That is, let's take the information we gleaned in our EDRA CSV report, 
and create an integration test out of it. There are two ways to achieve this goal:

* Procedural sequence assertions
* Declarative sequence assertions

#### Procedural Blackbox Dry Run Sequence Assertions

7. The procedural approach takes the _program invariant conjectures_ and simply asserts them 
inside of a for loop that iterates over the inputs and dry runs. One can call each dry run
execution independently, or use  `DryRunExecutor` convenience methods `dryrun_app_on_sequence()` and
`dryrun_logicsig_on_sequence()`. For example, let's assert that the above invariants hold for all
$`x \leq 100`$:

```python
algod = get_algod()
inputs = [(x,) for x in range(100)]
dryrun_results = DryRunExecutor.dryrun_logicsig_on_sequence(algod, teal, inputs)
for i, dryrun_result in enumerate(dryrun_results):
    args = inputs[i]
    x = args[0]
    assert dryrun_result.stack_top() == x ** 2
    assert dryrun_result.max_stack_height() == 2
    assert dryrun_result.status() == ("REJECT" if x == 0 else "PASS")
    assert dryrun_result.final_scratch() == ({} if x == 0 else {0: x})
```

#### Declarative Blackbox Dry Run Sequence Assertions

8. The TEAL Blackbox Toolkit also allows for declarative style test writing. 
Let's look at some sample assertions for our `lsig_square` TEAL program:

```python
    "lsig_square": {
        "inputs": [(i,) for i in range(100)],
        "assertions": {
            DRA.stackTop: lambda args: args[0] ** 2,
            DRA.maxStackHeight: 2,
            DRA.status: lambda i: "REJECT" if i[0] = 0 else "PASS",
            DRA.finalScratch: lambda args: ({} if args[0] else {0: args[0]}),
        },
    },
```

In the parlance of the TEAL Blackbox Toolkit, a set of such declarative assertions
is called a **test scenario**. Scenarios are dict's containing two keys `inputs` and `assertions` and follow [certain conventions](https://github.com/algorand/py-algorand-sdk/blob/3d3992ccc9b3758f28e68d2c00408d2e1363a3bb/algosdk/testing/teal_blackbox.py#L942). In particular:

* **inputs** are lists of tuples, each tuple representing the `args` to be fed into a single dry run execution
* **assertions** are dicts that map [DryRunProperty](https://github.com/algorand/py-algorand-sdk/blob/3d3992ccc9b3758f28e68d2c00408d2e1363a3bb/algosdk/testing/teal_blackbox.py#L20)'s to actual assertions
* here is an [live example scenario](https://github.com/algorand/py-algorand-sdk/blob/c6e91b86acf545b66a94d27581d6cfa6318206fc/x/blackbox/blackbox_test.py#L442) for $`x^2`$


In English, letting $`x`$ be the input variable for our square function, the above **test scenario**:

* provides a list of 100 tuples of the form $`(x)`$ that will serve as args.
  * IE: $`(0), (1), (2), ... , (99)`$
* establishes 4 different _sequence assertions_ as follows:
  * the **stack's top** will contain $`x^2`$
  * the **max stack height** during execution is always 2
  * the executions' **status** is **PASS** except for the case $`x=0`$
  * the **final scratch** will have $`x`$ stored at slot `0` except for that strange $`x=0`$ case (recall the [0-val scratch slot artifact](#0val-artifact))
  

## Slow and Bad Fibonacci - Another Example Report

[This](https://docs.google.com/spreadsheets/d/1ax-jQdYCkKT61Z6SPeGm5BqAMybgkWJa-Dv0yVjgFSA/edit?usp=sharing) is an example of `app_slow_fibonacci.teal`'s Dryrun stats:
<img width="1231" alt="image" src="https://user-images.githubusercontent.com/291133/158705149-302d755f-afcc-4380-976a-ca14800c138f.png">
A few items to take note of:

* the app was **REJECT**ed for `n = 0` because `fibonacci(0) == 0` is left at the top of the stack
* the app was **REJECT**ed for `n > 7` because of exceeding budget
* the app **errored** only for `n > 16` because of exceeding _dynamic_ budget
* the **cost** is growing exponentially (bad algorithm design)
* the **top of stack** contains the `fibonacci(n)` except in the error case
* the **final_log** contains `hex(fibonacci(n))` except in the error and reject cases
* `n` is given by **Arg_00**
* **max stack height** `= 2*n` except for `n=0` and the error case
* you can see the final values of scratch slots **s@000** and **s@001**

## TODO's (not in this PR)

* handle statefulness and non-determinism

## FORMERLY TODO's

* [x]  Figure out how to integrate this (if at all) with the existing [DryRunContext](https://github.com/algorand/py-algorand-sdk/blob/develop/algosdk/testing/dryrun.py#L45). See usage examples [here](https://github.com/algorand/docs/blob/bbd379df193399f82686e9f6d5c2bcb9d676d2d7/docs/features/asc1/teal_test.md#basic-setup-and-simple-tests)
  * **UPSHOT**: ditches DryRunContext. It's too heavy.
* [x]  Allow CSV outputs?
  * **UPSHOT**: yes!
* [x]  Don't require logic sigs?
  * **UPSHOT**: yes, not needed. However, the ability to _test_ logic sigs is crucial, and so logic-sigs are considered as first-class citizens.
* [x]  See if we can simplify the roundtrips using the approach taken in PytealUtils:
  * [assert_output](https://github.com/algorand/pyteal-utils/blob/main/pytealutils/strings/test_string.py#L17)
  * [execute_app](https://github.com/algorand/pyteal-utils/blob/550b998e33985896607512992aef0e9c53680ea9/tests/helpers.py#L312)
  * [get_stats_from_dryrun](https://github.com/algorand/pyteal-utils/blob/550b998e33985896607512992aef0e9c53680ea9/tests/helpers.py#L360)
  * **UPSHOT**: no round trips at all