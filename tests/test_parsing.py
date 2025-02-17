"""Test lexing and parsing."""

import pytest
from functools import partial
from prover.language.lexer import TokenType, Operator, Token, Lexer
from prover.language.parser_ast import *
from prover.language.parser import parse


# Test helpers


def make_bracket(bracket: str) -> Token:
    return Token(TokenType.BRACKET, bracket)


def make_id(name: str) -> Token:
    return Token(TokenType.IDENTIFIER, name)


def make_comma() -> Token:
    return Token(TokenType.COMMA, ",")


def make_op(op: str) -> Token:
    return Token(TokenType.OPERATOR, op)


# Shorten AST names

Const = Constant
Var = Variable
Func = Function

Rel = Relation


def RelVar(name: str, *args: list[str]):
    """Relation consisting only of variables"""
    return Rel(name, list(map(Var, args)))


Forall = partial(Quantifier, "forall")
Exists = partial(Quantifier, "exists")
Not = partial(UnaryConnective, "!")
And = partial(BinaryConnective, "&")
Or = partial(BinaryConnective, "|")
Implies = partial(BinaryConnective, "->")
Iff = partial(BinaryConnective, "<->")


@pytest.mark.parametrize(
    "input_str, output_tokens",
    [
        (
            "forall x (exists y (!R(x, y)))",
            [
                make_op("forall"),
                make_id("x"),
                make_bracket("("),
                make_op("exists"),
                make_id("y"),
                make_bracket("("),
                make_op("!"),
                make_id("R"),
                make_bracket("("),
                make_id("x"),
                make_comma(),
                make_id("y"),
                make_bracket(")"),
                make_bracket(")"),
                make_bracket(")"),
            ],
        ),
        (
            "A & B | C -> D <-> E",
            [
                make_id("A"),
                make_op("&"),
                make_id("B"),
                make_op("|"),
                make_id("C"),
                make_op("->"),
                make_id("D"),
                make_op("<->"),
                make_id("E"),
            ],
        ),
    ],
)
def test_lexer(input_str, output_tokens):
    assert list(Lexer(input_str)) == output_tokens


@pytest.mark.parametrize(
    "input_str, output_ast",
    [
        (
            "A(x, y) & B(Y, f(z, 0), y)",
            And(
                RelVar("A", "x", "y"),
                Rel("B", [Const("Y"), Func("f", [Var("z"), Const("0")]), Var("y")]),
            ),
        ),
        (
            "A(x) & B(x) & C(x)",
            And(And(RelVar("A", "x"), RelVar("B", "x")), RelVar("C", "x")),
        ),
        (
            "(A(x) -> B(x) -> C(x))",
            Implies(Implies(RelVar("A", "x"), RelVar("B", "x")), RelVar("C", "x")),
        ),
        (
            "(A(x) & (B(x) & C(x)))",
            And(RelVar("A", "x"), And(RelVar("B", "x"), RelVar("C", "x"))),
        ),
        (
            "forall x forall y !R(x, y)",
            Forall("x", Forall("y", Not(RelVar("R", "x", "y")))),
        ),
        (
            "forall x (((F(x) & ((F(y) | F(z))))))",
            Forall("x", And(RelVar("F", "x"), Or(RelVar("F", "y"), RelVar("F", "z")))),
        ),
        (
            "A(x) | B(x) & !C(x) -> !!D(x) <-> E(x)",
            Iff(
                Implies(
                    Or(
                        RelVar("A", "x"),
                        And(RelVar("B", "x"), Not(RelVar("C", "x"))),
                    ),
                    Not(Not(Rel("D", [Var("x")]))),
                ),
                RelVar("E", "x"),
            ),
        ),
        (
            "F(x) | F(b) & forall z R(z, u) & F(z) | F(t)",
            Or(
                Or(
                    RelVar("F", "x"),
                    And(
                        And(RelVar("F", "b"), Forall("z", RelVar("R", "z", "u"))),
                        RelVar("F", "z"),
                    ),
                ),
                RelVar("F", "t"),
            ),
        ),
    ],
)
def test_parser(input_str, output_ast):
    assert parse(Lexer(input_str)) == output_ast
