from typing import Iterator
from collections import deque
from .clause import Clause


# Perform all resolutions of two clauses and return results as an iterator
def resolve(x: Clause, y: Clause) -> Iterator[Clause]:
    for lit in x:
        if -lit in y:
            new_clause = x.resolve(lit) + y.resolve(lit)
            if new_clause.isTautology():
                continue
            yield new_clause


# Perform resolution algorithm, return whether a contradiction was reached
def resolveAllClauses(clauses: list[Clause], next_clauses: deque[Clause]) -> bool:
    while len(next_clauses) > 0:
        cur_clause = next_clauses.popleft()
        for clause in clauses:
            for c in resolve(cur_clause, clause):
                if len(c) == 0:
                    # We obtain the empty clause (contradiction), thus return
                    return True
                next_clauses.append(c)
        clauses.append(cur_clause)
    return False
