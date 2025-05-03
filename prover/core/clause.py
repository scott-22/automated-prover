"""Data structure for clauses."""

from typing import Iterator, Self
from prover.language.lexer import Operator
from prover.language.normal_form import NormalFormException
from prover.language.parser_ast import *
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
        if len(self) == 0:
            return "⊥"
        return str(self.literals)


def extract_clauses(ast: Formula) -> list[Clause]:
    """Given a formula in CNF, return a list of all extracted clauses."""
    clauses: list[Clause] = []

    def extract_literals_from_disjunctive_subtree(
            ast: Formula,
            lit_set: set[Literal]
    ) -> None:
        """Recursive helper to add all literals from a disjunctive clause."""
        match ast:
            case BinaryConnective(Operator.OR, left, right):
                extract_literals_from_disjunctive_subtree(left, lit_set)
                extract_literals_from_disjunctive_subtree(right, lit_set)
            case UnaryConnective(Operator.NOT, Relation(name, args)):
                lit_set.add(Literal(name, True, args))
            case Relation(name, args):
                lit_set.add(Literal(name, False, args))
            case _:
                raise NormalFormException(
                    "Given AST was not converted into CNF properly, "
                    f"found {ast} when a disjunctive subtree was expected"
                )

    def extract_clause_from_conjunctive_subtree(ast: Formula) -> None:
        nonlocal clauses
        """Recursive helper to extract clauses from CNF."""
        match ast:
            case BinaryConnective(Operator.AND, left, right):
                extract_clause_from_conjunctive_subtree(left)
                extract_clause_from_conjunctive_subtree(right)
            case _:
                lit_set: set[Literal] = set()
                extract_literals_from_disjunctive_subtree(ast, lit_set)
                clauses.append(Clause(lit_set))

    extract_clause_from_conjunctive_subtree(ast)
    return clauses
