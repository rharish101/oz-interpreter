#!/usr/bin/env python3
"""Run the Oz interpreter on input."""
import logging
from argparse import ArgumentParser

from ozi import Ident, Interpreter, Literal

# TODO: Create a parser for the Oz input syntax
INPUT = [
    "var",
    Ident("x"),
    [
        "var",
        Ident("y"),
        [
            ["bind", Ident("y"), Literal(True)],
            [
                "var",
                Ident("f"),
                [
                    [
                        "bind",
                        [
                            "proc",
                            [Ident("x")],
                            ["bind", Ident("y"), Ident("x")],
                        ],
                        Ident("f"),
                    ],
                    ["apply", Ident("f"), Ident("x")],
                ],
            ],
        ],
    ],
]


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

    interp = Interpreter()
    interp.run(INPUT)


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Interpreter for the Oz kernel language"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="view some verbose output"
    )
    parser.add_argument(
        "-d", "--debug", action="store_true", help="view logging output"
    )
    main(parser.parse_args())
