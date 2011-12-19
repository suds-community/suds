# -*- coding: cp1250 -*-

# This program is free software; you can redistribute it and/or modify
# it under the terms of the (LGPL) GNU Lesser General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library Lesser General Public License for more details at
# ( http://www.gnu.org/licenses/lgpl.html ).
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
# written by: Jurko Gospodnetić ( jurko.gospodnetic@pke.hr )

"""
General pytest based automated suds Python library unit tests.

This whole module should be refactored into more specialized modules as more
tests get added to it and it acquires more structure.

"""

# TODO: Test accessing a list of types using client.wsdl.schema.types even when
# there is no wsdl:service/binding/portType tag specified in the WSDL schema.

if __name__ == "__main__":
    try:
        import pytest
        pytest.main(["--pyargs", __file__])
    except ImportError:
        print("'py.test' unit testing framework not available. Can not run "
            "'{}' directly as a script.".format(__file__))
    import sys
    sys.exit(-2)


import os
import pytest
import suds.client
import suds.store
import xml.sax


def test_empty_invalid_wsdl():
    try:
        client = _client_from_wsdl("")
        pytest.fail("Excepted exception xml.sax.SAXParseException not thrown.")
    except xml.sax.SAXParseException, e:
        assert e.getMessage() == "no element found"


def test_empty_valid_wsdl():
    client = _client_from_wsdl(
        "<?xml version='1.0' encoding='UTF-8'?><root />")
    assert not client.wsdl.services, "No service definitions must be read "  \
        "from an empty WSDL."


def test_function_parameters_global_sequence_in_a_sequence():
    client = _client_from_wsdl(
"""<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
xmlns:ns="my-namespace"
xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types>
    <xsd:schema targetNamespace="my-namespace"
    elementFormDefault="qualified"
    attributeFormDefault="unqualified"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:complexType name="UngaBunga">
        <xsd:sequence>
          <xsd:element name="u1" type="xsd:string" />
          <xsd:element name="u2" type="xsd:string" />
          <xsd:element name="u3" type="xsd:string" />
        </xsd:sequence>
      </xsd:complexType>
      <xsd:element name="Elemento">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="x1" type="xsd:string" />
            <xsd:element name="x2" type="UngaBunga" />
            <xsd:element name="x3" type="xsd:string" />
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>
    </xsd:schema>
  </wsdl:types>
  <wsdl:message name="fRequestMessage">
    <wsdl:part name="parameters" element="ns:Elemento" />
  </wsdl:message>
  <wsdl:portType name="dummyPortType">
    <wsdl:operation name="f">
      <wsdl:input message="ns:fRequestMessage" />
    </wsdl:operation>
  </wsdl:portType>
  <wsdl:binding name="dummy" type="ns:dummyPortType">
    <soap:binding style="document"
    transport="http://schemas.xmlsoap.org/soap/http" />
    <wsdl:operation name="f">
      <soap:operation soapAction="f" style="document" />
      <wsdl:input><soap:body use="literal" /></wsdl:input>
      <wsdl:output><soap:body use="literal" /></wsdl:output>
    </wsdl:operation>
  </wsdl:binding>
  <wsdl:service name="dummy">
    <wsdl:port name="dummy" binding="ns:dummy">
      <soap:address location="https://localhost/dummy" />
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>
""")

    service = client.sd[0]
    assert len(service.types) == 1

    # Method parameters as read from the service definition.
    assert len(service.params) == 3
    assert service.params[0][0].name == "x1"
    assert service.params[0][0].type[0] == "string"
    assert service.params[0][0].type[1] == "http://www.w3.org/2001/XMLSchema"
    assert isinstance(service.params[0][1], suds.xsd.sxbuiltin.XString)
    assert service.params[1][0].name == "x2"
    assert service.params[1][0].type[0] == "UngaBunga"
    assert service.params[1][0].type[1] == "my-namespace"
    assert isinstance(service.params[1][1], suds.xsd.sxbasic.Complex)
    assert service.params[2][0].name == "x3"
    assert service.params[2][0].type[0] == "string"
    assert service.params[2][0].type[1] == "http://www.w3.org/2001/XMLSchema"
    assert isinstance(service.params[2][1], suds.xsd.sxbuiltin.XString)

    # Method parameters as read from a method object.
    assert len(service.ports) == 1
    port, methods = service.ports[0]
    assert len(methods) == 1
    method = methods[0]
    assert len(method) == 2
    method_name = method[0]
    assert method_name == "f"
    method_params = method[1]
    assert len(method_params) == 3
    assert method_params[0][0] == "x1"
    assert method_params[0][1] is service.params[0][0]
    assert method_params[1][0] == "x2"
    assert method_params[1][1] is service.params[1][0]
    assert method_params[2][0] == "x3"
    assert method_params[2][1] is service.params[2][0]


