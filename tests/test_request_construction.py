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
Suds Python library request construction related unit tests.

Suds provides the user with an option to automatically 'hide' wrapper elements
around simple types and allow the user to specify such parameters without
explicitly creating those wrappers. For example: function taking a parameter of
type X, where X is a sequence containing only a single simple data type (e.g.
string or integer) will be callable by directly passing it that internal simple
data type value instead of first wrapping that value in an object of type X and
then passing that wrapper object instead.

"""

if __name__ == "__main__":
    import __init__
    __init__.runUsingPyTest(globals())


import suds
import suds.store
import tests

import pytest


# TODO: Update the current restriction type output parameter handling so such
# parameters get converted to the correct Python data type based on the
# restriction's underlying data type.
@pytest.mark.xfail
def test_bare_input_restriction_types():
    client_unnamed = tests.client_from_wsdl(tests.wsdl_input("""\
      <xsd:element name="Elemento">
        <xsd:simpleType>
          <xsd:restriction base="xsd:string">
            <xsd:enumeration value="alfa"/>
            <xsd:enumeration value="beta"/>
            <xsd:enumeration value="gamma"/>
          </xsd:restriction>
        </xsd:simpleType>
      </xsd:element>""", "Elemento"))

    client_named = tests.client_from_wsdl(tests.wsdl_input("""\
      <xsd:simpleType name="MyType">
        <xsd:restriction base="xsd:string">
          <xsd:enumeration value="alfa"/>
          <xsd:enumeration value="beta"/>
          <xsd:enumeration value="gamma"/>
        </xsd:restriction>
      </xsd:simpleType>
      <xsd:element name="Elemento" type="ns:MyType"/>""", "Elemento"))

    assert not _isInputWrapped(client_unnamed, "f")
    assert not _isInputWrapped(client_named, "f")


def parametrize_single_element_input_test(param_names, param_values):
    """
    Define different parametrized single element input test function calls.

    Parameter value input is a tuple containing 2+ parameters:
      * 1. element - input XSD element definition
      * 2. element - input element name
      * 3+ elements - tuples containing the following:
        * position argument list for the invoked test web service operation
        * expected request body content for the given arguments
        * [optional] reason for marking this test case as expected to fail

    """
    mark = pytest
    expanded_param_values = []
    for param_value in param_values:
        xsd, external_element_name = param_value[0:2]
        for next_value in param_value[2:]:
            assert len(next_value) in (2, 3)
            args, request_body = next_value[:2]
            xfail = len(next_value) == 3
            param = (xsd, external_element_name, args, request_body)
            if xfail:
                param = pytest.mark.xfail(param, reason=next_value[2])
            expanded_param_values.append(param)
    return (param_names, expanded_param_values), {}

@pytest.mark.indirect_parametrize(parametrize_single_element_input_test,
    ("xsd", "external_element_name", "args", "request_body"), (
    # Bare non-optional element.
    ('<xsd:element name="a" type="xsd:integer"/>', "a",
        ([], "<ns0:a/>"),
        ([5], "<ns0:a>5</ns0:a>")),
    # Bare optional element.
    ('<xsd:element name="a" type="xsd:integer" minOccurs="0"/>', "a",
        ([], ""),
        ([5], "<ns0:a>5</ns0:a>")),
    # Choice with a non-empty sub-sequence.
    ("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:choice>
            <xsd:element name="a" type="xsd:integer"/>
            <xsd:sequence>
              <xsd:element name="b1" type="xsd:integer"/>
              <xsd:element name="b2" type="xsd:integer"/>
            </xsd:sequence>
          </xsd:choice>
        </xsd:complexType>
      </xsd:element>""", "Wrapper",
        ([], "<ns0:Wrapper><ns0:a/></ns0:Wrapper>",
            "non-optional choice handling buggy"),
        ([5], "<ns0:Wrapper><ns0:a>5</ns0:a></ns0:Wrapper>"),
        ([None, 1], "<ns0:Wrapper><ns0:b1>1</ns0:b1><ns0:b2/></ns0:Wrapper>",
            "non-optional choice handling buggy"),
        ([None, 1, 2],
            "<ns0:Wrapper><ns0:b1>1</ns0:b1><ns0:b2>2</ns0:b2></ns0:Wrapper>"),
        ([None, None, 1],
            "<ns0:Wrapper><ns0:b1/><ns0:b2>1</ns0:b2></ns0:Wrapper>",
            "non-optional choice handling buggy")),
    # Choice with a non-optional element.
    ("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:choice>
            <xsd:element name="a" type="xsd:integer"/>
          </xsd:choice>
        </xsd:complexType>
      </xsd:element>""", "Wrapper",
        ([], "<ns0:Wrapper><ns0:a/></ns0:Wrapper>",
            "non-optional choice handling buggy"),
        ([5], "<ns0:Wrapper><ns0:a>5</ns0:a></ns0:Wrapper>")),
    # Choice with an optional element.
    ("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:choice>
            <xsd:element name="a" type="xsd:integer" minOccurs="0"/>
          </xsd:choice>
        </xsd:complexType>
      </xsd:element>""", "Wrapper",
        ([], "<ns0:Wrapper/>"),
        ([5], "<ns0:Wrapper><ns0:a>5</ns0:a></ns0:Wrapper>")),
    # Choices with multiple elements, at least one of which is optional.
    ("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:choice>
            <xsd:element name="a" type="xsd:integer" minOccurs="0"/>
            <xsd:element name="b" type="xsd:integer"/>
          </xsd:choice>
        </xsd:complexType>
      </xsd:element>""", "Wrapper",
        ([], "<ns0:Wrapper/>"),
        ([5], "<ns0:Wrapper><ns0:a>5</ns0:a></ns0:Wrapper>"),
        ([None, 5], "<ns0:Wrapper><ns0:b>5</ns0:b></ns0:Wrapper>")),
    ("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:choice>
            <xsd:element name="a" type="xsd:integer"/>
            <xsd:element name="b" type="xsd:integer" minOccurs="0"/>
          </xsd:choice>
        </xsd:complexType>
      </xsd:element>""", "Wrapper",
        ([], "<ns0:Wrapper/>"),
        ([5], "<ns0:Wrapper><ns0:a>5</ns0:a></ns0:Wrapper>"),
        ([None, 5], "<ns0:Wrapper><ns0:b>5</ns0:b></ns0:Wrapper>")),
    ("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:choice>
            <xsd:element name="a" type="xsd:integer" minOccurs="0"/>
            <xsd:element name="b" type="xsd:integer" minOccurs="0"/>
          </xsd:choice>
        </xsd:complexType>
      </xsd:element>""", "Wrapper",
        ([], "<ns0:Wrapper/>"),
        ([5], "<ns0:Wrapper><ns0:a>5</ns0:a></ns0:Wrapper>"),
        ([None, 5], "<ns0:Wrapper><ns0:b>5</ns0:b></ns0:Wrapper>")),
    # Choice with multiple non-empty sub-sequences.
    ("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:choice>
            <xsd:sequence>
              <xsd:element name="a1" type="xsd:integer"/>
              <xsd:element name="a2" type="xsd:integer"/>
            </xsd:sequence>
            <xsd:sequence>
              <xsd:element name="b1" type="xsd:integer"/>
              <xsd:element name="b2" type="xsd:integer"/>
            </xsd:sequence>
          </xsd:choice>
        </xsd:complexType>
      </xsd:element>""", "Wrapper",
        ([], "<ns0:Wrapper><ns0:a1/><ns0:a2/></ns0:Wrapper>",
            "non-optional choice handling buggy"),
        ([5], "<ns0:Wrapper><ns0:a1>5</ns0:a1><ns0:a2/></ns0:Wrapper>",
            "non-optional choice handling buggy"),
        ([5, 9], """\
          <ns0:Wrapper>
            <ns0:a1>5</ns0:a1>
            <ns0:a2>9</ns0:a2>
          </ns0:Wrapper>"""),
        ([None, 1], "<ns0:Wrapper><ns0:a1/><ns0:a2>1</ns0:a2></ns0:Wrapper>",
            "non-optional choice handling buggy"),
        ([None, None, 1],
            "<ns0:Wrapper><ns0:b1>1</ns0:b1><ns0:b2/></ns0:Wrapper>",
            "non-optional choice handling buggy"),
        ([None, None, 1, 2],
            "<ns0:Wrapper><ns0:b1>1</ns0:b1><ns0:b2>2</ns0:b2></ns0:Wrapper>"),
        ([None, None, None, 1],
            "<ns0:Wrapper><ns0:b1/><ns0:b2>1</ns0:b2></ns0:Wrapper>",
            "non-optional choice handling buggy")),
    # Empty choice.
    ("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:choice/>
        </xsd:complexType>
      </xsd:element>""", "Wrapper",
        ([], "<ns0:Wrapper/>")),
    # Empty sequence.
    ("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence/>
        </xsd:complexType>
      </xsd:element>""", "Wrapper",
        ([], "<ns0:Wrapper/>")),
    # Optional choice.
    ("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:choice minOccurs="0">
            <xsd:element name="a" type="xsd:integer"/>
            <xsd:element name="b" type="xsd:integer"/>
          </xsd:choice>
        </xsd:complexType>
      </xsd:element>""", "Wrapper",
        ([], "<ns0:Wrapper/>",
            # This test passes by accident - the following two bugs seem to
            # cancel each other out:
            #  - choice order indicators explicitly marked optional unsupported
            #  - not constructing correct input parameter values when using no
            #    input arguments for a choice
            #"suds does not yet support minOccurs/maxOccurs attributes on "
            #"all/choice/sequence order indicators"
            ),
        ([5], "<ns0:Wrapper><ns0:a>5</ns0:a></ns0:Wrapper>"),
        ([None, 1],
            "<ns0:Wrapper><ns0:b>1</ns0:b></ns0:Wrapper>")),
    # Optional sequence.
    ("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence minOccurs="0">
            <xsd:element name="a" type="xsd:integer"/>
            <xsd:element name="b" type="xsd:integer"/>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", "Wrapper",
        ([], "<ns0:Wrapper/>",
            "suds does not yet support minOccurs/maxOccurs attributes on all/"
            "choice/sequence order indicators"),
        ([5], "<ns0:Wrapper><ns0:a>5</ns0:a><ns0:b/></ns0:Wrapper>"),
        ([None, 1],
            "<ns0:Wrapper><ns0:a/><ns0:b>1</ns0:b></ns0:Wrapper>"),
        ([1, 2], """\
            <ns0:Wrapper>
              <ns0:a>1</ns0:a>
              <ns0:b>2</ns0:b>
            </ns0:Wrapper>""")),
    # Sequence with a non-empty sub-sequence.
    ("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="a" type="xsd:integer"/>
            <xsd:sequence>
              <xsd:element name="b1" type="xsd:integer"/>
              <xsd:element name="b2" type="xsd:integer"/>
            </xsd:sequence>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", "Wrapper",
        ([], "<ns0:Wrapper><ns0:a/><ns0:b1/><ns0:b2/></ns0:Wrapper>"),
        ([5], "<ns0:Wrapper><ns0:a>5</ns0:a><ns0:b1/><ns0:b2/></ns0:Wrapper>"),
        ([None, 1],
            "<ns0:Wrapper><ns0:a/><ns0:b1>1</ns0:b1><ns0:b2/></ns0:Wrapper>"),
        ([None, 1, 2], """\
            <ns0:Wrapper>
              <ns0:a/>
              <ns0:b1>1</ns0:b1>
              <ns0:b2>2</ns0:b2>
            </ns0:Wrapper>"""),
        ([None, None, 1],
            "<ns0:Wrapper><ns0:a/><ns0:b1/><ns0:b2>1</ns0:b2></ns0:Wrapper>")),
    # Sequence with a non-optional element.
    ("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="a" type="xsd:integer"/>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", "Wrapper",
        ([], "<ns0:Wrapper><ns0:a/></ns0:Wrapper>"),
        ([5], "<ns0:Wrapper><ns0:a>5</ns0:a></ns0:Wrapper>")),
    # Sequence with an optional element.
    ("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="a" type="xsd:integer" minOccurs="0"/>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", "Wrapper",
        ([], "<ns0:Wrapper/>"),
        ([5], "<ns0:Wrapper><ns0:a>5</ns0:a></ns0:Wrapper>")),
    # Sequence with multiple consecutive choices.
    ("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:choice>
              <xsd:element name="aString1" type="xsd:string"/>
              <xsd:element name="anInt1" type="xsd:integer"/>
            </xsd:choice>
            <xsd:choice>
              <xsd:element name="aString2" type="xsd:string"/>
              <xsd:element name="anInt2" type="xsd:integer" minOccurs="0"/>
            </xsd:choice>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", "Wrapper",
        ([], "<ns0:Wrapper><ns0:aString1/></ns0:Wrapper>",
            "non-optional choice handling buggy"),
        ([5], "<ns0:Wrapper><ns0:aString1>5</ns0:aString1></ns0:Wrapper>"),
        ([None, 1, 2], """\
            <ns0:Wrapper>
              <ns0:anInt1>1</ns0:anInt1>
              <ns0:aString2>2</ns0:aString2>
            </ns0:Wrapper>"""),
        ([None, 1, None, 2], """\
            <ns0:Wrapper>
              <ns0:anInt1>1</ns0:anInt1>
              <ns0:anInt2>2</ns0:anInt2>
            </ns0:Wrapper>""")),
    # Sequence with multiple optional elements.
    ("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="a" type="xsd:integer" minOccurs="0"/>
            <xsd:element name="b" type="xsd:integer" minOccurs="0"/>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", "Wrapper",
        ([], "<ns0:Wrapper/>"),
        ([5], "<ns0:Wrapper><ns0:a>5</ns0:a></ns0:Wrapper>"),
        ([None, 1], "<ns0:Wrapper><ns0:b>1</ns0:b></ns0:Wrapper>"),
        ([5, 1],
            "<ns0:Wrapper><ns0:a>5</ns0:a><ns0:b>1</ns0:b></ns0:Wrapper>")),
    ))
def test_document_literal_request_for_single_element_input(xsd,
        external_element_name, args, request_body):
    wsdl = tests.wsdl_input(xsd, external_element_name)
    client = tests.client_from_wsdl(wsdl, nosend=True, prettyxml=True)

    assert _compare_request(client.service.f(*args), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>%s</ns1:Body>
</SOAP-ENV:Envelope>""" % (request_body,))


