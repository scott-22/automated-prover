"""Convert an AST into clauses by converting into prenex normal form and skolemizing."""

from collections.abc import Iterator
from contextlib import contextmanager
from functools import partial
from .lexer import Operator
from .parser_ast import *


class NormalFormException(Exception):
    """
    Exception class representing errors while converting into normal form.
    Since all valid ASTs can be converted to normal form, these errors
    are strictly programming errors.
    """


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
        while (func := f"func_{numeric_id}") in self.global_unique_funcs:
            numeric_id += 1
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
            ast = BinaryConnective(Operator.OR, UnaryConnective(Operator.NOT, left), right)
        case BinaryConnective(Operator.IFF, left, right):
            left = simplifyConnectives(left)
            right = simplifyConnectives(right)
            ast = BinaryConnective(
                Operator.AND,
                BinaryConnective(Operator.OR, UnaryConnective(Operator.NOT, left), right),
                BinaryConnective(Operator.OR, UnaryConnective(Operator.NOT, right), left)
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
                case (
                    BinaryConnective(Operator.AND, left, right)
                    | BinaryConnective(Operator.OR, left, right)
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
                    dual_op = Operator.EXISTS if op == Operator.FORALL else Operator.FORALL
                    inner_arg = moveNegationsInward(UnaryConnective(Operator.NOT, inner_arg))
                    return Quantifier(dual_op, var, inner_arg)
                # No other connectives are expected
                case BinaryConnective(op) | UnaryConnective(op):
                    raise NormalFormException(
                        f"Unexpected connective {op}. Note that this function "
                        "expects binary connectives to be simplified into "
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
    standardizeVariablesFormula(ast, name_map)
    return ast


def standardizeVariablesFormula(
    ast: Formula,
    name_map: SymbolManager.VariableStandardizer
) -> None:
    """Helper for standardizeVariables, walks a formula AST."""
    match ast:
        case Relation(_, args):
            map(partial(standardizeVariablesTerm, name_map=name_map), args)
        case BinaryConnective(_, left, right):
            standardizeVariablesFormula(left, name_map)
            standardizeVariablesFormula(right, name_map)
        case UnaryConnective(_, arg):
            standardizeVariablesFormula(arg, name_map)
        case Quantifier(_, var, arg):
            with name_map.mapBoundVar(var.name) as new_name:
                var.name = new_name
                standardizeVariablesFormula(arg, name_map)


def standardizeVariablesTerm(ast: Term, name_map: SymbolManager.VariableStandardizer) -> None:
    """Helper for standardizeVariables, walks a term AST and renames vars if necessary."""
    match ast:
        case Variable(name):
            ast.name = name_map(name)
        case Function(name, args):
            name_map.registerFunc(name)
            map(partial(standardizeVariablesTerm, name_map=name_map), args)


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
    """Skolemize a formula in PNF."""
    # Universally-quantified variables to use as arg list for skolem func
    var_list: list[Variable] = []
    # Maps existentially-quantified variables to their skolem func
    skolem_map: dict[str, Function] = {}
    # The root formula (first universal quantifier or non-quantified formula)
    root: Formula = None
    # The previous universal quantifier
    prev_quantifier: Quantifier = None

    while isinstance(ast, Quantifier):
        if ast.name == Operator.EXISTS:
            # We replace the existential variable with a skolem func, and remove
            # the quantifier from the AST
            skolem_func = symbol_manager.getSkolemFunc()
            skolem_map[ast.var.name] = Function(skolem_func, var_list.copy())
            if prev_quantifier is not None:
                prev_quantifier.arg = ast.arg
        else:
            # Add the variable to the var_list and set prev_quantifier (as well
            # as root if needed)
            var_list.append(ast.var)
            prev_quantifier = ast
            if root is None:
                root = ast
    if root is None:
        root = ast
    skolemizeFormula(ast, skolem_map)
    return root


def skolemizeFormula(ast: Formula, name_map: dict[str, Function]) -> None:
    """Helper for skolemize, skolemizes a quantifier-free formula."""
    match ast:
        case Relation(_, args):
            ast.args = [skolemizeTerm(arg, name_map) for arg in args]
        case BinaryConnective(_, left, right):
            skolemizeFormula(left, name_map)
            skolemizeFormula(right, name_map)
        case UnaryConnective(_, arg):
            skolemizeFormula(arg, name_map)
        case Quantifier(op, _, _):
            raise SkolemizationException(
                f"Unexpected quantifier {op} found within quantifier-free formula"
            )


def skolemizeTerm(ast: Term, name_map: dict[str, Function]) -> Term:
    """Helper for skolemize, walks a term AST and replaces vars with skolem functions."""
    match ast:
        case Variable(name):
            if name in name_map:
                return name_map[name]
        case Function(_, args):
            ast.args = [skolemizeTerm(arg, name_map) for arg in args]
    return ast
