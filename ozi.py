"""Interpreter for the Oz programming language."""
import logging
import random
import string
from copy import deepcopy
from pprint import pformat


class UnificationError(Exception):
    """Exception for unification errors."""


class Suspension(Exception):
    """Exception for interpreter suspension."""


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
            raise NotImplementedError(f"{value}")

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
            raise NotImplementedError(f"{value}")

        logging.debug(f"free vars of {value[0]}: {fvars}")
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

        elif stmt[0] == "conditional":
            fvars = {stmt[1][1]}
            fvars = fvars.union(self._get_fvars(stmt[2]))
            fvars = fvars.union(self._get_fvars(stmt[3]))

        elif stmt[0] == "match":
            fvars = {stmt[1][1]}
            fvars = fvars.union(self._get_fvars(stmt[4]))
            fvars = fvars.union(
                self._get_fvars(stmt[3]).difference(self._get_fvars(stmt[2]))
            )

        elif stmt[0] == "apply":
            fvars = {ident[1] for ident in stmt[1:]}

        else:
            raise NotImplementedError(f"{stmt}")

        logging.debug(f"free vars of {stmt[0]}: {fvars}")
        return fvars

    def _match_records(self, lhs, rhs):
        """Unify two records without recursion, and return their dict forms.

        This is used for unification with recursion, and also in pattern
        matching.

        Args:
            lhs (tuple): The first record value
            rhs (tuple): The second record value

        Returns:
            dict: The dictionary representation of the first record
            dict: The dictionary representation of the second record

        """
        if lhs[0] != "record" or rhs[0] != "record":
            raise TypeError("Input arguments are not records")

        if lhs[1] != rhs[1]:
            raise UnificationError("Record literals do not match")

        elif len(lhs[2]) != len(rhs[2]):
            raise UnificationError("Record arities do not match")

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
                raise UnificationError("Record features do not match")
            else:
                return lhs_record, rhs_record

    def _unify_vars(self, env, lhs, rhs):
        """Unify two variables."""
        eq_classes = []
        sas_vars = []

        for oper in [lhs, rhs]:
            if oper[0] == "ident":
                sas_vars.append(env[oper[1]])
                eq_classes.append(self.sas[env[oper[1]]])
            else:  # SAS variable
                sas_vars.append(oper[1])
                eq_classes.append(self.sas[oper[1]])

        class1, class2 = eq_classes
        logging.debug(f"unifying: {sas_vars[0]} & {sas_vars[1]}")

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
                logging.debug("marking both as unified before check")
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
        logging.debug(f"unifying {lhs} and {rhs}")

        if lhs[0] != rhs[0]:
            raise TypeError("Values are not of the same type")

        if lhs[0] == "proc":  # procedure values
            raise UnificationError("Procedures cannot match")

        if lhs[0] == "literal" and lhs[1] != rhs[1]:  # numeric values
            raise UnificationError("Numeric values do not match")

        elif lhs[0] == "record":
            lhs_record, rhs_record = self._match_records(lhs, rhs)
            for key in lhs_record:
                self._unify(env, lhs_record[key], rhs_record[key])

    def _unify(self, env, lhs, rhs):
        """Unify both input variables/values."""
        var_check = {"ident", "variable"}

        if lhs[0] in var_check and rhs[0] in var_check:  # <x> = <y>
            self._unify_vars(env, lhs, rhs)

        elif lhs[0] in var_check or rhs[0] in var_check:  # <x> = <v>
            # Input can be either `<x> = <v>` or `<v> = <x>`, so convert it
            # into `<x> = <v>`.
            if lhs[0] == "ident":
                var, value = env[lhs[1]], rhs
            elif lhs[0] == "variable":
                var, value = lhs[1], rhs
            elif rhs[0] == "ident":
                var, value = env[rhs[1]], lhs
            else:
                var, value = rhs[1], lhs

            value = self._compute(env, value)
            class1 = self.sas[var]
            logging.debug(f"unifying {var} and {value}")

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
        stack = [(ast, {})]  # initialize with empty environment

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

                # Avoid editing environments of other statements in the stack
                new_env = deepcopy(env)
                new_env[stmt[1][1]] = self._alloc_var()

                logging.debug(f"new env: {pformat(new_env)}")
                logging.debug(f"sas: {pformat(self.sas)}")
                stack.append((stmt[2], new_env))

            elif stmt[0] == "bind":
                logging.info(f"binding lhs: {stmt[1]} & rhs: {stmt[2]}")
                logging.debug(f"env: {pformat(env)}")
                logging.debug(f"sas before: {pformat(self.sas)}")
                self._unify(env, stmt[1], stmt[2])
                logging.debug(f"sas after: {pformat(self.sas)}")

            elif stmt[0] == "conditional":
                ident = stmt[1][1]
                logging.info(f"if-else on: {ident}")
                eq_class = self.sas[env[ident]]
                if eq_class.is_bound():
                    value = eq_class.value
                    if value[0] != "literal" or type(value[1]) is not bool:
                        raise TypeError(f"{ident} is not a boolean")
                    elif value[1]:
                        stack.append((stmt[2], env))
                    else:
                        stack.append((stmt[3], env))
                else:
                    raise Suspension(f"{ident} is unbound")

            elif stmt[0] == "match":
                ident = stmt[1][1]
                logging.info(f"case on: {ident}")
                eq_class = self.sas[env[ident]]

                if stmt[2][0] != "record":
                    raise TypeError(f"Invalid pattern: {stmt[2]}")

                elif eq_class.is_bound():
                    try:
                        value, pattern = self._match_records(
                            eq_class.value, stmt[2]
                        )

                    except (TypeError, UnificationError):
                        # Either not a record, or doesn't match
                        logging.debug(f"{ident} doesn't match pattern")
                        stack.append((stmt[4], env))

                    else:
                        logging.debug(f"{ident} matches pattern")

                        # Avoid editing environments of other statements in the
                        # stack.
                        new_env = deepcopy(env)
                        for feat, item in pattern.items():
                            if item[0] == "ident":
                                new_env[item[1]] = self._alloc_var()
                                self._unify(new_env, item, value[feat])
                        logging.debug(f"env for case: {pformat(new_env)}")

                        stack.append((stmt[3], new_env))

                else:
                    raise Suspension(f"{ident} is unbound")

            elif stmt[0] == "apply":
                ident = stmt[1][1]
                logging.info(f"calling: {ident}")
                eq_class = self.sas[env[ident]]

                if eq_class.is_bound():
                    value = eq_class.value
                    if value[0] != "proc":
                        raise TypeError(f"{ident} is not a procedure")

                    elif len(value[1]) != len(stmt) - 2:
                        raise TypeError(
                            f"No. of arguments do not match arity of {ident}"
                        )

                    else:
                        # Avoid editing the contextual environment by reference
                        new_env = deepcopy(value[3])
                        for arg, param in zip(value[1], stmt[2:]):
                            new_env[arg[1]] = env[param[1]]
                        logging.info(f"call env: {new_env}")
                        stack.append((value[2], new_env))

                else:
                    raise Suspension(f"{ident} is unbound")

            else:
                raise NotImplementedError(f"{stmt}")
