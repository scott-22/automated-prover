"""Convert an AST into prenex normal form and apply skolemization."""

from collections.abc import Iterator
from contextlib import contextmanager
from .lexer import Operator
from .parser_ast import *


class SkolemizationException(Exception):
    """
    Exception class representing errors while skolemizing. Since all valid
    ASTs can be skolemized, these errors are strictly programming errors.
    """


class SymbolManager:
    """
    Singleton class to help manage generating unique names, used both for
    standardizing variables within the same formula and for generating
    function names during skolemization.

    Note that uniqueness of generated names is only guaranteed if all
    variable standardization steps occur before skolemization, since
    unique function names are currently registered during standardization.

    This symbol manager should be injected into the relevant functions.
    """

    def __init__(self):
        # All unique function names within a session
        self.global_unique_funcs: set[str] = set()
        # Use a monotonic number for generating unique names
        self.numeric_id = 0

    def registerFunc(self, name: str) -> None:
        self.global_unique_funcs.add(name)

    def getSkolemFunc(self) -> str:
        """Return a unique skolem function name."""
        while (func := f"func_{self.numeric_id}") in self.global_unique_funcs:
            self.numeric_id += 1
        self.global_unique_funcs.add(func)
        return func

    class VariableStandardizer:
        """
        Helper class to standardize variables within a single formula.
        Since variable standardization happens before skolemization,
        the global_unique_funcs set is also passed in, and function
        names are registered during this step.
        """

        def __init__(self, func_name_register: set[str]):
            # Tracks all names seen so far
            self.symbol_set: set[str] = set()
            # Maps bound variables to their new name
            self.bound_symbol_table: dict[str, str] = {}
            # Maps free variables to their new name
            self.free_symbol_table: dict[str, str] = {}
            # Use a monotonic number to append to IDs for generating unique names
            self.numeric_id = 0
            # Track unique function symbols seen so far
            self.func_name_register = func_name_register

        def getNewSymbol(self, name: str):
            """Generate a new symbol based on the given name."""
            while (new_symbol := f"{name}_{self.numeric_id}") in self.symbol_set:
                self.numeric_id += 1
            return new_symbol

        def registerFunc(self, name: str):
            self.func_name_register.add(name)

        @contextmanager
        def mapBoundVar(self, name: str) -> Iterator[str]:
            """
            Register and map a bound variable name, returning its new name. If
            this is the first time seeing it, simply return the name itself.
            Otherwise, generate a unique name and return it.

            Since renaming occurs recursively in the AST, the same bound variable
            can refer to different symbols at different points. Thus, this method
            is a context manager, storing previous names on the call stack, while
            the bound_symbol_table always points to the current mapped name.
            """
            original_var = self.bound_symbol_table.get(name)
            new_var = self.getNewSymbol(name) if name in self.symbol_set else name
            self.symbol_set.add(new_var)
            self.bound_symbol_table[name] = new_var
            yield new_var
            self.bound_symbol_table[name] = original_var

        def __call__(self, name: str) -> str:
            """Return the mapped name of a variable (free or bound)."""
            # Check if we have a bound or free variable. Note that a variable
            # might exist in bound_symbol_table but still be free (if it is
            # mapped to None, then it has already been popped off the stack).
            if (bound_var := self.bound_symbol_table.get(name)) is not None:
                return bound_var
            else:
                if name in self.free_symbol_table:
                    return self.free_symbol_table[name]
                new_var = self.getNewSymbol(name)
                self.symbol_set.add(new_var)
                self.free_symbol_table[name] = new_var
                return new_var

    def standardize_variables(self) -> VariableStandardizer:
        return self.VariableStandardizer(self.global_unique_funcs)


