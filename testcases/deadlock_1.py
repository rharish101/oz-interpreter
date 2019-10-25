"""Testcase for arithmetic."""
from ozi import Ident, Literal

ast = [
    "var",
    Ident("x"),
    [   "var",
        Ident("y"),
        [
            "thread",
            [
                ["nop"],
                ["nop"],
                ["bind", Ident("x"), ["sum", Ident("y"), Literal(2)]],
            ],
        ],
        [        
            ["bind", Ident("y"), ["product", Ident("x"), Literal(3)]],
        ],
    ],
]
