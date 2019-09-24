"""Testcase for Oz pattern matching."""
from ozi import Ident, Literal

ast = [
    "var",
    Ident("x"),
    [
        [
            "bind",
            Ident("x"),
            (
                "record",
                Literal("|"),
                [(Literal("1"), Literal("1")), (Literal("2"), Ident("x"))],
            ),
        ],
        [
            "match",
            Ident("x"),
            (
                "record",
                Literal("|"),
                [(Literal("1"), Ident("a")), (Literal("2"), Ident("b"))],
            ),
            ["bind", Ident("x"), Ident("b")],
            ["nop"],
        ],
    ],
]
