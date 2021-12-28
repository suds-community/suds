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
General suds Python library unit tests.

Implemented using the 'pytest' testing framework.

This whole module should be refactored into more specialized modules as more
tests get added to it and it acquires more structure.

"""

import testutils
from testutils import _assert_request_content
if __name__ == "__main__":
    testutils.run_using_pytest(globals())

import suds
import suds.store
from suds.sax.text import Raw
from testutils.compare_sax import CompareSAX

import pytest
from six import b, itervalues, next

import re
import xml.sax


@pytest.fixture
def client_with_optional_array_parameters():
    wsdl = b("""\
<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
    xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
    xmlns:tns="my-namespace"
    xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types>
    <xsd:schema targetNamespace="my-namespace"
        elementFormDefault="qualified"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema">
        <xsd:complexType name="inputData">
          <xsd:sequence>
            <xsd:element name="Optional1" minOccurs="0" type="Foo"/>
            <xsd:element name="FooBar" type="foobar"/>
          </xsd:sequence>
        </xsd:complexType>
        <xsd:complexType name="foobar">
          <xsd:sequence>
            <xsd:element name="Optional1" minOccurs="0" maxOccurs="1" type="Foo"/>
            <xsd:element name="BarArray" minOccurs="0" maxOccurs="unbounded" type="Bar"/>
            <xsd:element name="NonOptional1" type="Bar"/>
          </xsd:sequence>
        </xsd:complexType>
      <xsd:complexType name="Foo">
        <xsd:sequence>
          <xsd:element name="foo" minOccurs="0" maxOccurs="1">
            <xsd:simpleType>
              <xsd:restriction base="xsd:boolean">
              </xsd:restriction>
            </xsd:simpleType>
          </xsd:element>
        </xsd:sequence>
      </xsd:complexType>
      <xsd:complexType name="Bar">
        <xsd:sequence>
          <xsd:element name="bar" minOccurs="1" maxOccurs="1">
            <xsd:simpleType>
              <xsd:restriction base="xsd:boolean">
              </xsd:restriction>
            </xsd:simpleType>
          </xsd:element>
          <xsd:element name="Optional1" minOccurs="0" maxOccurs="1" type="Foo"/>
        </xsd:sequence>
      </xsd:complexType>
      <xsd:element name="inputData" type="tns:inputData"/>
    </xsd:schema>
  </wsdl:types>
  <wsdl:message name="inputData">
    <wsdl:part name="inputData" element="tns:inputData"/>
  </wsdl:message>


  <wsdl:service name="dummy">
    <wsdl:port name="dummy" binding="tns:dummy">
      <soap:address location="https://localhost/dummy"/>
    </wsdl:port>
  </wsdl:service>


  <wsdl:portType name="dummy">
    <wsdl:operation name="f">
      <wsdl:input name="inputData" message="tns:inputData"/>
    </wsdl:operation>
  </wsdl:portType>

  <wsdl:binding name="dummy" type="tns:dummy">
    <soap:binding style="document"
      transport="http://schemas.xmlsoap.org/soap/http"/>
    <wsdl:operation name="f">
      <soap:operation soapAction="f" style="document"/>
      <wsdl:input name="inputData">
       <soap:body use="literal"/>
      </wsdl:input>
      <wsdl:output><soap:body use="literal"/></wsdl:output>
    </wsdl:operation>
  </wsdl:binding>
</wsdl:definitions>
""")

    client = testutils.client_from_wsdl(wsdl, nosend=True, prettyxml=True)

    return client


#TODO: Update the current choice parameter handling implementation to make this
# test pass.
@pytest.mark.xfail
def test_choice_parameter_implementation_inconsistencies():
    """
    Choice parameter support implementation needs to be cleaned up.

    If you declare a message part's element of a simple type X, or you define
    it as a complex type having a single member of type X, and suds has been
    configured to automatically unwrap such single-member complex types, the
    web service proxy object's constructed function declarations should match.
    They should both accept a single parameter of type X.

    However the current choice support implementation causes only the 'complex'
    case to get an additional 'choice' flag information to be included in the
    constructed parameter definition structure.

    """
    def client(x, y):
        return testutils.client_from_wsdl(testutils.wsdl(x, input=y))

    client_simple_short = client("""\
      <xsd:element name="Elemento" type="xsd:string"/>""", "Elemento")

    client_simple_long = client("""\
      <xsd:element name="Elemento">
        <xsd:simpleType>
          <xsd:restriction base="xsd:string"/>
        </xsd:simpleType>
      </xsd:element>""", "Elemento")

    client_complex_wrapped = client("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="Elemento" type="xsd:string"/>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", "Wrapper")

    method_param = lambda x : x.sd[0].ports[0][1][0][1][0]
    method_param_simple_short = method_param(client_simple_short)
    method_param_simple_long = method_param(client_simple_long)
    method_param_complex_wrapped = method_param(client_complex_wrapped)

    assert len(method_param_simple_short) == len(method_param_simple_long)
    assert len(method_param_simple_long) == len(method_param_complex_wrapped)


def test_converting_client_to_string_must_not_raise_an_exception():
    client = testutils.client_from_wsdl(
        b("<?xml version='1.0' encoding='UTF-8'?><root/>"))
    str(client)


def test_converting_metadata_to_string():
    client = testutils.client_from_wsdl(b("""\
<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
    xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
    xmlns:ns="my-namespace"
    xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types>
    <xsd:schema targetNamespace="my-namespace"
        elementFormDefault="qualified"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:complexType name="AAA">
        <xsd:sequence>
          <xsd:element name="u1" type="xsd:string"/>
          <xsd:element name="u2" type="xsd:string"/>
          <xsd:element name="u3" type="xsd:string"/>
        </xsd:sequence>
      </xsd:complexType>
    </xsd:schema>
  </wsdl:types>
  <wsdl:portType name="dummyPortType">
  </wsdl:portType>
  <wsdl:binding name="dummy" type="ns:dummyPortType">
    <soap:binding style="document"
      transport="http://schemas.xmlsoap.org/soap/http"/>
  </wsdl:binding>
  <wsdl:service name="dummy">
    <wsdl:port name="dummy" binding="ns:dummy">
      <soap:address location="https://localhost/dummy"/>
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>
"""))
    # Metadata with empty content.
    metadata = client.wsdl.__metadata__
    assert len(metadata) == 0
    assert "<empty>" == str(metadata)

    # Metadata with non-empty content.
    metadata = client.factory.create("AAA").__metadata__
    assert len(metadata) == 2
    metadata_string = str(metadata)
    assert re.search(" sxtype = ", metadata_string)
    assert re.search(r" ordering\[\] = ", metadata_string)


def test_empty_invalid_WSDL(monkeypatch):
    monkeypatch.delitem(locals(), "e", False)
    e = pytest.raises(xml.sax.SAXParseException, testutils.client_from_wsdl,
        b(""))
    try:
        assert e.value.getMessage() == "no element found"
    finally:
        del e  # explicitly break circular reference chain in Python 3


def test_empty_valid_WSDL():
    client = testutils.client_from_wsdl(
        b("<?xml version='1.0' encoding='UTF-8'?><root/>"))
    assert not client.wsdl.services, "No service definitions must be read "  \
        "from an empty WSDL."


def test_enumeration_type_string_should_contain_its_value():
    client = testutils.client_from_wsdl(b("""\
<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
    xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
    xmlns:ns="my-namespace"
    xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types>
    <xsd:schema targetNamespace="my-namespace"
        elementFormDefault="qualified"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:simpleType name="AAA">
        <xsd:restriction base="xsd:string">
          <xsd:enumeration value="One"/>
          <xsd:enumeration value="Two"/>
          <xsd:enumeration value="Thirty-Two"/>
        </xsd:restriction>
      </xsd:simpleType>
    </xsd:schema>
  </wsdl:types>
  <wsdl:portType name="dummyPortType">
  </wsdl:portType>
  <wsdl:binding name="dummy" type="ns:dummyPortType">
    <soap:binding style="document"
      transport="http://schemas.xmlsoap.org/soap/http"/>
  </wsdl:binding>
  <wsdl:service name="dummy">
    <wsdl:port name="dummy" binding="ns:dummy">
      <soap:address location="https://localhost/dummy"/>
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>
"""))
    enumeration_data = client.wsdl.schema.types["AAA", "my-namespace"]
    # Legend:
    #   eX - enumeration element.
    #   aX - ancestry for the enumeration element.
    (e1, a1), (e2, a2), (e3, a3) = enumeration_data
    assert isinstance(e1, suds.xsd.sxbasic.Enumeration)
    assert isinstance(e2, suds.xsd.sxbasic.Enumeration)
    assert isinstance(e3, suds.xsd.sxbasic.Enumeration)
    assert e1.name == "One"
    assert e2.name == "Two"
    assert e3.name == "Thirty-Two"
    # Python 3 output does not include a trailing L after long integer output,
    # while Python 2 does. For example: 0x12345678 is output as 0x12345678L in
    # Python 2 and simply as 0x12345678 in Python 3.
    assert re.match('<Enumeration:0x[0-9a-f]+L? name="One" />$', e1.str())
    assert re.match('<Enumeration:0x[0-9a-f]+L? name="Two" />$', e2.str())
    assert re.match('<Enumeration:0x[0-9a-f]+L? name="Thirty-Two" />$',
        e3.str())


def test_function_parameters_global_sequence_in_a_sequence():
    client = testutils.client_from_wsdl(b("""\
<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
    xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
    xmlns:ns="my-namespace"
    xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types>
    <xsd:schema targetNamespace="my-namespace"
        elementFormDefault="qualified"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:complexType name="UngaBunga">
        <xsd:sequence>
          <xsd:element name="u1" type="xsd:string"/>
          <xsd:element name="u2" type="xsd:string"/>
          <xsd:element name="u3" type="xsd:string"/>
        </xsd:sequence>
      </xsd:complexType>
      <xsd:element name="Elemento">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="x1" type="xsd:string"/>
            <xsd:element name="x2" type="UngaBunga"/>
            <xsd:element name="x3" type="xsd:string"/>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>
    </xsd:schema>
  </wsdl:types>
  <wsdl:message name="fRequestMessage">
    <wsdl:part name="parameters" element="ns:Elemento"/>
  </wsdl:message>
  <wsdl:portType name="dummyPortType">
    <wsdl:operation name="f">
      <wsdl:input message="ns:fRequestMessage"/>
    </wsdl:operation>
  </wsdl:portType>
  <wsdl:binding name="dummy" type="ns:dummyPortType">
    <soap:binding style="document"
      transport="http://schemas.xmlsoap.org/soap/http"/>
    <wsdl:operation name="f">
      <soap:operation soapAction="f" style="document"/>
      <wsdl:input><soap:body use="literal"/></wsdl:input>
      <wsdl:output><soap:body use="literal"/></wsdl:output>
    </wsdl:operation>
  </wsdl:binding>
  <wsdl:service name="dummy">
    <wsdl:port name="dummy" binding="ns:dummy">
      <soap:address location="https://localhost/dummy"/>
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>
"""))

    service = client.sd[0]
    assert len(service.types) == 1

    # Method parameters as read from the service definition.
    assert len(service.params) == 3
    assert service.params[0][0].name == "x1"
    assert service.params[0][0].type == _string_type
    assert isinstance(service.params[0][1], suds.xsd.sxbuiltin.XString)
    assert service.params[1][0].name == "x2"
    assert service.params[1][0].type == ("UngaBunga", "my-namespace")
    assert isinstance(service.params[1][1], suds.xsd.sxbasic.Complex)
    assert service.params[2][0].name == "x3"
    assert service.params[2][0].type == _string_type
    assert isinstance(service.params[2][1], suds.xsd.sxbuiltin.XString)

    # Method parameters as read from a method object.
    assert len(service.ports) == 1
    port, methods = service.ports[0]
    assert len(methods) == 1
    method_name, method_params = methods[0]
    assert method_name == "f"
    assert len(method_params) == 3
    assert method_params[0][0] == "x1"
    assert method_params[0][1] is service.params[0][0]
    assert method_params[1][0] == "x2"
    assert method_params[1][1] is service.params[1][0]
    assert method_params[2][0] == "x3"
    assert method_params[2][1] is service.params[2][0]


def test_function_parameters_local_choice():
    client = testutils.client_from_wsdl(b("""\
