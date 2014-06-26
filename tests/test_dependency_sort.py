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

from suds.xsd.deplist import DepList

import pytest

from six import iteritems


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


def test_dependency_sort():
    # f --+-----+-----+
    # |   |     |     |
    # |   v     v     v
    # |   e --> d --> c --> b
    # |   |           |     |
    # +---+-----------+-----+--> a --> x
    dependency_list = [
        ("c", ("a", "b")),
        ("e", ("d", "a")),
        ("d", ("c",)),
        ("b", ("a",)),
        ("f", ("e", "c", "d", "a")),
        ("a", ("x",)),
        ("x", ())]
    input = [x[0] for x in dependency_list]
    deplist = DepList()
    deplist.add(*dependency_list)
    result = deplist.sort()
    assert sorted(result) == sorted(dependency_list)
    _assert_dependency_order((x[0] for x in result), dict(dependency_list))


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