def test_function_parameters_local_choice():
    client = _client_from_wsdl(
"""<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
xmlns:ns="my-namespace"
xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types>
    <xsd:schema targetNamespace="my-namespace"
    elementFormDefault="qualified"
    attributeFormDefault="unqualified"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:element name="Elemento">
        <xsd:complexType>
          <xsd:choice>
            <xsd:element name="u1" type="xsd:string" />
            <xsd:element name="u2" type="xsd:string" />
          </xsd:choice>
        </xsd:complexType>
      </xsd:element>
    </xsd:schema>
  </wsdl:types>
  <wsdl:message name="fRequestMessage">
    <wsdl:part name="parameters" element="ns:Elemento" />
  </wsdl:message>
  <wsdl:portType name="dummyPortType">
    <wsdl:operation name="f">
      <wsdl:input message="ns:fRequestMessage" />
    </wsdl:operation>
  </wsdl:portType>
  <wsdl:binding name="dummy" type="ns:dummyPortType">
    <soap:binding style="document"
    transport="http://schemas.xmlsoap.org/soap/http" />
    <wsdl:operation name="f">
      <soap:operation soapAction="f" style="document" />
      <wsdl:input><soap:body use="literal" /></wsdl:input>
      <wsdl:output><soap:body use="literal" /></wsdl:output>
    </wsdl:operation>
  </wsdl:binding>
  <wsdl:service name="dummy">
    <wsdl:port name="dummy" binding="ns:dummy">
      <soap:address location="https://localhost/dummy" />
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>
""")

    service = client.sd[0]
    assert not service.types

    # Method parameters as read from the service definition.
    assert len(service.params) == 2
    assert service.params[0][0].name == "u1"
    assert service.params[0][0].type[0] == "string"
    assert service.params[0][0].type[1] == "http://www.w3.org/2001/XMLSchema"
    assert isinstance(service.params[0][1], suds.xsd.sxbuiltin.XString)
    assert service.params[1][0].name == "u2"
    assert service.params[1][0].type[0] == "string"
    assert service.params[1][0].type[1] == "http://www.w3.org/2001/XMLSchema"
    assert isinstance(service.params[1][1], suds.xsd.sxbuiltin.XString)

    # Method parameters as read from a method object.
    assert len(service.ports) == 1
    port, methods = service.ports[0]
    assert len(methods) == 1
    assert len(methods[0]) == 2
    method_name, method_params = methods[0]
    assert method_name == "f"
    assert len(method_params) == 2
    assert method_params[0][0] == "u1"
    assert method_params[0][1] is service.params[0][0]
    assert method_params[1][0] == "u2"
    assert method_params[1][1] is service.params[1][0]

    # Construct method parameter element object.
    paramOut = client.factory.create("Elemento")
    __assert_dynamic_type(paramOut, "Elemento")
    assert not paramOut.__keylist__


def test_function_parameters_local_choice_in_a_sequence():
    client = _client_from_wsdl(
"""<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
xmlns:ns="my-namespace"
xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types>
    <xsd:schema targetNamespace="my-namespace"
    elementFormDefault="qualified"
    attributeFormDefault="unqualified"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:element name="Elemento">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="x1" type="xsd:string" />
            <xsd:element name="x2">
              <xsd:complexType>
                <xsd:choice>
                  <xsd:element name="u1" type="xsd:string" />
                  <xsd:element name="u2" type="xsd:string" />
                  <xsd:element name="u3" type="xsd:string" />
                </xsd:choice>
              </xsd:complexType>
            </xsd:element>
            <xsd:element name="x3" type="xsd:string" />
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>
    </xsd:schema>
  </wsdl:types>
  <wsdl:message name="fRequestMessage">
    <wsdl:part name="parameters" element="ns:Elemento" />
  </wsdl:message>
  <wsdl:portType name="dummyPortType">
    <wsdl:operation name="f">
      <wsdl:input message="ns:fRequestMessage" />
    </wsdl:operation>
  </wsdl:portType>
  <wsdl:binding name="dummy" type="ns:dummyPortType">
    <soap:binding style="document"
    transport="http://schemas.xmlsoap.org/soap/http" />
    <wsdl:operation name="f">
      <soap:operation soapAction="f" style="document" />
      <wsdl:input><soap:body use="literal" /></wsdl:input>
      <wsdl:output><soap:body use="literal" /></wsdl:output>
    </wsdl:operation>
  </wsdl:binding>
  <wsdl:service name="dummy">
    <wsdl:port name="dummy" binding="ns:dummy">
      <soap:address location="https://localhost/dummy" />
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>
""")

    service = client.sd[0]
    assert not service.types

    # Method parameters as read from the service definition.
    assert len(service.params) == 3
    assert service.params[0][0].name == "x1"
    assert service.params[0][0].type[0] == "string"
    assert service.params[0][0].type[1] == "http://www.w3.org/2001/XMLSchema"
    assert isinstance(service.params[0][1], suds.xsd.sxbuiltin.XString)
    assert service.params[1][0].name == "x2"
    assert service.params[1][0].type is None
    assert isinstance(service.params[1][1], suds.xsd.sxbasic.Element)
    assert service.params[2][0].name == "x3"
    assert service.params[2][0].type[0] == "string"
    assert service.params[2][0].type[1] == "http://www.w3.org/2001/XMLSchema"
    assert isinstance(service.params[2][1], suds.xsd.sxbuiltin.XString)

    # Method parameters as read from a method object.
    assert len(service.ports) == 1
    port, methods = service.ports[0]
    assert len(methods) == 1
    method = methods[0]
    assert len(method) == 2
    method_name = method[0]
    assert method_name == "f"
    method_params = method[1]
    assert len(method_params) == 3
    assert method_params[0][0] == "x1"
    assert method_params[0][1] is service.params[0][0]
    assert method_params[1][0] == "x2"
    assert method_params[1][1] is service.params[1][0]
    assert method_params[2][0] == "x3"
    assert method_params[2][1] is service.params[2][0]

    # Construct method parameter element object.
    paramOut = client.factory.create("Elemento")
    __assert_dynamic_type(paramOut, "Elemento")
    assert paramOut.x1 is None
    __assert_dynamic_type(paramOut.x2, "x2")
    assert not paramOut.x2.__keylist__
    assert paramOut.x3 is None

    # Construct method parameter objects with a locally defined type.
    paramIn = client.factory.create("Elemento.x2")
    __assert_dynamic_type(paramIn, "x2")
    assert not paramOut.x2.__keylist__
    assert paramIn is not paramOut.x2


