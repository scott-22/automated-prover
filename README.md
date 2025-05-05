# Automated Theorem Prover

This is an automated theorem prover supporting first-order logic (FOL). Additional features are currently in progress, including support for equality and induction schemas, as well as smart premise selection. Given arguments and a conclusion, it uses a resolution procedure to determine entailment.

Note that FOL is complete but undecidable. This means that valid arguments should always be provable in theory (subject to resource constraints). However, the prover cannot always determine something to be unprovable, and might never terminate.

## Usage
To begin a proof session, run `intelligent-prover`. Ensure it has executable permissions (i.e, `chmod +x intelligent-prover`). Below is an example proof session. For more details on the FOL syntax, see the following section.

```
% ./intelligent-prover
--- Intelligent Prover ---
This is an interactive proof session.

Commands:
  axiom <FOL formula>        Register a formula as an axiom
  theorem <FOL formula>      Attempt to prove a theorem
  show <option>              Option should be "axioms" or "theorems"
  exit                       Terminate the proof session

>>> axiom forall animal (Cat(animal) -> Mammal(animal))
Axiom added.

>>> axiom exists animal (Pet(animal) & !Mammal(animal))
Axiom added.

>>> theorem exists animal (Pet(animal) & !Cat(animal))
Proof successful:
0. Mammal(animal), !Cat(animal) (Premise)
1. Pet(func_0()) (Premise)
2. !Mammal(func_0()) (Premise)
3. Cat(animal12), !Pet(animal12) (Conclusion)
4. Cat(func_0()) (Resolve 1, 3)
5. !Cat(func_0()) (Resolve 2, 0)
6. ⊥ (Resolve 5, 4)

>>> show axiom
0. forall animal (Cat(animal) -> Mammal(animal))
1. exists animal (Pet(animal) & !Mammal(animal))

>>> show theorem
0. exists animal (Pet(animal) & !Cat(animal))

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

## Development

To set up a virtual environment and run unit tests, run the following commands from the parent directory:
1. `python3 -m venv venv`
1. `source venv/bin/activate`
1. `pip install -r requirements.txt`
1. `pytest`
