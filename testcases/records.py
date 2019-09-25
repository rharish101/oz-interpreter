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
                "var",
                Ident("z"),
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
                    [
                        "bind",
                        Ident("z"),
                        (
                            "record",
                            Literal("|"),
                            [
                                (Literal("1"), Literal(1)),
                                (Literal("2"), Ident("z")),
                            ],
                        ),
                    ],
                    ["bind", Ident("x"), Ident("y")],
                    ["bind", Ident("y"), Ident("z")],
                ],
            ],
        ],
    ]
]
