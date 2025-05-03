"""Main resolution loop."""

from collections import deque
from dataclasses import dataclass
from .clause import Clause


@dataclass
class ProofClause:
    """Class that holds a clause and metadata to reconstruct the proof."""
    
    clause: Clause
    index: int | None  # Index corresponding to current clause, or None if not assigned yet
    resolvents: tuple[int, int] | None  # Indices corresponding to resolvents, if applicable


def resolution(clauses: list[ProofClause], next_clauses: deque[ProofClause]) -> ProofClause | None:
    """
    Perform the resolution algorithm, and return the empty clause if a contradiction is reached,
    or None if a contradiction could not be reached. Note that there is no guarantee that this
    function terminates.
    """
    while len(next_clauses) > 0:
        cur_clause = next_clauses.popleft()
        cur_clause.index = len(clauses)
        for clause in clauses:
            for new_clause in cur_clause.clause.resolve(clause.clause):
                new_proof_clause = ProofClause(
                    new_clause, None, (cur_clause.index, clause.index)
                )
                if len(new_clause) == 0:
                    # We obtain the empty clause (contradiction), thus return
                    return new_proof_clause
                next_clauses.append(new_proof_clause)
        clauses.append(cur_clause)
    return None

