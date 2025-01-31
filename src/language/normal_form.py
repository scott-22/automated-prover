"""Convert an AST into clauses by converting into normal form and skolemizing"""

from collections.abc import Callable
from .parser_ast import *

def simplifyConnectives(ast: Formula) -> Formula:
    """
    Simplify the connectives -> and <-> into their equivalents using !, &, |
    by performing a preorder traversal and replacing each node.
    """
    match ast:
        case BinaryConnective("->", left, right):
            left = simplifyConnectives(left)
            right = simplifyConnectives(right)
            ast = BinaryConnective("|", UnaryConnective("!", left), right)
        case BinaryConnective("<->", left, right):
            left = simplifyConnectives(left)
            right = simplifyConnectives(right)
            ast = BinaryConnective(
                "&",
                BinaryConnective("|", UnaryConnective("!", left), right),
                BinaryConnective("|", UnaryConnective("!", right), left)
            )
        case BinaryConnective(_, left, right):
            ast.left = simplifyConnectives(left)
            ast.right = simplifyConnectives(right)
        case UnaryConnective(_, arg) | Quantifier(_, _, arg):
            ast.arg = simplifyConnectives(arg)
    return ast


def standardizeVariables(ast: Formula):
    """Ensure all bound variables in a formula have different names"""
    # The symbol table maps the old name to the new name
    symbol_table = {}

    # Use a monotonic number to append to IDs for generating unique names
    numeric_id = 0
    def generate_unique_name(name: str) -> str:
        """
        Closure to generate a new unique name and bind it to the duplicated
        variable name (passed in as `name`). Returns the original name
        bound to the duplicated variable name.
        """
        nonlocal symbol_table, numeric_id
        original_name = symbol_table.get(name)
        while (new_name := f"{name}_{numeric_id}") in symbol_table:
            numeric_id += 1
        symbol_table[name] = new_name
        return original_name, new_name
    
    standardizeVariablesFormula(ast, symbol_table, generate_unique_name)


def standardizeVariablesFormula(
        ast: Formula,
        symbol_table: dict[str, str],
        generate_unique_name: Callable[[], str]
    ):
    """Helper for standardizeVariables, walks a formula AST"""
    match ast:
        case Relation(_, args):
            map(standardizeVariablesTerm, args)
        case BinaryConnective(_, left, right):
            standardizeVariablesFormula(left, symbol_table, generate_unique_name)
            standardizeVariablesFormula(right, symbol_table, generate_unique_name)
        case UnaryConnective(_, arg):
            standardizeVariablesFormula(arg, symbol_table, generate_unique_name)
        case Quantifier(_, var, arg):
            if var.name in symbol_table:
                original_name, new_name = generate_unique_name(var.name)
                var.name = new_name
            standardizeVariablesFormula(arg, symbol_table, generate_unique_name)
            symbol_table[var.name] = original_name


def standardizeVariablesTerm(ast: Term, symbol_table: dict[str, str]):
    """Helper for standardizeVariables, walks a term AST and renames vars if necessary"""
    match ast:
        case Variable():
            if ast.name in symbol_table:
                ast.name = symbol_table[ast.name]
        case Function(_, args):
            map(standardizeVariablesTerm, args)
    
