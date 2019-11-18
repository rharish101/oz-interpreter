# CS350A Assignment 2 & 3

This is the repository for assignment 2 & 3 of CS350A: Principles of Programming Languages, offered in the odd semester of 2019.
The goal is to build an interpreter for the kernel language of the [Oz](https://mozart.github.io) programming language, given its AST.
This supports the declarative concurrent model (lazy execution is not supported).

## Group Members
* Harish Rajagopal (160552)
* Vishwas Lathi (160808)

## Requirements
* Python 3.6+

## Instructions
1. Change the current directory to the root of this repository.
2. Choose a test case from the "testcases" directory.
3. Run the interpreter as follows:
    ```sh
    ./run.py name_of_testcase
    ```

    For example, if you want to use the test case "testcases/conditionals\_1.py":
    ```sh
    ./run.py conditionals_1
    ```

## AST Specification
The AST for the kernel language is to be written in Python.

For variables and values, the translations from the Oz syntax into the Python AST spec is as follows:
* Variable `X`: `Ident("X")`.
    The name of the variable must be in quotes.
* Literal `10`: `Literal(10)`.
    The value of the literal is written as a Python value.
    eg. `true` is `Literal(True)`
* Record `tree(key:10 left:nil right:nil)`:
    ```python
    [
        "record",
        Literal("tree"),
        [
            (Literal("key"), Literal(10)),
            (Literal("left"), Literal(None)),
            (Literal("right"), Literal(None)),
        ],
    ]
    ```
* Procedure `proc {$ X Y} skip end`:
    ```python
    [
        "proc",
        [Ident("X"), Ident("Y")],
        ["nop"],
    ]
    ```

The statements allowed in the kernel language, and the format of its AST, are as follows:

| Statement | Oz | AST |
| -- | -- | -- |
| No-op | `skip` | `["nop"]` |
| Compound statements | `skip skip` | `[["nop"], ["nop"]]` |
| Variable creation | `local X in skip end` | `["var", Ident("X"), ["nop"]]` |
| Binding | `X = Y` | `["bind", Ident("X"), Ident("Y")]` |
| | `X = 5` | `["bind", Ident("X"), Literal(5)]` |
| If-else | `if X then skip else skip end` | `["conditional", Ident("X"), ["nop"], ["nop"]]` |
| Pattern matching | `case X of nil then skip else skip end` | `["match", Ident("X"), Literal(None), ["nop"], ["nop"]]` |
| Procedure call | `{F X Y}` | `["apply", Ident("F"), Ident("X"), Ident("Y")]`
| Thread | `thread skip end` | `["thread", ["nop"]]`

## Test Cases
There are 14 test cases, with 12 positive ones and 2 negative ones.
The description of these test cases is:

| Test Case | Type | Description | 
| -- | -- | -- |
| arithmetic | Positive | Sum and product arithmetic operations |
| case\_1 | Positive | Pattern matching for `X = 1|X` |
| case\_2 | Positive | Both positive and negative pattern matches |
| conditionals\_1 | Positive | Simple if-else |
| conditionals\_2 | Positive | Simple if-else |
| deadlock\_1 | Negative | Two variable definitions depending on each other's values |
| deadlock\_2 | Positive | Two consecutive suspended threads, waiting for a third (the main thread) |
| deadlock\_3 | Positive | Same as "deadlock\_2", but the main thread is among the suspended |
| deadlock\_4 | Negative | Same as "deadlock\_2", but the third thread doesn't solve the deadlock |
| nested\_proc | Positive | Procedure defined inside another procedure |
| procedures\_1 | Positive | Procedure with two free variables |
| procedures\_2 | Positive | Procedure with one free variable |
| records | Positive | Unification of X, Y and Z, where `X = 1|Y`, `Y = 1|X`, `Z = 1|Z` |
| threads | Positive | Main thread suspended and waiting for a child thread |

For running all of these tests at once:
1. Change the current directory to the root of this repository.
2. Run the testing script as follows:
    ```sh
    ./test.sh
    ```
