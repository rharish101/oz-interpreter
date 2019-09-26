from ozi import Ident, Literal

ast = (
    [
        "var",
        Ident("x"),
        [
            [
                "var",
                Ident("y"),
                [
                    "var",
                    Ident("d"),
                    [
                        ["bind", Ident("y"), Literal(2)],
                        ["bind", Ident("d"), Literal(3)],
                        [
                            "bind",
                            Ident("x"),
                            [
                                "proc",
                                [Ident("k"), Ident("a")],
                                [
                                    "conditional",
                                    Ident("k"),
                                    ["bind", Ident("a"), Ident("y")],
                                    ["bind", Ident("a"), Ident("d")],
                                ],
                            ],
                        ],
                    ],
                ],
            ],
            [
                "var",
                Ident("y"),
                [
                    "var",
                    Ident("b"),
                    [
                        ["bind", Ident("y"), Literal(True)],
                        ["apply", Ident("x"), Ident("y"), Ident("b")],
                    ],
                ],
            ],
        ],
    ],
)

# local X in
#    local Y in
#      local D in
#        Y=2
#        D=3
#        X=proc{$ K A}
#            if K then A=Y else A=D end
#          end
#      end
#    end
#    local Y in
#      local B in
#        Y=true
#        {X Y B}
#      end
#    end
