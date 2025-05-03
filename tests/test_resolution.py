"""Integration test for resolution."""

import pytest
from prover.core.clause import extractClauses
from prover.core.resolution import resolution
from prover.language.lexer import Lexer, Operator
from prover.language.parser import parse, transform, SymbolManager, UnaryConnective
from utils import *


@pytest.fixture
def symbol_manager():
    return SymbolManager()


@pytest.mark.parametrize(
    "premises, conclusion, valid",
    [
        (
            ["forall x R(x, f(0))"],
            "forall x R(x, f(0))",
            True,  # Reflexivity
        ),
        (
            ["P(0) & R(1)", "P(0) & !R(1)"],
            "!P(0)",
            True,  # Contradiction
        ),
        (
            ["forall x (A(x) -> B(x))"],
            "forall y (!B(y) -> !A(y))",
            True,  # Contrapositive
        ),
        (
            ["A(X) & B(X)", "B(X) -> C(X)", "A(x) -> D(X)"],
            "C(X) & D(X)",
            True,  # Conjunction
        ),
        (
            ["forall x (A(x) | B(x))", "!A(1)"],
            "B(1)",
            True,  # Disjunction
        ),
        (
            [
                "forall x (A(x) -> B(x))",
                "forall y (B(y) -> C(y))",
                "exists x A(x)"
            ],
            "exists x C(x)",
            True,  # Implication
        ),
        (
            ["A(x) <-> B(x)", "B(x) | A(x)"],
            "A(x) & B(x)",
            True,  # Biconditional
        ),
        (
            ["forall x R(x)"],
            "R(0)",
            True,  # Universal quantifier
        ),
        (
            ["R(u)"],
            "forall x R(x)",
            True,  # Universal quantifier
        ),
        (
            ["R(0)"],
            "exists x R(x)",
            True,  # Existential quantifier
        ),
        (
            ["exists x R(x)", "R(u) -> R(0)"],
            "R(0)",
            True,  # Existential quantifier
        ),
        (
            ["forall x R(x)"],
            "exists y R(y)",
            True,  # Both quantifiers
        ),
    ]
)
def test_resolution(premises, conclusion, valid, symbol_manager):
    premise_clauses = []
    for premise in premises:
        premise_clauses.extend(
            extractClauses(transform(parse(Lexer(premise)), symbol_manager))
        )
    negated_conclusion = UnaryConnective(Operator.NOT, parse(Lexer(conclusion)))
    conclusion_clauses = extractClauses(transform(negated_conclusion, symbol_manager))
    if valid:
        assert resolution(premise_clauses, conclusion_clauses)
    else:
        assert resolution(premise_clauses, conclusion_clauses) is None 
