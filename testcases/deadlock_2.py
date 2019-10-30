"""Testcase for arithmetic."""
from ozi import Ident, Literal

ast = [
    "var",
    Ident("x"),
    [
        "var",
        Ident("y"),
        [
            ["thread", ["bind", Ident("x"), ["sum", Ident("y"), Literal(2)]]],
            ["thread", [["nop"], ["nop"], ["bind", Ident("x"), Literal(5)]]],
            ["bind", Ident("y"), ["product", Ident("x"), Literal(3)]],
        ],
    ],
]
