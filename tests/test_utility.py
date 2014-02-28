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

    Empty string & None XML element texts are considered the same to compensate
    for different XML object tree construction methods representing 'no text'
    elements differently, e.g. depending on whether a particular SAX parsed XML
    element had any whitespace characters in its textual data or whether the
    element got constructed in code to represent a SOAP request.

    """

    @classmethod
    def document2document(cls, lhs, rhs):
        """Compares two SAX XML documents."""
        assert lhs.__class__ is suds.sax.document.Document
        assert rhs.__class__ is suds.sax.document.Document
        assert len(lhs.getChildren()) == 1
        assert len(rhs.getChildren()) == 1
        return cls.element2element(lhs.getChildren()[0], rhs.getChildren()[0])

    @classmethod
    def document2element(cls, document, element):
        """
        Compares a SAX XML document structure to a SAX XML element.

        The given document & element are considered successfully matched if the
        document consists of a single XML element matching the given one.

        """
        assert document.__class__ is suds.sax.document.Document
        assert element.__class__ is suds.sax.element.Element
        return (len(document.getChildren()) == 1 and
            cls.element2element(document.getChildren()[0], element))

    @classmethod
    def element2element(cls, lhs, rhs):
        """Compares two SAX XML elements."""
        assert lhs.__class__ is suds.sax.element.Element
        assert rhs.__class__ is suds.sax.element.Element
        if lhs.namespace()[1] != rhs.namespace()[1]:
            return False
        if lhs.name != rhs.name:
            return False
        lhs_text = lhs.text
        rhs_text = rhs.text
        if lhs_text == "":
            lhs_text = None
        if rhs_text == "":
            rhs_text = None
        if lhs_text != rhs_text:
            return False
        if len(lhs.getChildren()) != len(rhs.getChildren()):
            return False
        for l, r in zip(lhs.getChildren(), rhs.getChildren()):
            if not cls.element2element(l, r):
                return False
        return True

    @classmethod
    def data2data(cls, lhs, rhs):
        """Compares two SAX XML documents given as strings or bytes objects."""
        lhs_document = cls.__parse_data(lhs)
        rhs_document = cls.__parse_data(rhs)
        return cls.document2document(lhs_document, rhs_document)

    @classmethod
    def document2data(cls, lhs, rhs):
        """
        Compares two SAX XML documents, second one given as a string or a bytes
        object.

        """
        return cls.document2document(lhs, cls.__parse_data(rhs))

    @staticmethod
    def __parse_data(data):
        """
        Construct a SAX XML document based on its data given as a string or a
        bytes object.

        """
        if isinstance(data, unicode):
            data = data.encode("utf-8")
        return suds.sax.parser.Parser().parse(string=data)
