"""Define all AST nodes representing FOL language elements"""

from dataclasses import dataclass
from typing import Self


@dataclass(unsafe_hash=True)
class Term:
    """
    Abstract class representing a term, defined recursively as a bound variable,
    a constant, or a function of terms
    """

    name: str

    def __contains__(self, var: Self) -> bool:
        """Checks if a term contains a variable or constant."""
        raise NotImplementedError()


@dataclass(unsafe_hash=True)
class Constant(Term):
    """
    Constant (as defined by a specific theory). Note that constants are differentiated
    from variables by beginning with an uppercase letter or a digit, whereas variables
    must begin with a lowercase letter
    """

    def __contains__(self, var: Term) -> bool:
        return self == var

    def __repr__(self) -> str:
        return self.name


@dataclass(unsafe_hash=True)
class Variable(Term):
    """
    Free or bound variable. Note that we include bound variables here too even
    though they're not technically terms, for easier parsing
    """

    def __contains__(self, var: Term) -> bool:
        return self == var

    def __repr__(self) -> str:
        return self.name


@dataclass
class Function(Term):
    """Function applied to a list of argument terms"""

    args: list[Term]

    def __contains__(self, var: Term) -> bool:
        return any(var in arg for arg in self.args)

    def __hash__(self) -> int:
        return hash((self.name, tuple(self.args)))

    def __repr__(self) -> str:
        return f"{self.name}({", ".join(map(str, self.args))})"


@dataclass
class Formula:
    """
    Abstract class representing a formula, defined recursively as an atom (relation) or
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

    var: str
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
