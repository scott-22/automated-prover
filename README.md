# Intelligent Prover

This is an automated theorem prover supporting first-order logic (FOL), with smart premise selection. Given a theorem, it will try to find a proof based on the axioms and theorems that it already knows. If a proof is found, then the theorem is added to the knowledge base and can be used to help prove other theorems. Additional features are currently in progress, including support for equality and induction schemas, and improvements to premise selection.

When attempting to prove a theorem, this prover will select premises as follows:
1. Include all known axioms
1. Include a relevant subset of previously proven theorems as lemmas

In theory, any theorem should be provable from just the axioms. However, including certain lemmas may cut down the search tree and speed up the process. For technical details, see the [Premise Selection](#premise-selection) section below.

Note that FOL is complete but undecidable. This means that valid arguments should always be provable in theory (subject to resource constraints). However, the prover cannot always determine something to be unprovable, and might never terminate.

## Usage
To begin a proof session, run `intelligent-prover`. Ensure it has executable permissions (i.e, `chmod +x intelligent-prover`). There may be a delay the first time the prover runs, as it needs to download the sentence encoder model.

Below is an example proof session. For more details on the FOL syntax used by this prover, see the [following section](#fol-syntax).

```
% ./intelligent-prover
--- Intelligent Prover ---
This is an interactive proof session.

You can define axioms and prove theorems using the commands below. If you
would like to use smart premise selection, ensure that you provide a non-
empty description for your theorem. Otherwise, you may leave the
description blank.

Commands:
  axiom <FOL formula>                          Register a formula as an axiom
  theorem <FOL formula>                        Attempt to prove a theorem, and optionally provide a description
  describe <option> <index> <description>      Add description to the axiom/theorem at the given index ("axiom", "theorem")
  show <option> [index]                        Show all axioms/theorems, or the one at the given index ("axiom", "theorem")
  verbose                                      Toggle verbosity (whether to show details during premise selection)
  exit                                         Terminate the proof session

>>> axiom forall x !(Even(x) & Odd(x))
Enter description (Optional): No integer is both even and odd
Axiom added.

>>> axiom forall x ((Even(x) -> Odd(addOne(x))) & (Odd(x) -> Even(addOne(x))))
Enter description (Optional): Adding one to an even integer results in an odd integer, and vice versa
Axiom added.

>>> axiom Integer(0) & Even(0)
Enter description (Optional): Zero is an integer, and it is even
Axiom added.

>>> theorem !Even(addOne(0))
Enter description (Optional): One is not an even integer
Proof successful:
0. !Odd(x), !Even(x) (Premise, Axiom 0)
1. !Even(x0), Odd(addOne(x0)) (Premise, Axiom 1)
2. Even(0) (Premise, Axiom 2)
3. Even(addOne(0)) (Conclusion)
4. !Odd(addOne(0)) (Resolve 0, 3)
5. Odd(addOne(0)) (Resolve 2, 1)
6. ⊥ (Resolve 5, 4)

>>> theorem !forall x Even(x)
Enter description (Optional): Not all integers are even
Proof successful:
0. !Even(addOne(0)) (Premise, Theorem 0)
1. Even(x1) (Conclusion)
2. ⊥ (Resolve 0, 1)

>>> exit
```

### FOL Syntax
This FOL language defines both terms and formulas. Note that logical operators in the formulas section are given in decreasing operator precedence.
```
Terms:
  x, y1, cat, ...      Variables begin with a lowercase letter, and are alphanumeric
  Ten, X, 0, ...       Constants begin with a capital letter or number
  f(x, y, ...)         Functions begin with a lowercase letter, and contain at least one term

Formulas:
  R(x, y, ...)         Relations begin with a capital letter, and contain zero or more terms
  forall x ...         Universal quantification
  exists x ...         Existential quantification
  ! R(x)               Negation
  A(x) & B(x)          Conjunction
  A(x) | B(x)          Disjunction
  A(x) -> B(x)         Implication
  A(x) <-> B(x)        Biconditional
```

## Premise Selection
Selecting the right premises can speed up a proof, but selecting irrelevant ones can slow it down. This prover currently uses a semantic approach as a selection heuristic.

To determine which lemmas (previously proven theorems) are relevant to a given theorem, the prover relies on user-provided natural language descriptions. It will compare the description of the theorem against the descriptions of all previously proven theorems, and select lemmas that are semantically similar. That is, it choose lemmas that involve or describe similar ideas.

In order to implement the semantic premise selection, it computes a similarity score between the sentence embeddings of these natural language descriptions, and chooses lemmas with a sufficiently high similarity. Currently, the prover uses a Hugging Face model as the sentence encoder, and calculates cosine similarity as its metric.

## Development

To set up a virtual environment and run unit tests, run the following commands from the parent directory:
1. `python3 -m venv venv`
1. `source venv/bin/activate`
1. `pip install -r requirements.txt`
1. `pytest`
