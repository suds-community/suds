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

import testutils
from testutils import _assert_request_content

if __name__ == "__main__":
    testutils.run_using_pytest(globals())

import suds
import suds.store

import pytest
from six import iterkeys, itervalues, next, u


#TODO: Update the current restriction type output parameter handling so such
# parameters get converted to the correct Python data type based on the
# restriction's underlying data type.
@pytest.mark.xfail
def test_bare_input_restriction_types():
    client_unnamed = testutils.client_from_wsdl(testutils.wsdl("""\
      <xsd:element name="Elemento">
        <xsd:simpleType>
          <xsd:restriction base="xsd:string">
            <xsd:enumeration value="alfa"/>
            <xsd:enumeration value="beta"/>
            <xsd:enumeration value="gamma"/>
          </xsd:restriction>
        </xsd:simpleType>
      </xsd:element>""", input="Elemento", operation_name="f"))

    client_named = testutils.client_from_wsdl(testutils.wsdl("""\
      <xsd:simpleType name="MyType">
        <xsd:restriction base="xsd:string">
          <xsd:enumeration value="alfa"/>
          <xsd:enumeration value="beta"/>
          <xsd:enumeration value="gamma"/>
        </xsd:restriction>
      </xsd:simpleType>
      <xsd:element name="Elemento" type="ns:MyType"/>""", input="Elemento",
        operation_name="f"))

    assert not _is_input_wrapped(client_unnamed, "f")
    assert not _is_input_wrapped(client_named, "f")


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
            # Manually skip xfails for now since there's no way to mark
            if not xfail:
                expanded_param_values.append(param)
    return (param_names, expanded_param_values), {}


