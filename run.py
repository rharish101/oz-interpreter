#!/usr/bin/env python3
"""Run the Oz interpreter on input."""
from ozi import Interpreter

INPUT = [["nop"], ["nop"], ["nop"]]

if __name__ == "__main__":
    interp = Interpreter()
    interp.run(INPUT)
