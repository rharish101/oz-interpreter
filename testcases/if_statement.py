from ozi import Ident, Literal

ast = [
    "var",
    Ident("x"),
    [
        "var",
        Ident("c"),
        [
            "var",
            Ident("y"),
            [
                ["bind", Ident("c"), Literal(False)],
                ["bind", Ident("x"), Literal(10)],
                [
                    "conditional",
                    Ident("c"),
                    ["bind", Ident("y"), Literal(30)],
                    ["bind", Ident("y"), Literal(40)],
                ],
            ],
        ],
    ],
]
