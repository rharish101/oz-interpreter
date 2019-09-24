"""Testcase for Oz procedures."""
from ozi import Ident, Literal

ast = [
    "var",
    Ident("x"),
    [
        "var",
        Ident("y"),
        [
            ["bind", Ident("y"), Literal("True")],
            [
                "var",
                Ident("f"),
                [
                    [
                        "bind",
                        (
                            "proc",
                            [Ident("x")],
                            ["bind", Ident("y"), Ident("x")],
                        ),
                        Ident("f"),
                    ],
                    ["apply", Ident("f"), Ident("x")],
                ],
            ],
        ],
    ],
]
