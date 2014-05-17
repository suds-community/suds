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
CompareSAX test utility class implementation.

Extracted into a separate module, named so pytest would apply its assertion
rewriting to it.

'pytest' assertion rewriting allows CompareSAX to use Python assertion based
XML mismatch reporting and have it work even when run with Python assertions
disabled.

"""

import suds.sax.document
import suds.sax.element
import suds.sax.parser

from six import text_type, u

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
            self.__document2document(lhs, rhs, context="document2document")
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
        self.__push_context("document2element")
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
        self.__push_context("element2element")
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
            self.__document2document(lhs_doc, rhs_doc, context="data2data")
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
            self.__document2document(lhs, rhs_doc, context="document2data")
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
        self.__push_context("namespace")
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
        self.__push_context("text")
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
            return text_type(element.name)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            return u("???")

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
            context_name = "%s/%s" % (context_lhs_name, context_rhs_name)
        if count == 1:
            return "<%s>" % (context_name,)
        return "<%s(%d/%d)>" % (context_name, n + 1, count)

    @staticmethod
    def __parse_data(data):
        """
        Construct a SAX XML document based on its data given as a string or a
        bytes object.

        """
        if isinstance(data, text_type):
            data = data.encode("utf-8")
        return suds.sax.parser.Parser().parse(string=data)

    def __pop_context(self):
        self.__context.pop()

    def __push_context(self, context):
        self.__context.append(context)

    def __report_context(self):
        if self.__context:
            sys.stderr.write("Failed SAX XML comparison context:\n")
            sys.stderr.write("  %s\n" % (".".join(self.__context)))