def test_function_parameters_local_sequence_in_a_sequence():
    client = _client_from_wsdl(
"""<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
xmlns:ns="my-namespace"
xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types>
    <xsd:schema targetNamespace="my-namespace"
    elementFormDefault="qualified"
    attributeFormDefault="unqualified"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:element name="Elemento">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="x1" type="xsd:string" />
            <xsd:element name="x2">
              <xsd:complexType>
                <xsd:sequence>
                  <xsd:element name="u1" type="xsd:string" />
                  <xsd:element name="u2" type="xsd:string" />
                  <xsd:element name="u3" type="xsd:string" />
                </xsd:sequence>
              </xsd:complexType>
            </xsd:element>
            <xsd:element name="x3" type="xsd:string" />
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>
    </xsd:schema>
  </wsdl:types>
  <wsdl:message name="fRequestMessage">
    <wsdl:part name="parameters" element="ns:Elemento" />
  </wsdl:message>
  <wsdl:portType name="dummyPortType">
    <wsdl:operation name="f">
      <wsdl:input message="ns:fRequestMessage" />
    </wsdl:operation>
  </wsdl:portType>
  <wsdl:binding name="dummy" type="ns:dummyPortType">
    <soap:binding style="document"
    transport="http://schemas.xmlsoap.org/soap/http" />
    <wsdl:operation name="f">
      <soap:operation soapAction="f" style="document" />
      <wsdl:input><soap:body use="literal" /></wsdl:input>
      <wsdl:output><soap:body use="literal" /></wsdl:output>
    </wsdl:operation>
  </wsdl:binding>
  <wsdl:service name="dummy">
    <wsdl:port name="dummy" binding="ns:dummy">
      <soap:address location="https://localhost/dummy" />
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>
""")

    service = client.sd[0]
    assert not service.types

    # Method parameters as read from the service definition.
    assert len(service.params) == 3
    assert service.params[0][0].name == "x1"
    assert service.params[0][0].type[0] == "string"
    assert service.params[0][0].type[1] == "http://www.w3.org/2001/XMLSchema"
    assert isinstance(service.params[0][1], suds.xsd.sxbuiltin.XString)
    assert service.params[1][0].name == "x2"
    assert service.params[1][0].type is None
    assert isinstance(service.params[1][1], suds.xsd.sxbasic.Element)
    assert service.params[2][0].name == "x3"
    assert service.params[2][0].type[0] == "string"
    assert service.params[2][0].type[1] == "http://www.w3.org/2001/XMLSchema"
    assert isinstance(service.params[2][1], suds.xsd.sxbuiltin.XString)

    # Method parameters as read from a method object.
    assert len(service.ports) == 1
    port, methods = service.ports[0]
    assert len(methods) == 1
    method = methods[0]
    assert len(method) == 2
    method_name = method[0]
    assert method_name == "f"
    method_params = method[1]
    assert len(method_params) == 3
    assert method_params[0][0] == "x1"
    assert method_params[0][1] is service.params[0][0]
    assert method_params[1][0] == "x2"
    assert method_params[1][1] is service.params[1][0]
    assert method_params[2][0] == "x3"
    assert method_params[2][1] is service.params[2][0]

    # Construct method parameter element object.
    paramOut = client.factory.create("Elemento")
    __assert_dynamic_type(paramOut, "Elemento")
    assert paramOut.x1 is None
    __assert_dynamic_type(paramOut.x2, "x2")
    assert paramOut.x2.u1 is None
    assert paramOut.x2.u2 is None
    assert paramOut.x2.u3 is None
    assert paramOut.x3 is None

    # Construct method parameter objects with a locally defined type.
    paramIn = client.factory.create("Elemento.x2")
    __assert_dynamic_type(paramIn, "x2")
    assert paramIn.u1 is None
    assert paramIn.u2 is None
    assert paramIn.u3 is None
    assert paramIn is not paramOut.x2


