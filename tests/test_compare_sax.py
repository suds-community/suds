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
CompareSAX testing utility unit tests.

"""

if __name__ == "__main__":
    import testutils
    testutils.run_using_pytest(globals())

import suds
import suds.sax.document
import suds.sax.parser
from testutils.assertion import assert_no_output
from testutils.compare_sax import CompareSAX

import pytest
from six import text_type, u

import xml.sax


# CompareSAX class uses Python assertions to report failed comparison results
# so we need to skip the tests in this module if Python assertions have been
# disabled in the CompareSAX implementation module.
skip_test_if_CompareSAX_assertions_disabled = pytest.mark.skipif(
    not CompareSAX.assertions_enabled(),
    reason="CompareSAX assertions disabled")


@skip_test_if_CompareSAX_assertions_disabled
@pytest.mark.parametrize("data", (
    "",
    "<bad1/><bad2/>",
    '<bad a="1" a="1"/>',
    "<bad><bad>xml</document></bad>"))
def test_failed_parsing(data, capsys):
    pytest.raises(xml.sax.SAXParseException, CompareSAX.data2data, data, data)
    assert_no_output(capsys)


class TestMatched:
    """Successful CompareSAX matching tests."""

    @skip_test_if_CompareSAX_assertions_disabled
    def test_empty_document(self, capsys):
        a = suds.sax.document.Document()
        b = suds.sax.document.Document()
        CompareSAX.document2document(a, b)
        assert_no_output(capsys)

    @skip_test_if_CompareSAX_assertions_disabled
    @pytest.mark.parametrize(("data1", "data2"), (
        # Simple matches.
        ('<a><ns:b xmlns:ns="x"/></a>', '<a><ns:b xmlns:ns="x"/></a>'),
        ('<a><b xmlns="x"/></a>', '<a><b xmlns="x"/></a>'),
        ('<a xmlns="x"><b/></a>', '<a xmlns="x"><b/></a>'),
        # Extra namespace declarations.
        ('<ns1:b xmlns:ns1="two"/>', '<ns2:b xmlns="one" xmlns:ns2="two"/>'),
        ('<ns1:b xmlns:ns1="2"/>', '<ns2:b xmlns:ns3="1" xmlns:ns2="2"/>'),
        ('<b xmlns="1"/>', '<ns1:b xmlns="0" xmlns:ns1="1" xmlns:ns2="2"/>'),
        # Mismatched namespace prefixes.
        ('<a xmlns="one"/>', '<ns:a xmlns:ns="one"/>'),
        ('<ns1:b xmlns:ns1="two"/>', '<ns2:b xmlns:ns2="two"/>'),
        # Numeric unicode character references.
        (u("<a>\u2606</a>"), "<a>&#%d;</a>" % (0x2606,))))
    def test_data2data(self, data1, data2, capsys):
        CompareSAX.data2data(data1, data2)
        assert_no_output(capsys)

    @skip_test_if_CompareSAX_assertions_disabled
    @pytest.mark.parametrize("type1", (suds.byte_str, text_type))
    @pytest.mark.parametrize("type2", (suds.byte_str, text_type))
    def test_string_input_types(self, type1, type2, capsys):
        xml = "<a/>"
        CompareSAX.data2data(type1(xml), type2(xml))
        assert_no_output(capsys)

    @skip_test_if_CompareSAX_assertions_disabled
    def test_xml_encoding(self, capsys):
        """Test that the encoding listed in the XML declaration is honored."""
        xml_format = u('<?xml version="1.0" encoding="%s"?><a>\u00D8</a>')
        data1 = (xml_format % ("UTF-8",)).encode('utf-8')
        data2 = (xml_format % ("latin1",)).encode('latin1')
        CompareSAX.data2data(data1, data2)
        assert_no_output(capsys)


class TestMismatched:
    """Failed CompareSAX matching tests."""

    @skip_test_if_CompareSAX_assertions_disabled
    @pytest.mark.parametrize(("data1", "data2", "expected_context"), (
        # Different element namespaces.
        ("<a/>", '<a xmlns="x"/>', "data2data.<a>.namespace"),
        ('<a xmlns="1"/>', '<a xmlns="2"/>', "data2data.<a>.namespace"),
        ('<r><a xmlns="1"/></r>', '<r><a xmlns="2"/></r>',
            "data2data.<r>.<a>.namespace"),
        ('<r><tag><a xmlns="1"/></tag><y/></r>',
            '<r><tag><a xmlns="2"/></tag><y/></r>',
            "data2data.<r>.<tag(1/2)>.<a>.namespace"),
        # Different textual content in text only nodes.
        ("<a>one</a>", "<a>two</a>", "data2data.<a>.text"),
        ("<a>x</a>", "<a>x </a>", "data2data.<a>.text"),
        ("<a>x</a>", "<a>x  </a>", "data2data.<a>.text"),
        ("<a>x </a>", "<a>x  </a>", "data2data.<a>.text"),
        ("<a> x</a>", "<a>x</a>", "data2data.<a>.text"),
        ("<a>  x</a>", "<a>x</a>", "data2data.<a>.text"),
        ("<a>  x</a>", "<a> x</a>", "data2data.<a>.text"),
        ("<a><b><c>x</c><c2/></b></a>", "<a><b><c>X</c><c2/></b></a>",
            "data2data.<a>.<b>.<c(1/2)>.text"),
        ("<a><b><c>x</c><d>y</d></b></a>", "<a><b><c>x</c><d>Y</d></b></a>",
            "data2data.<a>.<b>.<d(2/2)>.text"),
        # Different textual content in mixed content nodes with children.
        ("<a>42<b/><b/>42</a>", "<a>42<b/> <b/>42</a>", "data2data.<a>.text"),
        # Differently named elements.
        ("<a/>", "<b/>", "data2data.<a/b>"),
        ("<a><b/></a>", "<a><c/></a>", "data2data.<a>.<b/c>"),
        ("<a><b/><x/></a>", "<a><c/><x/></a>", "data2data.<a>.<b/c(1/2)>"),
        ("<a><x/><b/></a>", "<a><x/><c/></a>", "data2data.<a>.<b/c(2/2)>"),
        ("<a><b><c/></b></a>", "<a><b><d/></b></a>",
            "data2data.<a>.<b>.<c/d>"),
        ("<a><b><y1/><y2/><c/></b><x/></a>",
            "<a><b><y1/><y2/><d/></b><x/></a>",
            "data2data.<a>.<b(1/2)>.<c/d(3/3)>"),
        # Extra/missing non-root element.
        ("<a><b/></a>", "<a/>", "data2data.<a>"),
        ("<a/>", "<a><b/></a>", "data2data.<a>"),
        ("<a><x/><b/></a>", "<a><b/></a>", "data2data.<a>"),
        ("<a><b/><x/></a>", "<a><b/></a>", "data2data.<a>"),
        ("<a><b/></a>", "<a><x/><b/></a>", "data2data.<a>"),
        ("<a><b/></a>", "<a><b/><x/></a>", "data2data.<a>"),
        # Multiple differences.
        ("<a><b/></a>", "<c><d/></c>", "data2data.<a/c>"),
        ("<a><b/></a>", '<a xmlns="o"><c/></a>', "data2data.<a>.namespace"),
        ("<r><a><b/></a></r>", "<r><c><d/></c></r>", "data2data.<r>.<a/c>"),
        ("<r><a><b/></a></r>", '<r><a xmlns="o"><c/></a></r>',
            "data2data.<r>.<a>.namespace")))
    def test_data2data(self, data1, data2, expected_context, capsys):
        pytest.raises(AssertionError, CompareSAX.data2data, data1, data2)
        _assert_context_output(capsys, expected_context)

    @skip_test_if_CompareSAX_assertions_disabled
    def test_document2document_context(self, capsys):
        a = suds.sax.document.Document()
        b = suds.sax.parser.Parser().parse(string=suds.byte_str("<a/>"))
        pytest.raises(AssertionError, CompareSAX.document2document, a, b)
        _assert_context_output(capsys, "document2document")

    @skip_test_if_CompareSAX_assertions_disabled
    def test_document2element_context(self, capsys):
        a = suds.sax.parser.Parser().parse(string=suds.byte_str("<xx>1</xx>"))
        b = suds.sax.parser.Parser().parse(string=suds.byte_str("<xx>2</xx>"))
        pytest.raises(AssertionError, CompareSAX.document2element, a, b.root())
        _assert_context_output(capsys, "document2element.<xx>.text")

    @skip_test_if_CompareSAX_assertions_disabled
    def test_element2element_context(self, capsys):
        Parser = suds.sax.parser.Parser
        e1 = Parser().parse(string=suds.byte_str("<x/>")).root()
        e2 = Parser().parse(string=suds.byte_str("<y/>")).root()
        pytest.raises(AssertionError, CompareSAX.element2element, e1, e2)
        _assert_context_output(capsys, "element2element.<x/y>")

    @skip_test_if_CompareSAX_assertions_disabled
    def test_element2element_context_invalid_name__left(self, capsys):
        Parser = suds.sax.parser.Parser
        e = Parser().parse(string=suds.byte_str("<x/>")).root()
        e_invalid = object()
        pytest.raises(AssertionError, CompareSAX.element2element, e_invalid, e)
        _assert_context_output(capsys, "element2element.<???/x>")

    @skip_test_if_CompareSAX_assertions_disabled
    def test_element2element_context_invalid_name__right(self, capsys):
        Parser = suds.sax.parser.Parser
        e = Parser().parse(string=suds.byte_str("<y/>")).root()
        e_invalid = object()
        pytest.raises(AssertionError, CompareSAX.element2element, e, e_invalid)
        _assert_context_output(capsys, "element2element.<y/???>")

    @skip_test_if_CompareSAX_assertions_disabled
    def test_empty_vs_non_empty_document(self, capsys):
        document = suds.sax.document.Document()
        data = "<a/>"
        pytest.raises(AssertionError, CompareSAX.document2data, document, data)
        _assert_context_output(capsys, "document2data")


#TODO: TestSAXModelFeatures tests should be removed once their respective SAX
# document model features get tested by SAX document model specific unit tests.
#TODO: Additional missing suds SAX document model unit tests:
#  * SAX parser fails on documents with multiple root elements.
#  * SAX document may contain at most one element, accessible as root().
#  * SAX document append() overwrites the root element silently.
class TestSAXModelFeatures:
    """SAX document model feature testing using the CompareSAX interface."""

    @skip_test_if_CompareSAX_assertions_disabled
    @pytest.mark.parametrize(("data1", "data2"), (
        # Differently placed default namespace declaration.
        ('<ns:a xmlns:ns="1" xmlns="2"><b/></ns:a>',
        '<ns:a xmlns:ns="1"><b xmlns="2"/></ns:a>'),
        # Differently placed namespace prefix declaration.
        ('<a xmlns:ns="1"><ns:b/></a>', '<a><ns:b xmlns:ns="1"/></a>'),
        # Element's textual content merged.
        ("<a>111<b/>222</a>", "<a>111222<b/></a>"),
        ("<a>111<b/>222</a>", "<a><b/>111222</a>"),
        ("<a>111<b/>222</a>", "<a>11<b/>1222</a>"),
        # Explicit "" namespace == no prefix or default namespace.
        ('<a xmlns=""/>', "<a/>"),
        ('<ns:a xmlns:ns=""/>', "<a/>"),
        # Extra leading/trailing textual whitespace trimmed in mixed content
        # elements with more than one child element.
        ("<a>   \n\n <b/> \t\t\n\n</a>", "<a><b/></a>"),
        ("<a>   \nxxx\n <b/> \t\t\n\n</a>", "<a>xxx<b/></a>")))
    def test_data2data(self, data1, data2, capsys):
        CompareSAX.data2data(data1, data2)
        assert_no_output(capsys)


def _assert_context_output(capsys, context):
    """
    Test utility asserting an expected captured stderr context output and no
    captured stdout output.

    """
    out, err = capsys.readouterr()
    assert not out
    assert err == "Failed SAX XML comparison context:\n  %s\n" % (context,)
