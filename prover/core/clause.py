"""Data structure for clauses, and extraction of clauses from CNF."""

from typing import Iterator, Self
from ..language.lexer import Operator
from ..language.normal_form import NormalFormException
from ..language.parser_ast import *
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
        return ", ".join(map(str, self.literals))


def extractClauses(ast: Formula) -> list[Clause]:
    """Given a formula in CNF, return a list of all extracted clauses."""
    clauses: list[Clause] = []

    def extractLiteralsFromDisjunctiveSubtree(
            ast: Formula,
            lit_set: set[Literal]
    ) -> None:
        """Recursive helper to add all literals from a disjunctive clause."""
        match ast:
            case BinaryConnective(Operator.OR, left, right):
                extractLiteralsFromDisjunctiveSubtree(left, lit_set)
                extractLiteralsFromDisjunctiveSubtree(right, lit_set)
            case UnaryConnective(Operator.NOT, Relation(name, args)):
                lit_set.add(Literal(name, True, tuple(args)))
            case Relation(name, args):
                lit_set.add(Literal(name, False, tuple(args)))
            case _:
                raise NormalFormException(
                    "Given AST was not converted into CNF properly, "
                    f"found {ast} when a disjunctive subtree was expected"
                )

    def extractClauseFromConjunctiveSubtree(ast: Formula) -> None:
        nonlocal clauses
        """Recursive helper to extract clauses from CNF."""
        match ast:
            case BinaryConnective(Operator.AND, left, right):
                extractClauseFromConjunctiveSubtree(left)
                extractClauseFromConjunctiveSubtree(right)
            case _:
                lit_set: set[Literal] = set()
                extractLiteralsFromDisjunctiveSubtree(ast, lit_set)
                clauses.append(Clause(lit_set))

    extractClauseFromConjunctiveSubtree(ast)
    return clauses