@pytest.mark.indirect_parametrize(parametrize_single_element_input_test,
    ("xsd", "external_element_name", "args", "request_body"), (
    # Bare non-optional element.
    ('<xsd:element name="a" type="xsd:integer"/>', "a",
        ([], "<a/>"),
        ([5], "<a>5</a>")),
    # Bare optional element.
    ('<xsd:element name="a" type="xsd:integer" minOccurs="0"/>', "a",
        ([], ""),
        ([5], "<a>5</a>")),
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
        ([], "<Wrapper><a/></Wrapper>",
            "non-optional choice handling buggy"),
        ([5], "<Wrapper><a>5</a></Wrapper>"),
        ([None, 1], "<Wrapper><b1>1</b1><b2/></Wrapper>",
            "non-optional choice handling buggy"),
        ([None, 1, 2],
            "<Wrapper><b1>1</b1><b2>2</b2></Wrapper>"),
        ([None, None, 1],
            "<Wrapper><b1/><b2>1</b2></Wrapper>",
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
        ([], "<Wrapper><a/></Wrapper>",
            "non-optional choice handling buggy"),
        ([5], "<Wrapper><a>5</a></Wrapper>")),
    # Choice with an optional element.
    ("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:choice>
            <xsd:element name="a" type="xsd:integer" minOccurs="0"/>
          </xsd:choice>
        </xsd:complexType>
      </xsd:element>""", "Wrapper",
        ([], "<Wrapper/>"),
        ([5], "<Wrapper><a>5</a></Wrapper>")),
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
        ([], "<Wrapper/>"),
        ([5], "<Wrapper><a>5</a></Wrapper>"),
        ([None, 5], "<Wrapper><b>5</b></Wrapper>")),
    ("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:choice>
            <xsd:element name="a" type="xsd:integer"/>
            <xsd:element name="b" type="xsd:integer" minOccurs="0"/>
          </xsd:choice>
        </xsd:complexType>
      </xsd:element>""", "Wrapper",
        ([], "<Wrapper/>"),
        ([5], "<Wrapper><a>5</a></Wrapper>"),
        ([None, 5], "<Wrapper><b>5</b></Wrapper>")),
    ("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:choice>
            <xsd:element name="a" type="xsd:integer" minOccurs="0"/>
            <xsd:element name="b" type="xsd:integer" minOccurs="0"/>
          </xsd:choice>
        </xsd:complexType>
      </xsd:element>""", "Wrapper",
        ([], "<Wrapper/>"),
        ([5], "<Wrapper><a>5</a></Wrapper>"),
        ([None, 5], "<Wrapper><b>5</b></Wrapper>")),
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
        ([], "<Wrapper><a1/><a2/></Wrapper>",
            "non-optional choice handling buggy"),
        ([5], "<Wrapper><a1>5</a1><a2/></Wrapper>",
            "non-optional choice handling buggy"),
        ([5, 9], """\
          <Wrapper>
            <a1>5</a1>
            <a2>9</a2>
          </Wrapper>"""),
        ([None, 1], "<Wrapper><a1/><a2>1</a2></Wrapper>",
            "non-optional choice handling buggy"),
        ([None, None, 1],
            "<Wrapper><b1>1</b1><b2/></Wrapper>",
            "non-optional choice handling buggy"),
        ([None, None, 1, 2],
            "<Wrapper><b1>1</b1><b2>2</b2></Wrapper>"),
        ([None, None, None, 1],
            "<Wrapper><b1/><b2>1</b2></Wrapper>",
            "non-optional choice handling buggy")),
    # Empty choice.
    ("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:choice/>
        </xsd:complexType>
      </xsd:element>""", "Wrapper",
        ([], "<Wrapper/>")),
    # Empty sequence.
    ("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence/>
        </xsd:complexType>
      </xsd:element>""", "Wrapper",
        ([], "<Wrapper/>")),
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
        ([], "<Wrapper/>",
            # This test passes by accident - the following two bugs seem to
            # cancel each other out:
            #  - choice order indicators explicitly marked optional unsupported
            #  - not constructing correct input parameter values when using no
            #    input arguments for a choice
            #"suds does not yet support minOccurs/maxOccurs attributes on all/"
            #"choice/sequence order indicators"),
            ),
        ([5], "<Wrapper><a>5</a></Wrapper>"),
        ([None, 1],
            "<Wrapper><b>1</b></Wrapper>")),
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
        ([], "<Wrapper/>",
            "suds does not yet support minOccurs/maxOccurs attributes on all/"
            "choice/sequence order indicators"),
        ([5], "<Wrapper><a>5</a><b/></Wrapper>"),
        ([None, 1],
            "<Wrapper><a/><b>1</b></Wrapper>"),
        ([1, 2], """\
            <Wrapper>
              <a>1</a>
              <b>2</b>
            </Wrapper>""")),
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
        ([], "<Wrapper><a/><b1/><b2/></Wrapper>"),
        ([5], "<Wrapper><a>5</a><b1/><b2/></Wrapper>"),
        ([None, 1],
            "<Wrapper><a/><b1>1</b1><b2/></Wrapper>"),
        ([None, 1, 2], """\
            <Wrapper>
              <a/>
              <b1>1</b1>
              <b2>2</b2>
            </Wrapper>"""),
        ([None, None, 1],
            "<Wrapper><a/><b1/><b2>1</b2></Wrapper>")),
    # Sequence with a non-optional element.
    ("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="a" type="xsd:integer"/>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", "Wrapper",
        ([], "<Wrapper><a/></Wrapper>"),
        ([5], "<Wrapper><a>5</a></Wrapper>")),
    # Sequence with an optional element.
    ("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="a" type="xsd:integer" minOccurs="0"/>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", "Wrapper",
        ([], "<Wrapper/>"),
        ([5], "<Wrapper><a>5</a></Wrapper>")),
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
        ([], "<Wrapper><aString1/></Wrapper>",
            "non-optional choice handling buggy"),
        ([5], "<Wrapper><aString1>5</aString1></Wrapper>"),
        ([None, 1, 2], """\
            <Wrapper>
              <anInt1>1</anInt1>
              <aString2>2</aString2>
            </Wrapper>"""),
        ([None, 1, None, 2], """\
            <Wrapper>
              <anInt1>1</anInt1>
              <anInt2>2</anInt2>
            </Wrapper>""")),
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
        ([], "<Wrapper/>"),
        ([5], "<Wrapper><a>5</a></Wrapper>"),
        ([None, 1], "<Wrapper><b>1</b></Wrapper>"),
        ([5, 1],
            "<Wrapper><a>5</a><b>1</b></Wrapper>")),
    ))
def test_document_literal_request_for_single_element_input(xsd,
        external_element_name, args, request_body):
    wsdl = testutils.wsdl(xsd, input=external_element_name,
        xsd_target_namespace="dr. Doolittle", operation_name="f")
    client = testutils.client_from_wsdl(wsdl, nosend=True, prettyxml=True)
    _assert_request_content(client.service.f(*args), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
  <SOAP-ENV:Header/>
  <SOAP-ENV:Body xmlns="dr. Doolittle">%s</SOAP-ENV:Body>
</SOAP-ENV:Envelope>""" % (request_body,))


def test_disabling_automated_simple_interface_unwrapping():
    xsd_target_namespace = "woof"
    wsdl = testutils.wsdl("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="Elemento" type="xsd:string"/>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", input="Wrapper", operation_name="f",
        xsd_target_namespace=xsd_target_namespace)
    client = testutils.client_from_wsdl(wsdl, nosend=True, prettyxml=True,
        unwrap=False)
    assert not _is_input_wrapped(client, "f")
    element_data = "Wonderwall"
    wrapper = client.factory.create("my_xsd:Wrapper")
    wrapper.Elemento = element_data
    _assert_request_content(client.service.f(Wrapper=wrapper), """\
<?xml version="1.0" encoding="UTF-8"?>
<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
  <Header/>
  <Body>
    <Wrapper xmlns="%s">
      <Elemento>%s</Elemento>
    </Wrapper>
  </Body>
</Envelope>""" % (xsd_target_namespace, element_data))


def test_element_references_to_different_namespaces():
    wsdl = suds.byte_str("""\
<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="first-namespace"
    xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema"
    xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
    xmlns:tns="first-namespace">

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
            <xsd:element ref="tns:local_referenced"/>
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
</wsdl:definitions>""")

    external_schema = suds.byte_str("""\
<?xml version='1.0' encoding='UTF-8'?>
<schema
    targetNamespace="second-namespace"
    elementFormDefault="qualified"
    xmlns="http://www.w3.org/2001/XMLSchema">
  <element name="external" type="string"/>
</schema>""")

    store = suds.store.DocumentStore(external_schema=external_schema,
        wsdl=wsdl)
    client = suds.client.Client("suds://wsdl", cache=None, documentStore=store,
        nosend=True, prettyxml=True)
    _assert_request_content(client.service.f(local="--L--",
        local_referenced="--LR--", external="--E--"), """\
<?xml version="1.0" encoding="UTF-8"?>
<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
  <Header/>
  <Body xmlns:ns1="first-namespace" xmlns:ns2="second-namespace">
    <ns1:fRequest>
      <ns1:local>--L--</ns1:local>
      <ns1:local_referenced>--LR--</ns1:local_referenced>
      <ns2:external>--E--</ns2:external>
    </ns1:fRequest>
  </Body>
</Envelope>""")


def test_function_with_reserved_characters():
    wsdl = suds.byte_str("""\
<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="first-namespace"
    xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema"
    xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
    xmlns:tns="first-namespace">

  <wsdl:types>
    <xsd:schema
        targetNamespace="first-namespace"
        elementFormDefault="qualified"
        attributeFormDefault="unqualified">
      <xsd:element name="fRequest">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="local" type="xsd:string"/>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>
    </xsd:schema>
  </wsdl:types>

  <wsdl:message name="fRequestMessage">
    <wsdl:part name="parameters" element="tns:fRequest"/>
  </wsdl:message>

  <wsdl:portType name="DummyServicePortType">
    <wsdl:operation name=".f">
      <wsdl:input message="tns:fRequestMessage"/>
    </wsdl:operation>
    <wsdl:operation name="f">
      <wsdl:input message="tns:fRequestMessage"/>
    </wsdl:operation>
  </wsdl:portType>

  <wsdl:binding name="DummyServiceBinding" type="tns:DummyServicePortType">
    <soap:binding style="document" transport="http://schemas.xmlsoap.org/soap/http"/>
    <wsdl:operation name=".f">
      <soap:operation soapAction=".f"/>
      <wsdl:input><soap:body use="literal"/></wsdl:input>
    </wsdl:operation>
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
</wsdl:definitions>""")

    store = suds.store.DocumentStore(wsdl=wsdl)
    client = suds.client.Client("suds://wsdl", cache=None, documentStore=store,
        nosend=True, prettyxml=True)
    operation_name = ".f"
    method = getattr(client.service, operation_name)
    request = method(local="--L--")
    _assert_request_content(request, """\
<?xml version="1.0" encoding="UTF-8"?>
<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
  <Header/>
  <Body xmlns:ns1="first-namespace">
    <ns1:fRequest>
      <ns1:local>--L--</ns1:local>
    </ns1:fRequest>
  </Body>
</Envelope>""")


def test_invalid_input_parameter_type_handling():
    """
    Input parameters of invalid type get silently pushed into the constructed
    SOAP request as strings, even though the constructed SOAP request does not
    necessarily satisfy requirements set for it in the web service's WSDL
    schema. It is then left up to the web service implementation to detect and
    report this error.

    """
    xsd_target_namespace = "1234567890"
    wsdl = testutils.wsdl("""\
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
      </xsd:element>""", input="Wrapper", operation_name="f",
        xsd_target_namespace=xsd_target_namespace)
    client = testutils.client_from_wsdl(wsdl, nosend=True, prettyxml=True)

    # Passing an unrelated Python type value.
    class SomeType:
        def __str__(self):
            return "Some string representation."
    _assert_request_content(client.service.f(anInteger=SomeType()), """\
<?xml version="1.0" encoding="UTF-8"?>
<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
  <Header/>
  <Body>
    <Wrapper xmlns="%s">
      <p1/>
      <anInteger>Some string representation.</anInteger>
      <p2/>
    </Wrapper>
  </Body>
</Envelope>""" % (xsd_target_namespace,))

    # Passing a value of a WSDL schema defined type.
    value = client.factory.create("my_xsd:Freakazoid")
    value.freak1 = "Tiny"
    value.freak2 = "Miny"
    value.freak3 = "Mo"
    _assert_request_content(client.service.f(anInteger=value), """\
<?xml version="1.0" encoding="UTF-8"?>
<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
  <Header/>
  <Body>
    <Wrapper xmlns="%s">
      <p1/>
      <anInteger>
        <freak1>Tiny</freak1>
        <freak2>Miny</freak2>
        <freak3>Mo</freak3>
      </anInteger>
      <p2/>
    </Wrapper>
  </Body>
</Envelope>""" % (xsd_target_namespace,))


def test_missing_parameters():
    """Missing non-optional parameters should get passed as empty values."""
    xsd_target_namespace = "plonker"
    service = _service_from_wsdl(testutils.wsdl("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="aString" type="xsd:string"/>
            <xsd:element name="anInteger" type="xsd:integer"/>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", input="Wrapper", operation_name="f",
        xsd_target_namespace=xsd_target_namespace))

    _assert_request_content(service.f(), """\
<?xml version="1.0" encoding="UTF-8"?>
<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
  <Header/>
  <Body>
    <Wrapper xmlns="%s">
      <aString/>
      <anInteger/>
    </Wrapper>
  </Body>
</Envelope>""" % (xsd_target_namespace,))

    _assert_request_content(service.f((u("Pero \u017Ddero"))), u("""\
<?xml version="1.0" encoding="UTF-8"?>
<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
  <Header/>
  <Body>
    <Wrapper xmlns="%s">
      <aString>Pero \u017Ddero</aString>
      <anInteger/>
    </Wrapper>
  </Body>
</Envelope>""") % (xsd_target_namespace,))

    _assert_request_content(service.f(anInteger=666), """\
<?xml version="1.0" encoding="UTF-8"?>
<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
  <Header/>
  <Body>
    <Wrapper xmlns="%s">
      <aString/>
      <anInteger>666</anInteger>
    </Wrapper>
  </Body>
</Envelope>""" % (xsd_target_namespace,))

    # None value is treated the same as undefined.
    _assert_request_content(service.f(aString=None, anInteger=666), """\
<?xml version="1.0" encoding="UTF-8"?>
<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
  <Header/>
  <Body>
    <Wrapper xmlns="%s">
      <aString/>
      <anInteger>666</anInteger>
    </Wrapper>
  </Body>
</Envelope>""" % (xsd_target_namespace,))
    _assert_request_content(service.f(aString="Omega", anInteger=None), """\
<?xml version="1.0" encoding="UTF-8"?>
<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
  <Header/>
  <Body>
    <Wrapper xmlns="%s">
      <aString>Omega</aString>
      <anInteger/>
    </Wrapper>
  </Body>
</Envelope>""" % (xsd_target_namespace,))


def test_named_parameter():
    class Tester:
        def __init__(self, service, expected_xml):
            self.service = service
            self.expected_xml = expected_xml

        def test(self, *args, **kwargs):
            request = self.service.f(*args, **kwargs)
            _assert_request_content(request, self.expected_xml)

    # Test different ways to make the same web service operation call.
    xsd_target_namespace = "qwerty"
    service = _service_from_wsdl(testutils.wsdl("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="uno" type="xsd:string"/>
            <xsd:element name="due" type="xsd:string"/>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", input="Wrapper", operation_name="f",
        xsd_target_namespace=xsd_target_namespace))
    t = Tester(service, """\
<?xml version="1.0" encoding="UTF-8"?>
<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
  <Header/>
  <Body>
    <Wrapper xmlns="%s">
      <uno>einz</uno>
      <due>zwei</due>
    </Wrapper>
  </Body>
</Envelope>""" % (xsd_target_namespace,))
    t.test("einz", "zwei")
    t.test(uno="einz", due="zwei")
    t.test(due="zwei", uno="einz")
    t.test("einz", due="zwei")

    # The order of parameters in the constructed SOAP request should depend
    # only on the initial WSDL schema.
    xsd_target_namespace = "abracadabra"
    service = _service_from_wsdl(testutils.wsdl("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="due" type="xsd:string"/>
            <xsd:element name="uno" type="xsd:string"/>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", input="Wrapper", operation_name="f",
        xsd_target_namespace=xsd_target_namespace))
    t = Tester(service, """\
<?xml version="1.0" encoding="UTF-8"?>
<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
  <Header/>
  <Body>
    <Wrapper xmlns="%s">
      <due>zwei</due>
      <uno>einz</uno>
    </Wrapper>
  </Body>
</Envelope>""" % (xsd_target_namespace,))
    t.test("zwei", "einz")
    t.test(uno="einz", due="zwei")
    t.test(due="zwei", uno="einz")
    t.test("zwei", uno="einz")


def test_optional_parameter_handling():
    """Missing optional parameters should not get passed at all."""
    xsd_target_namespace = "RoOfIe"
    service = _service_from_wsdl(testutils.wsdl("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="aString" type="xsd:string" minOccurs="0"/>
            <xsd:element name="anInteger" type="xsd:integer" minOccurs="0"/>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", input="Wrapper", operation_name="f",
        xsd_target_namespace=xsd_target_namespace))

    _assert_request_content(service.f(), """\
<?xml version="1.0" encoding="UTF-8"?>
<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
  <Header/>
  <Body>
    <Wrapper xmlns="%s"/>
  </Body>
</Envelope>""" % (xsd_target_namespace,))

    # None is treated as an undefined value.
    _assert_request_content(service.f(None), """\
<?xml version="1.0" encoding="UTF-8"?>
<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
  <Header/>
  <Body>
    <Wrapper xmlns="%s"/>
  </Body>
</Envelope>""" % (xsd_target_namespace,))

    # Empty string values are treated as well defined values.
    _assert_request_content(service.f(""), """\
<?xml version="1.0" encoding="UTF-8"?>
<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
  <Header/>
  <Body>
    <Wrapper xmlns="%s">
      <aString/>
    </Wrapper>
  </Body>
</Envelope>""" % (xsd_target_namespace,))

    _assert_request_content(service.f("Kiflica"), """\
<?xml version="1.0" encoding="UTF-8"?>
<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
  <Header/>
  <Body>
    <Wrapper xmlns="%s">
      <aString>Kiflica</aString>
    </Wrapper>
  </Body>
</Envelope>""" % (xsd_target_namespace,))

    _assert_request_content(service.f(anInteger=666), """\
<?xml version="1.0" encoding="UTF-8"?>
<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
  <Header/>
  <Body>
    <Wrapper xmlns="%s">
      <anInteger>666</anInteger>
    </Wrapper>
  </Body>
</Envelope>""" % (xsd_target_namespace,))

    _assert_request_content(service.f("Alfa", 9), """\
<?xml version="1.0" encoding="UTF-8"?>
<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
  <Header/>
  <Body>
    <Wrapper xmlns="%s">
      <aString>Alfa</aString>
      <anInteger>9</anInteger>
    </Wrapper>
  </Body>
</Envelope>""" % (xsd_target_namespace,))


def test_optional_parameter_with_empty_object_value():
    """Missing optional parameters should not get passed at all."""
    xsd_target_namespace = "I'm a cute little swamp gorilla monster!"
    wsdl = testutils.wsdl("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="value" type="xsd:anyType" minOccurs="0"/>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", input="Wrapper", operation_name="f",
        xsd_target_namespace=xsd_target_namespace)
    client = testutils.client_from_wsdl(wsdl, nosend=True, prettyxml=True)
    service = client.service

    # Base line: nothing passed --> nothing marshalled.
    _assert_request_content(service.f(), """\
<?xml version="1.0" encoding="UTF-8"?>
<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
  <Header/>
  <Body>
    <Wrapper xmlns="%s"/>
  </Body>
</Envelope>""" % (xsd_target_namespace,))

    # Passing a empty object as an empty dictionary.
    _assert_request_content(service.f({}), """\
<?xml version="1.0" encoding="UTF-8"?>
<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
  <Header/>
  <Body>
    <Wrapper xmlns="%s">
        <value/>
    </Wrapper>
  </Body>
</Envelope>""" % (xsd_target_namespace,))

    # Passing a empty explicitly constructed `suds.sudsobject.Object`.
    empty_object = client.factory.create("my_xsd:Wrapper")
    _assert_request_content(service.f(empty_object), """\
<?xml version="1.0" encoding="UTF-8"?>
<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
  <Header/>
  <Body>
    <Wrapper xmlns="%s">
        <value/>
    </Wrapper>
  </Body>
</Envelope>""" % (xsd_target_namespace,))


def test_SOAP_headers():
    """Rudimentary 'soapheaders' option usage test."""
    wsdl = suds.byte_str("""\
<?xml version="1.0" encoding="utf-8"?>
<wsdl:definitions targetNamespace="my-target-namespace"
    xmlns:tns="my-target-namespace"
    xmlns:s="http://www.w3.org/2001/XMLSchema"
    xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
    xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/">

  <wsdl:types>
    <s:schema elementFormDefault="qualified"
        targetNamespace="my-target-namespace">
      <s:element name="MyHeader">
        <s:complexType>
          <s:sequence>
            <s:element name="Freaky" type="s:hexBinary"/>
          </s:sequence>
        </s:complexType>
      </s:element>
    </s:schema>
  </wsdl:types>

  <wsdl:message name="myOperationHeader">
    <wsdl:part name="MyHeader" element="tns:MyHeader"/>
  </wsdl:message>

  <wsdl:portType name="MyWSSOAP">
    <wsdl:operation name="my_operation"/>
  </wsdl:portType>

  <wsdl:binding name="MyWSSOAP" type="tns:MyWSSOAP">
    <soap:binding transport="http://schemas.xmlsoap.org/soap/http"/>
    <wsdl:operation name="my_operation">
      <soap:operation soapAction="my-SOAP-action" style="document"/>
      <wsdl:input>
        <soap:header message="tns:myOperationHeader" part="MyHeader"
            use="literal"/>
      </wsdl:input>
    </wsdl:operation>
  </wsdl:binding>

  <wsdl:service name="MyWS">
    <wsdl:port name="MyWSSOAP" binding="tns:MyWSSOAP">
      <soap:address location="protocol://my-WS-URL"/>
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>
""")
    header_data = "fools rush in where angels fear to tread"
    client = testutils.client_from_wsdl(wsdl, nosend=True, prettyxml=True)
    client.options.soapheaders = header_data
    _assert_request_content(client.service.my_operation(), """\
<?xml version="1.0" encoding="UTF-8"?>
<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
  <Header>
    <MyHeader xmlns="my-target-namespace">%s</MyHeader>
  </Header>
  <Body/>
</Envelope>""" % (header_data,))


def test_twice_wrapped_parameter():
    """
    Suds does not recognize 'twice wrapped' data structures and unwraps the
    external one but keeps the internal wrapping structure in place.

    """
    xsd_target_namespace = "spank me"
    wsdl = testutils.wsdl("""\
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
      </xsd:element>""", input="Wrapper1", operation_name="f",
        xsd_target_namespace=xsd_target_namespace)
    client = testutils.client_from_wsdl(wsdl, nosend=True, prettyxml=True)

    assert _is_input_wrapped(client, "f")

    # Web service operation calls made with 'valid' parameters.
    #
    # These calls are actually illegal and result in incorrectly generated SOAP
    # requests not matching the relevant WSDL schema. To make them valid we
    # would need to pass a more complex value instead of a simple string, but
    # the current simpler solution is good enough for what we want to test
    # here.
    value = "A B C"
    expected_request = """\
<?xml version="1.0" encoding="UTF-8"?>
<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
  <Header/>
  <Body>
    <Wrapper1 xmlns="%s">
      <Wrapper2>%s</Wrapper2>
    </Wrapper1>
  </Body>
</Envelope>""" % (xsd_target_namespace, value)
    _assert_request_content(client.service.f(value), expected_request)
    _assert_request_content(client.service.f(Wrapper2=value), expected_request)

    # Web service operation calls made with 'invalid' parameters.
    def test_invalid_parameter(**kwargs):
        assert len(kwargs) == 1
        keyword = next(iterkeys(kwargs))
        expected = "f() got an unexpected keyword argument '%s'" % (keyword,)
        e = pytest.raises(TypeError, client.service.f, **kwargs).value
        try:
            assert str(e) == expected
        finally:
            del e  # explicitly break circular reference chain in Python 3
    test_invalid_parameter(Elemento=value)
    test_invalid_parameter(Wrapper1=value)


def test_wrapped_parameter(monkeypatch):
    monkeypatch.delitem(locals(), "e", False)

    # Prepare web service proxies.
    def client(xsd, *input):
        wsdl = testutils.wsdl(xsd, input=input, xsd_target_namespace="toolyan",
            operation_name="f")
        return testutils.client_from_wsdl(wsdl, nosend=True, prettyxml=True)
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
      <xsd:element name="Elemento1" type="Wrapper"/>
      <xsd:element name="Elemento2" type="Wrapper"/>""", "Elemento1",
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
      <xsd:element name="Wrapper" type="WrapperType"/>""", "Wrapper")

    # Make sure suds library interprets our WSDL definitions as wrapped or bare
    # input interfaces as expected.
    assert not _is_input_wrapped(client_bare_single, "f")
    assert not _is_input_wrapped(client_bare_multiple_simple, "f")
    assert not _is_input_wrapped(client_bare_multiple_wrapped, "f")
    assert _is_input_wrapped(client_wrapped_unnamed, "f")
    assert _is_input_wrapped(client_wrapped_named, "f")

    # Both bare & wrapped single parameter input web service operations get
    # called the same way even though the wrapped one actually has an extra
    # wrapper element around its input data.
    data = "Maestro"
    def call_single(c):
        return c.service.f(data)

    _assert_request_content(call_single(client_bare_single), """\
<?xml version="1.0" encoding="UTF-8"?>
<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
  <Header/>
  <Body>
    <Elemento xmlns="toolyan">%s</Elemento>
  </Body>
</Envelope>""" % (data,))

    expected_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
  <Header/>
  <Body>
    <Wrapper xmlns="toolyan">
      <Elemento>%s</Elemento>
    </Wrapper>
  </Body>
</Envelope>""" % (data,)
    _assert_request_content(call_single(client_wrapped_unnamed), expected_xml)
    _assert_request_content(call_single(client_wrapped_named), expected_xml)

    # Suds library's automatic structure unwrapping prevents us from specifying
    # the external wrapper structure directly.
    e = pytest.raises(TypeError, client_wrapped_unnamed.service.f, Wrapper="A")
    try:
        expected = "f() got an unexpected keyword argument 'Wrapper'"
        assert str(e.value) == expected
    finally:
        del e  # explicitly break circular reference chain in Python 3

    # Multiple parameter web service operations are never automatically
    # unwrapped.
    data = ("Unga", "Bunga")
    def call_multiple(c):
        return c.service.f(*data)

    _assert_request_content(call_multiple(client_bare_multiple_simple), """\
<?xml version="1.0" encoding="UTF-8"?>
<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
  <Header/>
  <Body xmlns:ns="toolyan">
    <ns:Elemento1>%s</ns:Elemento1>
    <ns:Elemento2>%s</ns:Elemento2>
  </Body>
</Envelope>""" % data)

    _assert_request_content(call_multiple(client_bare_multiple_wrapped), """\
<?xml version="1.0" encoding="UTF-8"?>
<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
  <Header/>
  <Body xmlns:ns="toolyan">
    <ns:Elemento1>%s</ns:Elemento1>
    <ns:Elemento2>%s</ns:Elemento2>
  </Body>
</Envelope>""" % data)


###############################################################################
#
# Test utilities.
#
###############################################################################



def _is_input_wrapped(client, method_name):
    assert len(client.wsdl.bindings) == 1
    binding = next(itervalues(client.wsdl.bindings))
    operation = binding.operations[method_name]
    return operation.soap.input.body.wrapped


def _service_from_wsdl(wsdl):
    """
    Construct a suds Client service instance used in tests in this module.

    The constructed Client instance only prepares web service operation
    invocation requests and does not attempt to actually send them.

    """
    return testutils.client_from_wsdl(wsdl, nosend=True, prettyxml=True).service
