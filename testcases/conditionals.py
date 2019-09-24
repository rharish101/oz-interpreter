"""Testcase for Oz conditionals."""
from ozi import Ident, Literal

ast = [
    "var",
    Ident("x"),
    [
        "var",
        Ident("y"),
        [
            ["bind", Ident("x"), Literal(True)],
            [
                "conditional",
                Ident("x"),
                ["bind", Ident("y"), Literal("True")],
                ["nop"],
            ],
        ],
    ],
]