def test_function_parameters_strings():
    client = _client_from_wsdl(
"""<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
xmlns:ns="my-namespace"
xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types>
    <xsd:schema targetNamespace="my-namespace"
    elementFormDefault="qualified"
    attributeFormDefault="unqualified"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:element name="Elemento">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="x1" type="xsd:string" />
            <xsd:element name="x2" type="xsd:string" />
            <xsd:element name="x3" type="xsd:string" />
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>
    </xsd:schema>
  </wsdl:types>
  <wsdl:message name="fRequestMessage">
    <wsdl:part name="parameters" element="ns:Elemento" />
  </wsdl:message>
  <wsdl:portType name="dummyPortType">
    <wsdl:operation name="f">
      <wsdl:input message="ns:fRequestMessage" />
    </wsdl:operation>
  </wsdl:portType>
  <wsdl:binding name="dummy" type="ns:dummyPortType">
    <soap:binding style="document"
    transport="http://schemas.xmlsoap.org/soap/http" />
    <wsdl:operation name="f">
      <soap:operation soapAction="f" style="document" />
      <wsdl:input><soap:body use="literal" /></wsdl:input>
      <wsdl:output><soap:body use="literal" /></wsdl:output>
    </wsdl:operation>
  </wsdl:binding>
  <wsdl:service name="dummy">
    <wsdl:port name="dummy" binding="ns:dummy">
      <soap:address location="https://localhost/dummy" />
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>
""")

    service = client.sd[0]
    assert not service.types

    # Method parameters as read from the service definition.
    assert len(service.params) == 3
    assert service.params[0][0].name == "x1"
    assert service.params[0][0].type[0] == "string"
    assert service.params[0][0].type[1] == "http://www.w3.org/2001/XMLSchema"
    assert isinstance(service.params[0][1], suds.xsd.sxbuiltin.XString)
    assert service.params[1][0].name == "x2"
    assert service.params[1][0].type[0] == "string"
    assert service.params[1][0].type[1] == "http://www.w3.org/2001/XMLSchema"
    assert isinstance(service.params[1][1], suds.xsd.sxbuiltin.XString)
    assert service.params[2][0].name == "x3"
    assert service.params[2][0].type[0] == "string"
    assert service.params[2][0].type[1] == "http://www.w3.org/2001/XMLSchema"
    assert isinstance(service.params[2][1], suds.xsd.sxbuiltin.XString)

    # Method parameters as read from a method object.
    assert len(service.ports) == 1
    port, methods = service.ports[0]
    assert len(methods) == 1
    method = methods[0]
    assert len(method) == 2
    method_name = method[0]
    assert method_name == "f"
    method_params = method[1]
    assert len(method_params) == 3
    assert method_params[0][0] == "x1"
    assert method_params[0][1] is service.params[0][0]
    assert method_params[1][0] == "x2"
    assert method_params[1][1] is service.params[1][0]
    assert method_params[2][0] == "x3"
    assert method_params[2][1] is service.params[2][0]


def test_global_enumeration():
    client = _client_from_wsdl(
"""<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
xmlns:ns="my-namespace"
xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types>
    <xsd:schema targetNamespace="my-namespace"
    elementFormDefault="qualified"
    attributeFormDefault="unqualified"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:simpleType name="AAA">
        <xsd:restriction base="xsd:string">
          <xsd:enumeration value="One" />
          <xsd:enumeration value="Two" />
          <xsd:enumeration value="Thirty-Two" />
        </xsd:restriction>
      </xsd:simpleType>
    </xsd:schema>
  </wsdl:types>
  <wsdl:portType name="dummyPortType">
  </wsdl:portType>
  <wsdl:binding name="dummy" type="ns:dummyPortType">
    <soap:binding style="document"
    transport="http://schemas.xmlsoap.org/soap/http" />
  </wsdl:binding>
  <wsdl:service name="dummy">
    <wsdl:port name="dummy" binding="ns:dummy">
      <soap:address location="https://localhost/dummy" />
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>
""")

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
    assert aType.rawchildren[0].ref[0] == "string"
    assert aType.rawchildren[0].ref[1] == "http://www.w3.org/2001/XMLSchema"

    enum = client.factory.create("AAA")
    assert enum.One == "One"
    assert enum.Two == "Two"
    assert getattr(enum, "Thirty-Two") == "Thirty-Two"