def test_disabling_automated_simple_interface_unwrapping():
    client = tests.client_from_wsdl(tests.wsdl_input("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="Elemento" type="xsd:string"/>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", "Wrapper"), nosend=True, prettyxml=True, unwrap=False)
    assert not _isInputWrapped(client, "f")
    wrapper = client.factory.create("Wrapper")
    wrapper.Elemento = "Wonderwall"
    assert _compare_request(client.service.f(Wrapper=wrapper), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper>
         <ns0:Elemento>Wonderwall</ns0:Elemento>
      </ns0:Wrapper>
   </ns1:Body>
</SOAP-ENV:Envelope>""")


def test_element_references_to_different_namespaces():
    wsdl = suds.byte_str("""\
<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions
    xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema"
    xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
    xmlns:tns="first-namespace"
    targetNamespace="first-namespace">

  <wsdl:types>
    <xsd:schema
        targetNamespace="first-namespace"
        elementFormDefault="qualified"
        attributeFormDefault="unqualified"
        xmlns:second="second-namespace">
      <xsd:import namespace="second-namespace" schemaLocation="suds://external_schema"/>
      <xsd:element name="local_referenced" type="xsd:string"/>
      <xsd:element name="fRequest">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="local" type="xsd:string"/>
            <xsd:element ref="local_referenced"/>
            <xsd:element ref="second:external"/>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>
    </xsd:schema>
  </wsdl:types>

  <wsdl:message name="fRequestMessage">
    <wsdl:part name="parameters" element="tns:fRequest"/>
  </wsdl:message>

  <wsdl:portType name="DummyServicePortType">
    <wsdl:operation name="f">
      <wsdl:input message="tns:fRequestMessage"/>
    </wsdl:operation>
  </wsdl:portType>

  <wsdl:binding name="DummyServiceBinding" type="tns:DummyServicePortType">
    <soap:binding style="document" transport="http://schemas.xmlsoap.org/soap/http"/>
    <wsdl:operation name="f">
      <soap:operation soapAction="f"/>
      <wsdl:input><soap:body use="literal"/></wsdl:input>
    </wsdl:operation>
  </wsdl:binding>

  <wsdl:service name="DummyService">
    <wsdl:port name="DummyServicePort" binding="tns:DummyServiceBinding">
      <soap:address location="BoogaWooga"/>
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>
""")

    external_schema = suds.byte_str("""\
<?xml version='1.0' encoding='UTF-8'?>
<schema
    xmlns="http://www.w3.org/2001/XMLSchema"
    targetNamespace="second-namespace">
  <element name="external" type="string"/>
</schema>
""")

    store = suds.store.DocumentStore(external_schema=external_schema,
        wsdl=wsdl)
    client = suds.client.Client("suds://wsdl", cache=None, documentStore=store,
        nosend=True, prettyxml=True)
    assert _compare_request(client.service.f(local="--L--",
        local_referenced="--LR--", external="--E--"), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns1="first-namespace" xmlns:ns2="second-namespace" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <SOAP-ENV:Body>
      <ns1:fRequest>
         <ns1:local>--L--</ns1:local>
         <ns1:local_referenced>--LR--</ns1:local_referenced>
         <ns2:external>--E--</ns2:external>
      </ns1:fRequest>
   </SOAP-ENV:Body>
</SOAP-ENV:Envelope>""")


