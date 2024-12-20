from dataclasses import dataclass
from typing import Iterator

# Types of tokens representing basic FOL language
TYPES = [
    "operator",    # Logical operator
    "identifier",  # Name of a function, relation, or bound/free variable
    "infix_rel",   # Infix relation (ie, equality "=")
    "bracket",     # Open or close bracket
    "comma",       # Separator between function params
]


# Tokens to represent FOL
@dataclass
class Token:
    type: str
    val: str

    def __post_init__(self):
        assert self.type in TYPES


# Exception class representing syntax errors
class FOLSyntaxException(Exception):
    pass


# Lexer to parse FOL
# Pass in a stream of text and it will return a stream of tokens
class Lexer:
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
            return Token("bracket", cur_char)
        elif cur_char == ",":
            self.idx += 1
            return Token("comma", ",")
        elif cur_char in ["!", "&", "|"]:
            self.idx += 1
            return Token("bracket", cur_char)
        elif cur_char == "-":
            next_char = self.cur_text[self.idx + 1]
            if next_char == ">":
                self.idx += 2
                return Token("operator", "->")
            else:
                raise FOLSyntaxException(f"Syntax error at symbol: -{next_char}")
        elif cur_char == "<":
            next_str = self.cur_text[self.idx + 1 : self.idx + 3]
            if next_str == "->":
                self.idx += 3
                return Token("operator", "<->")
            else:
                raise FOLSyntaxException(f"Syntax error at symbol: <{next_str}")
        elif cur_char == "=":
            return Token("infix_rel", "=")
        elif cur_char.isalnum():
            tmp_idx = self.idx
            self.idx += 1
            while self.idx < len(self.cur_text) and self.cur_text[self.idx].isalnum():
                self.idx += 1
            return Token("identifier", self.cur_text[tmp_idx : self.idx])
        else:
            raise FOLSyntaxException(f"Syntax error at char: {cur_char}")
