"""Interpreter for the Oz programming language."""
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

    def is_bound(self):
        """Return True if the variables in this class are bound to a value."""
        return self.value is not None

    def get_refs(self):
        """Get the list of all variables/values in this equivalence class."""
        return self.vars.union({self.value})

    def merge(self, other):
        """Merge this equivalence class (in-place) with another."""
        if self.value is None:
            self.value = other.value
        elif other.value is not None and self.value != other.value:
            raise UnificationError
        self.vars = self.vars.union(other.vars)


class _Value:
    """Class for numeric values, records and procedures in Oz."""

    def __init__(self, kind, val):
        """Initialize the value."""
        self.kind = kind
        self.val = val

    def __eq__(self, other):
        """Perform unification on values."""
        if not isinstance(other, self.__class__):
            return False
        elif self.kind != other.kind():
            return False
        elif self.kind == "proc":
            return False
        elif self.kind == "record":
            # TODO: Recursive unification
            return False
        else:
            return self.val == other.val


class Interpreter:
    """The Oz interpreter."""

    def __init__(self):
        """Initialize the semantic stack and single-assignment store."""
        self.sas = {}
        self.stack = []

    # TODO: Run Oz operations on Oz "values"
    def _compute(self, value):
        """Compute the actual value of the given Oz "value"."""
        # TODO: This should return an instance of _Value
        return value

    # TODO:
    def _get_free_vars(self, ast):
        """Get the free variables for the given statement AST."""

    def _merge_classes(self, class1, class2):
        """Merge two equivalence classes."""
        if class1 is not class2:
            class1.merge(class2)
            for ref in class2.get_refs():
                self.sas[ref] = class1
            del class2

    def _unify(self, env, lhs, rhs):
        """Unify both input variables/values."""
        if lhs[0] == "ident" and rhs[0] == "ident":
            class1 = self.sas[env[lhs]]
            class2 = self.sas[env[rhs]]
            self._merge_classes(class1, class2)

        elif lhs[0] == "ident" or rhs[0] == "ident":
            if lhs[0] == "ident":
                var, val = lhs, rhs
            else:
                var, val = rhs, lhs

            val = self._compute(val)
            class1 = self.sas[env[var]]

            if class1.value is None:
                if val in self.sas:
                    class2 = self.sas[val]
                    self._merge_classes(class1, class2)
                else:
                    class1.value = val
                    self.sas[val] = class1

            elif class1.value != val:
                raise UnificationError

        else:
            if self._compute(lhs) != self._compute(rhs):
                raise UnificationError

    def _alloc_var(self, length=16):
        """Allocate a variable on the single-assignment store and return it."""
        while True:
            new = "".join(
                random.choices(string.ascii_letters + string.digits, k=length)
            )
            if new not in self.sas:
                self.sas[new] = _EqClass(new)
                return new

    def run(self, ast):
        """Run the given Oz AST."""
        # Clear the interpreter
        self.sas = {}
        self.stack = []

        # TODO:
        raise NotImplementedError
