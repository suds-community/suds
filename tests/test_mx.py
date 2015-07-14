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
Suds MX system unit tests.

Implemented using the 'pytest' testing framework.

"""

if __name__ == "__main__":
    import testutils
    testutils.run_using_pytest(globals())

from suds.mx.typer import Typer

import pytest


def _prefix(i):
    """Prefixes expected to be constructed by Typer.getprefix()."""
    return "ns%d" % (i,)


class TestTyper:

    class Test_genprefix:

        class MockNode:

            def __init__(self, namespace_mapping):
                self.mock_call_params = []
                self.__namespace_mapping = namespace_mapping

            def resolvePrefix(self, prefix, default):
                self.mock_call_params.append((prefix, default))
                return self.__namespace_mapping.get(prefix, default)

        def test_no_mapped_prefixes(self):
            node = self.__class__.MockNode({})
            test_namespace = "test namespace"
            result = Typer.genprefix(node, ("unused-prefix", test_namespace))
            assert result == (_prefix(1), test_namespace)
            assert node.mock_call_params == [(_prefix(1), None)]

        def test_several_already_mapped_prefixes(self):
            test_namespace = "test namespace"
            node = self.__class__.MockNode({
                _prefix(1): "another namespace",
                _prefix(2): "another namespace"})
            result = Typer.genprefix(node, ("unused-prefix", test_namespace))
            assert result == (_prefix(3), test_namespace)
            assert node.mock_call_params == [
                (_prefix(i), None) for i in [1, 2, 3]]

        def test_last_free_namespace(self):
            test_namespace = "test namespace"
            node = self.__class__.MockNode(dict(
                (_prefix(i), "another namespace")
                for i in range(1, 1023)))
            result = Typer.genprefix(node, ("unused-prefix", test_namespace))
            assert result == (_prefix(1023), test_namespace)
            expected_calls = [(_prefix(i), None) for i in range(1, 1024)]
            assert node.mock_call_params == expected_calls

        def test_no_free_namespace(self):
            test_namespace = "test namespace"
            node = self.__class__.MockNode(dict(
                (_prefix(i), "another namespace") for i in range(1, 1024)))
            e = pytest.raises(Exception,
                Typer.genprefix, node, ("unused-prefix", test_namespace)).value
            try:
                assert str(e) == "auto prefix, exhausted"
            finally:
                del e  # explicitly break circular reference chain in Python 3
            expected_calls = [(_prefix(i), None) for i in range(1, 1024)]
            assert node.mock_call_params == expected_calls

        def test_already_mapped_namespace_with_no_unused_prefix_before(self):
            test_prefix_index = 2
            test_namespace = "test namespace"
            node = self.__class__.MockNode({
                _prefix(1): "another namespace",
                _prefix(test_prefix_index): test_namespace,
                _prefix(3): "another namespace"})
            result = Typer.genprefix(node, ("unused-prefix", test_namespace))
            assert result == (_prefix(test_prefix_index), test_namespace)
            expected_calls = [(_prefix(i), None)
                for i in range(1, test_prefix_index + 1)]
            assert node.mock_call_params == expected_calls

        def test_already_mapped_namespace_with_unused_prefix_before(self):
            unused_prefix_index = 2
            test_namespace = "test namespace"
            node = self.__class__.MockNode({
                _prefix(1): "another namespace",
                _prefix(3): test_namespace,
                _prefix(4): "another namespace"})
            result = Typer.genprefix(node, ("unused-prefix", test_namespace))
            assert result == (_prefix(unused_prefix_index), test_namespace)
            expected_calls = [(_prefix(i), None)
                for i in range(1, unused_prefix_index + 1)]
            assert node.mock_call_params == expected_calls
