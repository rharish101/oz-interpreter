#!/usr/bin/env python3
"""Run the Oz interpreter on input."""
import logging
from argparse import ArgumentParser
from sys import stderr

from ozi import Interpreter

INPUT = [
    [
        "var",
        ("ident", "x"),
        [["var", ("ident", "y"), ["var", ("ident", "x"), ["nop"]]], ["nop"]],
    ]
]


def main(args):
    """Run the main program.

    Arguments:
        args (`argparse.Namespace`): The object containing the commandline
            arguments

    """
    if args.debug:
        logging.basicConfig(stream=stderr, level=logging.DEBUG)

    interp = Interpreter()
    interp.run(INPUT)


if __name__ == "__main__":
    parser = ArgumentParser(description="Run the Oz interpreter on input")
    parser.add_argument(
        "-d", "--debug", action="store_true", help="view logging output"
    )
    main(parser.parse_args())