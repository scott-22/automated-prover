"""A proof session to keep track of axioms and proved theorems."""

from dataclasses import dataclass
from sentence_transformers import SentenceTransformer
from ..core.clause import extractClauses, Clause
from ..core.resolution import resolution, ProofClause
from ..language.lexer import Lexer, Operator
from ..language.parser import parse, transform, SymbolManager, UnaryConnective


@dataclass
class Theorem:
    """
    An axiom or theorem used during the proof session. We cache its associated clauses
    and store semantic metadata, which is used during premise selection.
    """

    fol: str  # String representation as a FOL formula
    index: int  # Index corresponding to current theorem
    clauses: list[Clause]  # Clauses extracted from the theorem
    description: str = ""  # Semantic description of the theorem

    def __repr__(self) -> str:
        if len(self.description) == 0:
            return self.fol
        return self.fol + "\n" + self.description


class ProofSession:
    """
    Proof session that manages axioms and theorems, and decides which previously proved
    theorems should be used as premises. 
    """
    
    def __init__(self):
        self.symbol_manager = SymbolManager()
        self.axioms: list[Theorem] = []
        self.theorems: list[Theorem] = []
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.SIMILARITY_THRESHOLD = 0.5

    def addAxiom(self, axiom: str) -> None:
        """Add a user-supplied axiom."""
        self.axioms.append(
            Theorem(
                axiom,
                len(self.axioms),
                extractClauses(transform(parse(Lexer(axiom)), self.symbol_manager)),
            )
        )
    
    def getPremises(self, description: str) -> list[Clause]:
        """Get the premises used to prove a given theorem."""
        # Always include all axioms
        premises: list[Clause] = sum(
            map(lambda theorem: theorem.clauses, self.axioms), []
        )
        # If a description is given, use semantic similarity based on the sentence
        # embeddings to search for relevant theorems
        if len(description) > 0:
            all_theorems = list(
                filter(lambda theorem: theorem.description, self.theorems)
            )
            if len(all_theorems) > 0:
                all_theorem_embeddings = self.model.encode(
                    list(map(lambda theorem: theorem.description, all_theorems))
                )
                description_embedding = self.model.encode(description)
                similarities = self.model.similarity(
                    all_theorem_embeddings,
                    description_embedding,
                )
                for idx, similarity in enumerate(similarities):
                    if similarity > self.SIMILARITY_THRESHOLD:
                        premises.extend(all_theorems[idx].clauses)
        return premises
    
    def proveTheorem(self, theorem: str, description: str) -> list[ProofClause] | None:
        """
        Try to prove the given theorem via refutation. That is, by taking its negation
        and trying to derive a contradiction with the premises.

        If a non-empty description is passed, then it will select premises from among
        previously proven theorems.

        Returns the proof if one was found, or None if resolution terminates without
        proof. Note that first-order logic is complete, so if a proof exists, it will be
        found (in theory, subject to resource constraints of course). However, FOL is
        undecidable, so this function is not guaranteed to terminate if no proof exists.
        """
        conclusion_ast = parse(Lexer(theorem))
        negated_conclusion = UnaryConnective(Operator.NOT, conclusion_ast)
        conclusion_clauses = extractClauses(
            transform(negated_conclusion, self.symbol_manager)
        )
        proof_result = resolution(self.getPremises(description), conclusion_clauses)
        if proof_result is not None:
            self.theorems.append(
                Theorem(
                    theorem,
                    len(self.theorems),
                    extractClauses(transform(conclusion_ast, self.symbol_manager)),
                    description,
                )
            )
        return proof_result
