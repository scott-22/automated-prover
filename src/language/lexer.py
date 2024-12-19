from dataclasses import dataclass
from typing import Iterator

# Types of tokens representing basic FOL language
TYPES = [
    "operator",    # Logical operator
    "identifier",  # Name of a function, relation, or bound/free variable
    "infix_rel",   # Infix relation (ie, equality "=")
    "bracket",     # Open or close bracket
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
        self.token_type = ""
        self.token_val = ""

    def __iter__(self):
        return self
    
    def get_text_from_stream(self):
        if self.idx >= len(self.cur_text):
            if not self.text_stream:
                raise StopIteration
            self.cur_text = next(self.text_stream)
            self.idx = 0
        
    # Currently does not support identifier names split across multiple stream elements
    def __next__(self):
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
        elif cur_char in ["!", "&", "|"]:
            self.idx += 1
            return Token("bracket", cur_char)
        elif cur_char == "-":
            if self.cur_text[self.idx + 1] == ">":
                self.idx += 2
                return Token("operator", "->")
            else:
                raise FOLSyntaxException
        elif cur_char == "<":
            if self.cur_text[self.idx + 1 : self.idx + 3] == "->":
                self.idx += 3
                return Token("operator", "<->")
            else:
                raise FOLSyntaxException
        elif cur_char == "=":
            return Token("infix_rel", "=")
        elif cur_char.isalnum():
            tmp_idx = self.idx + 1
            while tmp_idx < len(self.cur_text) and self.cur_text[tmp_idx].isalnum():
                tmp_idx += 1
            return Token("identifier", self.cur_text[self.idx : tmp_idx])
        else:
            raise FOLSyntaxException
