# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify it under
# the terms of the (LGPL) GNU Lesser General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Library Lesser General Public License
# for more details at ( http://www.gnu.org/licenses/lgpl.html ).
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
# written by: Jurko Gospodnetić ( jurko.gospodnetic@pke.hr )

"""
Dependency sort unit tests.

Implemented using the 'pytest' testing framework.

"""

import testutils
if __name__ == "__main__":
    testutils.run_using_pytest(globals())

from suds.xsd.depsort import dependency_sort

import pytest
from six import iteritems

import copy


# some of the tests in this module make sense only with assertions enabled
# (note though that pytest's assertion rewriting technique, as used by default
# in recent pytest releases, will keep assertions enabled inside the used test
# modules even when the underlying Python interpreter has been run using the -O
# command-line option)
try:
    assert False
except AssertionError:
    assertions_enabled = True
else:
    assertions_enabled = False


# shared test data

# f --+-----+-----+
# |   |     |     |
# |   v     v     v
# |   e --> d --> c --> b
# |   |           |     |
# +---+-----------+-----+--> a --> x
_test_dependency_tree = {
    "x": (),
    "a": ("x",),
    "b": ("a",),
    "c": ("a", "b"),
    "d": ("c",),
    "e": ("d", "a"),
    "f": ("e", "c", "d", "a")}


def test_dependency_sort():
    dependency_tree = _test_dependency_tree
    result = dependency_sort(dependency_tree)
    assert sorted(result) == sorted(iteritems(dependency_tree))
    _assert_dependency_order((x[0] for x in result), dependency_tree)


def test_dependency_sort_does_not_mutate_input():
    dependency_tree = _test_dependency_tree

    # save the original dependency tree structure information
    expected_deps = {}
    expected_deps_ids = {}
    for x, y in iteritems(dependency_tree):
        expected_deps[x] = copy.copy(y)
        expected_deps_ids[id(x)] = id(y)

    # run the dependency sort
    dependency_sort(dependency_tree)

    # verify that the dependency tree structure is unchanged
    assert len(dependency_tree) == len(expected_deps)
    for key, deps in iteritems(dependency_tree):
        # same deps for each key
        assert id(deps) == expected_deps_ids[id(key)]
        # deps structure compare with the original copy
        assert deps == expected_deps[key]
        # explicit deps content id matching just in case the container's __eq__
        # is not precise enough
        _assert_same_content_set(deps, expected_deps[key])


###############################################################################
#
# Test utilities.
#
###############################################################################

def _assert_dependency_order(sequence, dependencies):
    """
    Assert that a sequence is ordered dependencies first.

    The only way an earlier entry is allowed to have a later entry as its
    dependency is if they are both part of the same dependency cycle.

    """
    sequence = list(sequence)
    dependency_closure = _transitive_dependency_closure(dependencies)
    for i, a in enumerate(sequence):
        for b in sequence[i + 1:]:
            a_dependent_on_b = b in dependency_closure[a]
            b_dependent_on_a = a in dependency_closure[b]
            assert b_dependent_on_a or not a_dependent_on_b


def _assert_same_content_set(lhs, rhs):
    """Assert that two iterables have the same content (order independent)."""
    counter_lhs = _counter(lhs)
    counter_rhs = _counter(rhs)
    assert counter_lhs == counter_rhs


def _counter(iterable):
    """Return an {id: count} dictionary for all items from `iterable`."""
    counter = {}
    for x in iterable:
        counter[id(x)] = counter.setdefault(id(x), 0) + 1
    return counter


def _transitive_dependency_closure(dependencies):
    """
    Returns a transitive dependency closure.

    If target A is dependent on target B, and target B is in turn dependent on
    target C, then target A is also implicitly dependent on target C. A
    transitive dependency closure is an expanded dependency collection so that
    in it all such implicit dependencies have been explicitly specified.

    """
    def clone(deps):
        return dict((k, set(v)) for k, v in iteritems(deps))
    closure = None
    new = clone(dependencies)
    while new != closure:
        closure = clone(new)
        for k, deps in iteritems(closure):
            for dep in deps:
                new[k] |= closure[dep]
    return closure


###############################################################################
#
# Test utility tests.
#
###############################################################################

