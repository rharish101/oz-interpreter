"""Testcase for infinitely-recursive Oz records."""
from ozi import Ident, Literal

ast = [
    [
        "var",
        Ident("x"),
        [
            "var",
            Ident("y"),
            [
                [
                    "bind",
                    Ident("x"),
                    (
                        "record",
                        Literal("|"),
                        [
                            (Literal("1"), Literal(1)),
                            (Literal("2"), Ident("y")),
                        ],
                    ),
                ],
                [
                    "bind",
                    Ident("y"),
                    (
                        "record",
                        Literal("|"),
                        [
                            (Literal("1"), Literal(1)),
                            (Literal("2"), Ident("x")),
                        ],
                    ),
                ],
                ["bind", Ident("x"), Ident("y")],
            ],
        ],
    ]
]
