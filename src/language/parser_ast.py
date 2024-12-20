from dataclasses import dataclass

# Define all AST nodes representing FOL language elements


# High-level class representing a term, defined recursively as a bound variable,
# a constant, or a function of terms
@dataclass
class Term:
    name: str

# Constant (as defined by a specific theory)
@dataclass
class Constant(Term):
    pass

# Free or bound variable. Note that we include bound variables here too even
# though they're not technically terms, for easier parsing
@dataclass
class Variable(Term):
    pass

# Function applied to a list of argument terms
@dataclass
class Function(Term):
    args: list[Term]


# High-level class representing a formula, defined recursively as an atom (relation) or
# a logical expression composed of formulas
@dataclass
class Formula:
    name: str

# A relation applied to a list of argument terms
@dataclass
class Relation(Formula):
    args: list[Term]

# A logical operator (quantifier or connective)
@dataclass
class Operator:
    pass

# A quantifier (has a bound variable and a formula)
@dataclass
class Quantifier:
    var: Variable
    arg: Formula

# A unary connective (i.e, negation)
@dataclass
class UnaryConnective:
    arg: Formula

# A binary connective (and, or, implies, etc)
@dataclass
class BinaryConnective:
    left: Formula
    right: Formula


type ASTNode = Term | Formula