<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
    xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
    xmlns:ns="my-namespace"
    xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types>
    <xsd:schema targetNamespace="my-namespace"
        elementFormDefault="qualified"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:element name="Elemento">
        <xsd:complexType>
          <xsd:choice>
            <xsd:element name="u1" type="xsd:string"/>
            <xsd:element name="u2" type="xsd:string"/>
          </xsd:choice>
        </xsd:complexType>
      </xsd:element>
    </xsd:schema>
  </wsdl:types>
  <wsdl:message name="fRequestMessage">
    <wsdl:part name="parameters" element="ns:Elemento"/>
  </wsdl:message>
  <wsdl:portType name="dummyPortType">
    <wsdl:operation name="f">
      <wsdl:input message="ns:fRequestMessage"/>
    </wsdl:operation>
  </wsdl:portType>
  <wsdl:binding name="dummy" type="ns:dummyPortType">
    <soap:binding style="document"
      transport="http://schemas.xmlsoap.org/soap/http"/>
    <wsdl:operation name="f">
      <soap:operation soapAction="f" style="document"/>
      <wsdl:input><soap:body use="literal"/></wsdl:input>
      <wsdl:output><soap:body use="literal"/></wsdl:output>
    </wsdl:operation>
  </wsdl:binding>
  <wsdl:service name="dummy">
    <wsdl:port name="dummy" binding="ns:dummy">
      <soap:address location="https://localhost/dummy"/>
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>
"""))

    service = client.sd[0]
    assert not service.types

    # Method parameters as read from the service definition.
    assert len(service.params) == 2
    assert service.params[0][0].name == "u1"
    assert service.params[0][0].type == _string_type
    assert isinstance(service.params[0][1], suds.xsd.sxbuiltin.XString)
    assert service.params[1][0].name == "u2"
    assert service.params[1][0].type == _string_type
    assert isinstance(service.params[1][1], suds.xsd.sxbuiltin.XString)

    # Method parameters as read from a method object.
    assert len(service.ports) == 1
    port, methods = service.ports[0]
    assert len(methods) == 1
    method_name, method_params = methods[0]
    assert method_name == "f"
    assert len(method_params) == 2
    assert method_params[0][0] == "u1"
    assert method_params[0][1] is service.params[0][0]
    assert method_params[1][0] == "u2"
    assert method_params[1][1] is service.params[1][0]

    # Construct method parameter element object.
    param_out = client.factory.create("Elemento")
    _assert_dynamic_type(param_out, "Elemento")
    assert not param_out.__keylist__


def test_function_parameters_local_choice_in_a_sequence():
    client = testutils.client_from_wsdl(b("""\
<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
    xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
    xmlns:ns="my-namespace"
    xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types>
    <xsd:schema targetNamespace="my-namespace"
        elementFormDefault="qualified"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:element name="Elemento">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="x1" type="xsd:string"/>
            <xsd:element name="x2">
              <xsd:complexType>
                <xsd:choice>
                  <xsd:element name="u1" type="xsd:string"/>
                  <xsd:element name="u2" type="xsd:string"/>
                  <xsd:element name="u3" type="xsd:string"/>
                </xsd:choice>
              </xsd:complexType>
            </xsd:element>
            <xsd:element name="x3" type="xsd:string"/>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>
    </xsd:schema>
  </wsdl:types>
  <wsdl:message name="fRequestMessage">
    <wsdl:part name="parameters" element="ns:Elemento"/>
  </wsdl:message>
  <wsdl:portType name="dummyPortType">
    <wsdl:operation name="f">
      <wsdl:input message="ns:fRequestMessage"/>
    </wsdl:operation>
  </wsdl:portType>
  <wsdl:binding name="dummy" type="ns:dummyPortType">
    <soap:binding style="document"
      transport="http://schemas.xmlsoap.org/soap/http"/>
    <wsdl:operation name="f">
      <soap:operation soapAction="f" style="document"/>
      <wsdl:input><soap:body use="literal"/></wsdl:input>
      <wsdl:output><soap:body use="literal"/></wsdl:output>
    </wsdl:operation>
  </wsdl:binding>
  <wsdl:service name="dummy">
    <wsdl:port name="dummy" binding="ns:dummy">
      <soap:address location="https://localhost/dummy"/>
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>
"""))

    service = client.sd[0]
    assert not service.types

    # Method parameters as read from the service definition.
    assert len(service.params) == 3
    assert service.params[0][0].name == "x1"
    assert service.params[0][0].type == _string_type
    assert isinstance(service.params[0][1], suds.xsd.sxbuiltin.XString)
    assert service.params[1][0].name == "x2"
    assert service.params[1][0].type is None
    assert isinstance(service.params[1][1], suds.xsd.sxbasic.Element)
    assert service.params[2][0].name == "x3"
    assert service.params[2][0].type == _string_type
    assert isinstance(service.params[2][1], suds.xsd.sxbuiltin.XString)

    # Method parameters as read from a method object.
    assert len(service.ports) == 1
    port, methods = service.ports[0]
    assert len(methods) == 1
    method_name, method_params = methods[0]
    assert method_name == "f"
    assert len(method_params) == 3
    assert method_params[0][0] == "x1"
    assert method_params[0][1] is service.params[0][0]
    assert method_params[1][0] == "x2"
    assert method_params[1][1] is service.params[1][0]
    assert method_params[2][0] == "x3"
    assert method_params[2][1] is service.params[2][0]

    # Construct method parameter element object.
    param_out = client.factory.create("Elemento")
    _assert_dynamic_type(param_out, "Elemento")
    assert param_out.x1 is None
    _assert_dynamic_type(param_out.x2, "x2")
    assert not param_out.x2.__keylist__
    assert param_out.x3 is None

    # Construct method parameter objects with a locally defined type.
    param_in = client.factory.create("Elemento.x2")
    _assert_dynamic_type(param_in, "x2")
    assert not param_out.x2.__keylist__
    assert param_in is not param_out.x2


def test_function_parameters_local_sequence_in_a_sequence():
    client = testutils.client_from_wsdl(b("""\
<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
    xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
    xmlns:ns="my-namespace"
    xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types>
    <xsd:schema targetNamespace="my-namespace"
        elementFormDefault="qualified"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:element name="Elemento">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="x1" type="xsd:string"/>
            <xsd:element name="x2">
              <xsd:complexType>
                <xsd:sequence>
                  <xsd:element name="u1" type="xsd:string"/>
                  <xsd:element name="u2" type="xsd:string"/>
                  <xsd:element name="u3" type="xsd:string"/>
                </xsd:sequence>
              </xsd:complexType>
            </xsd:element>
            <xsd:element name="x3" type="xsd:string"/>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>
    </xsd:schema>
  </wsdl:types>
  <wsdl:message name="fRequestMessage">
    <wsdl:part name="parameters" element="ns:Elemento"/>
  </wsdl:message>
  <wsdl:portType name="dummyPortType">
    <wsdl:operation name="f">
      <wsdl:input message="ns:fRequestMessage"/>
    </wsdl:operation>
  </wsdl:portType>
  <wsdl:binding name="dummy" type="ns:dummyPortType">
    <soap:binding style="document"
      transport="http://schemas.xmlsoap.org/soap/http"/>
    <wsdl:operation name="f">
      <soap:operation soapAction="f" style="document"/>
      <wsdl:input><soap:body use="literal"/></wsdl:input>
      <wsdl:output><soap:body use="literal"/></wsdl:output>
    </wsdl:operation>
  </wsdl:binding>
  <wsdl:service name="dummy">
    <wsdl:port name="dummy" binding="ns:dummy">
      <soap:address location="https://localhost/dummy"/>
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>
"""))

    service = client.sd[0]
    assert not service.types

    # Method parameters as read from the service definition.
    assert len(service.params) == 3
    assert service.params[0][0].name == "x1"
    assert service.params[0][0].type == _string_type
    assert isinstance(service.params[0][1], suds.xsd.sxbuiltin.XString)
    assert service.params[1][0].name == "x2"
    assert service.params[1][0].type is None
    assert isinstance(service.params[1][1], suds.xsd.sxbasic.Element)
    assert service.params[2][0].name == "x3"
    assert service.params[2][0].type == _string_type
    assert isinstance(service.params[2][1], suds.xsd.sxbuiltin.XString)

    # Method parameters as read from a method object.
    assert len(service.ports) == 1
    port, methods = service.ports[0]
    assert len(methods) == 1
    method_name, method_params = methods[0]
    assert method_name == "f"
    assert len(method_params) == 3
    assert method_params[0][0] == "x1"
    assert method_params[0][1] is service.params[0][0]
    assert method_params[1][0] == "x2"
    assert method_params[1][1] is service.params[1][0]
    assert method_params[2][0] == "x3"
    assert method_params[2][1] is service.params[2][0]

    # Construct method parameter element object.
    param_out = client.factory.create("Elemento")
    _assert_dynamic_type(param_out, "Elemento")
    assert param_out.x1 is None
    _assert_dynamic_type(param_out.x2, "x2")
    assert param_out.x2.u1 is None
    assert param_out.x2.u2 is None
    assert param_out.x2.u3 is None
    assert param_out.x3 is None

    # Construct method parameter objects with a locally defined type.
    param_in = client.factory.create("Elemento.x2")
    _assert_dynamic_type(param_in, "x2")
    assert param_in.u1 is None
    assert param_in.u2 is None
    assert param_in.u3 is None
    assert param_in is not param_out.x2


def test_function_parameters_sequence_in_a_choice():
    client = testutils.client_from_wsdl(b("""\
<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
    xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
    xmlns:ns="my-namespace"
    xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types>
    <xsd:schema targetNamespace="my-namespace"
        elementFormDefault="qualified"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:element name="Choice">
        <xsd:complexType>
          <xsd:choice>
            <xsd:element name="a1" type="xsd:string"/>
            <xsd:element name="sequence">
              <xsd:complexType>
                <xsd:sequence>
                  <xsd:element name="e1" type="xsd:string"/>
                  <xsd:element name="e2" type="xsd:string"/>
                  <xsd:element name="e3" type="xsd:string"/>
                </xsd:sequence>
              </xsd:complexType>
            </xsd:element>
            <xsd:element name="a2" type="xsd:string"/>
          </xsd:choice>
        </xsd:complexType>
      </xsd:element>
    </xsd:schema>
  </wsdl:types>
  <wsdl:message name="fRequestMessage">
    <wsdl:part name="parameters" element="ns:Choice"/>
  </wsdl:message>
  <wsdl:portType name="dummyPortType">
    <wsdl:operation name="f">
      <wsdl:input message="ns:fRequestMessage"/>
    </wsdl:operation>
  </wsdl:portType>
  <wsdl:binding name="dummy" type="ns:dummyPortType">
    <soap:binding style="document"
      transport="http://schemas.xmlsoap.org/soap/http"/>
    <wsdl:operation name="f">
      <soap:operation soapAction="f" style="document"/>
      <wsdl:input><soap:body use="literal"/></wsdl:input>
      <wsdl:output><soap:body use="literal"/></wsdl:output>
    </wsdl:operation>
  </wsdl:binding>
  <wsdl:service name="dummy">
    <wsdl:port name="dummy" binding="ns:dummy">
      <soap:address location="https://localhost/dummy"/>
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>
"""))

    # Input #1.
    request = _construct_SOAP_request(client, 'f', a1="Wackadoodle")
    CompareSAX.document2data(request, """\
