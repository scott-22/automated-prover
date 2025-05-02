"""Data structure for clauses."""

from typing import Iterator, Self
from prover.language.normal_form import NormalFormException
from prover.language.parser_ast import Formula
from .unification import Literal, Unifier


class Clause:
    """Class representing a clause (disjunctive set of literals)."""

    def __init__(self, literals: set[Literal]):
        self.literals = literals

    def __iter__(self) -> Iterator[Literal]:
        return iter(self.literals)

    def resolve(self, other: Self) -> Iterator[Self]:
        """Perform all resolutions of two clauses and return the results as an iterator."""
        for cur_lit in self:
            for other_lit in other:
                if cur_lit.id == other_lit.id and cur_lit.negated != other_lit.negated:
                    unifier = Unifier(cur_lit.terms, other_lit.terms)
                    if unifier:
                        new_clause = Clause(
                            set(unifier(lit) for lit in self if lit != cur_lit)
                            | set(unifier(lit) for lit in other if lit != other_lit)
                        )
                        if not new_clause.isTautology():
                            yield new_clause

    def __len__(self) -> int:
        return len(self.literals)

    def isTautology(self) -> bool:
        """Whether the current clause is a tautology (universally valid)."""
        for lit in self.literals:
            if -lit in self.literals:
                return True
        return False

    def __repr__(self) -> str:
        return str(self.literals)
