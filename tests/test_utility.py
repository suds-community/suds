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
Testing utilities used throughout the suds test suite.

Also includes tests for the test utilities themselves, where necessary.

Whether or not any tests are included in this module, when used by tests run by
the 'pytest' testing framework this module still needs to be recognizable by
'pytest' as a test module. Otherwise 'pytest' might not correctly interpret the
assertions used in this module as test assertions.

"""

import suds.sax.document
import suds.sax.element
import suds.sax.parser

import sys


class CompareSAX:
    """
    Support for comparing SAX XML structures.

    Not intended to be perfect, but only good enough XML comparison to be used
    internally inside the project's test suite.

    Raw XML data is parsed using a suds SAX parser and the resulting DOM
    structure compared. This means that any XML data differences lost during
    SAX parsing can not be detected. Some examples:
      - all textual content for a single node is concatenated together, so the
        following two XML data segments are considered equivalent:
          1. '<a>xx<b/>yy</a>'
          2. '<a>xxyy<b/></a>'
      - all leading and trailing whitespace is trimmed from textual content for
        nodes having at least one child element, so most XML indentation
        information is lost and the following two XML data segments are
        considered equivalent:
          1. '<a>   <b/>     </a>'
          2. '<a><b/></a>'

    Suds may generate different SOAP request XML data for the same input based
    on the order in which it reads some of its internal data held inside
    unordered containers, e.g. set or dictionary. To compensate for this we
    consider both namespace prefix & namespace declaration (either extra
    declarations or declaration placement) differences in XML documents as
    irrelevant. We do however compare each XML node's namespace, i.e. that
    their namespace names match even if their namespace prefixes do not or if
    those namespaces have been declared on different XML elements.

    """

    def __init__(self):
        self.__context = []

    @staticmethod
    def assertions_enabled():
        """
        Returns whether Python assertions have been enabled in this module.

        CompareSAX class uses Python assertions to report failed comparison
        results so this information in order to know whether related tests
        should be disabled.

        """
        try:
            assert False
        except AssertionError:
            return True
        return False

    @classmethod
    def document2document(cls, lhs, rhs):
        """Compares two SAX XML documents."""
        self = cls()
        try:
            self.__document2document(lhs, rhs, context=u"document2document")
        except Exception:
            self.__report_context()
            raise

    @classmethod
    def document2element(cls, document, element):
        """
        Compares a SAX XML document structure to a SAX XML element.

        The given document & element are considered successfully matched if the
        document consists of a single XML element matching the given one.

        """
        self = cls()
        self.__push_context(u"document2element")
        try:
            assert document.__class__ is suds.sax.document.Document
            assert element.__class__ is suds.sax.element.Element
            assert len(document.getChildren()) == 1
            self.__element2element(document.getChildren()[0], element)
        except Exception:
            self.__report_context()
            raise

    @classmethod
    def element2element(cls, lhs, rhs):
        """Compares two SAX XML elements."""
        self = cls()
        self.__push_context(u"element2element")
        try:
            self.__element2element(lhs, rhs)
        except Exception:
            self.__report_context()
            raise

    @classmethod
    def data2data(cls, lhs, rhs):
        """Compares two SAX XML documents given as strings or bytes objects."""
        self = cls()
        try:
            lhs_doc = self.__parse_data(lhs)
            rhs_doc = self.__parse_data(rhs)
            self.__document2document(lhs_doc, rhs_doc, context=u"data2data")
        except Exception:
            self.__report_context()
            raise

    @classmethod
    def document2data(cls, lhs, rhs):
        """
        Compares two SAX XML documents, second one given as a string or a bytes
        object.

        """
        self = cls()
        try:
            rhs_doc = self.__parse_data(rhs)
            self.__document2document(lhs, rhs_doc, context=u"document2data")
        except Exception:
            self.__report_context()
            raise

    def __compare_child_elements(self, lhs, rhs):
        """Compares the given entities' child elements."""
        assert len(lhs.getChildren()) == len(rhs.getChildren())
        count = len(lhs.getChildren())
        for i, (l, r) in enumerate(zip(lhs.getChildren(), rhs.getChildren())):
            self.__element2element(l, r, context_info=(i, count))

    def __compare_element_namespace(self, lhs, rhs):
        """
        Compares the given elements' namespaces.

        Empty string & None XML element namespaces are considered the same to
        compensate for the suds SAX document model representing the following
        'default namespace' scenarios differently:
          <a/>
          <a xmlns=""/>
          <ns:a xmlns:ns=""/>

        """
        #TODO: Make suds SAX element model consistently represent empty/missing
        # namespaces and then update both this method and its docstring.
        self.__push_context(u"namespace")
        lhs_namespace = lhs.namespace()[1]
        rhs_namespace = rhs.namespace()[1]
        if not lhs_namespace:
            lhs_namespace = None
        if not rhs_namespace:
            rhs_namespace = None
        assert lhs_namespace == rhs_namespace
        self.__pop_context()

    def __compare_element_text(self, lhs, rhs):
        """
        Compares the given elements' textual content.

        Empty string & None XML element texts are considered the same to
        compensate for different XML object tree construction methods
        representing 'no text' elements differently, e.g. depending on whether
        a particular SAX parsed XML element had any whitespace characters in
        its textual data or whether the element got constructed in code to
        represent a SOAP request.

        """
        #TODO: Make suds SAX element model consistently represent empty/missing
        # text content and then update both this method and its docstring.
        self.__push_context(u"text")
        lhs_text = lhs.text
        rhs_text = rhs.text
        if not lhs_text:
            lhs_text = None
        if not rhs_text:
            rhs_text = None
        assert lhs_text == rhs_text
        self.__pop_context()

    def __document2document(self, lhs, rhs, context):
        """
        Internal document2document comparison worker.

        See document2document() docstring for more detailed information.

        """
        self.__push_context(context)
        assert lhs.__class__ is suds.sax.document.Document
        assert rhs.__class__ is suds.sax.document.Document
        self.__compare_child_elements(lhs, rhs)
        self.__pop_context()

    @staticmethod
    def __element_name(element):
        """Returns a given SAX element's name as unicode or '???' on error."""
        try:
            return unicode(element.name)
        except Exception:
            return u"???"

    def __element2element(self, lhs, rhs, context_info=(0, 1)):
        """
        Internal element2element comparison worker.

        See element2element() docstring for more detailed information.

        The context information is an (n, count) 2-element collection
        indicating which element2element() call ('n') this is in a sequence of
        such calls ('count'). The exact context string is constructed based on
        the given elements' names and context information.

        """
        context = self.__element2element_context(lhs, rhs, context_info)
        self.__push_context(context)
        assert lhs.__class__ is suds.sax.element.Element
        assert rhs.__class__ is suds.sax.element.Element
        assert lhs.name == rhs.name
        self.__compare_element_namespace(lhs, rhs)
        self.__compare_element_text(lhs, rhs)
        self.__compare_child_elements(lhs, rhs)
        self.__pop_context()

    @classmethod
    def __element2element_context(cls, lhs, rhs, context_info):
        """
        Return a context string for a given element2element call.

        See the __element2element() docstring for more detailed information.

        """
        n, count = context_info
        assert 0 <= n < count, "broken CompareSAX implementation"
        context_lhs_name = cls.__element_name(lhs)
        context_rhs_name = cls.__element_name(rhs)
        if context_lhs_name == context_rhs_name:
            context_name = context_lhs_name
        else:
            context_name = u"%s/%s" % (context_lhs_name, context_rhs_name)
        if count == 1:
            return u"<%s>" % (context_name,)
        return u"<%s(%d/%d)>" % (context_name, n + 1, count)

    @staticmethod
    def __parse_data(data):
        """
        Construct a SAX XML document based on its data given as a string or a
        bytes object.

        """
        if isinstance(data, unicode):
            data = data.encode("utf-8")
        return suds.sax.parser.Parser().parse(string=data)

    def __pop_context(self):
        self.__context.pop()

    def __push_context(self, context):
        self.__context.append(context)

    def __report_context(self):
        if self.__context:
            sys.stderr.write("Failed SAX XML comparison context:\n")
            sys.stderr.write(u"  %s\n" % (u".".join(self.__context)))