<?xml version="1.0" encoding="UTF-8"?>
<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
   <Header/>
   <Body>
      <Choice xmlns="my-namespace">
         <a1>Wackadoodle</a1>
      </Choice>
   </Body>
</Envelope>""")

    # Input #2.
    param = client.factory.create("Choice.sequence")
    param.e2 = "Wackadoodle"
    request = _construct_SOAP_request(client, 'f', sequence=param)
    CompareSAX.document2data(request, """\
<?xml version="1.0" encoding="UTF-8"?>
<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
   <Header/>
   <Body>
      <Choice xmlns="my-namespace">
         <sequence>
            <e1/>
            <e2>Wackadoodle</e2>
            <e3/>
         </sequence>
      </Choice>
   </Body>
</Envelope>""")


def test_function_parameters_sequence_in_a_choice_in_a_sequence():
    client = testutils.client_from_wsdl(b("""\
<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
    xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
    xmlns:ns="my-namespace"
    xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types>
    <xsd:schema targetNamespace="my-namespace"
        elementFormDefault="qualified"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:element name="External">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="choice">
              <xsd:complexType>
                <xsd:choice>
                  <xsd:element name="a1" type="xsd:string"/>
                  <xsd:element name="sequence">
                    <xsd:complexType>
                      <xsd:sequence>
                        <xsd:element name="e1" type="xsd:string"/>
                        <xsd:element name="e2" type="xsd:string"/>
                        <xsd:element name="e3" type="xsd:string"/>
                      </xsd:sequence>
                    </xsd:complexType>
                  </xsd:element>
                  <xsd:element name="a2" type="xsd:string"/>
                </xsd:choice>
              </xsd:complexType>
            </xsd:element>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>
    </xsd:schema>
  </wsdl:types>
  <wsdl:message name="fRequestMessage">
    <wsdl:part name="parameters" element="ns:External"/>
  </wsdl:message>
  <wsdl:portType name="dummyPortType">
    <wsdl:operation name="f">
      <wsdl:input message="ns:fRequestMessage"/>
    </wsdl:operation>
  </wsdl:portType>
  <wsdl:binding name="dummy" type="ns:dummyPortType">
    <soap:binding style="document"
      transport="http://schemas.xmlsoap.org/soap/http"/>
    <wsdl:operation name="f">
      <soap:operation soapAction="f" style="document"/>
      <wsdl:input><soap:body use="literal"/></wsdl:input>
      <wsdl:output><soap:body use="literal"/></wsdl:output>
    </wsdl:operation>
  </wsdl:binding>
  <wsdl:service name="dummy">
    <wsdl:port name="dummy" binding="ns:dummy">
      <soap:address location="https://localhost/dummy"/>
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>
"""))

    # Construct input parameters.
    param = client.factory.create("External.choice")
    param.sequence = client.factory.create("External.choice.sequence")
    param.sequence.e2 = "Wackadoodle"

    # Construct a SOAP request containing our input parameters.
    request = _construct_SOAP_request(client, 'f', param)
    CompareSAX.document2data(request, """\
<?xml version="1.0" encoding="UTF-8"?>
<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
   <Header/>
   <Body>
      <External xmlns="my-namespace">
         <choice>
            <sequence>
               <e1/>
               <e2>Wackadoodle</e2>
               <e3/>
            </sequence>
         </choice>
      </External>
   </Body>
</Envelope>""")


def test_function_parameters_strings():
    client = testutils.client_from_wsdl(b("""\
<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
    xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
    xmlns:ns="my-namespace"
    xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types>
    <xsd:schema targetNamespace="my-namespace"
        elementFormDefault="qualified"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:element name="Elemento">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="x1" type="xsd:string"/>
            <xsd:element name="x2" type="xsd:string"/>
            <xsd:element name="x3" type="xsd:string"/>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>
    </xsd:schema>
  </wsdl:types>
  <wsdl:message name="fRequestMessage">
    <wsdl:part name="parameters" element="ns:Elemento"/>
  </wsdl:message>
  <wsdl:portType name="dummyPortType">
    <wsdl:operation name="f">
      <wsdl:input message="ns:fRequestMessage"/>
    </wsdl:operation>
  </wsdl:portType>
  <wsdl:binding name="dummy" type="ns:dummyPortType">
    <soap:binding style="document"
      transport="http://schemas.xmlsoap.org/soap/http"/>
    <wsdl:operation name="f">
      <soap:operation soapAction="f" style="document"/>
      <wsdl:input><soap:body use="literal"/></wsdl:input>
      <wsdl:output><soap:body use="literal"/></wsdl:output>
    </wsdl:operation>
  </wsdl:binding>
  <wsdl:service name="dummy">
    <wsdl:port name="dummy" binding="ns:dummy">
      <soap:address location="https://localhost/dummy"/>
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>
"""))

    service = client.sd[0]
    assert not service.types

    # Method parameters as read from the service definition.
    assert len(service.params) == 3
    assert service.params[0][0].name == "x1"
    assert service.params[0][0].type == _string_type
    assert isinstance(service.params[0][1], suds.xsd.sxbuiltin.XString)
    assert service.params[1][0].name == "x2"
    assert service.params[1][0].type == _string_type
    assert isinstance(service.params[1][1], suds.xsd.sxbuiltin.XString)
    assert service.params[2][0].name == "x3"
    assert service.params[2][0].type == _string_type
    assert isinstance(service.params[2][1], suds.xsd.sxbuiltin.XString)

    # Method parameters as read from a method object.
    assert len(service.ports) == 1
    port, methods = service.ports[0]
    assert len(methods) == 1
    method_name, method_params = methods[0]
    assert method_name == "f"
    assert len(method_params) == 3
    assert method_params[0][0] == "x1"
    assert method_params[0][1] is service.params[0][0]
    assert method_params[1][0] == "x2"
    assert method_params[1][1] is service.params[1][0]
    assert method_params[2][0] == "x3"
    assert method_params[2][1] is service.params[2][0]


def test_global_enumeration():
    client = testutils.client_from_wsdl(b("""\
<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
    xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
    xmlns:ns="my-namespace"
    xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types>
    <xsd:schema targetNamespace="my-namespace"
        elementFormDefault="qualified"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:simpleType name="AAA">
        <xsd:restriction base="xsd:string">
          <xsd:enumeration value="One"/>
          <xsd:enumeration value="Two"/>
          <xsd:enumeration value="Thirty-Two"/>
        </xsd:restriction>
      </xsd:simpleType>
    </xsd:schema>
  </wsdl:types>
  <wsdl:portType name="dummyPortType">
  </wsdl:portType>
  <wsdl:binding name="dummy" type="ns:dummyPortType">
    <soap:binding style="document"
      transport="http://schemas.xmlsoap.org/soap/http"/>
  </wsdl:binding>
  <wsdl:service name="dummy">
    <wsdl:port name="dummy" binding="ns:dummy">
      <soap:address location="https://localhost/dummy"/>
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>
"""))

    assert len(client.sd) == 1
    service = client.sd[0]

    assert len(service.types) == 1
    for typeTuple in service.types:
        # Tuple containing the same object twice.
        assert len(typeTuple) == 2
        assert typeTuple[0] is typeTuple[1]

    aType = service.types[0][0]
    assert isinstance(aType, suds.xsd.sxbasic.Simple)
    assert aType.name == "AAA"
    assert aType.enum()
    assert aType.mixed()
    assert aType.restriction()
    assert not aType.choice()
    assert not aType.sequence()

    assert len(aType.rawchildren) == 1
    assert isinstance(aType.rawchildren[0], suds.xsd.sxbasic.Restriction)
    assert aType.rawchildren[0].ref == _string_type

    enum = client.factory.create("AAA")
    assert enum.One == "One"
    assert enum.Two == "Two"
    assert getattr(enum, "Thirty-Two") == "Thirty-Two"


def test_global_sequence_in_a_global_sequence():
    client = testutils.client_from_wsdl(b("""\
<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
    xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
    xmlns:ns="my-namespace"
    xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types>
    <xsd:schema targetNamespace="my-namespace"
        elementFormDefault="qualified"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:complexType name="Oklahoma">
        <xsd:sequence>
          <xsd:element name="c1" type="xsd:string"/>
          <xsd:element name="c2" type="xsd:string"/>
          <xsd:element name="c3" type="xsd:string"/>
        </xsd:sequence>
      </xsd:complexType>
      <xsd:complexType name="Wackadoodle">
        <xsd:sequence>
          <xsd:element name="x1" type="xsd:string"/>
          <xsd:element name="x2" type="Oklahoma"/>
          <xsd:element name="x3" type="xsd:string"/>
        </xsd:sequence>
      </xsd:complexType>
    </xsd:schema>
  </wsdl:types>
  <wsdl:portType name="dummyPortType">
  </wsdl:portType>
  <wsdl:binding name="dummy" type="ns:dummyPortType">
    <soap:binding style="document"
      transport="http://schemas.xmlsoap.org/soap/http"/>
  </wsdl:binding>
  <wsdl:service name="dummy">
    <wsdl:port name="dummy" binding="ns:dummy">
      <soap:address location="https://localhost/dummy"/>
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>
"""))

    service = client.sd[0]

    assert len(service.types) == 2
    for typeTuple in service.types:
        # Tuple containing the same object twice.
        assert len(typeTuple) == 2
        assert typeTuple[0] is typeTuple[1]

    type_in = service.types[0][0]
    assert isinstance(type_in, suds.xsd.sxbasic.Complex)
    assert type_in.name == "Oklahoma"
    assert not type_in.sequence()
    assert type_in.rawchildren[0].sequence()

    type_out = service.types[1][0]
    assert isinstance(type_out, suds.xsd.sxbasic.Complex)
    assert type_out.name == "Wackadoodle"
    assert not type_out.sequence()
    assert type_out.rawchildren[0].sequence()

    assert len(type_out.rawchildren) == 1
    children = type_out.children()
    assert isinstance(children, list)
    assert len(children) == 3
    assert children[0][0].name == "x1"
    assert children[0][0].type == _string_type
    assert children[1][0].name == "x2"
    assert children[1][0].type == ("Oklahoma", "my-namespace")
    assert children[2][0].name == "x3"
    assert children[2][0].type == _string_type

    sequence_out = client.factory.create("Wackadoodle")
    _assert_dynamic_type(sequence_out, "Wackadoodle")
    assert sequence_out.__metadata__.sxtype is type_out
    assert sequence_out.x1 is None
    sequence_in = sequence_out.x2
    assert sequence_out.x3 is None
    _assert_dynamic_type(sequence_in, "Oklahoma")
    assert sequence_in.__metadata__.sxtype is type_in
    assert sequence_in.c1 is None
    assert sequence_in.c2 is None
    assert sequence_in.c3 is None


def test_global_string_sequence():
    client = testutils.client_from_wsdl(b("""\
