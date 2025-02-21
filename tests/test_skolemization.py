"""Test conversion to PNF and skolemization."""

import copy
import pytest
from prover.language.lexer import Lexer
from prover.language.parser import parse
from prover.language.skolemization import *
from utils import *


@pytest.fixture
def symbol_manager():
    return SymbolManager()


def make_ast(fol: str) -> Formula:
    return parse(Lexer(fol))


@pytest.mark.parametrize(
    "original_ast, transformed_ast",
    [
        (
            make_ast("exists x (F(x) | F(0) & forall z R(z, u) & F(z) | F(t)) | !R(z)"),
            make_ast("exists x (F(x) | F(0) & forall z R(z, u) & F(z) | F(t)) | !R(z)"),
        ),
        (
            make_ast("A(x) -> B(x)"),
            make_ast("!A(x) | B(x)"),
        ),
        (
            make_ast("A(x) <-> B(x)"),
            make_ast("(!A(x) | B(x)) & (A(x) | !B(x))"),
        ),
        (
            make_ast("!A(x) -> (B(x) & C(1) -> D(x))"),
            make_ast("!!A(x) | (!(B(x) & C(1)) | D(x))"),
        ),
        (
            make_ast("A(x) <-> B(x) <-> C(x)"),
            make_ast(
                "(!((!A(x) | B(x)) & (A(x) | !B(x))) | C(x))"
                "& (((!A(x) | B(x)) & (A(x) | !B(x))) | !C(x))"
            ),
        ),
    ],
)
def test_simplify_connectives(original_ast, transformed_ast):
    assert simplifyConnectives(original_ast) == transformed_ast


@pytest.mark.parametrize(
    "original_ast, transformed_ast",
    [
        (
            make_ast("exists x (F(x) | F(b) & forall z (R(z, u) & F(z) | F(t))) | R(z)"),
            make_ast("exists x (F(x) | F(b) & forall z (R(z, u) & F(z) | F(t))) | R(z)"),
        ),
        (make_ast("forall x !A(x) & !B(x)"), make_ast("forall x !A(x) & !B(x)")),
        (make_ast("!(A(1) & B(0))"), make_ast("!A(1) | !B(0)")),
        (make_ast("!(A(1) | B(0))"), make_ast("!A(1) & !B(0)")),
        (make_ast("!(A(x) & B(x) & C(x) & D(x))"), make_ast("!A(x) | !B(x) | !C(x) | !D(x)")),
        (make_ast("!(A(x) & B(x) | C(x) & D(x))"), make_ast("(!A(x) | !B(x)) & (!C(x) | !D(x))")),
        (
            make_ast("!forall x exists y R(x, y)"),
            make_ast("exists x forall y !R(x, y)"),
        ),
        (make_ast("!!!!A(0)"), make_ast("A(0)")),
        (make_ast("!!!!!B(0)"), make_ast("!B(0)")),
        (
            make_ast("forall x !(!forall y !(A(x) & B(x)) & C(x))"),
            make_ast("forall x (forall y (!A(x) | !B(x)) | !C(x))"),
        )
    ]
)
def test_move_negations_inward(original_ast, transformed_ast):
    assert moveNegationsInward(original_ast) == transformed_ast


@pytest.mark.parametrize(
    "first_ast, second_ast, strict_funcs",
    [
        (
            make_ast("A(x) & B(y) & C(x)"), make_ast("A(y) & B(x) & C(y)"), True
        ),
        (
            make_ast("forall x forall y R(x, y, g(u, f(x)))"),
            make_ast("forall y forall x R(y, x, g(v, f(y)))"),
            True,
        ),
        (
            make_ast("forall x (R(x) & exists x P(x) | R(u)) & P(x)"),
            make_ast("forall x (R(x) & exists y P(y) | R(v)) & P(w)"),
            True,
        ),
        (
            make_ast("R(x, g(y, x, z, f(y, h(z), x), w), h(f(z)))"),
            make_ast("R(y, f(x, y, w, g(x, h(w), y), z), h(g(w)))"),
            False,
        ),
        (
            make_ast("P(x) & Q(f(x, y, z), g(x)) & R(u, g(v), w)"),
            make_ast("P(u) & Q(g(u, z, y), f(u)) & R(x, f(w), v)"),
            False,
        ),
        (
            make_ast("forall x (forall y R(y) & exists z forall w P(w, w))"),
            make_ast("forall x (forall x R(x) & exists x forall x P(x, x))"),
            True,
        ),
    ]
)
def test_check_asts_are_isomorphic(first_ast, second_ast, strict_funcs):
    """
    Although check_isomorphic is a helper function for testing, it is non-trivial enough
    that it warrants its own tests.
    """
    check_isomorphic(first_ast, second_ast, strict_funcs=strict_funcs)