import suds

import pytest

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
    _assert_no_output(capsys)


class TestMatched:
    """Successful CompareSAX matching tests."""

    @skip_test_if_CompareSAX_assertions_disabled
    def test_empty_document(self, capsys):
        a = suds.sax.document.Document()
        b = suds.sax.document.Document()
        CompareSAX.document2document(a, b)
        _assert_no_output(capsys)

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
        (u"<a>☆</a>", "<a>&#9734;</a>")))
    def test_data2data(self, data1, data2, capsys):
        CompareSAX.data2data(data1, data2)
        _assert_no_output(capsys)

    @skip_test_if_CompareSAX_assertions_disabled
    @pytest.mark.parametrize("type1", (suds.byte_str, unicode))
    @pytest.mark.parametrize("type2", (suds.byte_str, unicode))
    def test_string_input_types(self, type1, type2, capsys):
        xml = "<a/>"
        CompareSAX.data2data(type1(xml), type2(xml))
        _assert_no_output(capsys)

    @skip_test_if_CompareSAX_assertions_disabled
    def test_xml_encoding(self, capsys):
        """Test that the encoding listed in the XML declaration is honored."""
        xml_format = u'<?xml version="1.0" encoding="%s"?><a>Ø</a>'
        data1 = (xml_format % ("UTF-8",)).encode('utf-8')
        data2 = (xml_format % ("latin1",)).encode('latin1')
        CompareSAX.data2data(data1, data2)
        _assert_no_output(capsys)