<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
    xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
    xmlns:ns="my-namespace"
    xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types>
    <xsd:schema targetNamespace="my-namespace"
        elementFormDefault="qualified"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:complexType name="Oklahoma">
        <xsd:sequence>
          <xsd:element name="c1" type="xsd:string"/>
          <xsd:element name="c2" type="xsd:string"/>
          <xsd:element name="c3" type="xsd:string"/>
        </xsd:sequence>
      </xsd:complexType>
    </xsd:schema>
  </wsdl:types>
  <wsdl:portType name="dummyPortType">
  </wsdl:portType>
  <wsdl:binding name="dummy" type="ns:dummyPortType">
    <soap:binding style="document"
      transport="http://schemas.xmlsoap.org/soap/http"/>
  </wsdl:binding>
  <wsdl:service name="dummy">
    <wsdl:port name="dummy" binding="ns:dummy">
      <soap:address location="https://localhost/dummy"/>
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>
"""))

    service = client.sd[0]

    assert len(service.types) == 1
    for typeTuple in service.types:
        # Tuple containing the same object twice.
        assert len(typeTuple) == 2
        assert typeTuple[0] is typeTuple[1]

    aType = service.types[0][0]
    assert isinstance(aType, suds.xsd.sxbasic.Complex)
    assert aType.name == "Oklahoma"
    assert not aType.choice()
    assert not aType.enum()
    assert not aType.mixed()
    assert not aType.restriction()
    assert not aType.sequence()

    assert len(aType.rawchildren) == 1
    sequence_node = aType.rawchildren[0]
    assert isinstance(sequence_node, suds.xsd.sxbasic.Sequence)
    assert sequence_node.sequence()
    assert len(sequence_node) == 3
    sequence_items = sequence_node.children()
    assert isinstance(sequence_items, list)
    assert len(sequence_items) == 3
    assert sequence_items[0][0].name == "c1"
    assert sequence_items[0][0].type == _string_type
    assert sequence_items[1][0].name == "c2"
    assert sequence_items[1][0].type == _string_type
    assert sequence_items[2][0].name == "c3"
    assert sequence_items[2][0].type == _string_type

    sequence = client.factory.create("Oklahoma")
    getattr(sequence, "c1")
    getattr(sequence, "c2")
    getattr(sequence, "c3")
    pytest.raises(AttributeError, getattr, sequence, "nonExistingChild")
    assert sequence.c1 is None
    assert sequence.c2 is None
    assert sequence.c3 is None
    sequence.c1 = "Pero"
    sequence.c3 = "Zdero"
    assert sequence.c1 == "Pero"
    assert sequence.c2 is None
    assert sequence.c3 == "Zdero"


def test_local_sequence_in_a_global_sequence():
    client = testutils.client_from_wsdl(b("""\
<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
    xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
    xmlns:ns="my-namespace"
    xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types>
    <xsd:schema targetNamespace="my-namespace"
        elementFormDefault="qualified"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:complexType name="Wackadoodle">
        <xsd:sequence>
          <xsd:element name="x1">
              <xsd:complexType name="Oklahoma">
                <xsd:sequence>
                  <xsd:element name="c1" type="xsd:string"/>
                  <xsd:element name="c2" type="xsd:string"/>
                  <xsd:element name="c3" type="xsd:string"/>
                </xsd:sequence>
              </xsd:complexType>
          </xsd:element>
          <xsd:element name="x2">
              <xsd:complexType>
                <xsd:sequence>
                  <xsd:element name="s" type="xsd:string"/>
                </xsd:sequence>
              </xsd:complexType>
          </xsd:element>
        </xsd:sequence>
      </xsd:complexType>
    </xsd:schema>
  </wsdl:types>
  <wsdl:portType name="dummyPortType">
  </wsdl:portType>
  <wsdl:binding name="dummy" type="ns:dummyPortType">
    <soap:binding style="document"
      transport="http://schemas.xmlsoap.org/soap/http"/>
  </wsdl:binding>
  <wsdl:service name="dummy">
    <wsdl:port name="dummy" binding="ns:dummy">
      <soap:address location="https://localhost/dummy"/>
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>
"""))

    service = client.sd[0]
    assert len(service.types) == 1

    type_out = service.types[0][0]
    assert isinstance(type_out, suds.xsd.sxbasic.Complex)
    assert type_out.name == "Wackadoodle"
    assert not type_out.sequence()
    assert type_out.rawchildren[0].sequence()

    children = type_out.children()
    assert isinstance(children, list)
    assert len(children) == 2
    type_in1 = children[0][0]
    assert isinstance(type_in1, suds.xsd.sxbasic.Element)
    assert not type_in1.sequence()
    assert type_in1.rawchildren[0].rawchildren[0].sequence()
    type_in2 = children[1][0]
    assert isinstance(type_in2, suds.xsd.sxbasic.Element)
    assert not type_in2.sequence()
    assert type_in2.rawchildren[0].rawchildren[0].sequence()
    assert type_in1.rawchildren[0].name == "Oklahoma"
    assert type_in1.rawchildren[0].type is None
    namespace1 = type_in1.rawchildren[0].namespace()
    assert namespace1 == ("ns", "my-namespace")
    assert type_in2.rawchildren[0].name is None
    assert type_in2.rawchildren[0].type is None
    assert type_in1.rawchildren[0].namespace() is namespace1

    sequence_out = client.factory.create("Wackadoodle")
    _assert_dynamic_type(sequence_out, "Wackadoodle")
    assert sequence_out.__metadata__.sxtype is type_out
    sequence_in1 = sequence_out.x1
    sequence_in2 = sequence_out.x2
    _assert_dynamic_type(sequence_in1, "x1")
    _assert_dynamic_type(sequence_in2, "x2")
    assert sequence_in1.__metadata__.sxtype is type_in1
    assert sequence_in2.__metadata__.sxtype is type_in2
    assert sequence_in1.c1 is None
    assert sequence_in1.c2 is None
    assert sequence_in1.c3 is None
    assert sequence_in2.s is None


def test_optional_parameter_not_instantiated():
    wsdl = b("""\
<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
    xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
    xmlns:tns="my-namespace"
    xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types>
    <xsd:schema targetNamespace="my-namespace"
        elementFormDefault="qualified"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema">
        <xsd:complexType name="inputData">
          <xsd:sequence>
            <xsd:element name="foobar" minOccurs="1" maxOccurs="1" type="foobar"/>
            <xsd:element name="Optional1" minOccurs="0" maxOccurs="1" type="Foo"/>
            <xsd:element name="Optional2" minOccurs="0" maxOccurs="1" type="Bar"/>
          </xsd:sequence>
        </xsd:complexType>
        <xsd:complexType name="foobar">
          <xsd:sequence>
            <xsd:element name="Optional1" minOccurs="0" maxOccurs="1" type="Foo"/>
            <xsd:element name="Optional2" minOccurs="0" maxOccurs="1" type="Bar"/>
            <xsd:element name="NonOptional1" minOccurs="1" maxOccurs="1" type="Bar"/>
          </xsd:sequence>
        </xsd:complexType>
      <xsd:complexType name="Foo">
        <xsd:sequence>
          <xsd:element name="foo" minOccurs="0" maxOccurs="1">
            <xsd:simpleType>
              <xsd:restriction base="xsd:boolean">
              </xsd:restriction>
            </xsd:simpleType>
          </xsd:element>
        </xsd:sequence>
      </xsd:complexType>
      <xsd:complexType name="Bar">
        <xsd:sequence>
          <xsd:element name="bar" minOccurs="1" maxOccurs="1">
            <xsd:simpleType>
              <xsd:restriction base="xsd:boolean">
              </xsd:restriction>
            </xsd:simpleType>
          </xsd:element>
          <xsd:element name="Optional1" minOccurs="0" maxOccurs="1" type="Foo"/>
        </xsd:sequence>
      </xsd:complexType>
      <xsd:element name="inputData" type="tns:inputData"/>
    </xsd:schema>
  </wsdl:types>
  <wsdl:message name="inputData">
    <wsdl:part name="inputData" element="tns:inputData"/>
  </wsdl:message>


  <wsdl:service name="dummy">
    <wsdl:port name="dummy" binding="tns:dummy">
      <soap:address location="https://localhost/dummy"/>
    </wsdl:port>
  </wsdl:service>


  <wsdl:portType name="dummy">
    <wsdl:operation name="f">
      <wsdl:input name="inputData" message="tns:inputData"/>
    </wsdl:operation>
  </wsdl:portType>

  <wsdl:binding name="dummy" type="tns:dummy">
    <soap:binding style="document"
      transport="http://schemas.xmlsoap.org/soap/http"/>
    <wsdl:operation name="f">
      <soap:operation soapAction="f" style="document"/>
      <wsdl:input name="inputData">
       <soap:body use="literal"/>
      </wsdl:input>
      <wsdl:output><soap:body use="literal"/></wsdl:output>
    </wsdl:operation>
  </wsdl:binding>
</wsdl:definitions>
""")

    expected_request_content = """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:inputData>
         <ns0:foobar>
            <ns0:NonOptional1>
               <ns0:bar/>
            </ns0:NonOptional1>
         </ns0:foobar>
      </ns0:inputData>
   </ns1:Body>
</SOAP-ENV:Envelope>"""

    client = testutils.client_from_wsdl(wsdl, nosend=True, prettyxml=True)


    foobar = client.factory.create("foobar")

    assert foobar.Optional1 is None
    assert foobar.Optional2 is None
    assert foobar.NonOptional1 is not None
    assert foobar.NonOptional1.Optional1 is None

    service = client.service

    result = service.f(foobar=foobar)

    _assert_request_content(result, expected_request_content)


def test_array_are_instantiated_even_if_optional(client_with_optional_array_parameters):
    expected_request_content = """\
<?xml version="1.0" encoding="UTF-8"?>
    <SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
       <SOAP-ENV:Header/>
       <ns1:Body>
          <ns0:inputData>
             <ns0:FooBar>
                <ns0:BarArray>
                  <ns0:bar>foo</ns0:bar>
                </ns0:BarArray>
                <ns0:BarArray>
                  <ns0:bar>bar</ns0:bar>
                </ns0:BarArray>
                <ns0:NonOptional1>
                   <ns0:bar/>
                </ns0:NonOptional1>
             </ns0:FooBar>
          </ns0:inputData>
       </ns1:Body>
    </SOAP-ENV:Envelope>"""

    client = client_with_optional_array_parameters

    foobar = client.factory.create("foobar")

    assert foobar.Optional1 is None
    assert foobar.NonOptional1 is not None
    assert isinstance(foobar.BarArray, list)

    bar = client.factory.create("Bar")
    bar.bar = "foo"
    foobar.BarArray.append(bar)
    bar = client.factory.create("Bar")
    bar.bar = 'bar'
    foobar.BarArray.append(bar)

    service = client.service

    result = service.f(FooBar=foobar)

    _assert_request_content(result, expected_request_content)


def test_empty_optional_array_is_not_present(client_with_optional_array_parameters):
    expected_request_content = """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:inputData>
         <ns0:FooBar>
            <ns0:NonOptional1>
               <ns0:bar/>
            </ns0:NonOptional1>
         </ns0:FooBar>
      </ns0:inputData>
   </ns1:Body>
</SOAP-ENV:Envelope>"""

    client = client_with_optional_array_parameters
    foobar = client.factory.create("foobar")
    assert foobar.Optional1 is None
    assert foobar.NonOptional1 is not None
    assert isinstance(foobar.BarArray, list)

    service = client.service
    result = service.f(FooBar=foobar)

    _assert_request_content(result, expected_request_content)


def test_named_parameter_with_underscore():
    client = testutils.client_from_wsdl(b("""\