def test_global_sequence_in_a_global_sequence():
    client = _client_from_wsdl(
"""<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
xmlns:ns="my-namespace"
xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types>
    <xsd:schema targetNamespace="my-namespace"
    elementFormDefault="qualified"
    attributeFormDefault="unqualified"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:complexType name="Oklahoma">
        <xsd:sequence>
          <xsd:element name="c1" type="xsd:string" />
          <xsd:element name="c2" type="xsd:string" />
          <xsd:element name="c3" type="xsd:string" />
        </xsd:sequence>
      </xsd:complexType>
      <xsd:complexType name="Wackadoodle">
        <xsd:sequence>
          <xsd:element name="x1" type="xsd:string" />
          <xsd:element name="x2" type="Oklahoma" />
          <xsd:element name="x3" type="xsd:string" />
        </xsd:sequence>
      </xsd:complexType>
    </xsd:schema>
  </wsdl:types>
  <wsdl:portType name="dummyPortType">
  </wsdl:portType>
  <wsdl:binding name="dummy" type="ns:dummyPortType">
    <soap:binding style="document"
    transport="http://schemas.xmlsoap.org/soap/http" />
  </wsdl:binding>
  <wsdl:service name="dummy">
    <wsdl:port name="dummy" binding="ns:dummy">
      <soap:address location="https://localhost/dummy" />
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>
""")

    service = client.sd[0]

    assert len(service.types) == 2
    for typeTuple in service.types:
        # Tuple containing the same object twice.
        assert len(typeTuple) == 2
        assert typeTuple[0] is typeTuple[1]

    aTypeIn = service.types[0][0]
    assert isinstance(aTypeIn, suds.xsd.sxbasic.Complex)
    assert aTypeIn.name == "Oklahoma"
    assert not aTypeIn.sequence()
    assert aTypeIn.rawchildren[0].sequence()

    aTypeOut = service.types[1][0]
    assert isinstance(aTypeOut, suds.xsd.sxbasic.Complex)
    assert aTypeOut.name == "Wackadoodle"
    assert not aTypeOut.sequence()
    assert aTypeOut.rawchildren[0].sequence()

    assert len(aTypeOut.rawchildren) == 1
    children = aTypeOut.children()
    assert isinstance(children, list)
    assert len(children) == 3
    assert children[0][0].name == "x1"
    assert children[0][0].type[0] == "string"
    assert children[0][0].type[1] == "http://www.w3.org/2001/XMLSchema"
    assert children[1][0].name == "x2"
    assert children[1][0].type[0] == "Oklahoma"
    assert children[1][0].type[1] == "my-namespace"
    assert children[2][0].name == "x3"
    assert children[2][0].type[0] == "string"
    assert children[2][0].type[1] == "http://www.w3.org/2001/XMLSchema"

    sequenceOut = client.factory.create("Wackadoodle")
    __assert_dynamic_type(sequenceOut, "Wackadoodle")
    assert sequenceOut.__metadata__.sxtype is aTypeOut
    assert sequenceOut.x1 is None
    sequenceIn = sequenceOut.x2
    assert sequenceOut.x3 is None
    __assert_dynamic_type(sequenceIn, "Oklahoma")
    assert sequenceIn.__metadata__.sxtype is aTypeIn
    assert sequenceIn.c1 is None
    assert sequenceIn.c2 is None
    assert sequenceIn.c3 is None


def test_global_string_sequence():
    client = _client_from_wsdl(
"""<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
xmlns:ns="my-namespace"
xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types>
    <xsd:schema targetNamespace="my-namespace"
    elementFormDefault="qualified"
    attributeFormDefault="unqualified"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:complexType name="Oklahoma">
        <xsd:sequence>
          <xsd:element name="c1" type="xsd:string" />
          <xsd:element name="c2" type="xsd:string" />
          <xsd:element name="c3" type="xsd:string" />
        </xsd:sequence>
      </xsd:complexType>
    </xsd:schema>
  </wsdl:types>
  <wsdl:portType name="dummyPortType">
  </wsdl:portType>
  <wsdl:binding name="dummy" type="ns:dummyPortType">
    <soap:binding style="document"
    transport="http://schemas.xmlsoap.org/soap/http" />
  </wsdl:binding>
  <wsdl:service name="dummy">
    <wsdl:port name="dummy" binding="ns:dummy">
      <soap:address location="https://localhost/dummy" />
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>
""")

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
    assert sequence_items[0][0].type[0] == "string"
    assert sequence_items[0][0].type[1] == "http://www.w3.org/2001/XMLSchema"
    assert sequence_items[1][0].name == "c2"
    assert sequence_items[1][0].type[0] == "string"
    assert sequence_items[1][0].type[1] == "http://www.w3.org/2001/XMLSchema"
    assert sequence_items[2][0].name == "c3"
    assert sequence_items[2][0].type[0] == "string"
    assert sequence_items[2][0].type[1] == "http://www.w3.org/2001/XMLSchema"

    sequence = client.factory.create("Oklahoma")
    getattr(sequence, "c1")
    getattr(sequence, "c2")
    getattr(sequence, "c3")
    with pytest.raises(AttributeError):
        getattr(sequence, "nonExistingChild")
    assert sequence.c1 is None
    assert sequence.c2 is None
    assert sequence.c3 is None
    sequence.c1 = "Pero"
    sequence.c3 = "Ždero"
    assert sequence.c1 == "Pero"
    assert sequence.c2 is None
    assert sequence.c3 == "Ždero"