def simplifyConnectives(ast: Formula) -> Formula:
    """
    Simplify the connectives -> and <-> into their equivalents using !, &, |
    by performing a postorder traversal and replacing each node.
    """
    match ast:
        case BinaryConnective(Operator.IMPLIES, left, right):
            left = simplifyConnectives(left)
            right = simplifyConnectives(right)
            ast = BinaryConnective(
                Operator.OR, UnaryConnective(Operator.NOT, left), right
            )
        case BinaryConnective(Operator.IFF, left, right):
            left = simplifyConnectives(left)
            right = simplifyConnectives(right)
            ast = BinaryConnective(
                Operator.AND,
                BinaryConnective(
                    Operator.OR, UnaryConnective(Operator.NOT, left), right
                ),
                BinaryConnective(
                    Operator.OR, left, UnaryConnective(Operator.NOT, right)
                ),
            )
        case BinaryConnective(_, left, right):
            ast.left = simplifyConnectives(left)
            ast.right = simplifyConnectives(right)
        case UnaryConnective(_, arg) | Quantifier(_, _, arg):
            ast.arg = simplifyConnectives(arg)
    return ast


def moveNegationsInward(ast: Formula) -> Formula:
    """
    Move all negations inwards (reducing their scope) so that they are only bound
    to relations as part of a literal. Assumes that all -> and <-> have already
    been simplified into !, &, |.
    """
    match ast:
        case UnaryConnective(Operator.NOT, arg):
            match arg:
                # Apply DeMorgan's Law
                case BinaryConnective(Operator.AND, left, right) | BinaryConnective(
                    Operator.OR, left, right
                ):
                    dual_op = Operator.AND if arg.name == Operator.OR else Operator.OR
                    left = moveNegationsInward(UnaryConnective(Operator.NOT, left))
                    right = moveNegationsInward(UnaryConnective(Operator.NOT, right))
                    return BinaryConnective(dual_op, left, right)
                # Double negations cancel out
                case UnaryConnective(Operator.NOT, inner_arg):
                    return moveNegationsInward(inner_arg)
                # Express quantifiers in terms of duals
                case Quantifier(op, var, inner_arg):
                    # We assume there are only two quantifiers, exists and forall
                    dual_op = (
                        Operator.EXISTS if op == Operator.FORALL else Operator.FORALL
                    )
                    inner_arg = moveNegationsInward(
                        UnaryConnective(Operator.NOT, inner_arg)
                    )
                    return Quantifier(dual_op, var, inner_arg)
                # No other connectives are expected
                case BinaryConnective(op) | UnaryConnective(op):
                    raise SkolemizationException(
                        f"Unexpected connective {op} while moving negations. "
                        "Note that this function expects binary connectives "
                        "to be simplified into "
                        f"{Operator.NOT}, {Operator.AND}, {Operator.OR}"
                    )
        case BinaryConnective(_, left, right):
            ast.left = moveNegationsInward(left)
            ast.right = moveNegationsInward(right)
        case UnaryConnective(_, arg) | Quantifier(_, _, arg):
            ast.arg = moveNegationsInward(arg)
    return ast


def standardizeVariables(ast: Formula, symbol_manager: SymbolManager) -> Formula:
    """Ensure all bound variables in a formula have different names."""
    name_map = symbol_manager.standardize_variables()

    def standardizeVariablesFormula(ast: Formula) -> None:
        """Helper for standardizeVariables, walks a formula AST."""
        nonlocal name_map
        match ast:
            case Relation(_, args):
                for arg in args:
                    standardizeVariablesTerm(arg)
            case BinaryConnective(_, left, right):
                standardizeVariablesFormula(left)
                standardizeVariablesFormula(right)
            case UnaryConnective(_, arg):
                standardizeVariablesFormula(arg)
            case Quantifier(_, var, arg):
                with name_map.mapBoundVar(var) as new_name:
                    ast.var = new_name
                    standardizeVariablesFormula(arg)

    def standardizeVariablesTerm(ast: Term) -> None:
        """Helper for standardizeVariables, walks a term AST and renames vars if necessary."""
        nonlocal name_map
        match ast:
            case Variable(name):
                ast.name = name_map(name)
            case Function(name, args):
                name_map.registerFunc(name)
                for arg in args:
                    standardizeVariablesTerm(arg)

    standardizeVariablesFormula(ast)
    return ast


