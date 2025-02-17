"""Test lexing and parsing."""

import pytest
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
    ],
)
def test_lexer(input_str, output_tokens):
    assert list(Lexer(input_str)) == output_tokens