<?xml version="1.0" encoding="utf-8"?>
<wsdl:definitions xmlns:s="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://schemas.xmlsoap.org/wsdl/soap12/" xmlns:http="http://schemas.xmlsoap.org/wsdl/http/" xmlns:mime="http://schemas.xmlsoap.org/wsdl/mime/" xmlns:tns="https://labelservice.gls-italy.com/" xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/" xmlns:tm="http://microsoft.com/wsdl/mime/textMatching/" xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/" targetNamespace="https://labelservice.gls-italy.com/" xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/">
  <wsdl:types>
    <s:schema elementFormDefault="qualified" targetNamespace="https://labelservice.gls-italy.com/">
      <s:element name="CloseWorkDayByShipmentNumber">
        <s:complexType>
          <s:sequence>
            <s:element minOccurs="0" maxOccurs="1" name="_xmlRequest" type="s:string" />
          </s:sequence>
        </s:complexType>
      </s:element>
      <s:element name="CloseWorkDayByShipmentNumberResponse">
        <s:complexType>
          <s:sequence>
            <s:element minOccurs="0" maxOccurs="1" name="CloseWorkDayByShipmentNumberResult">
              <s:complexType mixed="true">
                <s:sequence>
                  <s:any />
                </s:sequence>
              </s:complexType>
            </s:element>
          </s:sequence>
        </s:complexType>
      </s:element>
    </s:schema>
  </wsdl:types>
  <wsdl:message name="CloseWorkDayByShipmentNumberSoapIn">
    <wsdl:part name="parameters" element="tns:CloseWorkDayByShipmentNumber" />
  </wsdl:message>
  <wsdl:message name="CloseWorkDayByShipmentNumberSoapOut">
    <wsdl:part name="parameters" element="tns:CloseWorkDayByShipmentNumberResponse" />
  </wsdl:message>
  <wsdl:message name="CloseWorkDayByShipmentNumberHttpPostIn">
    <wsdl:part name="_xmlRequest" type="s:string" />
  </wsdl:message>
  <wsdl:message name="CloseWorkDayByShipmentNumberHttpPostOut">
    <wsdl:part name="Body" />
  </wsdl:message>
  <wsdl:message name="CloseWorkDayByShipmentNumberHttpGetIn">
    <wsdl:part name="_xmlRequest" type="s:string" />
  </wsdl:message>
  <wsdl:message name="CloseWorkDayByShipmentNumberHttpGetOut">
    <wsdl:part name="Body" />
  </wsdl:message>
  <wsdl:portType name="IlsWebServiceSoap">
    <wsdl:operation name="CloseWorkDayByShipmentNumber">
      <wsdl:documentation xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/">Invia le informazioni definitive di chiusura delle spedizioni (Esegue la trasmissione in sede.)</wsdl:documentation>
      <wsdl:input message="tns:CloseWorkDayByShipmentNumberSoapIn" />
      <wsdl:output message="tns:CloseWorkDayByShipmentNumberSoapOut" />
    </wsdl:operation>
  </wsdl:portType>
  <wsdl:portType name="IlsWebServiceHttpGet">
    <wsdl:operation name="CloseWorkDayByShipmentNumber">
      <wsdl:documentation xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/">Invia le informazioni definitive di chiusura delle spedizioni (Esegue la trasmissione in sede.)</wsdl:documentation>
      <wsdl:input message="tns:CloseWorkDayByShipmentNumberHttpGetIn" />
      <wsdl:output message="tns:CloseWorkDayByShipmentNumberHttpGetOut" />
    </wsdl:operation>
  </wsdl:portType>
  <wsdl:portType name="IlsWebServiceHttpPost">
    <wsdl:operation name="CloseWorkDayByShipmentNumber">
      <wsdl:documentation xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/">Invia le informazioni definitive di chiusura delle spedizioni (Esegue la trasmissione in sede.)</wsdl:documentation>
      <wsdl:input message="tns:CloseWorkDayByShipmentNumberHttpPostIn" />
      <wsdl:output message="tns:CloseWorkDayByShipmentNumberHttpPostOut" />
    </wsdl:operation>
  </wsdl:portType>
  <wsdl:binding name="IlsWebServiceSoap" type="tns:IlsWebServiceSoap">
    <soap:binding transport="http://schemas.xmlsoap.org/soap/http" />
    <wsdl:operation name="CloseWorkDayByShipmentNumber">
      <soap:operation soapAction="https://labelservice.gls-italy.com/CloseWorkDayByShipmentNumber" style="document" />
      <wsdl:input>
        <soap:body use="literal" />
      </wsdl:input>
      <wsdl:output>
        <soap:body use="literal" />
      </wsdl:output>
    </wsdl:operation>
  </wsdl:binding>
  <wsdl:binding name="IlsWebServiceSoap12" type="tns:IlsWebServiceSoap">
    <soap12:binding transport="http://schemas.xmlsoap.org/soap/http" />
    <wsdl:operation name="CloseWorkDayByShipmentNumber">
      <soap12:operation soapAction="https://labelservice.gls-italy.com/CloseWorkDayByShipmentNumber" style="document" />
      <wsdl:input>
        <soap12:body use="literal" />
      </wsdl:input>
      <wsdl:output>
        <soap12:body use="literal" />
      </wsdl:output>
    </wsdl:operation>
  </wsdl:binding>
  <wsdl:binding name="IlsWebServiceHttpGet" type="tns:IlsWebServiceHttpGet">
    <http:binding verb="GET" />
    <wsdl:operation name="CloseWorkDayByShipmentNumber">
      <http:operation location="/CloseWorkDayByShipmentNumber" />
      <wsdl:input>
        <http:urlEncoded />
      </wsdl:input>
      <wsdl:output>
        <mime:content part="Body" type="text/xml" />
      </wsdl:output>
    </wsdl:operation>
  </wsdl:binding>
  <wsdl:binding name="IlsWebServiceHttpPost" type="tns:IlsWebServiceHttpPost">
    <http:binding verb="POST" />
    <wsdl:operation name="CloseWorkDayByShipmentNumber">
      <http:operation location="/CloseWorkDayByShipmentNumber" />
      <wsdl:input>
        <mime:content type="application/x-www-form-urlencoded" />
      </wsdl:input>
      <wsdl:output>
        <mime:content part="Body" type="text/xml" />
      </wsdl:output>
    </wsdl:operation>
  </wsdl:binding>
  <wsdl:service name="IlsWebService">
    <wsdl:port name="IlsWebServiceSoap" binding="tns:IlsWebServiceSoap">
      <soap:address location="https://labelservice.gls-italy.com/ilswebservice.asmx" />
    </wsdl:port>
    <wsdl:port name="IlsWebServiceSoap12" binding="tns:IlsWebServiceSoap12">
      <soap12:address location="https://labelservice.gls-italy.com/ilswebservice.asmx" />
    </wsdl:port>
    <wsdl:port name="IlsWebServiceHttpGet" binding="tns:IlsWebServiceHttpGet">
      <http:address location="https://labelservice.gls-italy.com/ilswebservice.asmx" />
    </wsdl:port>
    <wsdl:port name="IlsWebServiceHttpPost" binding="tns:IlsWebServiceHttpPost">
      <http:address location="https://labelservice.gls-italy.com/ilswebservice.asmx" />
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>
"""), nosend=True, prettyxml=True)
    xml = Raw("""
    <info>
      <SedeGls>XX</SedeGls>
      <CodiceClienteGls>xxx</CodiceClienteGls>
      <PasswordClienteGls>xxx</PasswordClienteGls>
      <Parcel>
        <NumeroDiSpedizioneGLSDaConfermare>11111111</NumeroDiSpedizioneGLSDaConfermare>
      </Parcel>
    </info>""")
    result = client.service.CloseWorkDayByShipmentNumber(xml)

    expected_request_content = """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:ns0="https://labelservice.gls-italy.com/" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/">
  <SOAP-ENV:Header/>
  <ns1:Body>
    <ns0:CloseWorkDayByShipmentNumber>
      <ns0:_xmlRequest>
        <info>
          <SedeGls>XX</SedeGls>
          <CodiceClienteGls>xxx</CodiceClienteGls>
          <PasswordClienteGls>xxx</PasswordClienteGls>
          <Parcel>
            <NumeroDiSpedizioneGLSDaConfermare>11111111</NumeroDiSpedizioneGLSDaConfermare>
          </Parcel>
        </info>
      </ns0:_xmlRequest>
    </ns0:CloseWorkDayByShipmentNumber>
  </ns1:Body>
</SOAP-ENV:Envelope>"""
    _assert_request_content(result, expected_request_content)


def test_attributes_on_elements():
    client = testutils.client_from_wsdl(b("""\
<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
    xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
    xmlns:tns="my-namespace"
    xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types>
    <xsd:schema targetNamespace="my-namespace"
        elementFormDefault="qualified"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema">
        <xsd:complexType name="inputData">
          <xsd:sequence>
            <xsd:element name="foobar" minOccurs="1" maxOccurs="1" type="foobar"/>
          </xsd:sequence>
        </xsd:complexType>
        <xsd:complexType name="foobar">
          <xsd:sequence>
            <xsd:element minOccurs="0" maxOccurs="1" name="value" type="xsd:string" />
          </xsd:sequence>
          <xsd:attribute name="name" type="xsd:string" />
        </xsd:complexType>
      <xsd:element name="inputData" type="tns:inputData"/>
    </xsd:schema>
  </wsdl:types>
  <wsdl:message name="inputData">
    <wsdl:part name="inputData" element="tns:inputData"/>
  </wsdl:message>

  <wsdl:service name="dummy">
    <wsdl:port name="dummy" binding="tns:dummy">
      <soap:address location="https://localhost/dummy"/>
    </wsdl:port>
  </wsdl:service>

  <wsdl:portType name="dummy">
    <wsdl:operation name="f">
      <wsdl:input name="inputData" message="tns:inputData"/>
    </wsdl:operation>
  </wsdl:portType>

  <wsdl:binding name="dummy" type="tns:dummy">
    <soap:binding style="document"
      transport="http://schemas.xmlsoap.org/soap/http"/>
    <wsdl:operation name="f">
      <soap:operation soapAction="f" style="document"/>
      <wsdl:input name="inputData">
       <soap:body use="literal"/>
      </wsdl:input>
      <wsdl:output><soap:body use="literal"/></wsdl:output>
    </wsdl:operation>
  </wsdl:binding>
</wsdl:definitions>
"""), nosend=True)
    foobar = client.factory.create("foobar")

    assert foobar.value is None
    assert foobar._name == ""

    foobar.value = "foo"
    foobar._name = "bar"
    result = client.service.f(foobar)

    expected_request_content = """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:inputData>
         <ns0:foobar name="bar">
            <ns0:value>foo</ns0:value>
         </ns0:foobar>
      </ns0:inputData>
   </ns1:Body>
</SOAP-ENV:Envelope>"""
    _assert_request_content(result, expected_request_content)

def test_no_trailing_comma_in_function_prototype_description_string__0():
    client = testutils.client_from_wsdl(b("""\
