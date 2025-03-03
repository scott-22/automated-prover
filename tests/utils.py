from functools import partial
from prover.language.lexer import Lexer
from prover.language.parser import parse
from prover.language.parser_ast import *


# Helper functions

def check_isomorphic(x: Formula, y: Formula, strict_funcs: bool = True) -> None:
    """
    Check if two ASTs are isomorphic. Two FOL ASTs are considered isomorphic if the
    first can be converted into the second by renaming all variables (bound or free)
    with respect to their scoping rules. Renaming functions can also be allowed by
    setting strict_funcs = False, allowing us to test skolemization.

    Since different bound variables can share the same name, there might be
    ambiguity. To compare the bound variables of each AST, we enumerate all
    quantifiers, and compare each bound variable by the unique index of its
    corresponding quantifier. To compare free variables, we can simply try to
    construct a bijective mapping between the symbols.

    If the two ASTs are not isomorphic, this function throws an exception.
    """
    # Enumerate all quantifiers, starting at 0
    quantifier_enumeration: int = 0
    # Map from bound vars to quantifiers in first AST
    x_bound_var_map: dict[str, int] = {}
    # Map from bound vars to quantifiers in second AST
    y_bound_var_map: dict[str, int] = {}
    # Bijective map from free vars in first AST to second AST
    free_var_bijection: dict[str, str] = {}
    # Bijective from func names in first AST to second AST
    func_bijection: dict[str, str] = {}
    
    def check_isomorphic_formula(x: Formula, y: Formula) -> None:
        """Helper for is_isomorphic to recursively check two formulas."""
        nonlocal quantifier_enumeration, x_bound_var_map, y_bound_var_map
        assert type(x) is type(y)
        assert x.name == y.name
        match x:
            case BinaryConnective():
                check_isomorphic_formula(x.left, y.left)
                check_isomorphic_formula(x.right, y.right)
            case UnaryConnective():
                check_isomorphic_formula(x.arg, y.arg)
            case Relation():
                assert len(x.args) == len(y.args)
                for x_arg, y_arg in zip(x.args, y.args):
                    check_isomorphic_term(x_arg, y_arg)
            case Quantifier():
                # Get and remember the original quantifiers binding this variable.
                # Note that these original quantifiers are not related in any way,
                # and do not need to be the same, since the name of a bound var
                # can be arbitrarily chosen
                x_original_quantifier = x_bound_var_map.get(x.var)
                y_original_quantifier = y_bound_var_map.get(y.var)

                # Map this variable to the current quantifier
                x_bound_var_map[x.var] = quantifier_enumeration
                y_bound_var_map[y.var] = quantifier_enumeration
                quantifier_enumeration += 1

                # Recursively check arguments, then reset the variable mapping to
                # the original quantifier afterwards
                check_isomorphic_formula(x.arg, y.arg)
                x_bound_var_map[x.var] = x_original_quantifier
                y_bound_var_map[y.var] = y_original_quantifier
            case _:
                raise ValueError(f"Unrecognized AST node type {x}")

    def check_isomorphic_term(x: Term, y: Term) -> None:
        """Helper for is_isomorphic to recursively check two terms."""
        nonlocal x_bound_var_map, y_bound_var_map, free_var_bijection, func_bijection
        assert type(x) is type(y)
        match x:
            case Constant():
                # Constants should be exactly the same
                assert x.name == y.name
            case Variable():
                # Check if the variable is bound or free in both ASTs
                x_is_bound = x_bound_var_map.get(x.name) is not None
                y_is_bound = y_bound_var_map.get(y.name) is not None
                assert x_is_bound == y_is_bound
                
                if x_is_bound:
                    # For bound vars, check their corresponding quantifiers
                    assert x_bound_var_map[x.name] == y_bound_var_map[y.name]
                elif x.name in free_var_bijection:
                    # For free vars, we attempt to construct a bijection.
                    # If a free var is recognized, check that the mapping
                    # is well-defined (note that it is guaranteed to be
                    # surjective by construction)
                    assert free_var_bijection[x.name] == y.name
                else:
                    # For unrecognized free vars, check that the mapping
                    # is injective
                    assert y.name not in free_var_bijection.values()
                    free_var_bijection[x.name] = y.name
            case Function():
                if strict_funcs:
                    # If we do not allow renaming functions, then check for equality
                    assert x.name == y.name
                elif x.name in func_bijection:
                    # Otherwise we try to construct a bijection similar to above
                    # When a func is recognized, check the mapping is well-defined
                    assert func_bijection[x.name] == y.name
                else:
                    # If a func is not recognized, check the mapping is injective
                    assert y.name not in func_bijection.values()
                    func_bijection[x.name] = y.name
                for x_arg, y_arg in zip(x.args, y.args):
                    check_isomorphic_term(x_arg, y_arg)
    
    check_isomorphic_formula(x, y)


def check_unique_var_names(ast: Formula) -> None:
    """
    Check if an AST has all unique variable names. That is, no two bound variables
    share a name, and no free variable has the same name as a bound one.
    """
    # Currently bound variables
    currently_bound_vars: set[str] = set()
    # Unique bound var names
    bound_var_names: set[str] = set()
    # Unique free var names
    free_var_names: set[str] = set()

    def check_unique_var_names_formula(ast: Formula) -> None:
        """Helper to recursively check a formula."""
        nonlocal currently_bound_vars, bound_var_names, free_var_names
        match ast:
            case BinaryConnective(_, left, right):
                check_unique_var_names_formula(left)
                check_unique_var_names_formula(right)
            case UnaryConnective(_, arg):
                check_unique_var_names_formula(arg)
            case Relation(_, args):
                for arg in args:
                    check_unique_var_names_term(arg)
            case Quantifier(_, var, arg):
                assert var not in bound_var_names
                assert var not in free_var_names
                bound_var_names.add(var)
                currently_bound_vars.add(var)
                check_unique_var_names_formula(arg)
                currently_bound_vars.remove(var)
    
    def check_unique_var_names_term(ast: Term) -> None:
        """Helper to recursively check a term."""
        nonlocal currently_bound_vars, bound_var_names, free_var_names
        match ast:
            case Variable(name):
                is_bound = name in currently_bound_vars
                if is_bound:
                    assert name not in free_var_names
                else:
                    assert name not in bound_var_names
                    free_var_names.add(name)
            case Function(_, args):
                for arg in args:
                    check_unique_var_names_term(arg)
    
    check_unique_var_names_formula(ast)


def make_ast(fol: str) -> Formula:
    return parse(Lexer(fol))


# Shorten AST names

Const = Constant
Var = Variable
Func = Function
Rel = Relation


def RelVar(name: str, *args: list[str]):
    """Relation consisting only of variables"""
    return Rel(name, list(map(Var, args)))


Forall = partial(Quantifier, "forall")
Exists = partial(Quantifier, "exists")
Not = partial(UnaryConnective, "!")
And = partial(BinaryConnective, "&")
Or = partial(BinaryConnective, "|")
Implies = partial(BinaryConnective, "->")
Iff = partial(BinaryConnective, "<->")
