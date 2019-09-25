"""Testcase for arithmetic."""
from ozi import Ident, Literal

ast = [
    "var",
    Ident("x"),
    [
        ["bind", Ident("x"), Literal(1)],
        [
            "var",
            Ident("y"),
            [
                ["bind", Ident("y"), ["sum", Literal(2), Ident("x")]],
                ["bind", Ident("y"), ["sum", Literal(3), Literal(0)]],
                [
                    "var",
                    Ident("z"),
                    ["bind", Ident("z"), ["product", Ident("y"), Ident("x")]],
                ],
            ],
        ],
    ],
]