def moveQuantifiersOutward(ast: Formula) -> Formula:
    """
    Move all quantifiers outwards (increasing their scope) to convert the formula
    into prenex normal form (PNF).
    """
    match ast:
        case BinaryConnective(op, left, right):
            left = moveQuantifiersOutward(left)
            right = moveQuantifiersOutward(right)
            left_last_quantifier = getInnermostQuantifier(left)
            right_last_quantifier = getInnermostQuantifier(right)

            left_arg = left_last_quantifier.arg if left_last_quantifier else left
            right_arg = right_last_quantifier.arg if right_last_quantifier else right
            binary_formula = BinaryConnective(op, left_arg, right_arg)
            if left_last_quantifier and right_last_quantifier:
                right_last_quantifier.arg = binary_formula
                left_last_quantifier.arg = right
                return left
            elif left_last_quantifier:
                left_last_quantifier.arg = binary_formula
                return left
            elif right_last_quantifier:
                right_last_quantifier.arg = binary_formula
                return right
            return binary_formula
            # Combine quantifiers
        case UnaryConnective(op, arg):
            # This case is handled, but should not occur if moveNegationsInward
            # has already been called
            arg = moveQuantifiersOutward(arg)
            if (last_quantifier := getInnermostQuantifier(arg)) is not None:
                last_quantifier.arg = UnaryConnective(op, last_quantifier.arg)
                return arg
            else:
                ast.arg = arg
        case Quantifier(_, _, arg):
            ast.arg = moveQuantifiersOutward(arg)
    return ast


def getInnermostQuantifier(ast: Formula) -> Formula | None:
    """
    Helper to return the innermost quantifier (assuming that all quantifiers are
    on the outside).
    """
    if isinstance(ast, Quantifier):
        innermost_quantifier = ast
        while isinstance(innermost_quantifier.arg, Quantifier):
            innermost_quantifier = innermost_quantifier.arg
        return innermost_quantifier
    return None


def skolemize(ast: Formula, symbol_manager: SymbolManager) -> Formula:
    """
    Skolemize a formula in PNF, and return a quantifier-free formula. This
    formula is implicitly universally-quantified, but the quantifiers are no
    longer relevant after this step.
    """
    # Variables/skolem funcs to use as arg list for nextskolem func
    var_list: list[Variable | Function] = []
    # Maps existentially-quantified variables to their skolem func
    skolem_map: dict[str, Function] = {}

    while isinstance(ast, Quantifier):
        if ast.name == Operator.EXISTS:
            # We replace the existentially-quantified variable with a skolem func
            skolem_func_symbol = symbol_manager.getSkolemFunc()
            skolem_func = Function(skolem_func_symbol, var_list.copy())
            skolem_map[ast.var] = skolem_func
            var_list.append(skolem_func)
        else:
            # Add the universally-quantified variable to the var_list
            var_list.append(Variable(ast.var))
        ast = ast.arg

    def skolemizeFormula(ast: Formula) -> None:
        """Helper for skolemize, skolemizes a quantifier-free formula."""
        match ast:
            case Relation(_, args):
                ast.args = list(map(skolemizeTerm, args))
            case BinaryConnective(_, left, right):
                skolemizeFormula(left)
                skolemizeFormula(right)
            case UnaryConnective(_, arg):
                skolemizeFormula(arg)
            case Quantifier(op, _, _):
                raise SkolemizationException(
                    f"Unexpected quantifier {op} found within quantifier-free formula"
                )

    def skolemizeTerm(ast: Term) -> Term:
        """Helper for skolemize, walks a term AST and replaces vars with skolem functions."""
        nonlocal skolem_map
        match ast:
            case Variable(name):
                if name in skolem_map:
                    return skolem_map[name]
            case Function(_, args):
                ast.args = list(map(skolemizeTerm, args))
        return ast

    skolemizeFormula(ast)
    return ast
