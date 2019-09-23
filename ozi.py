"""Interpreter for the Oz programming language."""
import logging
import random
import string


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

    # TODO: Run Oz operations on Oz "values"
    def _compute(self, value):
        """Compute the actual value of the given Oz "value"."""
        return value

    # TODO: Complete for all statement types and Oz values/operations
    def _get_free_vars(self, stmt):
        """Get the free variables for the given statement."""
        if stmt[0] == "nop":
            fvars = set()

        elif type(stmt[0]) is list:
            fvars = self._get_free_vars(stmt[0])
            for sub_stmt in stmt[1:]:
                fvars = fvars.union(self._get_free_vars(sub_stmt))

        elif stmt[0] == "var":
            fvars = self._get_free_vars(stmt[2])
            fvars.remove(stmt[1])

        elif stmt[0] == "bind":
            fvars = set()
            for oper in stmt[1:]:
                if oper[0] == "ident":
                    fvars.add(oper[1])
                else:
                    fvars = fvars.union(self._get_free_vars(oper))

        else:
            raise NotImplementedError

        return fvars

    def _merge_classes(self, class1, class2):
        """Merge two equivalence classes."""
        if class1 is not class2:
            if not class1.is_bound():
                # If the class2 class is bound, then this take its value, else
                # it stays unbound (as the class2 class's value is None)
                class1.value = class2.value
            elif class2.is_bound() and not self._equals(
                class1.value, class2.value
            ):
                raise UnificationError
            class1.vars = class1.vars.union(class2.vars)

            for ref in class2.vars:
                # All variables that map to the second equivalence class are to
                # be pointed to the merged equivalence class
                self.sas[ref] = class1
            del class2

    def _equals(self, lhs, rhs):
        """Perform unification on values."""
        if lhs[0] != rhs[0] or lhs[0] == "proc":
            return False

        elif lhs[0] == "record":
            # TODO: Recursive unification
            return False

        else:  # numeric values
            return lhs[1] == rhs[1]

    def _unify(self, env, lhs, rhs):
        """Unify both input variables/values."""
        if lhs[0] == "ident" and rhs[0] == "ident":  # <x> = <y>
            class1 = self.sas[env[lhs[1]]]
            class2 = self.sas[env[rhs[1]]]
            self._merge_classes(class1, class2)

        elif lhs[0] == "ident" or rhs[0] == "ident":  # <x> = <v>
            if lhs[0] == "ident":
                var, value = lhs[1], rhs
            else:
                var, value = rhs[1], lhs

            value = self._compute(value)
            class1 = self.sas[env[var]]

            if not class1.is_bound():
                class1.value = value
            elif not self._equals(class1.value, value):
                raise UnificationError

        else:
            if not self._equals(self._compute(lhs), self._compute(rhs)):
                raise UnificationError

    def _alloc_var(self, length=16):
        """Allocate a variable on the single-assignment store and return it."""
        while True:
            # Choose a random string made of ASCII alphanumeric characters of a
            # certain length
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
                env[stmt[1][1]] = new
                logging.debug(f"env: {env}")
                logging.debug(f"sas: {self.sas}")
                stack.append((stmt[2], env))

            elif stmt[0] == "bind":
                logging.info(f"binding lhs: {stmt[1]} & rhs: {stmt[2]}")
                logging.debug(f"env: {env}")
                logging.debug(f"sas before: {self.sas}")
                self._unify(env, stmt[1], stmt[2])
                logging.debug(f"sas after: {self.sas}")

            else:
                raise NotImplementedError
