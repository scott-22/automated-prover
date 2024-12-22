"""Simple recursive descent parser to generate an AST"""

from .parser_ast import *
from .lexer import *


def parse(lexer: Lexer) -> Formula:
    """Generate an AST from a Lexer"""
    try:
        return parseFormula("begin", lexer)
    except StopIteration:
        raise FOLSyntaxException("Unexpected end of expression")


# Operator precedence (higher means higher precedence)
OP_PRECEDENCE = {
    "!": 3,       # Unary operators all have the highest precedence by default
    "forall": 3,
    "exists": 3,
    "&": 2,
    "|": 1,
    "->": 0,
    "<->": 0,
    "begin": -1,  # Dummy to indicate no current operator
}


def parseFormula(parent_op: str, lexer: Lexer, parenthesized = False) -> Formula:
    """
    Parse a formula.
    Pass in the parent operator (logical connective) to parse according to precedence,
    and whether this expression is parenthesized.
    """
    left_form = parseOperand(lexer)
    # Keep parsing binary connectives in a left-associative way until we reach end of stream or
    # we hit an operator with lower precedence than current context
    while True:
        try:
            tok = lexer.peek()
        except StopIteration:
            return left_form 
        match tok:
            case Token("bracket", ")"):
                if parenthesized:
                    next(lexer)  # Clear bracket from token stream
                    return left_form
                else:
                    raise FOLSyntaxException(f"Unexpected closing bracket while parsing formula")
            case Token("operator", op) if op not in ["!", "forall", "exists"]:
                if OP_PRECEDENCE[parent_op] >= OP_PRECEDENCE[op]:
                    return left_form
            case _:
                raise FOLSyntaxException(f"Expected an operator, instead got {tok.type}: {tok.val}")
        op = next(lexer)
        right_form = parseFormula(op.val, lexer, parenthesized)
        left_form = BinaryConnective(op.val, left_form, right_form)


def parseOperand(lexer: Lexer) -> Formula:
    """Parse an operand to be part of a binary connective expression."""
    tok = next(lexer)
    match tok:
        case Token("bracket", "("):
            # Parse a parenthesized formula expression
            return parseFormula("begin", lexer, True)
        case Token("identifier", name):
            # Expect a relation
            return parseRelation(name, lexer)
        case Token("operator", "!"):
            # Parse a unary connective (negation)
            form = parseOperand(lexer)
            return UnaryConnective("!", form)
        case Token("operator", op) if op in ["forall", "exists"]:
            # First parse the bound variable for the quantifier
            var = next(lexer)
            if var.type != "identifier":
                raise FOLSyntaxException(f"Expected variable after quantifier, instead got {tok.type}: {tok.val}")
            # Then parse the formula
            form = parseOperand(lexer)
            return Quantifier(op, var.val, form)
        case _:
            raise FOLSyntaxException(f"Unexpected {tok.type} while parsing formula: {tok.val}")
    

def parseNegation(lexer: Lexer) -> Formula:
    """Parse the negation of a formula (without initial negation operator)"""
    form = parseFormula(lexer)
    return UnaryConnective("!", form)


def parseRelation(name: str, lexer: Lexer) -> Relation:
    """Parse a relation (without initial identifier, which is passed in)"""
    tok = next(lexer)
    if tok != Token("bracket", "("):
        raise FOLSyntaxException(f"Expected open bracket after relation {name}")
    terms: list[Term] = []
    tok = next(lexer)
    while tok != Token("bracket", ")"):
        match tok:
            case Token("identifier", arg_name):
                terms.append(parseTerm(arg_name, lexer))
            case Token("comma", _):
                # Commas are technically optional
                pass
            case _:
                raise FOLSyntaxException(f"Unexpected {tok.type} in relation {name}: {tok.val}")
        tok = next(lexer)
    return Relation(name, terms)


def parseTerm(name: str, lexer: Lexer) -> Term:
    """Parse a term (without initial identifier, which is passed in)"""
    tok = lexer.peek()
    match tok:
        case Token("comma", _) | Token("bracket", ")"):
            # We either have a constant or variable
            if name[0].isupper() or name[0].isdigit():
                return Constant(name)
            else:
                return Variable(name)
        case Token("bracket", "("):
            return parseFunction(name, lexer)
        case _:
            raise FOLSyntaxException(f"Unexpected {tok.type} while parsing term {name}: {tok.val}")


def parseFunction(name: str, lexer: Lexer) -> Term:
    """Parse a function (without initial identifier, which is passed in)"""
    tok = next(lexer)
    if tok != Token("bracket", "("):
        raise FOLSyntaxException(f"Expected open bracket after function {name}")
    terms: list[Term] = []
    tok = next(lexer)
    while tok != Token("bracket", ")"):
        match tok:
            case Token("identifier", arg_name):
                terms.append(parseTerm(arg_name, lexer))
            case Token("comma", _):
                # Commas are technically optional
                pass
            case _:
                raise FOLSyntaxException(f"Unexpected {tok.type} in function {name}: {tok.val}")
        tok = next(lexer)
    if len(terms) == 0:
        raise FOLSyntaxException(f"Function {name} of arity 0 should be a constant instead")
    return Function(name, terms)
