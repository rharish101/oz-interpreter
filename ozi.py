"""Interpreter for the Oz kernel language's AST."""
import logging
from collections import namedtuple
from copy import deepcopy
from pprint import pformat
from queue import Queue

Literal = namedtuple("Literal", ["value"])
Ident = namedtuple("Identifier", ["name"])
Variable = namedtuple("Variable", ["name"])
Record = namedtuple("Record", ["literal", "fields"])
Proc = namedtuple("Procedure", ["args", "contents", "ctxenv"])


class UnificationError(Exception):
    """Exception for unification errors."""


class UnboundVariableError(Exception):
    """Exception for unbound variables."""

    def __init__(self, message, var):
        """Store the variable that is unbound."""
        super().__init__(message)
        self.var = var


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


class _Thread:
    """Class for threads with editable attributes."""

    def __init__(self, num, stack):
        """Create a thread."""
        self.num = num
        self.stack = stack
        self.suspension = None
        self.tick = 0

class Interpreter:
    """The Oz interpreter."""

    def __init__(self):
        """Initialize the single-assignment store."""
        self.sas = []

    def _compute(self, env, value):
        """Compute the actual value of the given Oz "value"."""
        if type(value) in {Literal, Variable, Record, Proc}:  # already done
            return value

        elif type(value) is Ident:
            # Storing record values in the SAS which have variables inside them
            # should store the environment-mapped SAS variable instead of the
            # Oz identifier.
            return Variable(env[value.name])

        elif value[0] == "record":
            return Record(
                value[1],
                {feat: self._compute(env, val) for feat, val in value[2]},
            )

        elif value[0] == "proc":
            fvars = self.get_fvars_value(value)
            ctx_env = {fvar: env[fvar] for fvar in fvars}
            return Proc(value[1], value[2], ctx_env)

        elif value[0] in {"sum", "product"}:
            operands = []
            for oper in value[1:]:
                if type(oper) is Ident:
                    eq_class = self.sas[env[oper.name]]
                    if eq_class.is_bound():
                        oper_val = eq_class.value
                    else:
                        raise UnboundVariableError(
                            f"{oper.name} is unbound", env[oper.name]
                        )
                else:
                    oper_val = self._compute(env, oper)

                if type(oper_val) is not Literal:
                    raise TypeError(
                        f"{value[0]} can only be performed over literals"
                    )
                else:
                    operands.append(oper_val)

            if value[0] == "sum":
                return Literal(operands[0].value + operands[1].value)
            else:
                return Literal(operands[0].value * operands[1].value)

        else:  # Misc. Oz operations
            raise NotImplementedError(f"{value}")

    def get_fvars_value(self, value):
        """Get the free variables of an Oz variable or value/operation.

        NOTE: The input must not have been "computed" using `_compute`, as free
        variables of Oz operations are lost on computation.

        Args:
            value (tuple): The input Oz value

        Returns:
            set: The set of free variables (Oz identifiers) as a set of strings

        """
        if type(value) is Ident:
            fvars = {value.name}
            logging.debug(f"free vars of {value.name}: {fvars}")

        elif type(value) is Literal:
            fvars = set()
            logging.debug(f"free vars of {value.value}: {fvars}")

        elif value[0] == "record":
            fvars = set()
            for _, sub_val in value[2]:
                fvars = fvars.union(self.get_fvars_value(sub_val))
            logging.debug(f"free vars of {value[0]}: {fvars}")

        elif value[0] == "proc":
            args = {arg.name for arg in value[1]}
            fvars = self.get_fvars(value[2])
            fvars.difference_update(args)
            logging.debug(f"free vars of {value[0]}: {fvars}")

        elif value[0] in {"sum", "product"}:
            lhs = self.get_fvars_value(value[1])
            rhs = self.get_fvars_value(value[2])
            fvars = lhs.union(rhs)
            logging.debug(f"free vars of {value[0]}: {fvars}")

        else:  # Misc. Oz operation
            raise NotImplementedError(f"{value}")

        return fvars

    def get_fvars(self, stmt):
        """Get the free variables of the given statement.

        Args:
            stmt (tuple): The input Oz statement's AST

        Returns:
            set: The set of free variables (Oz identifiers) as a set of strings

        """
        if stmt[0] == "nop":
            fvars = set()

        elif type(stmt[0]) is list:
            fvars = set()
            for sub_stmt in stmt:
                fvars = fvars.union(self.get_fvars(sub_stmt))

        elif stmt[0] == "var":
            fvars = self.get_fvars(stmt[2])
            fvars.remove(stmt[1].name)

        elif stmt[0] == "bind":
            fvars = set()
            for oper in stmt[1:]:
                fvars = fvars.union(self.get_fvars_value(oper))

        elif stmt[0] == "conditional":
            fvars = {stmt[1].name}
            fvars = fvars.union(self.get_fvars(stmt[2]))
            fvars = fvars.union(self.get_fvars(stmt[3]))

        elif stmt[0] == "match":
            fvars = {stmt[1].name}
            fvars = fvars.union(self.get_fvars(stmt[4]))
            fvars = fvars.union(
                self.get_fvars(stmt[3]).difference(self.get_fvars(stmt[2]))
            )

        elif stmt[0] == "apply":
            fvars = {ident.name for ident in stmt[1:]}

        else:
            raise ValueError(f"{stmt} is an invalid statement")

        if type(stmt[0]) is list:
            logging.debug(f"free vars of combined statement: {fvars}")
        else:
            logging.debug(f"free vars of {stmt[0]}: {fvars}")
        return fvars

    def _match_records(self, lhs, rhs):
        """Unify two records without recursion, and return their dict forms.

        This is used for unification with recursion, and also in pattern
        matching.

        Args:
            lhs (tuple): The first record value
            rhs (tuple): The second record value

        """
        if type(lhs) is not Record or type(rhs) is not Record:
            raise TypeError("Input arguments are not records")

        if lhs.literal != rhs.literal:
            raise UnificationError("Record literals do not match")

        elif len(lhs.fields) != len(rhs.fields):
            raise UnificationError("Record arities do not match")

        elif lhs.fields.keys() != rhs.fields.keys():
            # Value returned by `dict.keys` acts like a set, so
            # order doesn't matter.
            raise UnificationError("Record features do not match")

    def _unify_vars(self, env, lhs, rhs, marked):
        """Unify two variables."""
        sas_vars = []
        for oper in [lhs, rhs]:
            if type(oper) is Ident:
                sas_vars.append(env[oper.name])
            else:  # SAS variable
                sas_vars.append(oper.name)

        # overwriting the input arguments, as they are no longer required
        lhs, rhs = sas_vars
        logging.debug(f"unifying: {lhs} & {rhs}")

        if rhs == marked.get(lhs, "") or lhs == marked.get(rhs, ""):
            logging.debug(
                f"ignoring unification as {lhs} & {rhs} are marked unified"
            )
            return

        class1 = self.sas[lhs]
        class2 = self.sas[rhs]

        if class1 is not class2:
            if not class1.is_bound():
                # If the class2 class is bound, then this take its value, else
                # it stays unbound (as the class2 class's value is None).
                class1.value = class2.value
            elif class2.is_bound():
                # Both variables are bound, so in order to prevent infinite
                # recursion in unification of record values, we need to unify
                # their values after marking the variables as unified.
                logging.debug("marking both as unified before check")
                marked[lhs] = rhs
                self._unify_values(
                    env, class1.value, class2.value, marked=marked
                )
            class1.vars = class1.vars.union(class2.vars)

            for ref in class2.vars:
                # All variables that map to the second equivalence class are to
                # be pointed to the merged equivalence class.
                self.sas[ref] = class1
            del class2

    def _unify_values(self, env, lhs, rhs, marked):
        """Unify two Oz values."""
        lhs = self._compute(env, lhs)
        rhs = self._compute(env, rhs)
        logging.debug(f"unifying {lhs} & {rhs}")

        if type(lhs) is not type(rhs):
            raise TypeError("Values are not of the same type")

        if type(lhs) is Proc:
            raise UnificationError("Procedures cannot match")

        if type(lhs) is Literal and lhs.value != rhs.value:
            raise UnificationError("Literal values do not match")

        elif type(lhs) is Record:
            self._match_records(lhs, rhs)
            for key in lhs.fields:
                self.unify(
                    env, lhs.fields[key], rhs.fields[key], marked=marked
                )

    def unify(self, env, lhs, rhs, marked={}):
        """Unify both input variables/values.

        Args:
            env (dict): The current variable environment
            lhs (tuple): The LHS of a bind statement, or the first argument for
                unification
            rhs (tuple): The RHS of a bind statement, or the second argument
                for unification
            marked (tuple):

        Raises:
            UnificationError: If the input operands cannot be unified

        """
        var_types = {Ident, Variable}

        if type(lhs) in var_types and type(rhs) in var_types:  # <x> = <y>
            self._unify_vars(env, lhs, rhs, marked=marked)

        elif type(lhs) in var_types or type(rhs) in var_types:  # <x> = <v>
            # Input can be either `<x> = <v>` or `<v> = <x>`, so convert it
            # into `<x> = <v>`.
            if type(lhs) is Ident:
                var, value = env[lhs.name], rhs
            elif type(lhs) is Variable:
                var, value = lhs.name, rhs
            elif type(rhs) is Ident:
                var, value = env[rhs.name], lhs
            else:
                var, value = rhs.name, lhs

            value = self._compute(env, value)
            class1 = self.sas[var]
            logging.debug(f"unifying {var} & {value}")

            if not class1.is_bound():
                class1.value = value
            else:
                self.unify(env, class1.value, value, marked=marked)

        else:  # <v> = <v>
            self._unify_values(env, lhs, rhs, marked=marked)

    def _alloc_var(self, length=16):
        """Allocate a variable on the single-assignment store and return it."""
        new = len(self.sas)
        self.sas.append(_EqClass(new))
        return new

    def _if_stmt(self, stmt, env):
        """Process a suspendable Oz if-else statement.

        Args:
            stmt (tuple): The Oz if-else statement's AST
            env (dict): The current variable environment

        Returns:
            tuple: The resulting statement to be pushed onto the stack

        """
        ident = stmt[1].name
        logging.info(f"if-else on: {ident}")
        eq_class = self.sas[env[ident]]
        if not eq_class.is_bound():
            raise UnboundVariableError(f"{ident} is unbound", env[ident])

        cond = eq_class.value
        if type(cond) is not Literal or type(cond.value) is not bool:
            raise TypeError(f"{ident} is not a boolean")
        elif cond.value:
            return stmt[2]
        else:
            return stmt[3]

    def _match_stmt(self, stmt, env):
        """Process a suspendable Oz case statement.

        Args:
            stmt (tuple): The Oz case statement's AST
            env (dict): The current variable environment

        Returns:
            tuple: The resulting statement to be pushed onto the stack
            dict: The resulting environment to be pushed onto the stack

        """
        ident = stmt[1].name
        logging.info(f"case on: {ident}")

        eq_class = self.sas[env[ident]]
        if not eq_class.is_bound():
            raise UnboundVariableError(f"{ident} is unbound", env[ident])

        if stmt[2][0] != "record":
            raise TypeError(f"Invalid pattern: {stmt[2]}")
        else:
            pattern = Record(
                stmt[2][1], {feat: val for feat, val in stmt[2][2]}
            )

        try:
            self._match_records(eq_class.value, pattern)

        except (TypeError, UnificationError):
            # Either not a record, or doesn't match
            logging.debug(f"{ident} doesn't match pattern")
            return stmt[4], env

        else:
            logging.debug(f"{ident} matches pattern")

            # Avoid editing environments of other statements in the
            # stack.
            new_env = deepcopy(env)
            for feat, item in pattern.fields.items():
                if type(item) is Ident:
                    new_env[item.name] = self._alloc_var()
                    self.unify(new_env, item, eq_class.value.fields[feat])
            logging.debug(f"env for case: {pformat(new_env)}")

            return stmt[3], new_env

    def _apply_stmt(self, stmt, env):
        """Process a suspendable Oz procedure call.

        Args:
            stmt (tuple): The Oz procedure call statement's AST
            env (dict): The current variable environment

        Returns:
            tuple: The resulting statement to be pushed onto the stack
            dict: The resulting environment to be pushed onto the stack

        """
        proc = stmt[1].name
        logging.info(f"calling: {proc}")
        eq_class = self.sas[env[proc]]
        if not eq_class.is_bound():
            raise UnboundVariableError(f"{proc} is unbound", env[proc])

        value = eq_class.value
        if type(value) is not Proc:
            raise TypeError(f"{proc} is not a procedure")
        elif len(value.args) != len(stmt) - 2:
            raise TypeError(f"No. of arguments do not match arity of {proc}")

        # Avoid editing the contextual environment by reference
        new_env = deepcopy(value.ctxenv)
        for arg, param in zip(value.args, stmt[2:]):
            new_env[arg.name] = env[param.name]
        logging.debug(f"call env: {new_env}")

        return value.contents, new_env

    def _exec_stmt(self, stack, stmt, env):
        """Process an Oz statement."""
        if stmt[0] == "nop":
            logging.info("skip statement")

        elif type(stmt[0]) is list:
            logging.info(f"combined statement of {len(stmt)} sub-statements")
            for sub_stmt in reversed(stmt):
                stack.append((sub_stmt, env))

        elif stmt[0] == "var":
            logging.info(f"local statement with var: {stmt[1].name}")

            # Avoid editing envs of other statements in the stack
            new_env = deepcopy(env)
            new_env[stmt[1].name] = self._alloc_var()

            logging.debug(f"new env: {pformat(new_env)}")
            logging.debug(f"sas: {pformat(self.sas)}")
            stack.append((stmt[2], new_env))

        elif stmt[0] == "bind":
            logging.info(f"binding lhs: {stmt[1]} & rhs: {stmt[2]}")
            logging.debug(f"env: {pformat(env)}")
            logging.debug(f"sas before: {pformat(self.sas)}")
            self.unify(env, stmt[1], stmt[2])
            logging.debug(f"sas after: {pformat(self.sas)}")

        elif stmt[0] == "conditional":
            # The environment doesn't change, so this function is
            # made to not return the environment.
            stack.append((self._if_stmt(stmt, env), env))

        elif stmt[0] == "match":
            stack.append(self._match_stmt(stmt, env))

        elif stmt[0] == "apply":
            stack.append(self._apply_stmt(stmt, env))

        else:
            raise ValueError(f"{stmt} is an invalid statement")

    def run(self, ast):
        """Run the given Oz AST."""
        self.sas = []  # clear the interpreter
        thr_queue = Queue()
        thr_count = 0  # for debugging
        # Initialize the main thread with an empty env
        thr_queue.put(_Thread(thr_count, [(ast, {})]))
        thr_count += 1
        global_tick = 0
        change_tick = 0
        # TODO: Check for deadlock, ie., all threads are indefinitely suspended
        while not thr_queue.empty():
            global_tick += 1
            thread = thr_queue.get()
            old_tick = thread.tick 
            thread.tick = global_tick
            logging.debug(f"processing thread: {thread.num}")

            if thread.suspension is not None:
                # Checking if thread can be resumed
                logging.info(
                    f"thread {thread.num} suspended on: {thread.suspension}"
                )
                logging.debug(f"sas: {pformat(self.sas)}")
                eq_class = self.sas[thread.suspension]
                if not eq_class.is_bound():
                    if change_tick < old_tick:
                        logging.info("Deadlock encountered") 
                        return 
                    thr_queue.put(thread)
                    continue

            stmt, env = thread.stack.pop()

            if stmt[0] == "thread":
                is_running = True
                logging.info(f"creating new thread with no: {thr_count}")
                thr_queue.put(_Thread(thr_count, [(stmt[1], env)]))
                change_tick = global_tick 

            else:
                try:
                    self._exec_stmt(thread.stack, stmt, env)
                    change_tick = global_tick
                except UnboundVariableError as ex:
                    logging.info(f"thread {thread.num} suspended on: {ex.var}")
                    thread.suspension = ex.var
                    # Restore the popped stmt and env.
                    # NOTE: This assumes that no state (stack, env or sas)
                    # was altered before detecting the unbound variable
                    thread.stack.append((stmt, env))

            if len(thread.stack) > 0:
                logging.debug(f"thread {thread.num} is incomplete")
                thr_queue.put(thread)
            else:
                logging.debug(f"thread {thread.num} is complete")
