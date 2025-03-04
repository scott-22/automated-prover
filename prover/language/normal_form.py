"""Convert an existential-free formula into conjuctive normal form to create clauses."""

from typing import Protocol
from .parser_ast import *
from .skolemization import *


class NormalFormException(Exception):
    """
    Exception class representing errors while converting into normal form.
    Since all valid ASTs can be converted to normal form, these errors
    are strictly programming errors.
    """


class DecoratedFormula(Protocol):
    """
    Annotating a formula node with additional data to help conversion to CNF.
    Note that formula nodes will implement this protocol implicitly rather
    than explicitly inheriting from or instantiating it.
    """

    # Store number of conjunction (&) nodes
    num_conjunctions: int


def annotateAstData(ast: Formula) -> DecoratedFormula:
    """
    Annotate all AST nodes with the number of conjunction and disjunction
    nodes belonging to that subtree.
    """
    match ast:
        case BinaryConnective(Operator.AND, left, right) | BinaryConnective(
            Operator.OR, left, right
        ):
            is_conjunction = 1 if ast.name == Operator.AND else 0
            annotateAstData(left)
            annotateAstData(right)
            ast.num_conjunctions = (
                left.num_conjunctions + right.num_conjunctions + is_conjunction
            )
        case UnaryConnective() | Relation():
            ast.num_conjunctions = 0
        case _:
            raise NormalFormException(
                f"Unexpected node {type(ast)} within AST {ast}. Only conjunctions, "
                "disjunctions, and literals should be present when converting to CNF",
            )
    return ast


def lowerDisjunction(ast: DecoratedFormula) -> DecoratedFormula:
    """
    Lower a given disjunction as far down the tree as necessary, such that
    no conjunctions are below it. We repeatedly apply the distributive law,
    "pushing" a disjunction into a conjunctive clause. It is a precondition
    that the current AST node is a disjunction (| node) and that both left
    and right child trees are in CNF.

    Note that we use the number of conjunctions as a heuristic for which
    branch to lower the disjunction into. We lower into the branch with more
    conjunctions, since the other branch will be duplicated. In case of a
    tie, we lower into the left branch.
    """
    if ast.num_conjunctions == 0:
        return ast
    left_is_conjunction = (
        isinstance(ast.left, BinaryConnective) and ast.left.name == Operator.AND
    )
    right_is_conjunction = (
        isinstance(ast.right, BinaryConnective) and ast.right.name == Operator.AND
    )
    # Use number of conjunctions as a heuristic for which branch to lower into
    if left_is_conjunction and (
        not right_is_conjunction
        or ast.left.num_conjunctions >= ast.right.num_conjunctions
    ):
        # Lower into the left branch
        ast = BinaryConnective(
            Operator.AND,
            BinaryConnective(Operator.OR, ast.left.left, ast.right),
            BinaryConnective(Operator.OR, ast.left.right, ast.right),
        )
    elif right_is_conjunction:
        # Lower into the right branch
        ast = BinaryConnective(
            Operator.AND,
            BinaryConnective(Operator.OR, ast.left, ast.right.left),
            BinaryConnective(Operator.OR, ast.left, ast.right.right),
        )
    else:
        raise NormalFormException(
            f"Expected {ast.num_conjunctions} conjunctions at the top of the given "
            f"AST {ast}, but they are either not present or the subtree is not in CNF"
        )
    # Update number of conjunctions
    ast.left.num_conjunctions = (
        ast.left.left.num_conjunctions + ast.left.right.num_conjunctions
    )
    ast.right.num_conjunctions = (
        ast.right.left.num_conjunctions + ast.right.right.num_conjunctions
    )
    ast.num_conjunctions = ast.left.num_conjunctions + ast.right.num_conjunctions + 1
    # Recursively lower disjunctions down subtrees
    ast.left = lowerDisjunction(ast.left)
    ast.right = lowerDisjunction(ast.right)
    return ast


def conjunctiveNormalForm(ast: DecoratedFormula) -> Formula:
    """Convert a skolemized formula into CNF."""
    match ast:
        case BinaryConnective(op, left, right):
            ast.left = conjunctiveNormalForm(left)
            ast.right = conjunctiveNormalForm(right)
            if op == Operator.OR:
                # Lower the disjunction if necessary
                ast = lowerDisjunction(ast)
    return ast
