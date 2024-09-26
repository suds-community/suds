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
Suds MX appender unit tests.

Implemented using the 'pytest' testing framework.

"""

if __name__ == "__main__":
    import testutils
    testutils.run_using_pytest(globals())

from suds.mx.appender import PrimitiveAppender, TextAppender
from suds.xsd.sxbasic import Attribute
from suds.sax.element import Element

from unittest.mock import Mock


class MockContent:
    def __init__(self, tag, value):
        self.tag = tag
        self.value = value
        self.type = Mock(spec=Attribute)


class TestPrimitiveAppender:

    def test_append_string(self):
        parent = Element('foo')
        content = MockContent("_TEST_TAG", "")
        primitive_appender = PrimitiveAppender(Mock())
        primitive_appender.append(parent, content)
        assert parent.get("TEST_TAG") == ""

        parent = Element('foo')
        content = MockContent("_TEST_TAG", "bar")
        primitive_appender = PrimitiveAppender(Mock())
        primitive_appender.append(parent, content)
        assert parent.get("TEST_TAG") == "bar"

    def test_append_string_to_child(self):
        parent = Mock()
        content = MockContent("TEST_TAG", "")
        primitive_appender = PrimitiveAppender(Mock())
        mock_node = Mock()
        primitive_appender.node = Mock(return_value=mock_node)
        primitive_appender.append(parent, content)
        mock_node.setText.assert_called_once_with("")
        parent.append.assert_called_once_with(mock_node)

        parent = Mock()
        content = MockContent("TEST_TAG", "bar")
        primitive_appender = PrimitiveAppender(Mock())
        mock_node = Mock()
        primitive_appender.node = Mock(return_value=mock_node)
        primitive_appender.append(parent, content)
        mock_node.setText.assert_called_once_with("bar")
        parent.append.assert_called_once_with(mock_node)


class TestTextAppender:

    def test_append_string(self):
        parent = Element('foo')
        content = MockContent("_TEST_TAG", "")
        primitive_appender = TextAppender(Mock())
        primitive_appender.append(parent, content)
        assert parent.get("TEST_TAG") == ""

        parent = Element('foo')
        content = MockContent("_TEST_TAG", "bar")
        primitive_appender = TextAppender(Mock())
        primitive_appender.append(parent, content)
        assert parent.get("TEST_TAG") == "bar"

    def test_append_string_to_child(self):
        parent = Mock()
        content = MockContent("TEST_TAG", "")
        primitive_appender = TextAppender(Mock())
        mock_node = Mock()
        primitive_appender.node = Mock(return_value=mock_node)
        primitive_appender.append(parent, content)
        mock_node.setText.assert_called_once_with("")
        parent.append.assert_called_once_with(mock_node)

        parent = Mock()
        content = MockContent("TEST_TAG", "bar")
        primitive_appender = TextAppender(Mock())
        mock_node = Mock()
        primitive_appender.node = Mock(return_value=mock_node)
        primitive_appender.append(parent, content)
        mock_node.setText.assert_called_once_with("bar")
        parent.append.assert_called_once_with(mock_node)