<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
    xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
    xmlns:ns="my-namespace"
    xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types>
    <xsd:schema targetNamespace="my-namespace"
        elementFormDefault="qualified"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:element name="InputData">
        <xsd:complexType>
          <xsd:sequence/>
        </xsd:complexType>
      </xsd:element>
    </xsd:schema>
  </wsdl:types>
  <wsdl:message name="fRequestMessage">
    <wsdl:part name="parameters" element="ns:InputData"/>
  </wsdl:message>
  <wsdl:portType name="dummyPortType">
    <wsdl:operation name="f">
      <wsdl:input message="ns:fRequestMessage"/>
    </wsdl:operation>
  </wsdl:portType>
  <wsdl:binding name="dummy" type="ns:dummyPortType">
    <soap:binding style="document"
      transport="http://schemas.xmlsoap.org/soap/http"/>
    <wsdl:operation name="f">
      <soap:operation soapAction="f" style="document"/>
      <wsdl:input><soap:body use="literal"/></wsdl:input>
      <wsdl:output><soap:body use="literal"/></wsdl:output>
    </wsdl:operation>
  </wsdl:binding>
  <wsdl:service name="dummy">
    <wsdl:port name="dummy" binding="ns:dummy">
      <soap:address location="https://localhost/dummy"/>
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>
"""))
    s = str(client)
    assert " f()\n" in s


def test_no_trailing_comma_in_function_prototype_description_string__1():
    client = testutils.client_from_wsdl(b("""\
<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
    xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
    xmlns:ns="my-namespace"
    xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types>
    <xsd:schema targetNamespace="my-namespace"
        elementFormDefault="qualified"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:element name="InputData">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="x1" type="xsd:string"/>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>
    </xsd:schema>
  </wsdl:types>
  <wsdl:message name="fRequestMessage">
    <wsdl:part name="parameters" element="ns:InputData"/>
  </wsdl:message>
  <wsdl:portType name="dummyPortType">
    <wsdl:operation name="f">
      <wsdl:input message="ns:fRequestMessage"/>
    </wsdl:operation>
  </wsdl:portType>
  <wsdl:binding name="dummy" type="ns:dummyPortType">
    <soap:binding style="document"
      transport="http://schemas.xmlsoap.org/soap/http"/>
    <wsdl:operation name="f">
      <soap:operation soapAction="f" style="document"/>
      <wsdl:input><soap:body use="literal"/></wsdl:input>
      <wsdl:output><soap:body use="literal"/></wsdl:output>
    </wsdl:operation>
  </wsdl:binding>
  <wsdl:service name="dummy">
    <wsdl:port name="dummy" binding="ns:dummy">
      <soap:address location="https://localhost/dummy"/>
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>
"""))
    s = str(client)
    assert " f(xs:string x1)\n" in s


def test_no_trailing_comma_in_function_prototype_description_string__3():
    client = testutils.client_from_wsdl(b("""\
<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
    xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
    xmlns:ns="my-namespace"
    xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types>
    <xsd:schema targetNamespace="my-namespace"
        elementFormDefault="qualified"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:element name="InputData">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="x1" type="xsd:string"/>
            <xsd:element name="x2" type="xsd:string"/>
            <xsd:element name="x3" type="xsd:string"/>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>
    </xsd:schema>
  </wsdl:types>
  <wsdl:message name="fRequestMessage">
    <wsdl:part name="parameters" element="ns:InputData"/>
  </wsdl:message>
  <wsdl:portType name="dummyPortType">
    <wsdl:operation name="f">
      <wsdl:input message="ns:fRequestMessage"/>
    </wsdl:operation>
  </wsdl:portType>
  <wsdl:binding name="dummy" type="ns:dummyPortType">
    <soap:binding style="document"
      transport="http://schemas.xmlsoap.org/soap/http"/>
    <wsdl:operation name="f">
      <soap:operation soapAction="f" style="document"/>
      <wsdl:input><soap:body use="literal"/></wsdl:input>
      <wsdl:output><soap:body use="literal"/></wsdl:output>
    </wsdl:operation>
  </wsdl:binding>
  <wsdl:service name="dummy">
    <wsdl:port name="dummy" binding="ns:dummy">
      <soap:address location="https://localhost/dummy"/>
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>
"""))
    s = str(client)
    assert " f(xs:string x1, xs:string x2, xs:string x3)\n" in s


def test_no_types():
    client = testutils.client_from_wsdl(b("""\
<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
    xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
    xmlns:ns="my-namespace"
    xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types>
    <xsd:schema targetNamespace="my-namespace"
        elementFormDefault="qualified"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema"/>
  </wsdl:types>
  <wsdl:portType name="dummyPortType">
  </wsdl:portType>
  <wsdl:binding name="dummy" type="ns:dummyPortType">
    <soap:binding style="document"
      transport="http://schemas.xmlsoap.org/soap/http"/>
  </wsdl:binding>
  <wsdl:service name="dummy">
    <wsdl:port name="dummy" binding="ns:dummy">
      <soap:address location="https://localhost/dummy"/>
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>
"""))

    assert len(client.sd) == 1
    service = client.sd[0]

    assert not client.wsdl.schema.types
    assert not service.types

    pytest.raises(suds.TypeNotFound, client.factory.create, "NonExistingType")


def test_parameter_referencing_missing_element(monkeypatch):
    wsdl = testutils.wsdl("", input="missingElement",
        xsd_target_namespace="aaa")
    monkeypatch.delitem(locals(), "e", False)
    e = pytest.raises(suds.TypeNotFound, testutils.client_from_wsdl, wsdl)
    try:
        assert str(e.value) == "Type not found: '(missingElement, aaa, )'"
    finally:
        del e  # explicitly break circular reference chain in Python 3


class TestFindTypeInXSDSchemaWithRecursiveTypeDefinitions:
    """Must not cause an infinite loop."""

    def test_with_recursion_in_imported_schema(self):
        client = testutils.client_from_wsdl(b("""\
<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
    xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
    xmlns:ns="my-namespace"
    xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types
        xmlns:imported="my-imported-namespace"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema">
    <xsd:schema targetNamespace="my-imported-namespace"
        elementFormDefault="qualified">
      <xsd:element name="Keys">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="value" type="xsd:string"/>
            <xsd:element ref="imported:Keys" minOccurs="0"/>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>
    </xsd:schema>
    <xsd:schema targetNamespace="my-namespace"
        elementFormDefault="qualified"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:import namespace="my-imported-namespace"/>
      <xsd:complexType name="Wrapper">
        <xsd:sequence>
          <xsd:element ref="imported:Keys"/>
        </xsd:sequence>
      </xsd:complexType>
    </xsd:schema>
  </wsdl:types>
  <wsdl:portType name="dummyPortType"/>
  <wsdl:binding name="dummy" type="ns:dummyPortType">
    <soap:binding style="document"
      transport="http://schemas.xmlsoap.org/soap/http"/>
  </wsdl:binding>
  <wsdl:service name="dummy">
    <wsdl:port name="dummy" binding="ns:dummy">
      <soap:address location="https://localhost/dummy"/>
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>
"""))
        assert pytest.raises(
            suds.TypeNotFound, client.factory.create, 'ns:DoesNotExist')

    def test_with_recursion_in_same_schema(self):
        client = testutils.client_from_wsdl(b("""\
<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
    xmlns:ns="my-namespace"
    xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
    xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types>
    <xsd:schema targetNamespace="my-namespace"
        elementFormDefault="qualified"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:element name="Keys">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="value" type="xsd:string"/>
            <xsd:element ref="ns:Keys" minOccurs="0"/>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>
    </xsd:schema>
  </wsdl:types>
  <wsdl:portType name="dummyPortType"/>
  <wsdl:binding name="dummy" type="ns:dummyPortType">
    <soap:binding style="document"
      transport="http://schemas.xmlsoap.org/soap/http"/>
  </wsdl:binding>
  <wsdl:service name="dummy">
    <wsdl:port name="dummy" binding="ns:dummy">
      <soap:address location="https://localhost/dummy"/>
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>
"""))
        assert pytest.raises(
            suds.TypeNotFound, client.factory.create, 'ns:DoesNotExist')


def test_recursive_XSD_import():
    url_xsd = "suds://xsd"
    xsd = b("""\
<xsd:schema targetNamespace="my-xsd-namespace"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <xsd:import namespace="my-xsd-namespace" schemaLocation="%(url_imported)s"/>
</xsd:schema>
""" % dict(url_imported=url_xsd))
    wsdl = b("""\
<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-wsdl-namespace"
    xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/">
  <wsdl:import location="%(url_imported)s"/>
</wsdl:definitions>""" % dict(url_imported=url_xsd))
    store = suds.store.DocumentStore(xsd=xsd)
    testutils.client_from_wsdl(wsdl, documentStore=store)


#TODO: Update the current restriction type input parameter handling so they get
# 'unwrapped' correctly instead of each of their enumeration values getting
# interpreted as a separate input parameter.
@pytest.mark.xfail
def test_restrictions():
    client_unnamed = testutils.client_from_wsdl(testutils.wsdl("""\
      <xsd:element name="Elemento">
        <xsd:simpleType>
          <xsd:restriction base="xsd:int">
            <xsd:enumeration value="1"/>
            <xsd:enumeration value="3"/>
            <xsd:enumeration value="5"/>
          </xsd:restriction>
        </xsd:simpleType>
      </xsd:element>""", input="Elemento"))

    client_named = testutils.client_from_wsdl(testutils.wsdl("""\
      <xsd:simpleType name="MyType">
        <xsd:restriction base="xsd:int">
          <xsd:enumeration value="1"/>
          <xsd:enumeration value="3"/>
          <xsd:enumeration value="5"/>
        </xsd:restriction>
      </xsd:simpleType>
      <xsd:element name="Elemento" type="ns:MyType"/>""", input="Elemento"))

    client_twice_restricted = testutils.client_from_wsdl(testutils.wsdl("""\
      <xsd:simpleType name="MyTypeGeneric">
        <xsd:restriction base="xsd:int">
          <xsd:enumeration value="1"/>
          <xsd:enumeration value="2"/>
          <xsd:enumeration value="3"/>
          <xsd:enumeration value="4"/>
          <xsd:enumeration value="5"/>
        </xsd:restriction>
      </xsd:simpleType>
      <xsd:simpleType name="MyType">
        <xsd:restriction base="ns:MyTypeGeneric">
          <xsd:enumeration value="1"/>
          <xsd:enumeration value="3"/>
          <xsd:enumeration value="5"/>
        </xsd:restriction>
      </xsd:simpleType>
      <xsd:element name="Elemento" type="ns:MyType"/>""", input="Elemento"))

    element_qref = ("Elemento", "my-namespace")
    type_named_qref = ("MyType", "my-namespace")

    element_unnamed = client_unnamed.wsdl.schema.elements[element_qref]
    element_named = client_named.wsdl.schema.elements[element_qref]
    element_twice_restricted = client_twice_restricted.wsdl.schema.elements[
        element_qref]

    type_unnamed = element_unnamed.resolve()
    type_named = element_named.resolve()
    type_twice_restricted = element_twice_restricted.resolve()
    assert type_unnamed is element_unnamed
    assert type_named is client_named.wsdl.schema.types[type_named_qref]
    assert type_twice_restricted is client_twice_restricted.wsdl.schema.types[
        type_named_qref]

    # Regression test against suds automatically unwrapping input parameter
    # type's enumeration values as separate parameters.
    params_unnamed = client_unnamed.sd[0].params
    params_named = client_named.sd[0].params
    params_twice_restricted = client_twice_restricted.sd[0].params
    assert len(params_unnamed) == 1
    assert len(params_named) == 1
    assert len(params_twice_restricted) == 1
    assert params_unnamed[0][0] is element_unnamed
    assert params_unnamed[0][1] is type_unnamed
    assert params_named[0][0] is element_named
    assert params_named[0][1] is type_named
    assert params_twice_restricted[0][0] is element_twice_restricted
    assert params_twice_restricted[0][1] is type_twice_restricted


def test_schema_node_occurrences():
    client = testutils.client_from_wsdl(b("""\
