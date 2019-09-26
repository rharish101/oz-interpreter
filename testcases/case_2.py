"""Another testcase for Oz pattern matching."""
from ozi import Ident, Literal

# local X in
#     local Y in
#         X = map(name:10 2:14)
#         case X
#         of map(name:A 3:B) then
#             Y=10
#         else
#             case X
#             of map(name:C 2:D) then Y=20
#             else Y=30
#             end
#         end
#     end
# end

ast = [
    "var",
    Ident("x"),
    [
        "var",
        Ident("y"),
        [
            [
                "bind",
                Ident("x"),
                [
                    "record",
                    Literal("map"),
                    [
                        [Literal("name"), Literal(10)],
                        [Literal(2), Literal(14)],
                    ],
                ],
            ],
            [
                "match",
                Ident("x"),
                [
                    "record",
                    Literal("map"),
                    [[Literal("name"), Ident("a")], [Literal(3), Ident("b")]],
                ],
                ["bind", Ident("y"), Literal(10)],
                [
                    "match",
                    Ident("x"),
                    [
                        "record",
                        Literal("map"),
                        [
                            [Literal("name"), Ident("c")],
                            [Literal(2), Ident("d")],
                        ],
                    ],
                    ["bind", Ident("y"), Literal(20)],
                    ["bind", Ident("y"), Literal(30)],
                ],
            ],
        ],
    ],
]
