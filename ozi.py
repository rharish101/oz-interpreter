"""Interpreter for the Oz programming language."""
import logging
import random
import string
from copy import deepcopy
from pprint import pformat


class UnificationError(Exception):
    """Exception for unification errors."""


class _EqClass:
    """Equivalence class for the single-assignment store."""

    def __init__(self, var):
        """Initialize the class with the given unbound variable."""
        self.vars = {var}
        self.value = None

    def __repr__(self):
        """Get a string representation for printing this equivalence class."""
        return f"{{value: {self.value}, vars: {self.vars}}}"

    def is_bound(self):
        """Return True if the variables in this class are bound to a value."""
        return self.value is not None


class Interpreter:
    """The Oz interpreter."""

    def __init__(self):
        """Initialize the single-assignment store."""
        self.sas = {}

    # TODO: Run Oz operations
    def _compute(self, env, value):
        """Compute the actual value of the given Oz "value"."""
        if value[0] in {"literal", "variable"}:
            return value

        elif value[0] == "ident":
            # Storing record values in the SAS which have variables inside them
            # should store the environment-mapped SAS variable instead of the
            # Oz identifier.
            return ("variable", env[value[1]])

        elif value[0] == "record":
            return (
                "record",
                value[1],
                [(feat, self._compute(env, val)) for feat, val in value[2]],
            )

        elif value[0] == "proc":
            fvars = self._get_fvars_value(value)
            ctx_env = {fvar: env[fvar] for fvar in fvars}
            return ("proc", value[1], value[2], ctx_env)

        else:  # Oz operations
            raise NotImplementedError

    # TODO: Complete for Oz operations
    def _get_fvars_value(self, value):
        """Get the free variables of an Oz variable or value/operation.

        NOTE: The input must not have been "computed" using `_compute`, as free
        variables of Oz operations are lost on computation.
        """
        if value[0] == "ident":
            fvars = {value[1]}

        elif value[0] == "literal":
            fvars = set()

        elif value[0] == "record":
            fvars = set()
            for _, sub_val in value[2]:
                fvars = fvars.union(self._get_fvars_value(sub_val))

        elif value[0] == "proc":
            args = {arg for _, arg in value[1]}
            fvars = self._get_fvars(value[2])
            fvars.difference_update(args)

        else:  # Oz operation
            raise NotImplementedError

        return fvars

    # TODO: Complete for all statement types
    def _get_fvars(self, stmt):
        """Get the free variables of the given statement."""
        if stmt[0] == "nop":
            fvars = set()

        elif type(stmt[0]) is list:
            fvars = set()
            for sub_stmt in stmt:
                fvars = fvars.union(self._get_fvars(sub_stmt))

        elif stmt[0] == "var":
            fvars = self._get_fvars(stmt[2])
            fvars.remove(stmt[1][1])

        elif stmt[0] == "bind":
            fvars = set()
            for oper in stmt[1:]:
                fvars = fvars.union(self._get_fvars_value(oper))

        else:
            print(stmt)
            raise NotImplementedError

        return fvars

    def _unify_vars(self, env, lhs, rhs):
        """Unify two variables."""
        eq_classes = []
        for oper in [lhs, rhs]:
            if oper[0] == "ident":
                eq_classes.append(self.sas[env[oper[1]]])
            else:  # SAS variable
                eq_classes.append(self.sas[oper[1]])
        class1, class2 = eq_classes

        if class1 is not class2:
            # Flag for unifying values after merging equivalence classes.
            unify_vals = False
            if not class1.is_bound():
                # If the class2 class is bound, then this take its value, else
                # it stays unbound (as the class2 class's value is None).
                class1.value = class2.value
            elif class2.is_bound():
                # Both variables are bound, so in order to prevent infinite
                # recursion in unification of record values, we need to unify
                # their values after merging their equivalence classes, which
                # marks the variables as unified.
                unify_vals = True
            class1.vars = class1.vars.union(class2.vars)

            for ref in class2.vars:
                # All variables that map to the second equivalence class are to
                # be pointed to the merged equivalence class.
                self.sas[ref] = class1

            if unify_vals:
                self._unify_values(env, class1.value, class2.value)
            del class2

    def _unify_values(self, env, lhs, rhs):
        """Unify two Oz values."""
        lhs = self._compute(env, lhs)
        rhs = self._compute(env, rhs)

        if (
            lhs[0] != rhs[0]
            or lhs[0] == "proc"  # procedure values
            or (lhs[0] == "literal" and lhs[1] != rhs[1])  # numeric values
        ):
            raise UnificationError

        elif lhs[0] == "record":
            if lhs[1] != rhs[1] or len(lhs[2]) != len(rhs[2]):
                raise UnificationError

            else:
                # Save into a record for matching record features
                # independent of the order of the feature declaration.
                lhs_record = {}
                rhs_record = {}
                for item in lhs[2]:
                    lhs_record[item[0]] = item[1]
                for item in rhs[2]:
                    rhs_record[item[0]] = item[1]

                if lhs_record.keys() != rhs_record.keys():
                    # Value returned by `dict.keys` acts like a set, so
                    # order doesn't matter.
                    raise UnificationError
                else:
                    for key in lhs_record:
                        self._unify(env, lhs_record[key], rhs_record[key])

    def _unify(self, env, lhs, rhs):
        """Unify both input variables/values."""
        if lhs[0] == "ident" and rhs[0] == "ident":  # <x> = <y>
            self._unify_vars(env, lhs, rhs)

        elif lhs[0] == "ident" or rhs[0] == "ident":  # <x> = <v>
            # Input can be either `<x> = <v>` or `<v> = <x>`, so convert it
            # into `<x> = <v>`.
            if lhs[0] == "ident":
                var, value = lhs[1], rhs
            else:
                var, value = rhs[1], lhs

            value = self._compute(env, value)
            class1 = self.sas[env[var]]

            if not class1.is_bound():
                class1.value = value
            else:
                self._unify(env, class1.value, value)

        else:  # <v> = <v>
            self._unify_values(env, lhs, rhs)

    def _alloc_var(self, length=16):
        """Allocate a variable on the single-assignment store and return it."""
        while True:
            # Choose a random string made of ASCII alphanumeric characters of a
            # certain length.
            new = "".join(
                random.choices(string.ascii_letters + string.digits, k=length)
            )
            if new not in self.sas:
                self.sas[new] = _EqClass(new)
                return new

    def run(self, ast):
        """Run the given Oz AST."""
        self.sas = {}  # clear the interpreter
        # Initialize with empty environments
        stack = [(stmt, {}) for stmt in reversed(ast)]

        # TODO: Complete for all statement types
        while len(stack) > 0:
            stmt, env = stack.pop()

            if stmt[0] == "nop":
                logging.info("skip statement")

            elif type(stmt[0]) is list:
                logging.info(
                    f"combined statement with {len(stmt)} sub-statements"
                )
                for sub_stmt in reversed(stmt):
                    stack.append((sub_stmt, env))

            elif stmt[0] == "var":
                logging.info(f"local statement with var: {stmt[1][1]}")
                new = self._alloc_var()

                # Avoid editing environments of other statements in the stack
                new_env = deepcopy(env)
                new_env[stmt[1][1]] = new

                logging.debug(f"new env: {pformat(new_env)}")
                logging.debug(f"sas: {pformat(self.sas)}")
                stack.append((stmt[2], new_env))

            elif stmt[0] == "bind":
                logging.info(f"binding lhs: {stmt[1]} & rhs: {stmt[2]}")
                logging.debug(f"env: {pformat(env)}")
                self._unify(env, stmt[1], stmt[2])
                logging.debug(f"sas after: {pformat(self.sas)}")

            else:
                raise NotImplementedError
