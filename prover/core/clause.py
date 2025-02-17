from typing import Iterator, Self


# An atomic formula or its negation
class Literal:
    def __init__(self, id: str, negated: bool):
        self.id = id
        self.negated = negated

    def __eq__(self, other) -> bool:
        return self.id == other.id and self.negated == other.negated

    def __hash__(self) -> int:
        return hash((self.id, self.negated))

    def isSameAtom(self, other) -> bool:
        return self.id == other.id

    def __neg__(self) -> Self:
        return Literal(self.id, not self.negated)

    def __repr__(self) -> str:
        return f"Literal({self.id}, {self.negated})"


# Disjunctive set of literals to perform resolution
class Clause:
    def __init__(self, literals: list[Literal]):
        self.literals = literals

    def __iter__(self) -> Iterator[Literal]:
        return iter(self.literals)

    def resolve(self, lit) -> Self:
        return Clause([l for l in self.literals if l.id != lit.id])

    def __add__(self, other) -> Self:
        lit_set = set()
        new_literals = []
        for lit in self.literals + other.literals:
            if lit not in lit_set:
                lit_set.add(lit)
                new_literals.append(lit)
        return Clause(new_literals)

    def __len__(self) -> int:
        return len(self.literals)

    def isTautology(self) -> bool:
        lit_set = set()
        for lit in self.literals:
            if -lit in lit_set:
                return True
            lit_set.add(lit)
        return False

    def __repr__(self) -> str:
        return str(self.literals)
