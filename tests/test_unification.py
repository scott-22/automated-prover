"""Test unifying two terms during resolution."""

import pytest
from prover.core.unification import Unifier
from utils import *


@pytest.mark.parametrize(
    "first_terms, second_terms, valid, test_unifier_cases",
    [
        (
            make_terms("a, b, c"),
            make_terms("b, c, a"),
            True,
            [
                (make_terms("a"), make_terms("c")),
                (make_terms("b"), make_terms("c")),
                (make_terms("c"), make_terms("c")),
                (make_terms("a, b, c"), make_terms("c, c, c")),
                (make_terms("b, c, a"), make_terms("c, c, c")),
                (make_terms("f(a, A, g(x, b))"), make_terms("f(c, A, g(x, c))")),
            ],
        ),
        (
            make_terms("f(f, f(g(f), h(f)))"),
            make_terms("f(g, f(g(h), h(h)))"),
            True,
            [
                (make_terms("f"), make_terms("h")),
                (make_terms("g"), make_terms("h")),
                (make_terms("h"), make_terms("h")),
                (make_terms("f(f, f(g(f), h(f)))"), make_terms("f(h, f(g(h), h(h)))")),
                (make_terms("f(g, f(g(h), h(h)))"), make_terms("f(h, f(g(h), h(h)))")),
            ],
        ),
        (
            make_terms("u, h(t, h(x))"),
            make_terms("h(t, h(x)), u"),
            True,
            [
                (make_terms("u"), make_terms("h(t, h(x))")),
                (make_terms("t"), make_terms("t")),
                (make_terms("x"), make_terms("x")),
                (make_terms("u, h(t, h(x))"), make_terms("h(t, h(x)), h(t, h(x))")),
                (make_terms("h(t, h(x)), u"), make_terms("h(t, h(x)), h(t, h(x))")),
            ],
        ),
        (
            make_terms("0, f(y), y, g(h(f(z)))"),
            make_terms("x, z, 1, g(h(t))"),
            True,
            [
                (make_terms("x"), make_terms("0")),
                (make_terms("y"), make_terms("1")),
                (make_terms("z"), make_terms("f(1)")),
                (make_terms("t"), make_terms("f(f(1))")),
                (make_terms("0, f(y), y, g(h(f(z)))"), make_terms("0, f(1), 1, g(h(f(f(1))))")),
                (make_terms("x, z, 1, g(h(t))"), make_terms("0, f(1), 1, g(h(f(f(1))))")),
            ],
        ),
        (
            make_terms("f(g(v, w), h(u, FIVE), TEN)"),
            make_terms("f(u, h(g(v, w), FIVE), v)"),
            True,
            [
                (make_terms("u"), make_terms("g(TEN, w)")),
                (make_terms("v"), make_terms("TEN")),
                (make_terms("w"), make_terms("w")),
                (
                    make_terms("f(g(v, w), h(u, FIVE), TEN)"),
                    make_terms("f(g(TEN, w), h(g(TEN, w), FIVE), TEN)"),
                ),
                (
                    make_terms("f(u, h(g(v, w), FIVE), v)"),
                    make_terms("f(g(TEN, w), h(g(TEN, w), FIVE), TEN)"),
                ),
            ],
        ),
        (
            make_terms("f(x, y, z)"),
            make_terms("g(x, y, z)"),
            False,
            [],
        ),
        (
            make_terms("f(x, y)"),
            make_terms("f(x, y, z)"),
            False,
            [],
        ),
        (
            make_terms("f(0, 1)"),
            make_terms("f(x, x)"),
            False,
            [],
        ),
        (
            make_terms("x"),
            make_terms("g(y, z, f(h(y), h(x)))"),
            False,
            [],
        ),
        (
            make_terms("y, g(y)"),
            make_terms("f(g(x)), x"),
            False,
            [],
        ),
    ]
)
def test_unification(first_terms, second_terms, valid, test_unifier_cases):
    """
    Test unification of two terms.
    """
    unifier = Unifier(first_terms, second_terms)
    if valid:
        assert unifier
        for original_terms, mapped_terms in test_unifier_cases:
            for original_term, mapped_term in zip(original_terms, mapped_terms):
                assert unifier.replaceVars(original_term) == mapped_term
    else:
        assert not unifier
