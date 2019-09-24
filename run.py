#!/usr/bin/env python3
"""Run the Oz interpreter on input."""
import logging
from argparse import ArgumentParser

from ozi import Interpreter

# TODO: Create a parser for the Oz input syntax
INPUT = [
    [
        "var",
        ("ident", "x"),
        [
            [
                "var",
                ("ident", "y"),
                [
                    [
                        "bind",
                        ("ident", "x"),
                        (
                            "record",
                            ("literal", "|"),
                            [
                                (("literal", 1), ("literal", 1)),
                                (("literal", 2), ("ident", "y")),
                            ],
                        ),
                    ],
                    [
                        "bind",
                        ("ident", "y"),
                        (
                            "record",
                            ("literal", "|"),
                            [
                                (("literal", 1), ("literal", 1)),
                                (("literal", 2), ("ident", "x")),
                            ],
                        ),
                    ],
                    ["bind", ("ident", "x"), ("ident", "y")],
                ],
            ],
            [
                "var",
                ("ident", "f"),
                [
                    "bind",
                    ("ident", "f"),
                    (
                        "proc",
                        [("ident", "y")],
                        ["bind", ("ident", "x"), ("ident", "y")],
                    ),
                ],
            ],
        ],
    ]
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
    parser = ArgumentParser(description="Run the Oz interpreter on input")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="view some verbose output"
    )
    parser.add_argument(
        "-d", "--debug", action="store_true", help="view logging output"
    )
    main(parser.parse_args())