def test_local_sequence_in_a_global_sequence():
    client = _client_from_wsdl(
"""<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
xmlns:ns="my-namespace"
xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types>
    <xsd:schema targetNamespace="my-namespace"
    elementFormDefault="qualified"
    attributeFormDefault="unqualified"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:complexType name="Wackadoodle">
        <xsd:sequence>
          <xsd:element name="x1">
              <xsd:complexType name="Oklahoma">
                <xsd:sequence>
                  <xsd:element name="c1" type="xsd:string" />
                  <xsd:element name="c2" type="xsd:string" />
                  <xsd:element name="c3" type="xsd:string" />
                </xsd:sequence>
              </xsd:complexType>
          </xsd:element>
          <xsd:element name="x2">
              <xsd:complexType>
                <xsd:sequence>
                  <xsd:element name="s" type="xsd:string" />
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
    transport="http://schemas.xmlsoap.org/soap/http" />
  </wsdl:binding>
  <wsdl:service name="dummy">
    <wsdl:port name="dummy" binding="ns:dummy">
      <soap:address location="https://localhost/dummy" />
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>
""")

    service = client.sd[0]
    assert len(service.types) == 1

    aTypeOut = service.types[0][0]
    assert isinstance(aTypeOut, suds.xsd.sxbasic.Complex)
    assert aTypeOut.name == "Wackadoodle"
    assert not aTypeOut.sequence()
    assert aTypeOut.rawchildren[0].sequence()

    children = aTypeOut.children()
    assert isinstance(children, list)
    assert len(children) == 2
    aTypeIn1 = children[0][0]
    assert isinstance(aTypeIn1, suds.xsd.sxbasic.Element)
    assert not aTypeIn1.sequence()
    assert aTypeIn1.rawchildren[0].rawchildren[0].sequence()
    aTypeIn2 = children[1][0]
    assert isinstance(aTypeIn2, suds.xsd.sxbasic.Element)
    assert not aTypeIn2.sequence()
    assert aTypeIn2.rawchildren[0].rawchildren[0].sequence()
    assert aTypeIn1.rawchildren[0].name == "Oklahoma"
    assert aTypeIn1.rawchildren[0].type is None
    namespace1 = aTypeIn1.rawchildren[0].namespace()
    assert namespace1 == ("ns", "my-namespace")
    assert aTypeIn2.rawchildren[0].name is None
    assert aTypeIn2.rawchildren[0].type is None
    assert aTypeIn1.rawchildren[0].namespace() is namespace1

    sequenceOut = client.factory.create("Wackadoodle")
    __assert_dynamic_type(sequenceOut, "Wackadoodle")
    assert sequenceOut.__metadata__.sxtype is aTypeOut
    sequenceIn1 = sequenceOut.x1
    sequenceIn2 = sequenceOut.x2
    __assert_dynamic_type(sequenceIn1, "x1")
    __assert_dynamic_type(sequenceIn2, "x2")
    assert sequenceIn1.__metadata__.sxtype is aTypeIn1
    assert sequenceIn2.__metadata__.sxtype is aTypeIn2
    assert sequenceIn1.c1 is None
    assert sequenceIn1.c2 is None
    assert sequenceIn1.c3 is None
    assert sequenceIn2.s is None


def test_no_types():
    client = _client_from_wsdl(
"""<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
xmlns:ns="my-namespace"
xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types>
    <xsd:schema targetNamespace="my-namespace"
    elementFormDefault="qualified"
    attributeFormDefault="unqualified"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema" />
  </wsdl:types>
  <wsdl:portType name="dummyPortType">
  </wsdl:portType>
  <wsdl:binding name="dummy" type="ns:dummyPortType">
    <soap:binding style="document"
    transport="http://schemas.xmlsoap.org/soap/http" />
  </wsdl:binding>
  <wsdl:service name="dummy">
    <wsdl:port name="dummy" binding="ns:dummy">
      <soap:address location="https://localhost/dummy" />
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>
""")

    assert len(client.sd) == 1
    service = client.sd[0]

    assert not client.wsdl.schema.types
    assert not service.types

    with pytest.raises(suds.TypeNotFound):
        client.factory.create("NonExistingType")


def test_parameter_referencing_missing_element():
    try:
        client = _client_from_wsdl(
"""<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
xmlns:ns="my-namespace"
xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types>
    <xsd:schema targetNamespace="my-namespace"
    elementFormDefault="qualified"
    attributeFormDefault="unqualified"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema">
    </xsd:schema>
  </wsdl:types>
  <wsdl:message name="fRequestMessage">
    <wsdl:part name="parameters" element="ns:missingElement" />
  </wsdl:message>
  <wsdl:portType name="dummyPortType">
    <wsdl:operation name="f">
      <wsdl:input message="ns:fRequestMessage" />
    </wsdl:operation>
  </wsdl:portType>
  <wsdl:binding name="dummy" type="ns:dummyPortType">
    <soap:binding style="document"
    transport="http://schemas.xmlsoap.org/soap/http" />
    <wsdl:operation name="f">
      <soap:operation soapAction="f" style="document" />
      <wsdl:input><soap:body use="literal" /></wsdl:input>
      <wsdl:output><soap:body use="literal" /></wsdl:output>
    </wsdl:operation>
  </wsdl:binding>
  <wsdl:service name="dummy">
    <wsdl:port name="dummy" binding="ns:dummy">
      <soap:address location="https://localhost/dummy" />
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>
""")
        pytest.fail("Excepted exception suds.TypeNotFound not thrown.")
    except suds.TypeNotFound, e:
        assert str(e) == "Type not found: '(missingElement, my-namespace, )'"