<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
    xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
    xmlns:ns="my-namespace"
    xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types>
    <xsd:schema targetNamespace="my-namespace"
        elementFormDefault="qualified"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema">
"""
    + _element_node_xml("AnElement1")
    + _element_node_xml("AnElement2", min=1)
    + _element_node_xml("AnElement3", max=1)

    + _element_node_xml("AnOptionalElement1", min=0)
    + _element_node_xml("AnOptionalElement2", min=0, max=1)

    + _element_node_xml("Array_0_2", min=0, max=2)
    + _element_node_xml("Array_0_999", min=0, max=999)
    + _element_node_xml("Array_0_X", min=0, max="unbounded")

    + _element_node_xml("Array_x_2", max=2)
    + _element_node_xml("Array_x_999", max=999)
    + _element_node_xml("Array_x_X", max="unbounded")

    + _element_node_xml("Array_1_2", min=1, max=2)
    + _element_node_xml("Array_1_999", min=1, max=999)
    + _element_node_xml("Array_1_X", min=1, max="unbounded")

    + _element_node_xml("Array_5_5", min=5, max=5)
    + _element_node_xml("Array_5_999", min=5, max=999)
    + _element_node_xml("Array_5_X", min=5, max="unbounded")
+ """
    </xsd:schema>
  </wsdl:types>
</wsdl:definitions>
"""))
    schema = client.wsdl.schema

    def a(schema, name, min=None, max=None):
        element = schema.elements[name, "my-namespace"]

        if min is None:
            assert element.min is None
            min = 1
        else:
            assert str(min) == element.min
        if max is None:
            assert element.max is None
            max = 1
        else:
            assert str(max) == element.max

        expected_optional = min == 0
        assert expected_optional == element.optional()

        expected_required = not expected_optional
        assert expected_required == element.required()

        expected_multi_occurrence = (max == "unbounded") or (max > 1)
        assert expected_multi_occurrence == element.multi_occurrence()

    a(schema, "AnElement1")
    a(schema, "AnElement2", min=1)
    a(schema, "AnElement3", max=1)

    a(schema, "AnOptionalElement1", min=0)
    a(schema, "AnOptionalElement2", min=0, max=1)

    a(schema, "Array_0_2", min=0, max=2)
    a(schema, "Array_0_999", min=0, max=999)
    a(schema, "Array_0_X", min=0, max="unbounded")

    a(schema, "Array_x_2", max=2)
    a(schema, "Array_x_999", max=999)
    a(schema, "Array_x_X", max="unbounded")

    a(schema, "Array_1_2", min=1, max=2)
    a(schema, "Array_1_999", min=1, max=999)
    a(schema, "Array_1_X", min=1, max="unbounded")

    a(schema, "Array_5_5", min=5, max=5)
    a(schema, "Array_5_999", min=5, max=999)
    a(schema, "Array_5_X", min=5, max="unbounded")


def test_schema_node_resolve():
    client = testutils.client_from_wsdl(b("""\
<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
    xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
    xmlns:ns="my-namespace"
    xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types>
    <xsd:schema targetNamespace="my-namespace"
        elementFormDefault="qualified"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:complexType name="Typo">
        <xsd:sequence>
          <xsd:element name="u1" type="xsd:string"/>
          <xsd:element name="u2" type="xsd:string"/>
          <xsd:element name="u3" type="xsd:string"/>
        </xsd:sequence>
      </xsd:complexType>
      <xsd:element name="Elemento">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="x1" type="xsd:string"/>
            <xsd:element name="x2" type="Typo"/>
            <xsd:element name="x3">
              <xsd:complexType>
                <xsd:sequence>
                  <xsd:element name="a1" type="xsd:string"/>
                  <xsd:element name="a2" type="xsd:string"/>
                </xsd:sequence>
              </xsd:complexType>
            </xsd:element>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>
      <xsd:element name="ElementoTyped" type="Typo"/>
    </xsd:schema>
  </wsdl:types>
</wsdl:definitions>
"""))
    schema = client.wsdl.schema

    # Collect references to the test schema type nodes.
    assert len(schema.types) == 1
    typo = schema.types["Typo", "my-namespace"]
    typo_u1 = typo.children()[0][0]
    assert typo_u1.name == "u1"

    # Collect references to the test schema element nodes.
    assert len(schema.elements) == 2
    elemento = schema.elements["Elemento", "my-namespace"]
    elemento_x2 = elemento.children()[1][0]
    assert elemento_x2.name == "x2"
    elemento_x3 = elemento.children()[2][0]
    assert elemento_x3.name == "x3"
    elemento_typed = schema.elements["ElementoTyped", "my-namespace"]

    # Resolving top-level locally defined non-content nodes.
    assert typo.resolve() is typo

    # Resolving a correctly typed top-level locally typed element.
    assert elemento.resolve() is elemento

    # Resolving top-level globally typed elements.
    assert elemento_typed.resolve() is typo

    # Resolving a subnode referencing a globally defined type.
    assert elemento_x2.resolve() is typo

    # Resolving a locally defined subnode.
    assert elemento_x3.resolve() is elemento_x3

    # Resolving builtin type nodes.
    assert typo_u1.resolve().__class__ is suds.xsd.sxbuiltin.XString
    assert typo_u1.resolve(nobuiltin=False).__class__ is  \
        suds.xsd.sxbuiltin.XString
    assert typo_u1.resolve(nobuiltin=True) is typo_u1
    assert elemento_x2.resolve(nobuiltin=True) is typo
    assert elemento_x3.resolve(nobuiltin=True) is elemento_x3


def test_schema_node_resolve__nobuiltin_caching():
    client = testutils.client_from_wsdl(b("""\
<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
    xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
    xmlns:ns="my-namespace"
    xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types>
    <xsd:schema targetNamespace="my-namespace"
        elementFormDefault="qualified"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:element name="Elemento1" type="xsd:string"/>
      <xsd:element name="Elemento2" type="xsd:string"/>
      <xsd:element name="Elemento3" type="xsd:string"/>
      <xsd:element name="Elemento4" type="xsd:string"/>
    </xsd:schema>
  </wsdl:types>
</wsdl:definitions>
"""))
    schema = client.wsdl.schema

    # Collect references to the test schema element nodes.
    assert len(schema.elements) == 4
    e1 = schema.elements["Elemento1", "my-namespace"]
    e2 = schema.elements["Elemento2", "my-namespace"]
    e3 = schema.elements["Elemento3", "my-namespace"]
    e4 = schema.elements["Elemento4", "my-namespace"]

    # Repeating the same resolve() call twice makes sure that the first call
    # does not cache an incorrect value, thus causing the second call to return
    # an incorrect result.

    assert e1.resolve().__class__ is suds.xsd.sxbuiltin.XString
    assert e1.resolve().__class__ is suds.xsd.sxbuiltin.XString

    assert e2.resolve(nobuiltin=True) is e2
    assert e2.resolve(nobuiltin=True) is e2

    assert e3.resolve().__class__ is suds.xsd.sxbuiltin.XString
    assert e3.resolve(nobuiltin=True) is e3
    assert e3.resolve(nobuiltin=True) is e3

    assert e4.resolve(nobuiltin=True) is e4
    assert e4.resolve().__class__ is suds.xsd.sxbuiltin.XString
    assert e4.resolve().__class__ is suds.xsd.sxbuiltin.XString


def test_schema_node_resolve__invalid_type():
    client = testutils.client_from_wsdl(b("""\
<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
    xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
    xmlns:ns="my-namespace"
    xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types>
    <xsd:schema targetNamespace="my-namespace"
        elementFormDefault="qualified"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:element name="Elemento1" type="Elemento1"/>
      <xsd:element name="Elemento2" type="Elemento1"/>
      <xsd:element name="Elemento3" type="XXX"/>
    </xsd:schema>
  </wsdl:types>
</wsdl:definitions>
"""))
    schema = client.wsdl.schema
    assert len(schema.elements) == 3
    elemento1 = schema.elements["Elemento1", "my-namespace"]
    elemento2 = schema.elements["Elemento2", "my-namespace"]
    elemento3 = schema.elements["Elemento3", "my-namespace"]
    pytest.raises(suds.TypeNotFound, elemento1.resolve)
    pytest.raises(suds.TypeNotFound, elemento2.resolve)
    pytest.raises(suds.TypeNotFound, elemento3.resolve)


def test_schema_node_resolve__references():
    client = testutils.client_from_wsdl(b("""\
<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
    xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
    xmlns:ns="my-namespace"
    xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types>
    <xsd:schema targetNamespace="my-namespace"
        elementFormDefault="qualified"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:complexType name="Typo">
        <xsd:sequence>
          <xsd:element name="u1" type="xsd:string"/>
          <xsd:element name="u2" type="xsd:string"/>
          <xsd:element name="u3" type="xsd:string"/>
        </xsd:sequence>
      </xsd:complexType>
      <xsd:element name="ElementoTyped" type="Typo"/>
      <xsd:element name="ElementoTyped11" ref="ElementoTyped"/>
      <xsd:element name="ElementoTyped12" ref="ElementoTyped11"/>
      <xsd:element name="ElementoTyped13" ref="ElementoTyped12"/>
      <xsd:element name="ElementoTyped21" ref="ElementoTyped"/>
      <xsd:element name="ElementoTyped22" ref="ElementoTyped21"/>
      <xsd:element name="ElementoTyped23" ref="ElementoTyped22"/>
      <xsd:element name="ElementoTypedX" ref="ElementoTypedX"/>
      <xsd:element name="ElementoTypedX1" ref="ElementoTypedX2"/>
      <xsd:element name="ElementoTypedX2" ref="ElementoTypedX1"/>
    </xsd:schema>
  </wsdl:types>
</wsdl:definitions>
"""))
    schema = client.wsdl.schema

    # Collect references to the test schema element & type nodes.
    assert len(schema.types) == 1
    typo = schema.types["Typo", "my-namespace"]
    assert len(schema.elements) == 10
    elemento_typed = schema.elements["ElementoTyped", "my-namespace"]
    elemento_typed11 = schema.elements["ElementoTyped11", "my-namespace"]
    elemento_typed12 = schema.elements["ElementoTyped12", "my-namespace"]
    elemento_typed13 = schema.elements["ElementoTyped13", "my-namespace"]
    elemento_typed21 = schema.elements["ElementoTyped21", "my-namespace"]
    elemento_typed22 = schema.elements["ElementoTyped22", "my-namespace"]
    elemento_typed23 = schema.elements["ElementoTyped23", "my-namespace"]
    elemento_typedX = schema.elements["ElementoTypedX", "my-namespace"]
    elemento_typedX1 = schema.elements["ElementoTypedX1", "my-namespace"]
    elemento_typedX2 = schema.elements["ElementoTypedX2", "my-namespace"]

    # For referenced element node chains try resolving their nodes in both
    # directions and try resolving them twice to try and avoid any internal
    # resolve result caching that might cause some recursive resolution branch
    # to not get taken.
    #
    # Note that these assertions are actually redundant since inter-element
    # references get processed and referenced type information merged back into
    # the referencee when the schema information is loaded so no recursion is
    # needed here in the first place. The tests should still be left in place
    # and pass to serve as a safeguard in case this reference processing gets
    # changed in the future.
    assert elemento_typed11.resolve() is typo
    assert elemento_typed11.resolve() is typo
    assert elemento_typed13.resolve() is typo
    assert elemento_typed13.resolve() is typo

    assert elemento_typed23.resolve() is typo
    assert elemento_typed23.resolve() is typo
    assert elemento_typed21.resolve() is typo
    assert elemento_typed21.resolve() is typo

    # Recursive element references.
    assert elemento_typedX.resolve() is elemento_typedX
    assert elemento_typedX1.resolve() is elemento_typedX1
    assert elemento_typedX2.resolve() is elemento_typedX2


def test_schema_object_child_access_by_index():
    client = testutils.client_from_wsdl(b("""\
