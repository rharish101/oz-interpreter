#!/usr/bin/env python3
"""Run the Oz interpreter on input."""
import logging
from argparse import ArgumentParser
from importlib import import_module

from ozi import Interpreter


def main(args):
    """Run the main program.

    Arguments:
        args (`argparse.Namespace`): The object containing the commandline
            arguments

    """
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    elif args.verbose:
        logging.basicConfig(level=logging.INFO)

    testcase = import_module(f"testcases.{args.testcase}")
    interp = Interpreter()
    interp.run(testcase.ast)


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Interpreter for the Oz kernel language's AST"
    )
    parser.add_argument(
        "testcase",
        metavar="TESTCASE",
        type=str,
        help="the name of the testcase",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="view some verbose output"
    )
    parser.add_argument(
        "-d", "--debug", action="store_true", help="view logging output"
    )
    main(parser.parse_args())
