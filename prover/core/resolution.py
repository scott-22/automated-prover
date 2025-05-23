"""Main resolution loop and proof generation."""

from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Iterable
from .clause import Clause


class ClauseType(Enum):
    """Whether a clause came from a premise, conclusion, or was resolved."""
    
    PREMISE = 0  # Clause from one of the argument premises
    CONCLUSION = 1  # Clause from the conclusion
    OTHER = 2  # Intermediate result of resolving two other clauses

    def __lt__(self, other) -> bool:
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented


@dataclass
class ClauseSource:
    """The originating source of a premise clause (the index of its axiom or theorem)."""

    is_axiom: bool  # Whether it comes from an axiom or theorem
    index: int  # The index of its originating axiom of theorem


@dataclass
class ProofClause:
    """Class that holds a clause and metadata to reconstruct the proof."""

    clause: Clause
    index: int | None  # Index corresponding to current clause, or None if not assigned yet
    resolvents: tuple[int, int] | None  # Indices corresponding to resolvents, if applicable
    clause_type: ClauseType = ClauseType.OTHER
    clause_source: ClauseSource | None = None  # Is not None iff clause is from a premise

    def __repr__(self) -> str:
        suffix = ""
        if self.resolvents is not None:
            suffix = f" (Resolve {", ".join(map(str, self.resolvents))})"
        elif self.clause_type == ClauseType.PREMISE:
            suffix = (
                f" (Premise, {"Axiom" if self.clause_source.is_axiom else "Theorem"}"
                f" {self.clause_source.index})"
            )
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
        clauses.append(cur_clause)
        for clause in clauses[:-1]:
            for new_clause in cur_clause.clause.resolve(clause.clause):
                new_proof_clause = ProofClause(
                    new_clause, None, (cur_clause.index, clause.index)
                )
                if len(new_clause) == 0:
                    # We obtain the empty clause (contradiction), thus return
                    return new_proof_clause
                next_clauses.append(new_proof_clause)
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
            for idx in clause.resolvents:
                if idx not in included_indices:
                    included_indices.add(idx)
                    included_clauses.append(clauses[idx])

    proof: list[ProofClause] = []
    new_index_map: dict[int, int] = {}
    # Add all included clauses into a result list, ensuring that premises come
    # before conclusions. Note that the sort is guaranteed to be stable, so the
    # resolved clauses remain in dependency order. Only premises and conclusions
    # are rearranged, which is ok since they do not have dependencies.
    for idx in sorted(
        included_indices, key=lambda idx: (clauses[idx].clause_type, clauses[idx].index)
    ):
        clause = clauses[idx]
        new_index_map[clause.index] = len(proof)
        clause.index = len(proof)
        if clause.resolvents is not None:
            clause.resolvents = (
                new_index_map[clause.resolvents[0]],
                new_index_map[clause.resolvents[1]],
            )
        proof.append(clause)

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
    premises: Iterable[tuple[ClauseSource, Clause]], conclusions: Iterable[Clause]
) -> list[ProofClause] | None:
    """
    Perform resolution on the premise clauses, and the clauses obtained from the negation
    of the conclusion. Returns the proof if one was found, or None if resolution
    terminates without proof. Premise clauses should be passed in as a 2-tuple containing
    its source and the clause itself.

    Note that first-order logic is complete, so if a proof exists, it will be found (in
    theory, subject to resource constraints of course). However, FOL is undecidable, so
    this function is not guaranteed to terminate if no proof exists.
    """
    clauses = []
    next_clauses = deque(
        ProofClause(clause, None, None, ClauseType.CONCLUSION) for clause in conclusions
    )
    next_clauses.extend(
        ProofClause(clause, None, None, ClauseType.PREMISE, source)
        for source, clause in premises
    )
    proof_result = resolveAllClauses(clauses, next_clauses)
    if proof_result is not None:
        return extractProof(proof_result, clauses)
    return None
