"""Data structure for literals as well as a unification algorithm."""

from dataclasses import dataclass
from typing import Self
from prover.language.parser_ast import *


@dataclass
class Literal:
    """
    An atomic formula or its negation. A formula is atomic iff it is a relation.
    Note that literals may share term objects, so terms should be treated as immutable.
    """

    id: str  # Name of the relation
    negated: bool  # Whether the atom is negated
    terms: list[Term]  # Arguments of the relation


class Unifier:
    """
    A helper class to unify two literals. Represents a substitution that maps variables
    to terms and can be applied to an entire literal.
    """

    def __init__(self, left: list[Term], right: list[Term]):
        self.var_map: dict[str, Term] | None = {}
        for left_term, right_term in zip(left, right):
            self.unify(self.replaceVars(left_term), self.replaceVars(right_term))
            if not self:
                break

    def invalid(self) -> None:
        """Make the unifier invalid (set var map to None)."""
        self.var_map = None

    def unify(self, left: Term, right: Term) -> None:
        """
        Attempts to recursively unify the two terms, initializing the Unifier object to
        a valid unification. If no unification exists, then the var maps is set to None.
        At the top-level call, the var map should start off empty. Note that variable
        names should be standardized apart such that two variables share the same name
        only if they came from the same clause.
        """
        match left, right:
            case Variable(left_name), Variable(right_name):
                if left_name != right_name:
                    match self.mapVar(left_name), self.mapVar(right_name):
                        case None, None:
                            self.var_map[left_name] = right
                        case mapped, None:
                            if mapped != right:
                                self.var_map[right_name] = mapped
                        case None, mapped:
                            if mapped != left:
                                self.var_map[left_name] = mapped
                        case left_mapped, right_mapped:
                            if left_mapped != right_mapped:
                                self.invalid()
            case Variable(name), _:
                if (mapped := self.mapVar(name)) is not None:
                    if mapped != right:
                        self.invalid()
                else:
                    right_mapped = self.replaceVars(right)
                    if left in right_mapped:
                        self.invalid()
                    else:
                        self.var_map[name] = right_mapped
            case _, Variable(name):
                if (mapped := self.mapVar(name)) is not None:
                    if mapped != left:
                        self.invalid()
                else:
                    left_mapped = self.replaceVars(left)
                    if right in left_mapped:
                        self.invalid()
                    else:
                        self.var_map[name] = left_mapped
            case Constant(left_name), Constant(right_name):
                if left_name != right_name:
                    self.invalid()
            case Function(left_name, left_args), Function(right_name, right_args):
                if left_name != right_name or len(left_args) != len(right_args):
                    self.invalid()
                else:
                    for left_arg, right_arg in zip(left_args, right_args):
                        self.unify(self.replaceVars(left_arg), self.replaceVars(right_arg))
                        if not self:
                            break
            case _:
                self.invalid()

    def mapVar(self, var: str, default: Term | None = None) -> Term:
        """
        Get the term associated with the given variable. We recursively replace the
        variables in the returned term.
        """
        if var not in self.var_map:
            return default
        self.var_map[var] = self.replaceVars(self.var_map[var])
        return self.var_map[var]

    def replaceVars(self, term: Term) -> Term:
        """Map all the variables in a term."""
        match term:
            case Variable(name):
                return self.mapVar(name, term)
            case Function(name, args):
                return Function(name, list(map(self.replaceVars, args)))
        return term
    
    def __bool__(self) -> bool:
        """Whether this unifier is valid."""
        return self.var_map is not None

    def __call__(self, lit: Literal) -> Self:
        """Apply this unifier to a literal."""
        return Literal(lit.id, lit.negated, list(map(self.replaceVars, lit.terms)))
