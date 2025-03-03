""""""

import pytest
from collections.abc import Callable
from prover.language.normal_form import *
from utils import *


def Dec(ast_func: Callable[..., Formula], num_conjunctions: int) -> Callable[..., DecoratedFormula]:
    """
    Given a formula helper, returns a closure that wraps it and annotates the
    returned formula with data. Makes decorating formula nodes easier.
    """
    def decorating_closure(*args, **kwargs) -> DecoratedFormula:
        result_formula = ast_func(*args, **kwargs)
        result_formula.num_conjunctions = num_conjunctions
        return result_formula
    return decorating_closure


def compare_annotations(left: DecoratedFormula, right: DecoratedFormula) -> None:
    assert left == right
    assert left.num_conjunctions == right.num_conjunctions
    if isinstance(left, BinaryConnective):
        compare_annotations(left.left, right.left)
        compare_annotations(left.right, right.right)


@pytest.mark.parametrize(
    "original_ast, annotated_ast",
    [
        (
            make_ast("(A(x) & B(x)) | (C(x) | D(x) & E(x))"),
            Dec(Or, 2)(
                Dec(And, 1)(Dec(RelVar, 0)("A", "x"), Dec(RelVar, 0)("B", "x")),
                Dec(Or, 1)(Dec(RelVar, 0)("C", "x"), Dec(And, 1)(Dec(RelVar, 0)("D", "x"), Dec(RelVar, 0)("E", "x")))
            )
        ),
        (
            make_ast("(!A(x) & B(x) & (C(x) & !D(x))) | ((!A(x) | B(x)) & C(x))"),
            Dec(Or, 4)(
                Dec(And, 3)(
                    Dec(And, 1)(Dec(Not, 0)(RelVar("A", "x")), Dec(RelVar, 0)("B", "x")),
                    Dec(And, 1)(Dec(RelVar, 0)("C", "x"), Dec(Not, 0)(RelVar("D", "x")))
                ),
                Dec(And, 1)(
                    Dec(Or, 0)(Dec(Not, 0)(RelVar("A", "x")), Dec(RelVar, 0)("B", "x")),
                    Dec(RelVar, 0)("C", "x")
                )
            )
        ),
    ]
)
def test_annotate_ast_data(original_ast, annotated_ast):
    compare_annotations(annotateAstData(original_ast), annotated_ast)


@pytest.mark.parametrize(
    "original_ast, transformed_ast", 
    [
        (
            make_ast("A(x) | B(x) & C(x)"),
            make_ast("(A(x) | B(x)) & (A(x) | C(x))"),
        )
    ]
)
def test_lower_disjunction(original_ast, transformed_ast):
    assert lowerDisjunction(annotateAstData(original_ast)) == transformed_ast