def test_invalid_input_parameter_type_handling():
    """
    Input parameters of invalid type get silently pushed into the constructed
    SOAP request as strings, even though the constructed SOAP request does not
    necessarily satisfy requirements set for it in the web service's WSDL
    schema. It is then left up to the web service implementation to detect and
    report this error.

    """
    client = tests.client_from_wsdl(tests.wsdl_input("""\
      <xsd:complexType name="Freakazoid">
        <xsd:sequence>
          <xsd:element name="freak1" type="xsd:string"/>
          <xsd:element name="freak2" type="xsd:string"/>
          <xsd:element name="freak3" type="xsd:string"/>
        </xsd:sequence>
      </xsd:complexType>
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="p1" type="xsd:string"/>
            <xsd:element name="anInteger" type="xsd:integer"/>
            <xsd:element name="p2" type="xsd:string"/>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", "Wrapper"), nosend=True, prettyxml=True)

    # Passing an unrelated Python type value.
    class SomeType:
        def __str__(self):
            return "Some string representation."
    assert _compare_request(client.service.f(anInteger=SomeType()), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper>
         <ns0:p1/>
         <ns0:anInteger>Some string representation.</ns0:anInteger>
         <ns0:p2/>
      </ns0:Wrapper>
   </ns1:Body>
</SOAP-ENV:Envelope>""")

    # Passing a value of a WSDL schema defined type.
    value = client.factory.create("Freakazoid")
    value.freak1 = "Tiny"
    value.freak2 = "Miny"
    value.freak3 = "Mo"
    assert _compare_request(client.service.f(anInteger=value), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper>
         <ns0:p1/>
         <ns0:anInteger>
            <ns0:freak1>Tiny</ns0:freak1>
            <ns0:freak2>Miny</ns0:freak2>
            <ns0:freak3>Mo</ns0:freak3>
         </ns0:anInteger>
         <ns0:p2/>
      </ns0:Wrapper>
   </ns1:Body>
</SOAP-ENV:Envelope>""")


def test_missing_parameters():
    """Missing non-optional parameters should get passed as empty values."""
    service = _service_from_wsdl(tests.wsdl_input("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="aString" type="xsd:string"/>
            <xsd:element name="anInteger" type="xsd:integer"/>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", "Wrapper"))

    assert _compare_request(service.f(), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper>
         <ns0:aString/>
         <ns0:anInteger/>
      </ns0:Wrapper>
   </ns1:Body>
</SOAP-ENV:Envelope>""")

    assert _compare_request(service.f(u"Pero Ždero"), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper>
         <ns0:aString>Pero Ždero</ns0:aString>
         <ns0:anInteger/>
      </ns0:Wrapper>
   </ns1:Body>
</SOAP-ENV:Envelope>""")

    assert _compare_request(service.f(anInteger=666), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper>
         <ns0:aString/>
         <ns0:anInteger>666</ns0:anInteger>
      </ns0:Wrapper>
   </ns1:Body>
</SOAP-ENV:Envelope>""")

    # None value is treated the same as undefined.
    assert _compare_request(service.f(aString=None, anInteger=666), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper>
         <ns0:aString/>
         <ns0:anInteger>666</ns0:anInteger>
      </ns0:Wrapper>
   </ns1:Body>
</SOAP-ENV:Envelope>""")
    assert _compare_request(service.f(aString="Omega", anInteger=None), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper>
         <ns0:aString>Omega</ns0:aString>
         <ns0:anInteger/>
      </ns0:Wrapper>
   </ns1:Body>
</SOAP-ENV:Envelope>""")


def test_named_parameter():
    class Tester:
        def __init__(self, service, expected_xml):
            self.service = service
            self.expected_xml = expected_xml

        def test(self, *args, **kwargs):
            request = self.service.f(*args, **kwargs)
            assert _compare_request(request, self.expected_xml)

    # Test different ways to make the same web service operation call.
    service = _service_from_wsdl(tests.wsdl_input("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="uno" type="xsd:string"/>
            <xsd:element name="due" type="xsd:string"/>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", "Wrapper"))
    t = Tester(service, """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper>
         <ns0:uno>einz</ns0:uno>
         <ns0:due>zwei</ns0:due>
      </ns0:Wrapper>
   </ns1:Body>
</SOAP-ENV:Envelope>""")
    t.test("einz", "zwei")
    t.test(uno="einz", due="zwei")
    t.test(due="zwei", uno="einz")
    t.test("einz", due="zwei")

    #   The order of parameters in the constructed SOAP request should depend
    # only on the initial WSDL schema.
    service = _service_from_wsdl(tests.wsdl_input("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="due" type="xsd:string"/>
            <xsd:element name="uno" type="xsd:string"/>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", "Wrapper"))
    t = Tester(service, """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper>
         <ns0:due>zwei</ns0:due>
         <ns0:uno>einz</ns0:uno>
      </ns0:Wrapper>
   </ns1:Body>
</SOAP-ENV:Envelope>""")
    t.test("zwei", "einz")
    t.test(uno="einz", due="zwei")
    t.test(due="zwei", uno="einz")
    t.test("zwei", uno="einz")


def test_optional_parameter_handling():
    """Missing optional parameters should not get passed at all."""
    service = _service_from_wsdl(tests.wsdl_input("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="aString" type="xsd:string" minOccurs="0"/>
            <xsd:element name="anInteger" type="xsd:integer" minOccurs="0"/>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", "Wrapper"))

    assert _compare_request(service.f(), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper/>
   </ns1:Body>
</SOAP-ENV:Envelope>""")

    # None is treated as an undefined value.
    assert _compare_request(service.f(None), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper/>
   </ns1:Body>
</SOAP-ENV:Envelope>""")

    # Empty string values are treated as well defined values.
    assert _compare_request(service.f(""), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper>
         <ns0:aString></ns0:aString>
      </ns0:Wrapper>
   </ns1:Body>
</SOAP-ENV:Envelope>""")

    assert _compare_request(service.f("Kiflica"), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper>
         <ns0:aString>Kiflica</ns0:aString>
      </ns0:Wrapper>
   </ns1:Body>
</SOAP-ENV:Envelope>""")

    assert _compare_request(service.f(anInteger=666), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper>
         <ns0:anInteger>666</ns0:anInteger>
      </ns0:Wrapper>
   </ns1:Body>
</SOAP-ENV:Envelope>""")

    assert _compare_request(service.f("Alfa", 9), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper>
         <ns0:aString>Alfa</ns0:aString>
         <ns0:anInteger>9</ns0:anInteger>
      </ns0:Wrapper>
   </ns1:Body>
</SOAP-ENV:Envelope>""")


def test_twice_wrapped_parameter():
    """
      Suds does not recognize 'twice wrapped' data structures and unwraps the
    external one but keeps the internal wrapping structure in place.

    """
    client = tests.client_from_wsdl(tests.wsdl_input("""\
      <xsd:element name="Wrapper1">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="Wrapper2">
              <xsd:complexType>
                <xsd:sequence>
                  <xsd:element name="Elemento" type="xsd:string"/>
                </xsd:sequence>
              </xsd:complexType>
            </xsd:element>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", "Wrapper1"), nosend=True, prettyxml=True)

    assert _isInputWrapped(client, "f")

    # Web service operation calls made with 'valid' parameters.
    #
    # These calls are actually illegal and result in incorrectly generated SOAP
    # requests not matching the relevant WSDL schema. To make them valid we
    # would need to pass a more complex value instead of a simple string, but
    # the current simpler solution is good enough for what we want to test
    # here.
    value = "A B C"
    expectedRequest = """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper1>
         <ns0:Wrapper2>%s</ns0:Wrapper2>
      </ns0:Wrapper1>
   </ns1:Body>
</SOAP-ENV:Envelope>""" % (value,)
    assert _compare_request(client.service.f(value), expectedRequest)
    assert _compare_request(client.service.f(Wrapper2=value), expectedRequest)

    # Web service operation calls made with 'invalid' parameters.
    def testInvalidParameter(**kwargs):
        assert len(kwargs) == 1
        element = kwargs.keys()[0]
        expected = "f() got an unexpected keyword argument '%s'" % (element,)
        e = pytest.raises(TypeError, client.service.f, **kwargs).value
        try:
            assert str(e) == expected
        finally:
            del e
    testInvalidParameter(Elemento="A B C")
    testInvalidParameter(Wrapper1="A B C")


def test_wrapped_parameter(monkeypatch):
    monkeypatch.delitem(locals(), "e", False)

    # Prepare web service proxies.
    client = lambda *args : tests.client_from_wsdl(tests.wsdl_input(*args),
        nosend=True, prettyxml=True)
    client_bare_single = client("""\
      <xsd:element name="Elemento" type="xsd:string"/>""", "Elemento")
    client_bare_multiple_simple = client("""\
      <xsd:element name="Elemento1" type="xsd:string"/>
      <xsd:element name="Elemento2" type="xsd:string"/>""", "Elemento1",
        "Elemento2")
    client_bare_multiple_wrapped = client("""\
      <xsd:complexType name="Wrapper">
        <xsd:sequence>
          <xsd:element name="Elemento" type="xsd:string"/>
        </xsd:sequence>
      </xsd:complexType>
      <xsd:element name="Elemento1" type="ns:Wrapper"/>
      <xsd:element name="Elemento2" type="ns:Wrapper"/>""", "Elemento1",
        "Elemento2")
    client_wrapped_unnamed = client("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="Elemento" type="xsd:string"/>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", "Wrapper")
    client_wrapped_named = client("""\
      <xsd:complexType name="WrapperType">
        <xsd:sequence>
          <xsd:element name="Elemento" type="xsd:string"/>
        </xsd:sequence>
      </xsd:complexType>
      <xsd:element name="Wrapper" type="ns:WrapperType"/>""", "Wrapper")

    #   Make sure suds library interprets our WSDL definitions as wrapped or
    # bare input interfaces as expected.
    assert not _isInputWrapped(client_bare_single, "f")
    assert not _isInputWrapped(client_bare_multiple_simple, "f")
    assert not _isInputWrapped(client_bare_multiple_wrapped, "f")
    assert _isInputWrapped(client_wrapped_unnamed, "f")
    assert _isInputWrapped(client_wrapped_named, "f")

    #   Both bare & wrapped single parameter input web service operations get
    # called the same way even though the wrapped one actually has an extra
    # wrapper element around its input data.
    data = "Maestro"
    call_single = lambda c : c.service.f(data)

    assert _compare_request(call_single(client_bare_single), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Elemento>%s</ns0:Elemento>
   </ns1:Body>
</SOAP-ENV:Envelope>""" % data)

    expected_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper>
         <ns0:Elemento>%s</ns0:Elemento>
      </ns0:Wrapper>
   </ns1:Body>
</SOAP-ENV:Envelope>""" % data
    assert _compare_request(call_single(client_wrapped_unnamed), expected_xml)
    assert _compare_request(call_single(client_wrapped_named), expected_xml)

    #   Suds library's automatic structure unwrapping prevents us from
    # specifying the external wrapper structure directly.
    e = pytest.raises(TypeError, client_wrapped_unnamed.service.f, Wrapper="A")
    assert str(e.value) == "f() got an unexpected keyword argument 'Wrapper'"

    #   Multiple parameter web service operations are never automatically
    # unwrapped.
    data = ("Unga", "Bunga")
    call_multiple = lambda c : c.service.f(*data)

    assert _compare_request(call_multiple(client_bare_multiple_simple), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Elemento1>%s</ns0:Elemento1>
      <ns0:Elemento2>%s</ns0:Elemento2>
   </ns1:Body>
</SOAP-ENV:Envelope>""" % data)

    assert _compare_request(call_multiple(client_bare_multiple_wrapped), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Elemento1>%s</ns0:Elemento1>
      <ns0:Elemento2>%s</ns0:Elemento2>
   </ns1:Body>
</SOAP-ENV:Envelope>""" % data)


def _compare_request(request, expected_xml):
    return tests.compare_xml_to_string(request.original_envelope, expected_xml)


def _isInputWrapped(client, method_name):
    assert len(client.wsdl.bindings) == 1
    operation = client.wsdl.bindings.values()[0].operations[method_name]
    return operation.soap.input.body.wrapped


def _service_from_wsdl(wsdl):
    """
    Construct a suds Client service instance used in tests in this module.

    The constructed Client instance only prepares web service operation
    invocation requests and does not attempt to actually send them.

    """
    client = tests.client_from_wsdl(wsdl, nosend=True, prettyxml=True)
    return client.service