class TestMismatched:
    """Failed CompareSAX matching tests."""

    @skip_test_if_CompareSAX_assertions_disabled
    @pytest.mark.parametrize(("data1", "data2", "expected_context"), (
        # Different element namespaces.
        ("<a/>", '<a xmlns="x"/>', u"data2data.<a>.namespace"),
        ('<a xmlns="1"/>', '<a xmlns="2"/>', u"data2data.<a>.namespace"),
        ('<r><a xmlns="1"/></r>', '<r><a xmlns="2"/></r>',
            u"data2data.<r>.<a>.namespace"),
        ('<r><tag><a xmlns="1"/></tag><y/></r>',
            '<r><tag><a xmlns="2"/></tag><y/></r>',
            u"data2data.<r>.<tag(1/2)>.<a>.namespace"),
        # Different textual content in text only nodes.
        ("<a>one</a>", "<a>two</a>", u"data2data.<a>.text"),
        ("<a>x</a>", "<a>x </a>", u"data2data.<a>.text"),
        ("<a>x</a>", "<a>x  </a>", u"data2data.<a>.text"),
        ("<a>x </a>", "<a>x  </a>", u"data2data.<a>.text"),
        ("<a> x</a>", "<a>x</a>", u"data2data.<a>.text"),
        ("<a>  x</a>", "<a>x</a>", u"data2data.<a>.text"),
        ("<a>  x</a>", "<a> x</a>", u"data2data.<a>.text"),
        ("<a><b><c>x</c><c2/></b></a>", "<a><b><c>X</c><c2/></b></a>",
            u"data2data.<a>.<b>.<c(1/2)>.text"),
        ("<a><b><c>x</c><d>y</d></b></a>", "<a><b><c>x</c><d>Y</d></b></a>",
            u"data2data.<a>.<b>.<d(2/2)>.text"),
        # Different textual content in mixed content nodes with children.
        ("<a>42<b/><b/>42</a>", "<a>42<b/> <b/>42</a>", u"data2data.<a>.text"),
        # Differently named elements.
        ("<a/>", "<b/>", u"data2data.<a/b>"),
        ("<a><b/></a>", "<a><c/></a>", u"data2data.<a>.<b/c>"),
        ("<a><b/><x/></a>", "<a><c/><x/></a>", u"data2data.<a>.<b/c(1/2)>"),
        ("<a><x/><b/></a>", "<a><x/><c/></a>", u"data2data.<a>.<b/c(2/2)>"),
        ("<a><b><c/></b></a>", "<a><b><d/></b></a>",
            u"data2data.<a>.<b>.<c/d>"),
        ("<a><b><y1/><y2/><c/></b><x/></a>",
            "<a><b><y1/><y2/><d/></b><x/></a>",
            u"data2data.<a>.<b(1/2)>.<c/d(3/3)>"),
        # Extra/missing non-root element.
        ("<a><b/></a>", "<a/>", u"data2data.<a>"),
        ("<a/>", "<a><b/></a>", u"data2data.<a>"),
        ("<a><x/><b/></a>", "<a><b/></a>", u"data2data.<a>"),
        ("<a><b/><x/></a>", "<a><b/></a>", u"data2data.<a>"),
        ("<a><b/></a>", "<a><x/><b/></a>", u"data2data.<a>"),
        ("<a><b/></a>", "<a><b/><x/></a>", u"data2data.<a>"),
        # Multiple differences.
        ("<a><b/></a>", "<c><d/></c>", u"data2data.<a/c>"),
        ("<a><b/></a>", '<a xmlns="o"><c/></a>', u"data2data.<a>.namespace"),
        ("<r><a><b/></a></r>", "<r><c><d/></c></r>", u"data2data.<r>.<a/c>"),
        ("<r><a><b/></a></r>", '<r><a xmlns="o"><c/></a></r>',
            u"data2data.<r>.<a>.namespace")))
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
        _assert_no_output(capsys)


def _assert_context_output(capsys, context):
    """
    Test utility asserting an expected captured stderr context output and no
    captured stdout output.

    """
    out, err = capsys.readouterr()
    assert not out
    assert err == u"Failed SAX XML comparison context:\n  %s\n" % (context,)


def _assert_no_output(capsys):
    """Test utility asserting there was no captured stdout or stderr output."""
    out, err = capsys.readouterr()
    assert not out
    assert not err