@pytest.mark.parametrize(
    "first_ast, second_ast, strict_funcs",
    [
        (
            make_ast("forall x forall y R(y)"),
            make_ast("forall x R(x)"),
            False
        ),
        (
            make_ast("A(x) & B(y) & C(x)"),
            make_ast("A(y) & B(x) & C(x)"),
            True,
        ),
        (
            make_ast("forall x forall y R(x, y)"),
            make_ast("forall x forall x R(x, x)"),
            True
        ),
        (
            make_ast("forall x forall y R(f(x, y))"),
            make_ast("forall x forall y R(g(y, x))"),
            False
        ),
        (
            make_ast("R(x, g(y, x, z, f(y, h(z), x), w), h(f(z)))"),
            make_ast("R(y, f(x, y, w, g(x, h(w), y), z), h(g(w)))"),
            True
        ),
    ]
)
def test_check_asts_are_not_isomorphic(first_ast, second_ast, strict_funcs):
    with pytest.raises(Exception):
        check_isomorphic(first_ast, second_ast, strict_funcs=strict_funcs)


@pytest.mark.parametrize(
    "original_ast",
    [
        make_ast("forall x (R(x) & exists x P(x))"),
        make_ast("exists x R(u) & P(x) | exists y R(y)"),
        make_ast(
            """
            forall x (
                R(x) &
                exists x (
                    P(x, f(x, g(x, x))) |
                    forall x (
                        R(f(x)) & P(x)
                    )
                )
            )
            """
        ),
        make_ast(
            """
            forall x (
                A(x) &
                forall x (
                    B(x) |
                    exists z ( A(z) ) &
                    exists x ( A(x) ) &
                    forall x ( B(x) )
                )
            )
            """
        ),
    ]
)
def test_standardize_variables(original_ast, symbol_manager):
    original_ast_copy = copy.deepcopy(original_ast)
    standardized_ast = standardizeVariables(original_ast, symbol_manager)
    check_unique_var_names(standardized_ast)
    check_isomorphic(standardized_ast, original_ast_copy)        


@pytest.mark.parametrize(
    "original_ast, transformed_ast",
    [
        (
            make_ast("forall x R(x) & forall y R(y)"),
            make_ast("forall x forall y (R(x) & R(y))"),
        ),
        (
            make_ast("forall x R(x) | R(y)"),
            make_ast("forall x (R(x) | R(y))"),
        ),
        (
            make_ast("forall x R(x) & forall y R(y)"),
            make_ast("forall x forall y (R(x) & R(y))"),
        ),
        (
            make_ast(
                """
                forall x (
                    R(x, u) &
                    exists y (
                        P(y) &
                        forall w R(w) &
                        S(u)
                    )
                ) &
                exists z P(z)
                """
            ),
            make_ast(
                """
                    forall x
                    exists y
                    forall w
                    exists z (
                        R(x, u) &
                        (
                            P(y) &
                            R(w) &
                            S(u)
                        ) &
                        P(z)
                    )
                """
            )
        )
    ]
)
def test_move_quantifiers_outwards(original_ast, transformed_ast):
    assert moveQuantifiersOutward(original_ast) == transformed_ast


@pytest.mark.parametrize(
    "original_ast, transformed_ast",
    [
        (
            make_ast(
                """
                forall x exists y forall z exists w (
                    A(x) & B(y) | C(z) & D(w)
                )
                """
            ),
            make_ast("A(x) & B(f(x)) | C(z) & D(g(x, f(x), z))"),
        ),
        (
            make_ast(
                """
                forall x1 forall x2 exists x3 exists x4 forall x5 exists x6 (
                    A(x1, x2, f0(x3), f1(x4)) & B(x2, f1(x5)) | C(x6, x1, x3)
                )
                """
            ),
            make_ast(
                "A(x1, x2, f0(g0(x1, x2)), f1(g1(x1, x2, g0(x1, x2)))) & "
                "B(x2, f1(x5)) | "
                "C(g2(x1, x2, g0(x1, x2), g1(x1, x2, g0(x1, x2)), x5), x1, g0(x1, x2))"
            )
        )
    ]
)
def test_skolemize(original_ast, transformed_ast, symbol_manager):
    skolemized_ast = skolemize(original_ast, symbol_manager)
    check_isomorphic(skolemized_ast, transformed_ast, strict_funcs=False)
