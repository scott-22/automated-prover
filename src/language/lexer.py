"""Lex a string stream into a stream of tokens representing FOL"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Iterator


# Types of tokens representing basic FOL language
class TokenType(StrEnum):
    OPERATOR = "operator"      # Logical operator
    IDENTIFIER = "identifier"  # Name of a function, relation, or bound/free variable
    BRACKET = "bracket"        # Open or close bracket
    COMMA = "comma"            # Separator between function params

    def __repr__(self):
        return f"'{self.value}'"


# Operators supported by FOL language
class Operator(StrEnum):
    NOT = "!"
    FORALL = "forall"
    EXISTS = "exists"
    AND = "&"
    OR = "|"
    IMPLIES = "->"
    IFF = "<->"
    DUMMY = "begin"  # Dummy operator that denotes the beginning of a formula

    def __repr__(self):
        return f"'{self.value}'"


@dataclass
class Token:
    """Tokens to represent FOL"""
    type: TokenType
    val: str

    def __post_init__(self):
        assert self.type in TokenType
        if self.type == TokenType.OPERATOR:
            assert self.val in Operator


class FOLSyntaxException(Exception):
    """Exception class representing syntax errors"""


class LexerStream:
    """
    Lexer stream implementation to parse FOL.
    Pass in a stream of text and it will return a stream of tokens
    """
    def __init__(self, text_stream: Iterator[str] | str):
        if isinstance(text_stream, str):
            self.text_stream = None
            self.cur_text = text_stream
        else:
            self.text_stream = text_stream
            # Text stream shouldn't be empty, fine to throw exception
            self.cur_text = next(text_stream)
        self.idx = 0

    def __iter__(self):
        return self
    
    def get_text_from_stream(self):
        if self.idx >= len(self.cur_text):
            if not self.text_stream:
                raise StopIteration
            self.cur_text = next(self.text_stream)
            self.idx = 0
        
    # Currently does not support identifier names split across multiple stream elements
    def __next__(self) -> Token:
        # Find next non-whitespace character
        self.get_text_from_stream()
        cur_char = self.cur_text[self.idx]
        while cur_char.isspace():
            self.idx += 1
            self.get_text_from_stream()
            cur_char = self.cur_text[self.idx]

        # Return correct token type
        if cur_char in ["(", ")"]:
            self.idx += 1
            return Token(TokenType.BRACKET, cur_char)
        elif cur_char == ",":
            self.idx += 1
            return Token(TokenType.COMMA, ",")
        elif cur_char in ["!", "&", "|"]:
            self.idx += 1
            return Token(TokenType.OPERATOR, Operator(cur_char))
        elif cur_char == "-":
            next_char = self.cur_text[self.idx + 1]
            if next_char == ">":
                self.idx += 2
                return Token(TokenType.OPERATOR, Operator.IMPLIES)
            else:
                raise FOLSyntaxException(f"Unrecognized symbol: -{next_char}")
        elif cur_char == "<":
            next_str = self.cur_text[self.idx + 1 : self.idx + 3]
            if next_str == "->":
                self.idx += 3
                return Token(TokenType.OPERATOR, Operator.IFF)
            else:
                raise FOLSyntaxException(f"Unrecognized symbol: <{next_str}")
        elif cur_char.isalnum():
            tmp_idx = self.idx
            self.idx += 1
            while self.idx < len(self.cur_text) and self.cur_text[self.idx].isalnum():
                self.idx += 1
            ident_str = self.cur_text[tmp_idx : self.idx]
            if ident_str in ["forall", "exists"]:
                return Token(TokenType.OPERATOR, Operator(ident_str))
            return Token(TokenType.IDENTIFIER, ident_str)
        else:
            raise FOLSyntaxException(f"Unrecognized symbol: {cur_char}")


class Lexer:
    """
    Tokenize a string (or stream of strings) into a stream of tokens.
    Wraps the LexerStream to allow peeking of tokens
    """
    def __init__(self, text_stream: Iterator[str] | str):
        self.lexer = LexerStream(text_stream)
        self.token_stack: list[Token] = []
    
    def __iter__(self):
        return self
    
    def __next__(self) -> Token:
        if len(self.token_stack) > 0:
            return self.token_stack.pop()
        return next(self.lexer)
    
    def put_back(self, tok: Token):
        self.token_stack.append(tok)
    
    def peek(self):
        tok = self.__next__()
        self.put_back(tok)
        return tok
