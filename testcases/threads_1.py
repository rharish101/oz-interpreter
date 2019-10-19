"""Testcase for arithmetic."""
from ozi import Ident, Literal

ast = [
    "var",
    Ident("x"),
    [
        [
            "thread",
            [
                ["nop"],
                ["nop"],
                ["bind", Ident("x"), ["sum", Literal(1), Literal(2)]],
            ],
        ],
        [
            "var",
            Ident("y"),
            ["bind", Ident("y"), ["product", Ident("x"), Literal(3)]],
        ],
    ],
]
