"""Define all AST nodes representing FOL language elements"""

from dataclasses import dataclass


@dataclass
class Term:
    """
    High-level class representing a term, defined recursively as a bound variable,
    a constant, or a function of terms
    """

    name: str


@dataclass
class Constant(Term):
    """
    Constant (as defined by a specific theory). Note that constants are differentiated
    from variables by beginning with an uppercase letter or a digit, whereas variables
    must begin with a lowercase letter
    """

    pass


@dataclass
class Variable(Term):
    """
    Free or bound variable. Note that we include bound variables here too even
    though they're not technically terms, for easier parsing
    """

    pass


@dataclass
class Function(Term):
    """Function applied to a list of argument terms"""

    args: list[Term]


@dataclass
class Formula:
    """
    High-level class representing a formula, defined recursively as an atom (relation) or
    a logical expression composed of formulas
    """

    name: str


@dataclass
class Relation(Formula):
    """A relation applied to a list of argument terms. Note that relations are atoms"""

    args: list[Term]


@dataclass
class Quantifier(Formula):
    """A quantifier (has a bound variable and a formula)"""

    var: Variable
    arg: Formula


@dataclass
class UnaryConnective(Formula):
    """A unary connective (i.e, negation)"""

    arg: Formula


@dataclass
class BinaryConnective(Formula):
    """A binary connective (and, or, implies, etc)"""

    left: Formula
    right: Formula