@pytest.mark.skipif(not assertions_enabled, reason="assertions disabled")
@pytest.mark.parametrize("sequence, dependencies", (
    (["x", "y"], {"x": ("y",), "y": ()}),
    (["x", "y"], {"x": ("z",), "z": ("y",), "y": ()}),
    (["y", "x", "z"], {"x": ("z",), "z": ("y",), "y": ()}),
    (["z", "y", "x"], {"x": ("z",), "z": ("y",), "y": ()}),
    # unrelated element groups
    (["y", "a", "x", "b"], {"x": (), "y": ("x",), "a": (), "b": ("a",)}),
    (["x", "b", "y", "a"], {"x": (), "y": ("x",), "a": (), "b": ("a",)}),
    (["b", "x", "y", "a"], {"x": (), "y": ("x",), "a": (), "b": ("a",)}),
    (["a", "y", "b", "x"], {"x": (), "y": ("x",), "a": (), "b": ("a",)}),
    (["a", "b", "y", "x"], {"x": (), "y": ("x",), "a": (), "b": ("a",)})))
def test_assert_dependency_order__invalid(sequence, dependencies):
    pytest.raises(AssertionError, _assert_dependency_order, sequence,
        dependencies)


@pytest.mark.parametrize("sequence, dependencies", (
    (["y", "x"], {"x": ("y",), "y": ()}),
    (["y", "x"], {"x": ("z",), "z": ("y",), "y": ()}),
    (["y", "z", "x"], {"x": ("z",), "z": ("y",), "y": ()}),
    # unrelated element groups
    (["x", "y", "a", "b"], {"x": (), "y": ("x",), "a": (), "b": ("a",)}),
    (["x", "a", "y", "b"], {"x": (), "y": ("x",), "a": (), "b": ("a",)}),
    (["a", "x", "y", "b"], {"x": (), "y": ("x",), "a": (), "b": ("a",)}),
    (["a", "x", "b", "y"], {"x": (), "y": ("x",), "a": (), "b": ("a",)}),
    (["a", "b", "x", "y"], {"x": (), "y": ("x",), "a": (), "b": ("a",)}),
    # dependency cycle
    (["x", "y"], {"x": ("y",), "y": ("x",)}),
    (["y", "x"], {"x": ("y",), "y": ("x",)}),
    # elements not mentioned in the dependency tree
    ([1], {}),
    (["a"], {"x": ("y",), "y": ()})))
def test_assert_dependency_order__valid(sequence, dependencies):
    _assert_dependency_order(sequence, dependencies)


@pytest.mark.skipif(not assertions_enabled, reason="assertions disabled")
@pytest.mark.parametrize("lhs, rhs", (
    # empty
    #    ([1, 2.0, 6], [1, 2, 6]),
    ((), (1,)),
    ([2], []),
    ([], (4, 2)),
    ([], (x for x in [8, 4])),
    ((x for x in [1, 1]), []),
    # without duplicates
    ([1, 2, 3], [1, 2, 4]),
    ([1, 2, 3], [1, 2]),
    ([1, 2, 3], [1, 4]),
    ([0], [0.0]),
    ([0], [0.0]),
    # with duplicates
    ([1, 1], [1]),
    ((x for x in [1, 1]), [1]),
    ([1, 1], [1, 2, 1]),
    ([1, 1, 2, 2], [1, 2, 1]),
    # different object ids
    ([object()], [object()])))
def test_assert_same_content_set__invalid(lhs, rhs):
    pytest.raises(AssertionError, _assert_same_content_set, lhs, rhs)


@pytest.mark.parametrize("lhs, rhs", (
    # empty
    ((), ()),
    ([], []),
    ([], ()),
    ([], (x for x in [])),
    ((x for x in []), []),
    # matching without duplicates
    ([1, 2, 6], [1, 2, 6]),
    ([1, 2, 6], [6, 2, 1]),
    # matching with duplicates
    ([1, 2, 2, 6], [6, 2, 1, 2]),
    # matching object ids
    ([_assert_same_content_set], [_assert_same_content_set])))
def test_assert_same_content_set__valid(lhs, rhs):
    _assert_same_content_set(lhs, rhs)


def test_counter():
    a = object()
    b = object()
    c = object()
    d = object()
    input = [a, b, b, c, c, d, a, a, a, d, b, b, b, b, b, a, d]
    result = _counter(input)
    assert len(result) == 4
    assert result[id(a)] == input.count(a)
    assert result[id(b)] == input.count(b)
    assert result[id(c)] == input.count(c)
    assert result[id(d)] == input.count(d)


def test_counter__empty():
    assert _counter([]) == {}
