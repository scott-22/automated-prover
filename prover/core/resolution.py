"""Main resolution loop."""

from typing import Iterator
from collections import deque
from .clause import Clause


def resolution(clauses: list[Clause], next_clauses: deque[Clause]) -> bool:
    """Perform the resolution algorithm, and return whether a contradiction was reached."""
    while len(next_clauses) > 0:
        cur_clause = next_clauses.popleft()
        for clause in clauses:
            for new_clause in cur_clause.resolve(clause):
                if len(new_clause) == 0:
                    # We obtain the empty clause (contradiction), thus return
                    return True
                next_clauses.append(new_clause)
        clauses.append(cur_clause)
    return False