def test_resolving_schema_node_types():
    client = _client_from_wsdl(
"""<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
xmlns:ns="my-namespace"
xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types>
    <xsd:schema targetNamespace="my-namespace"
    elementFormDefault="qualified"
    attributeFormDefault="unqualified"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:complexType name="UngaBunga">
        <xsd:sequence>
          <xsd:element name="u1" type="xsd:string" />
          <xsd:element name="u2" type="xsd:string" />
          <xsd:element name="u3" type="xsd:string" />
        </xsd:sequence>
      </xsd:complexType>
      <xsd:element name="Elemento">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="x1" type="xsd:string" />
            <xsd:element name="x2" type="UngaBunga" />
            <xsd:element name="x3">
              <xsd:complexType>
                <xsd:sequence>
                  <xsd:element name="a1" type="xsd:string" />
                  <xsd:element name="a2" type="xsd:string" />
                </xsd:sequence>
              </xsd:complexType>
            </xsd:element>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>
      <xsd:element name="ElementoTyped" type="UngaBunga" />
    </xsd:schema>
  </wsdl:types>
</wsdl:definitions>
""")
    schema = client.wsdl.schema

    # Collect references to the test schema element & type nodes.
    assert len(schema.elements) == 2
    elemento = schema.elements["Elemento", "my-namespace"]
    elemento_x2 = elemento.children()[1][0]
    assert elemento_x2.name == "x2"
    elemento_x3 = elemento.children()[2][0]
    assert elemento_x3.name == "x3"
    elementoTyped = schema.elements["ElementoTyped", "my-namespace"]
    assert len(schema.types) == 1
    typo = schema.types["UngaBunga", "my-namespace"]
    typo_u1 = typo.children()[0][0]
    assert typo_u1.name == "u1"

    # Resolving top-level locally defined elements.
    assert elemento.resolve() is elemento
    assert elementoTyped.resolve() is typo
    assert typo.resolve() is typo

    # Resolving a subnode referencing a globally defined type.
    assert elemento_x2.resolve() is typo

    # Resolving a locally defined subnode.
    assert elemento_x3.resolve() is elemento_x3

    # Resolving a builtin type nodes.
    assert typo_u1.resolve().__class__ is suds.xsd.sxbuiltin.XString
    assert typo_u1.resolve(nobuiltin=True) is typo_u1
    assert elemento_x2.resolve(nobuiltin=True) is typo
    assert elemento_x3.resolve(nobuiltin=True) is elemento_x3


def test_schema_object_child_access_by_index():
    client = _client_from_wsdl(
"""<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
xmlns:ns="my-namespace"
xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types>
    <xsd:schema targetNamespace="my-namespace"
    elementFormDefault="qualified"
    attributeFormDefault="unqualified"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:complexType name="Oklahoma">
        <xsd:sequence>
          <xsd:element name="c1" type="xsd:string" />
          <xsd:element name="c2" type="xsd:string" />
          <xsd:element name="c3" type="xsd:string" />
        </xsd:sequence>
      </xsd:complexType>
    </xsd:schema>
  </wsdl:types>
  <wsdl:portType name="dummyPortType">
  </wsdl:portType>
  <wsdl:binding name="dummy" type="ns:dummyPortType">
    <soap:binding style="document"
    transport="http://schemas.xmlsoap.org/soap/http" />
  </wsdl:binding>
  <wsdl:service name="dummy">
    <wsdl:port name="dummy" binding="ns:dummy">
      <soap:address location="https://localhost/dummy" />
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>
""")

    service = client.sd[0]
    aType = service.types[0][0]
    sequence = aType.rawchildren[0]
    assert isinstance(sequence, suds.xsd.sxbasic.Sequence)
    children = aType.children()
    assert isinstance(children, list)

    assert sequence[-1] is None

    # TODO: Children are returned as a 2-tuple containing the child element and
    # its ancestry (list of its parent elements). For some reason the ancestry
    # list is returned as a new list on every __getitem__() call and so can not
    # be compared using the 'is' operator. Also the children() function and
    # accesing children by index does not seem to return ancestry lists of the
    # same depth. See whether this can be updated so we always get the same
    # ancestry list object.
    # TODO: Add more detailed tests for the ancestry list structure.
    # TODO: Add more detailed tests for the rawchildren list structure.

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
    client = _client_from_wsdl(
"""<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
xmlns:ns="my-namespace"
xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types>
    <xsd:schema targetNamespace="my-namespace"
    elementFormDefault="qualified"
    attributeFormDefault="unqualified"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:element name="f">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="a" type="xsd:string" />
            <xsd:element name="b" type="xsd:string" />
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>
      <xsd:element name="fResponse">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="c" type="xsd:string" />
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>
    </xsd:schema>
  </wsdl:types>
  <wsdl:message name="fRequestMessage">
    <wsdl:part name="parameters" element="ns:f" />
  </wsdl:message>
  <wsdl:message name="fResponseMessage">
    <wsdl:part name="parameters" element="ns:fResponse" />
  </wsdl:message>
  <wsdl:portType name="dummyPortType">
    <wsdl:operation name="f">
      <wsdl:input message="ns:fRequestMessage" />
      <wsdl:output message="ns:fResponseMessage" />
    </wsdl:operation>
  </wsdl:portType>
  <wsdl:binding name="dummy" type="ns:dummyPortType">
    <soap:binding style="document"
    transport="http://schemas.xmlsoap.org/soap/http" />
    <wsdl:operation name="f">
      <soap:operation soapAction="f" style="document" />
      <wsdl:input><soap:body use="literal" /></wsdl:input>
      <wsdl:output><soap:body use="literal" /></wsdl:output>
    </wsdl:operation>
  </wsdl:binding>
  <wsdl:service name="dummy">
    <wsdl:port name="dummy" binding="ns:dummy">
      <soap:address location="https://localhost/dummy" />
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>
""")

    # Target namespace.
    assert client.wsdl.tns[0] == "ns"
    assert client.wsdl.tns[1] == "my-namespace"

    # Elements.
    assert len(client.wsdl.schema.elements) == 2
    elementIn = client.wsdl.schema.elements["f", "my-namespace"]
    elementOut = client.wsdl.schema.elements["fResponse", "my-namespace"]
    assert isinstance(elementIn, suds.xsd.sxbasic.Element)
    assert isinstance(elementOut, suds.xsd.sxbasic.Element)
    assert elementIn.name == "f"
    assert elementOut.name == "fResponse"

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

    # Methods (from wsdl).
    assert len(port.methods) == 1
    method_name, method = _first_from_dict(port.methods)
    assert method_name == "f"
    assert method.name == "f"
    assert method.location == b"https://localhost/dummy"

    # Methods (from service definition, for format specifications see the
    # suds.ServiceDefinition.addports() docstring).
    port, methods = service_definition.ports[0]
    assert len(methods) == 1
    method = methods[0]
    assert len(method) == 2
    method_name = method[0]
    assert method_name == "f"
    method_params = method[1]
    assert len(method_params) == 2
    assert method_params[0][0] == "a"
    assert method_params[1][0] == "b"

    # TODO: Once we learn more about suds - add the following assertions:
    #   * assert method.input parameters = a (string), b (string).
    #   * assert method.output parameters = c (string).


