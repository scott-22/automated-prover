"""Main resolution loop and proof generation."""

from collections import deque
from dataclasses import dataclass
from enum import StrEnum
from typing import Iterable
from .clause import Clause


class ClauseType(StrEnum):
    PREMISE = "premise"  # Clause from one of the argument premises
    CONCLUSION = "conclusion"  # Clause representing the conclusion
    OTHER = "other"  # Intermediate result of resolving two other clauses


@dataclass
class ProofClause:
    """Class that holds a clause and metadata to reconstruct the proof."""

    clause: Clause
    index: int | None  # Index corresponding to current clause, or None if not assigned yet
    resolvents: tuple[int, int] | None  # Indices corresponding to resolvents, if applicable
    clause_type: ClauseType = ClauseType.OTHER

    def __repr__(self) -> str:
        suffix = ""
        if self.resolvents is not None:
            suffix = f" (Resolve {", ".join(self.resolvents)})"
        elif self.clause_type == ClauseType.PREMISE:
            suffix = " (Premise)"
        elif self.clause_type == ClauseType.CONCLUSION:
            suffix = " (Conclusion)"
        return f"{self.index}. {self.clause}" + suffix


def resolveAllClauses(
    clauses: list[ProofClause], next_clauses: deque[ProofClause]
) -> ProofClause | None:
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


def extractProof(
    empty_clause: ProofClause, clauses: list[ProofClause]
) -> list[ProofClause]:
    """
    Given an empty clause obtained during resolution, and the list of all obtained clauses,
    extract and return the proof. Note that this function will mutate the original clause list
    such that it is no longer valid after calling.
    """
    included_indices: set[int] = set()
    included_clauses: deque[ProofClause] = deque([empty_clause])
    # Traverse the proof dependency graph and note all included indices
    while len(included_clauses) > 0:
        clause = included_clauses.popleft()
        if clause.resolvents is not None:
            for index in clause.resolvents:
                if index not in included_indices:
                    included_indices.add(index)
                    included_clauses.append(clauses[index])
    proof: list[ProofClause] = []
    new_index_map: dict[int, int] = {}
    # Add all included clauses into a result list
    for index in sorted(included_indices):
        clause = clauses[index]
        new_index_map[clause.index] = len(proof)
        clause.index = len(proof)
        proof.append(clause)

    # Ensure that conclusion comes after all premises. First find index of the conclusion
    conclusion_index = len(proof)
    for index, clause in enumerate(proof):
        if clause.clause_type == ClauseType.CONCLUSION:
            conclusion_index = index
            break
    # Swap elements until there are no more premises after the conclusion. Note that all
    # premises will appear before resolved clauses since they have no dependent clauses
    while (
        conclusion_index < len(proof) - 1
        and proof[conclusion_index + 1].clause_type == ClauseType.PREMISE
    ):
        proof[conclusion_index], proof[conclusion_index + 1] = (
            proof[conclusion_index + 1],
            proof[conclusion_index],
        )
        conclusion_index += 1

    # Add the empty clause
    proof.append(
        ProofClause(
            empty_clause.clause,
            len(proof),
            (
                new_index_map[empty_clause.resolvents[0]],
                new_index_map[empty_clause.resolvents[1]],
            ),
        )
    )
    return proof


def resolution(
    premises: Iterable[Clause], conclusion: Clause
) -> list[ProofClause] | None:
    """
    Try to prove the conclusion from the premises using resolution. Returns the proof if one
    was found, or None if resolution terminates without proof.

    Note that first-order logic is complete, so if a proof exists, it will be found (in
    theory, subject to resource constraints of course). However, FOL is undecidable, so this
    function is not guaranteed to terminate if no proof exists.
    """
    clauses = [conclusion]
    next_clauses = deque(premises)
    proof_result = resolveAllClauses(clauses, next_clauses)
    if proof_result is not None:
        return extractProof(proof_result, clauses)
    return None
