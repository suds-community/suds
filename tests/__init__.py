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

import suds.client
import suds.store


def client_from_wsdl(wsdl_content, *args, **kwargs):
    """
    Constructs a non-caching suds Client based on the given WSDL content.

      The wsdl_content is expected to be a raw byte string and not a unicode
    string. This simple structure suits us fine here because XML content holds
    its own embedded encoding identification ('utf-8' if not specified
    explicitly).

      Stores the content directly inside the suds library internal document
    store under a hard-coded id to avoid having to load the data from a
    temporary file.

      Uses a locally created empty document store unless one is provided
    externally using the 'documentStore' keyword argument.

      Explicitly disables caching or otherwise, because we use the same
    hardcoded id for our main WSDL document, suds would always reuse the first
    such local document from its cache instead of fetching it from our document
    store.

    """
    assert wsdl_content.__class__ is suds.byte_str_class
    store = kwargs.get("documentStore")
    if store is None:
        store = suds.store.DocumentStore()
        kwargs.update(documentStore=store)
    testFileId = "whatchamacallit"
    store.update({testFileId: wsdl_content})
    kwargs.update(cache=None)
    return suds.client.Client("suds://" + testFileId, *args, **kwargs)


def compare_xml(lhs, rhs):
    """
    Compares two XML documents.

    Not intended to be perfect, but only good enough comparison to be used
    internally inside the project's test suite.

    Does not compare namespace prefixes and considers them irrelevant. This is
    because suds may generate different namespace prefixes for the same
    underlying XML structure when used from different Python versions.

    """
    if lhs.__class__ is not suds.sax.document.Document:
        return False
    if rhs.__class__ is not suds.sax.document.Document:
        return False
    if len(lhs.getChildren()) != 1:
        return False
    if len(rhs.getChildren()) != 1:
        return False
    return compare_xml_element(lhs.getChildren()[0], rhs.getChildren()[0])


def compare_xml_element(lhs, rhs):
    """
    Compares two XML elements.

    Not intended to be perfect, but only good enough comparison to be used
    internally inside the project's test suite.

    Does not compare namespace prefixes and considers them irrelevant. This is
    because suds may generate different namespace prefixes for the same
    underlying XML structure when used from different Python versions.

    Empty string & None XML element texts are considered the same to compensate
    for different XML object tree construction methods representing 'no text'
    elements differently, e.g. when constructed by the sax parser or when
    constructed in code to represent a SOAP request.

    """
    if lhs.__class__ is not suds.sax.element.Element:
        return False
    if rhs.__class__ is not suds.sax.element.Element:
        return False
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
        if not compare_xml_element(l, r):
            return False
    return True


def compare_xml_string_to_string(lhs, rhs):
    """
    Compares two XML documents, both given as strings or bytes objects.

    Not intended to be perfect, but only good enough comparison to be used
    internally inside the project's test suite.

    Does not compare namespace prefixes and considers them irrelevant. This is
    because suds may generate different namespace prefixes for the same
    underlying XML structure when used from different Python versions.

    """
    if isinstance(lhs, unicode):
        lhs = suds.byte_str(lhs)
    if isinstance(rhs, unicode):
        rhs = suds.byte_str(rhs)
    lhs_document = suds.sax.parser.Parser().parse(string=lhs)
    rhs_document = suds.sax.parser.Parser().parse(string=rhs)
    return compare_xml(lhs_document, rhs_document)


def compare_xml_to_string(lhs, rhs):
    """
    Compares two XML documents, second one given as a string or a bytes object.

    Not intended to be perfect, but only good enough comparison to be used
    internally inside the project's test suite.

    Does not compare namespace prefixes and considers them irrelevant. This is
    because suds may generate different namespace prefixes for the same
    underlying XML structure when used from different Python versions.

    """
    if isinstance(rhs, unicode):
        rhs = suds.byte_str(rhs)
    rhs_document = suds.sax.parser.Parser().parse(string=rhs)
    return compare_xml(lhs, rhs_document)


def runUsingPyTest(callerGlobals):
    """Run the caller test script using the pytest testing framework."""
    import sys
    # Trick setuptools into not recognizing we are referencing __file__ here.
    # If setuptools detects __file__ usage in a module, any package containing
    # this module will be installed as an actual folder instead of a zipped
    # archive. This __file__ usage is safe since it is used only when a script
    # has been run directly, and that can not be done from a zipped package
    # archive.
    filename = callerGlobals.get("file".join(["__"] * 2))
    if not filename:
        sys.exit("Internal error: can not determine test script name.")
    try:
        import pytest
    except ImportError:
        filename = filename or "<unknown-script>"
        sys.exit("'py.test' unit testing framework not available. Can not run "
            "'%s' directly as a script." % (filename,))
    exitCode = pytest.main(["--pyargs", filename] + sys.argv[1:])
    sys.exit(exitCode)