def test_wsdl_schema_content():
    client = _client_from_wsdl(
"""<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
xmlns:ns="my-namespace"
xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types>
    <xsd:schema targetNamespace="my-namespace"
    elementFormDefault="qualified"
    attributeFormDefault="unqualified"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:complexType name="UngaBunga">
        <xsd:sequence>
          <xsd:element name="u1" type="xsd:string" />
          <xsd:element name="u2" type="xsd:string" />
          <xsd:element name="u3" type="xsd:string" />
        </xsd:sequence>
      </xsd:complexType>
      <xsd:complexType name="Fifi">
        <xsd:sequence>
          <xsd:element name="x" type="xsd:string" />
        </xsd:sequence>
      </xsd:complexType>
      <xsd:element name="Elemento">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="x1" type="xsd:string" />
            <xsd:element name="x2" type="UngaBunga" />
            <xsd:element name="x3">
              <xsd:complexType>
                <xsd:sequence>
                  <xsd:element name="a1" type="xsd:string" />
                  <xsd:element name="a2" type="xsd:string" />
                </xsd:sequence>
              </xsd:complexType>
            </xsd:element>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>
    </xsd:schema>
  </wsdl:types>
</wsdl:definitions>
""")

    # Elements.
    assert len(client.wsdl.schema.elements) == 1
    elemento = client.wsdl.schema.elements["Elemento", "my-namespace"]
    assert isinstance(elemento, suds.xsd.sxbasic.Element)

    with pytest.raises(KeyError):
        client.wsdl.schema.elements["DoesNotExist", "OMG"]

    # Types.
    assert len(client.wsdl.schema.types) == 2
    unga_bunga = client.wsdl.schema.types["UngaBunga", "my-namespace"]
    assert isinstance(unga_bunga, suds.xsd.sxbasic.Complex)
    fifi = client.wsdl.schema.types["Fifi", "my-namespace"]
    assert isinstance(unga_bunga, suds.xsd.sxbasic.Complex)

    with pytest.raises(KeyError):
        client.wsdl.schema.types["DoesNotExist", "OMG"]


def __assert_dynamic_type(anObject, typename):
    assert anObject.__module__ == suds.sudsobject.__name__
    assert anObject.__metadata__.sxtype.name == typename
    #   In order to be compatible with old style classes (py2 only) we need to
    # access the object's class information using its __class__ member and not
    # the type() function. type() function always returns <type 'instance'> for
    # old-style class instances while the __class__ member returns the correct
    # class information for both old and new-style classes.
    assert anObject.__class__.__module__ == suds.sudsobject.__name__
    assert anObject.__class__.__name__ == typename


def _client_from_wsdl(wsdl_content):
    """
    Constructs a non-caching suds Client based on the given WSDL content.

      Stores the content directly inside the suds library internal document
    store under a hard-coded id to avoid having to load the data from a
    temporary file.

      Caveats:
        * All files stored under the same id so each new local file overwrites
          the previous one.
        * We need to explicitly disable caching here or otherwise, because we
          are using the same id for all our local WSDL documents, suds would
          always reuse the first such local document from its cache.

    """
    # Idea for an alternative implementation:
    #   Custom suds.cache.Cache subclass that would know how to access our
    # locally stored documents or at least not cache them if we are storing
    # them inside the suds library DocumentStore. Not difficult, allows us to
    # have per-client instead of global configuration & allows us to support
    # other cache types but certainly not as short as the current
    # implementation.
    testFileId = "whatchamacallit"
    suds.store.DocumentStore.store[testFileId] = wsdl_content
    return suds.client.Client("suds://" + testFileId, cache=None)


def _first_from_dict(d):
    """Returns the first name/value pair from a dictionary or None if empty."""
    for x in d.items():
        return x[0], x[1]