<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
    xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
    xmlns:ns="my-namespace"
    xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types>
    <xsd:schema targetNamespace="my-namespace"
        elementFormDefault="qualified"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:complexType name="Oklahoma">
        <xsd:sequence>
          <xsd:element name="c1" type="xsd:string"/>
          <xsd:element name="c2" type="xsd:string"/>
          <xsd:element name="c3" type="xsd:string"/>
        </xsd:sequence>
      </xsd:complexType>
    </xsd:schema>
  </wsdl:types>
  <wsdl:portType name="dummyPortType">
  </wsdl:portType>
  <wsdl:binding name="dummy" type="ns:dummyPortType">
    <soap:binding style="document"
      transport="http://schemas.xmlsoap.org/soap/http"/>
  </wsdl:binding>
  <wsdl:service name="dummy">
    <wsdl:port name="dummy" binding="ns:dummy">
      <soap:address location="https://localhost/dummy"/>
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>
"""))

    service = client.sd[0]
    a_type = service.types[0][0]
    sequence = a_type.rawchildren[0]
    assert isinstance(sequence, suds.xsd.sxbasic.Sequence)
    children = a_type.children()
    assert isinstance(children, list)

    assert sequence[-1] is None

    #TODO: Children are returned as a 2-tuple containing the child element and
    # its ancestry (list of its parent elements). For some reason the ancestry
    # list is returned as a new list on every __getitem__() call and so can not
    # be compared using the 'is' operator. Also the children() function and
    # accessing children by index does not seem to return ancestry lists of the
    # same depth. See whether this can be updated so we always get the same
    # ancestry list object.
    #TODO: Add more detailed tests for the ancestry list structure.
    #TODO: Add more detailed tests for the rawchildren list structure.

    assert isinstance(sequence[0], tuple)
    assert len(sequence[0]) == 2
    assert sequence[0][0] is children[0][0]

    assert isinstance(sequence[1], tuple)
    assert len(sequence[1]) == 2
    assert sequence[1][0] is children[1][0]

    assert isinstance(sequence[2], tuple)
    assert len(sequence[2]) == 2
    assert sequence[2][0] is children[2][0]

    assert sequence[3] is None


def test_simple_wsdl():
    client = testutils.client_from_wsdl(b("""\
<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
    xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
    xmlns:ns="my-namespace"
    xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types>
    <xsd:schema targetNamespace="my-namespace"
        elementFormDefault="qualified"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:element name="f">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="a" type="xsd:string"/>
            <xsd:element name="b" type="xsd:string"/>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>
      <xsd:element name="fResponse">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="c" type="xsd:string"/>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>
    </xsd:schema>
  </wsdl:types>
  <wsdl:message name="fRequestMessage">
    <wsdl:part name="parameters" element="ns:f"/>
  </wsdl:message>
  <wsdl:message name="fResponseMessage">
    <wsdl:part name="parameters" element="ns:fResponse"/>
  </wsdl:message>
  <wsdl:portType name="dummyPortType">
    <wsdl:operation name="f">
      <wsdl:input message="ns:fRequestMessage"/>
      <wsdl:output message="ns:fResponseMessage"/>
    </wsdl:operation>
  </wsdl:portType>
  <wsdl:binding name="dummy" type="ns:dummyPortType">
    <soap:binding style="document"
      transport="http://schemas.xmlsoap.org/soap/http"/>
    <wsdl:operation name="f">
      <soap:operation soapAction="f" style="document"/>
      <wsdl:input><soap:body use="literal"/></wsdl:input>
      <wsdl:output><soap:body use="literal"/></wsdl:output>
    </wsdl:operation>
  </wsdl:binding>
  <wsdl:service name="dummy">
    <wsdl:port name="dummy" binding="ns:dummy">
      <soap:address location="https://localhost/dummy"/>
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>
"""))

    # Target namespace.
    assert client.wsdl.tns[0] == "ns"
    assert client.wsdl.tns[1] == "my-namespace"

    # Elements.
    assert len(client.wsdl.schema.elements) == 2
    element_in = client.wsdl.schema.elements["f", "my-namespace"]
    element_out = client.wsdl.schema.elements["fResponse", "my-namespace"]
    assert isinstance(element_in, suds.xsd.sxbasic.Element)
    assert isinstance(element_out, suds.xsd.sxbasic.Element)
    assert element_in.name == "f"
    assert element_out.name == "fResponse"
    assert len(element_in.children()) == 2
    param_in_1 = element_in.children()[0][0]
    param_in_2 = element_in.children()[1][0]
    assert param_in_1.name == "a"
    assert param_in_1.type == _string_type
    assert param_in_2.name == "b"
    assert param_in_2.type == _string_type
    assert len(element_out.children()) == 1
    param_out_1 = element_out.children()[0][0]
    assert param_out_1.name == "c"
    assert param_out_1.type == _string_type

    # Service definition.
    assert len(client.sd) == 1
    service_definition = client.sd[0]
    assert service_definition.wsdl is client.wsdl

    # Service.
    assert len(client.wsdl.services) == 1
    service = client.wsdl.services[0]
    assert service_definition.service is service

    # Ports.
    assert len(service.ports) == 1
    port = service.ports[0]
    assert len(service_definition.ports) == 1
    assert len(service_definition.ports[0]) == 2
    assert service_definition.ports[0][0] is port

    # Methods (from WSDL).
    assert len(port.methods) == 1
    method = port.methods["f"]
    assert method.name == "f"
    assert method.location == "https://localhost/dummy"

    # Operations (from WSDL).
    assert len(client.wsdl.bindings) == 1
    binding_qname, binding = _first_from_dict(client.wsdl.bindings)
    assert binding_qname == ("dummy", "my-namespace")
    assert binding.__class__ is suds.wsdl.Binding
    assert len(binding.operations) == 1
    operation = next(itervalues(binding.operations))
    input = operation.soap.input.body
    output = operation.soap.output.body
    assert len(input.parts) == 1
    assert len(output.parts) == 1
    input_element_qname = input.parts[0].element
    output_element_qname = output.parts[0].element
    assert input_element_qname == element_in.qname
    assert output_element_qname == element_out.qname

    # Methods (from service definition, for format specifications see the
    # suds.serviceDefinition.ServiceDefinition.addports() docstring).
    port, methods = service_definition.ports[0]
    assert len(methods) == 1
    method_name, method_params = methods[0]
    assert method_name == "f"

    param_name, param_element, param_ancestry = method_params[0]
    assert param_name == "a"
    assert param_element is param_in_1
    assert len(param_ancestry) == 3
    assert type(param_ancestry[0]) is suds.xsd.sxbasic.Element
    assert param_ancestry[0].name == "f"
    assert type(param_ancestry[1]) is suds.xsd.sxbasic.Complex
    assert type(param_ancestry[2]) is suds.xsd.sxbasic.Sequence

    param_name, param_element, param_ancestry = method_params[1]
    assert param_name == "b"
    assert param_element is param_in_2
    assert len(param_ancestry) == 3
    assert type(param_ancestry[0]) is suds.xsd.sxbasic.Element
    assert param_ancestry[0].name == "f"
    assert type(param_ancestry[1]) is suds.xsd.sxbasic.Complex
    assert type(param_ancestry[2]) is suds.xsd.sxbasic.Sequence


def test_wsdl_schema_content():
    client = testutils.client_from_wsdl(b("""\
<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
    xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
    xmlns:ns="my-namespace"
    xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types>
    <xsd:schema targetNamespace="my-namespace"
        elementFormDefault="qualified"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:complexType name="UngaBunga">
        <xsd:sequence>
          <xsd:element name="u1" type="xsd:string"/>
          <xsd:element name="u2" type="xsd:string"/>
          <xsd:element name="u3" type="xsd:string"/>
        </xsd:sequence>
      </xsd:complexType>
      <xsd:complexType name="Fifi">
        <xsd:sequence>
          <xsd:element name="x" type="xsd:string"/>
        </xsd:sequence>
      </xsd:complexType>
      <xsd:element name="Elemento">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="x1" type="xsd:string"/>
            <xsd:element name="x2" type="UngaBunga"/>
            <xsd:element name="x3">
              <xsd:complexType>
                <xsd:sequence>
                  <xsd:element name="a1" type="xsd:string"/>
                  <xsd:element name="a2" type="xsd:string"/>
                </xsd:sequence>
              </xsd:complexType>
            </xsd:element>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>
    </xsd:schema>
  </wsdl:types>
</wsdl:definitions>
"""))

    # Elements.
    assert len(client.wsdl.schema.elements) == 1
    elemento = client.wsdl.schema.elements["Elemento", "my-namespace"]
    assert isinstance(elemento, suds.xsd.sxbasic.Element)

    pytest.raises(KeyError, client.wsdl.schema.elements.__getitem__,
        ("DoesNotExist", "OMG"))

    # Types.
    assert len(client.wsdl.schema.types) == 2
    unga_bunga = client.wsdl.schema.types["UngaBunga", "my-namespace"]
    assert isinstance(unga_bunga, suds.xsd.sxbasic.Complex)
    fifi = client.wsdl.schema.types["Fifi", "my-namespace"]
    assert isinstance(unga_bunga, suds.xsd.sxbasic.Complex)

    pytest.raises(KeyError, client.wsdl.schema.types.__getitem__,
        ("DoesNotExist", "OMG"))


def _assert_dynamic_type(anObject, typename):
    assert anObject.__module__ == suds.sudsobject.__name__
    assert anObject.__metadata__.sxtype.name == typename
    # In order to be compatible with old style classes (py2 only) we need to
    # access the object's class information using its __class__ member and not
    # the type() function. type() function always returns <type 'instance'> for
    # old-style class instances while the __class__ member returns the correct
    # class information for both old and new-style classes.
    assert anObject.__class__.__module__ == suds.sudsobject.__name__
    assert anObject.__class__.__name__ == typename


def _construct_SOAP_request(client, operation_name, *args, **kwargs):
    """
    Construct a SOAP request for a given web service operation invocation.

    To make the test case code calling this function simpler, assumes we want
    to call the operation on the given client's first service & port.

    """
    method = client.wsdl.services[0].ports[0].methods[operation_name]
    return method.binding.input.get_message(method, args, kwargs)


def _element_node_xml(name, min=None, max=None):
    s = []
    s.append('      <xsd:element name="')
    s.append(name)
    s.append('" type="xsd:string" ')
    if min is not None:
        s.append('minOccurs="%s" ' % (min,))
    if max is not None:
        s.append('maxOccurs="%s" ' % (max,))
    s.append("/>\n")
    return "".join(s)


def _first_from_dict(d):
    """Returns the first name/value pair from a dictionary or None if empty."""
    for x in d.items():
        return x[0], x[1]


_string_type = ("string", "http://www.w3.org/2001/XMLSchema")
