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
Suds SAX Element unit tests.

Implemented using the 'pytest' testing framework.

"""

if __name__ == "__main__":
    import testutils
    testutils.run_using_pytest(globals())

from suds.sax.element import Element

import pytest


class TestChildAtPath:

    def test_backslash_as_path_separator(self):
        name1 = "child"
        name2 = "grandchild"
        root = self.__create_single_branch("root", name1, name2)[0]
        result = root.childAtPath(name1 + "\\" + name2)
        assert result is None

    def test_backslash_in_name(self):
        root, a, _, _ = self.__create_single_branch("root", "a", "b", "c")
        b_c = Element("b\\c")
        a.append(b_c)
        result = root.childAtPath("a/b\\c")
        assert result is b_c

    def test_child_leaf(self):
        root, child = self.__create_single_branch("root", "child")
        result = root.childAtPath("child")
        assert result is child

    def test_child_not_leaf(self):
        root, child, _ = self.__create_single_branch("root", "child",
            "grandchild")
        result = root.childAtPath("child")
        assert result is child

    def test_grandchild_leaf(self):
        root, _, grandchild = self.__create_single_branch("root", "child",
            "grandchild")
        result = root.childAtPath("child/grandchild")
        assert result is grandchild

    def test_grandchild_not_leaf(self):
        root, _, grandchild, _ = self.__create_single_branch("root", "child",
            "grandchild", "great grandchild")
        result = root.childAtPath("child/grandchild")
        assert result is grandchild

    def test_misplaced(self):
        root = self.__create_single_branch("root", "a", "x", "b")[0]
        result = root.childAtPath("a/b")
        assert result is None

    def test_missing(self):
        root = Element("root")
        result = root.childAtPath("an invalid path")
        assert result is None

    def test_name_including_spaces(self):
        root, _, child, _ = self.__create_single_branch("root", "dumbo",
            "foo  -  bar", "baz")
        result = root.childAtPath("dumbo/foo  -  bar")
        assert result is child

    @pytest.mark.parametrize("n", (2, 3))
    def test_repeated_path_separators(self, n):
        root, child, grandchild = self.__create_single_branch("root", "child",
            "grandchild")
        sep = "/" * n
        path = "child" + sep + "grandchild"
        result = root.childAtPath(path)
        assert result is grandchild

    def test_same_named(self):
        root, _, child, _ = self.__create_single_branch("root", "a", "a", "a")
        result = root.childAtPath("a/a")
        assert result is child

    @staticmethod
    def __create_single_branch(*args):
        """
        Construct a single branch element tree with given element names.

        Returns a list of constructed Element nodes from root to leaf.

        """
        result = []
        parent = None
        for name in args:
            e = Element(name)
            result.append(e)
            if parent is not None:
                parent.append(e)
            parent = e
        return result


@pytest.mark.parametrize("name, expected_prefix, expected_name", (
    ("", None, ""),
    ("bazinga", None, "bazinga"),
    ("test element name", None, "test element name"),
    ("aaa:bbb", "aaa", "bbb"),
    ("aaa:", "aaa", ""),
    (":aaa", "", "aaa"),
    ("aaa::bbb", "aaa", ":bbb"),
    ("aaa:bbb:ccc", "aaa", "bbb:ccc")))
def test_init_name(name, expected_prefix, expected_name):
    e = Element(name)
    assert e.prefix == expected_prefix
    assert e.name == expected_name
