from ozi import Ident, Literal

# procedures inside procedure
ast = (
    [
        "var",
        Ident("x"),
        [
            "var",
            Ident("p1"),
            [
                [
                    "bind",
                    Ident("p1"),
                    [
                        "proc",
                        [Ident("y")],
                        [
                            "var",
                            Ident("p2"),
                            [
                                [
                                    "bind",
                                    Ident("p2"),
                                    [
                                        "proc",
                                        [Ident("z")],
                                        [
                                            "conditional",
                                            Ident("z"),
                                            [
                                                "bind",
                                                Ident("y"),
                                                ["product", Ident("x"), Ident("x")],
                                            ],
                                            ["bind", Ident("x"), Ident("z")],
                                        ],
                                    ],
                                ],
                                [
                                    "var",
                                    Ident("w"),
                                    [
                                        ["bind", Ident("w"), Literal(True)],
                                        ["apply", Ident("p2"), Ident("w")],
                                    ],
                                ],
                            ],
                        ],
                    ],
                ],
                ["bind", Ident("x"), Literal(10)],
                ["var", Ident("x"), ["apply", Ident("p1"), Ident("x")]],
            ],
        ],
    ],
)

"""
local X in
    local P1 in
      P1=proc{$ Y}
          local P2 in
            P2=proc{$ Z}
                if Z then Y=X*X
                else X=Z  end
               end
            local W in
              W=true
              {P2 W}
            end
          end
         end
      X=10
      local X in
        {P1 X}
      end
    end
  end
"""
