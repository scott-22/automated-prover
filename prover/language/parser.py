"""Simple recursive descent parser to generate an AST."""

from .lexer import *
from .normal_form import *
from .parser_ast import *
from .skolemization import *


def parse(lexer: Lexer) -> Formula:
    """Generate an AST from a Lexer. Binary connectives are left-associative."""
    try:
        return parseFormula("begin", lexer)
    except StopIteration:
        raise FOLSyntaxException("Unexpected end of expression")


# Operator precedence (higher means higher precedence)
OP_PRECEDENCE = {
    Operator.NOT: 3,  # Unary operators all have the highest precedence by default
    Operator.FORALL: 3,
    Operator.EXISTS: 3,
    Operator.AND: 2,
    Operator.OR: 1,
    Operator.IMPLIES: 0,
    Operator.IFF: 0,
    Operator.DUMMY: -1,  # Dummy to indicate no current operator
}


def parseFormula(
    parent_op: Operator, lexer: Lexer, parenthesized=False, top_level_paren=False
) -> Formula:
    """
    Parse a formula.
    Pass in the parent operator (logical connective) to parse according to precedence,
    and whether this expression is parenthesized. If this expression is parenthesized,
    we keep track of whether it is a "top-level" parenthesized expression, in which case
    we clear the closing bracket from the token stream. Note that binary connectives are
    parsed to be left-associative.
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
            case Token(TokenType.BRACKET, ")"):
                if parenthesized:
                    if top_level_paren:
                        next(lexer)  # Clear bracket from token stream
                    return left_form
                else:
                    raise FOLSyntaxException(
                        f"Unexpected closing bracket while parsing formula"
                    )
            case Token(TokenType.OPERATOR, op) if op not in [
                Operator.NOT,
                Operator.FORALL,
                Operator.EXISTS,
            ]:
                if OP_PRECEDENCE[parent_op] >= OP_PRECEDENCE[op]:
                    return left_form
            case _:
                raise FOLSyntaxException(
                    f"Expected an operator, instead got {tok.type}: {tok.val}"
                )
        op = next(lexer)
        right_form = parseFormula(
            op.val, lexer, parenthesized, False
        )  # Right-hand operands are not top-level paren expressions
        left_form = BinaryConnective(op.val, left_form, right_form)


def parseOperand(lexer: Lexer) -> Formula:
    """Parse an operand to be part of a binary connective expression."""
    tok = next(lexer)
    match tok:
        case Token(TokenType.BRACKET, "("):
            # Parse a parenthesized formula expression
            return parseFormula("begin", lexer, True, True)
        case Token(TokenType.IDENTIFIER, name):
            # Expect a relation
            return parseRelation(name, lexer)
        case Token(TokenType.OPERATOR, Operator.NOT):
            # Parse a unary connective (negation)
            form = parseOperand(lexer)
            return UnaryConnective(Operator.NOT, form)
        case Token(TokenType.OPERATOR, op) if op in [Operator.FORALL, Operator.EXISTS]:
            # First parse the bound variable for the quantifier
            var = next(lexer)
            if var.type != "identifier":
                raise FOLSyntaxException(
                    f"Expected variable after quantifier, instead got {tok.type}: {tok.val}"
                )
            elif var.val[0].isupper() or var.val[0].isdigit():
                raise FOLSyntaxException(
                    f"Bound variable {var.val} cannot begin with capital letter or digit"
                )
            # Then parse the formula
            form = parseOperand(lexer)
            return Quantifier(op, var.val, form)
        case _:
            raise FOLSyntaxException(
                f"Unexpected {tok.type} while parsing formula: {tok.val}"
            )


def parseNegation(lexer: Lexer) -> Formula:
    """Parse the negation of a formula (without initial negation operator)"""
    form = parseFormula(lexer)
    return UnaryConnective("!", form)


def parseRelation(name: str, lexer: Lexer) -> Relation:
    """Parse a relation (without initial identifier, which is passed in)"""
    tok = next(lexer)
    if tok != Token(TokenType.BRACKET, "("):
        raise FOLSyntaxException(f"Expected open bracket after relation {name}")
    terms: list[Term] = []
    tok = next(lexer)
    while tok != Token(TokenType.BRACKET, ")"):
        match tok:
            case Token(TokenType.IDENTIFIER, arg_name):
                terms.append(parseTerm(arg_name, lexer))
            case Token(TokenType.COMMA, _):
                # Commas are technically optional
                pass
            case _:
                raise FOLSyntaxException(
                    f"Unexpected {tok.type} in relation {name}: {tok.val}"
                )
        tok = next(lexer)
    return Relation(name, terms)


def parseTerm(name: str, lexer: Lexer) -> Term:
    """Parse a term (without initial identifier, which is passed in)"""
    tok = lexer.peek()
    match tok:
        case Token(TokenType.COMMA, _) | Token(TokenType.BRACKET, ")"):
            # We either have a constant or variable
            if name[0].isupper() or name[0].isdigit():
                return Constant(name)
            else:
                return Variable(name)
        case Token(TokenType.BRACKET, "("):
            return parseFunction(name, lexer)
        case _:
            raise FOLSyntaxException(
                f"Unexpected {tok.type} while parsing term {name}: {tok.val}"
            )


def parseFunction(name: str, lexer: Lexer) -> Term:
    """Parse a function (without initial identifier, which is passed in)"""
    tok = next(lexer)
    if tok != Token(TokenType.BRACKET, "("):
        raise FOLSyntaxException(f"Expected open bracket after function {name}")
    terms: list[Term] = []
    tok = next(lexer)
    while tok != Token(TokenType.BRACKET, ")"):
        match tok:
            case Token(TokenType.IDENTIFIER, arg_name):
                terms.append(parseTerm(arg_name, lexer))
            case Token(TokenType.COMMA, _):
                # Commas are technically optional
                pass
            case _:
                raise FOLSyntaxException(
                    f"Unexpected {tok.type} in function {name}: {tok.val}"
                )
        tok = next(lexer)
    if len(terms) == 0:
        raise FOLSyntaxException(
            f"Function {name} of arity 0 should be a constant instead"
        )
    return Function(name, terms)