def wsdl(schema_content, input=None, output=None, operation_name="f"):
    """
    Returns a WSDL schema used in different suds library tests.

    Defines a single operation taking an externally specified input structure
    and returning an externally defined output structure.

    input/output parameters accept the following values:
      * None - operation has no input/output message.
      * list/tuple - operation has an input/output message consisting of
        message parts referencing top-level XSD schema elements with the given
        names.
      * Otherwise operation has an input/output message consisting of a single
        message part referencing a top-level XSD schema element with the given
        name.

    """
    has_input = input is not None
    has_output = output is not None

    wsdl = ["""\
<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
xmlns:ns="my-namespace"
xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types>
    <xsd:schema targetNamespace="my-namespace"
    elementFormDefault="qualified"
    attributeFormDefault="unqualified"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema">
%s
    </xsd:schema>
  </wsdl:types>""" % (schema_content,)]

    if has_input:
        if input.__class__ not in (list, tuple):
            input = [input]
        wsdl.append("""\
  <wsdl:message name="fRequestMessage">""")
        for element in input:
            wsdl.append("""\
    <wsdl:part name="parameters" element="ns:%s" />""" % (element,))
        wsdl.append("""\
  </wsdl:message>""")

    if has_output:
        if output.__class__ not in (list, tuple):
            output = [output]
        wsdl.append("""\
  <wsdl:message name="fResponseMessage">""")
        for element in output:
            wsdl.append("""\
    <wsdl:part name="parameters" element="ns:%s" />""" % (element,))
        wsdl.append("""\
  </wsdl:message>""")

    wsdl.append("""\
  <wsdl:portType name="dummyPortType">
    <wsdl:operation name="%s">""" % (operation_name,))

    if has_input:
        wsdl.append("""\
      <wsdl:input message="ns:fRequestMessage" />""")
    if has_output:
        wsdl.append("""\
      <wsdl:output message="ns:fResponseMessage" />""")

    wsdl.append("""\
    </wsdl:operation>
  </wsdl:portType>
  <wsdl:binding name="dummy" type="ns:dummyPortType">
    <soap:binding style="document"
    transport="http://schemas.xmlsoap.org/soap/http" />
    <wsdl:operation name="%s">
      <soap:operation soapAction="my-soap-action" style="document" />""" %
        (operation_name,))

    if has_input:
        wsdl.append("""\
      <wsdl:input><soap:body use="literal" /></wsdl:input>""")
    if has_output:
        wsdl.append("""\
      <wsdl:output><soap:body use="literal" /></wsdl:output>""")

    wsdl.append("""\
    </wsdl:operation>
  </wsdl:binding>
  <wsdl:service name="dummy">
    <wsdl:port name="dummy" binding="ns:dummy">
      <soap:address location="unga-bunga-location" />
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>
""")

    return suds.byte_str("\n".join(wsdl))


def wsdl_input(schema_content, *args, **kwargs):
    """
    Returns an input-only WSDL schema used in different suds library tests.

    Defines a single operation taking an externally specified input structure
    and returning no output. The operation is named 'f' by default, but a
    custom name may be defined for it using the 'operation_name' keyword
    argument.

    Initial input argument is the schema part of the WSDL, any remaining
    positional arguments are interpreted as names of included top level input
    parameter elements.

    """
    assert len(args) >= 1
    if kwargs:
        assert len(kwargs) == 1
        assert "operation_name" in kwargs
    return wsdl(schema_content, input=args, **kwargs)


def wsdl_output(schema_content, *args, **kwargs):
    """
    Returns an output-only WSDL schema used in different suds library tests.

    Defines a single operation, taking no input and returning an externally
    specified output structure. The operation is named 'f' by default, but a
    custom name may be defined for it using the 'operation_name' keyword
    argument.

    The first input parameter is the schema part of the WSDL, the rest of the
    parameters identify top level output parameter elements.

    """
    assert len(args) >= 1
    if kwargs:
        assert len(kwargs) == 1
        assert "operation_name" in kwargs
    return wsdl(schema_content, output=args, **kwargs)
