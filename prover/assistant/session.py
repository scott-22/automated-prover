"""A proof session to keep track of axioms and proved theorems."""

from ..core.clause import extractClauses, Clause
from ..core.resolution import resolution, ProofClause
from ..language.lexer import Lexer, Operator
from ..language.parser import parse, transform, SymbolManager, UnaryConnective


class ProofSession:
    """
    Proof session that manages axioms and theorems, and decides which previously proved
    theorems should be used as premises. 
    """
    
    def __init__(self):
        self.symbol_manager = SymbolManager()
        self.axioms: dict[str, list[Clause]] = {}
        self.theorems: dict[str, list[Clause]] = {}

    def addAxiom(self, axiom: str) -> None:
        """Add a user-supplied axiom."""
        self.axioms[axiom] = extractClauses(
            transform(parse(Lexer(axiom)), self.symbol_manager)
        )
    
    def getPremises(self, theorem: str) -> list[Clause]:
        """Get the premises used to prove a given theorem."""
        # TODO: Add heuristics based on theorem embeddings
        return sum(self.axioms.values(), [])
    
    def proveTheorem(self, theorem: str) -> list[ProofClause] | None:
        """
        Try to prove the given theorem via refutation. That is, by taking its negation
        and trying to derive a contradiction with the premises.

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
        proof_result = resolution(self.getPremises(theorem), conclusion_clauses)
        if proof_result is not None:
            self.theorems[theorem] = extractClauses(
                transform(conclusion_ast, self.symbol_manager)
            )
        return proof_result
