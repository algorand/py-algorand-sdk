# TEAL Blackbox: Program Reporting and Testing via Dry Runs

**NOTE: to get math formulas to render here using Chrome, add the [xhub extension](https://chrome.google.com/webstore/detail/xhub/anidddebgkllnnnnjfkmjcaallemhjee/related) to chrome and reload the page**

## TLDR; Dry Run Singleton Apps/LogicSigs, View Stats, and make Assertions on Behavior

### Trying out the new test:
```sh
$ pytest x/blackbox/blackbox_test.py 
```

## Example Usage
Suppose you have a [TEAL program](https://github.com/algorand/py-algorand-sdk/blob/23c21170cfb19652d5da854e499dca47eabb20e8/x/blackbox/teal/lsig_square.teal) that purportedly computes $`x^2`$. You'd like to write some unit tests to validate that it computes what you think it should, and also make **assertions** regarding:
* the total program cost
* the contents at the stack's top at the end of execution
* the maximum height of the stack during evaluation
* the contents of the scratch variables at the end
* the contents of the final log message (this is especially useful for [ABI-compliant programs](https://developer.algorand.org/docs/get-details/dapps/smart-contracts/ABI/))
* the status of the program (**PASS**, **REJECT** or _erroring_)
* error conditions that are and are not encountered

Even better, before making assertions, you'd like to get a sense of what the program is doing on a large set of inputs so you can come up with reasonable assertions.  The pattern for TEAL Blackbox testing that is provided in this PR suggests following a 2-part process:

### Part 1. Dryrun Setup and Reporting
1. Start with a running local node and make note of Algod's port number (for our [standard sandbox](https://github.com/algorand/sandbox) this is `4001`)
2. Set the `ALGOD_PORT` value in [x/testnet.py](https://github.com/algorand/py-algorand-sdk/blob/7977ed80c0d3b77fc6d6fdd5a640181eb0f65f21/x/testnet.py#L6) to this port number. (The port is set to `60000` by default because [SDK-testing](https://github.com/algorand/algorand-sdk-testing) bootstraps with this setting on Circle and also to avoid conflicting with the typical local sandbox setup)
3. Next, you'll need to figure out if your TEAL program should be a Logic Sig or an Application. Each have their merits, and I won't get into that here. But from a Blackbox test's perspective, the main difference is how each receive arguments. Logic sigs rely on the [arg opcode](https://developer.algorand.org/docs/get-details/dapps/avm/teal/opcodes/#arg-n) while apps rely on [txna ApplicationArgs i](https://developer.algorand.org/docs/get-details/dapps/avm/teal/opcodes/#txna-f-i). In our $`x^2`$ **logic sig** example, you can see on [line 2](https://github.com/algorand/py-algorand-sdk/blob/23c21170cfb19652d5da854e499dca47eabb20e8/x/blackbox/teal/lsig_square.teal#L2) that the `arg` opcode is used.
4. Save the TEAL program you want to test. In this PR, TEAL's are located under `x/blackbox/teal/`. (You could also inline them in your test)
5. Provide a test definition for the TEAL source. In the parlance of this PR, this is called a **test scenario**. Scenarios are dict's containing two keys `inputs` and `assertions` which follow [certain conventions](https://github.com/algorand/py-algorand-sdk/blob/350ba0c158e9bcadd7347b0907c53c6e9bf7c9be/algosdk/testing/teal_blackbox.py#L312). In particular:
  * **inputs** are lists of tuples, each tuple representing the `args` to be fed into a single dry run execution
  *  **assertions** are dicts that map [DryRunAsssertionType](https://github.com/algorand/py-algorand-sdk/blob/350ba0c158e9bcadd7347b0907c53c6e9bf7c9be/algosdk/testing/teal_blackbox.py#L14)'s to actual assertions
  * here is an [example such scenario](https://github.com/algorand/py-algorand-sdk/blob/20de2cd2e98409cf89a5f3208833db1564c266f6/x/blackbox/blackbox_test.py#L314) for $`x^2`$
  * **NOTE**: assertions are ***totally optional*** for this example. Omitting them will skip specific assertions at the end but still attempt the dry run sequence and CSV report generation
6. Now you're ready to generate a report from your scenario for analysis purposes. You can see the [test_logicsig_with_report()](https://github.com/algorand/py-algorand-sdk/blob/20de2cd2e98409cf89a5f3208833db1564c266f6/x/blackbox/blackbox_test.py#L424) unit test as an example. In particular:
 * `# 0.` validates the scenarios and digs out `inputs` and `assertions` using `get_blackbox_scenario_components()`
 * `# 1.` reads the TEAL source
 * `# 2.` builds up a sequence of dry run requests by applying `DryRunHelper.build_simple_logicsig_request` to the `inputs`
 * `# 3.` run `algod.dryrun` on the sequence obtaining the responses vector `dryrun_resps`
 * `# 4.` generate the comma separated report for the dry run sequence using `csv_from_dryruns()`, and save it to `csvpath`

**NOTE:** similar logic is used for tesing apps instead of logic sigs, but you would use:
* `DryRunHelper.build_simple_app_request` (instead of `DryRunHelper.build_simple_logicsig_request`)

At this point, you'll be able to look at your dry run sequence results and conduct some analysis. For the $`x^2`$ example if you load the CSV in google sheets and reformat a bit it will look like:
<img width="465" alt="image" src="https://user-images.githubusercontent.com/291133/158812699-318169e2-487c-4dac-b97b-a9db8148b638.png">

Perusing the above, it looks right. In particular, the top of the stack does indeed store $`x^2`$ at the end of the calculation. Each of the runs _except for **Run 1** with **Arg 00** = 0_ **PASS**es. The first run **REJECT**s because $`0^2 = 0`$ and TEAL programs reject when the top of the stack is 0.

### Part 2. Making Assertions

Now that we're satisfied with the results, we'd like to make some assertions. For example, this would be useful if you are planning to tweak or optimize the TEAL source and want to ensure that no regressions will occur, or if you want make assertions on an even bigger set of inputs that can't be readily eyeballed in a spreadsheet. Or you may be a practitioner of TTDD (TEAL Test Driven Development), in which case, beginning with some such assertions is crucial before you even write a single line of TEAL.

Let's look at some sample assertions for our `lsig_square` TEAL program:
```python
    "lsig_square": {
        "inputs": [(i,) for i in range(100)],
        "assertions": {
            DRA.finalScratch: lambda args: ({0: args[0]} if args[0] else {}),
            DRA.stackTop: lambda args: args[0] ** 2,
            DRA.maxStackHeight: 2,
            DRA.status: lambda i: "PASS" if i[0] > 0 else "REJECT",
            DRA.passed: lambda i: i[0] > 0,
            DRA.rejected: lambda i: i[0] == 0,
            DRA.noError: True,
        },
    },
```
In English, letting $`x`$ be the input variable for our square function, the above **test scenario**:
* provides a list of 100 tuples of the form $`(x)`$ that will serve as args. 
  * IE: $`(0), (1), (2), ... , (99)`$
* establishes 7 different _sequence assertions_ as follows:
  * the **final scratch** will have $`x`$ stored at slot `0` (except for the case $`x=0`$ which is an artificat of dryrun not producing any information on slots containing 0)
  * the **stack's top** will contain $`x^2`$
  * the **max stack height** during execution is always 2
  * the executions' **status** is **PASS** except for the case $`x=0`$
  * the runs all **passed** except for the case $`x=0`$
  * the runs **rejected** only for the case $`x=0`$
  * all the runs prodced **no error**'s
  
Let's continue on with [the unit test example](https://github.com/algorand/py-algorand-sdk/blob/20de2cd2e98409cf89a5f3208833db1564c266f6/x/blackbox/blackbox_test.py#L462). After generating the csv report, the test continues:
* `# 5. Sequential assertions`
Basically, now each assertion is picked up from the **test scenario**, some basic validations are done to ensure that the assertion makes sense for the program type, and the assertion then proceeds.

In the case that one of the assertions fails, an execution stack trace will be printed out. For example, let's break one of our assertions and see what happens:

```python
    "lsig_square": {
        "inputs": [(i,) for i in range(100)],
        "assertions": {
            ... same as before, but let's assert x^3 instead of x^2:
            DRA.stackTop: lambda args: args[0] ** 3,
            ... others same as before ...
        },
    },
```

If we run the test we'll get the following at the top
```sh
❯ pytest x/blackbox/blackbox_test.py

=============================================================================================== test session starts ===============================================================================================
platform darwin -- Python 3.9.10, pytest-6.2.5, py-1.11.0, pluggy-1.0.0
rootdir: /Users/zeph/github/algorand/py-algorand-sdk
plugins: typeguard-2.13.3
collected 14 items                                                                                                                                                                                                

x/blackbox/blackbox_test.py .........F....```
```
so we can see that we have a failure. The main details look like:

```sh
E               AssertionError: ===============
E               <<<<<<<<<<<SequenceAssertion for 'lsig_square[1]@Mode.Signature-DryRunAssertionType.stackTop' failed for for args (2,): actual is [4] BUT expected [8]>>>>>>>>>>>>>
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
E               <<<<<<<<<<<SequenceAssertion for 'lsig_square[1]@Mode.Signature-DryRunAssertionType.stackTop' failed for for args (2,): actual is [4] BUT expected [8]>>>>>>>>>>>>>
E               ===============

algosdk/testing/teal_blackbox.py:681: AssertionError
```
In particular, we can:
* Track the program execution by viewing its **App Trace**
  * 2 was assigned to **scratch slot #0** at step 5
  * the stack ended up with **4** on top
  * the run **PASS**'ed
* Read exactly what was expected versus what actually occurred:
```plain
SequenceAssertion for 'lsig_square[1]@Mode.Signature-DryRunAssertionType.stackTop' failed for for args (2,): actual is [4] BUT expected [8]
                       ^^^^^^^^^^^                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^                 ^^^^^^^^^             ^                ^
                       test case that failed         assertion type that was violated             the failing input     actual output    expected output
```

## Another Example Report
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

- [x]  Figure out how to integrate this (if at all) with the existing [DryRunContext](https://github.com/algorand/py-algorand-sdk/blob/develop/algosdk/testing/dryrun.py#L45). See usage examples [here](https://github.com/algorand/docs/blob/bbd379df193399f82686e9f6d5c2bcb9d676d2d7/docs/features/asc1/teal_test.md#basic-setup-and-simple-tests)
  * **UPSHOT**: ditches DryRunContext. It's too heavy.
- [x]  Allow CSV outputs?
  * **UPSHOT**: yes!
- [x]  Don't require logic sigs?
  * **UPSHOT**: yes, not needed. However, the ability to _test_ logic sigs is crucial, and so logic-sigs are considered as first-class citizens.
- [x]  See if we can simplify the roundtrips using the approach taken in PytealUtils:
  * [assert_output](https://github.com/algorand/pyteal-utils/blob/main/pytealutils/strings/test_string.py#L17)
  * [execute_app](https://github.com/algorand/pyteal-utils/blob/550b998e33985896607512992aef0e9c53680ea9/tests/helpers.py#L312)
  * [get_stats_from_dryrun](https://github.com/algorand/pyteal-utils/blob/550b998e33985896607512992aef0e9c53680ea9/tests/helpers.py#L360)
  * **UPSHOT**: no round trips at all