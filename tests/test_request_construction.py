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

  Suds provides the user with an option to automatically 'hide' wrapper
elements simple types and allow the user to specify such parameters without
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
            <xsd:enumeration value="alfa" />
            <xsd:enumeration value="beta" />
            <xsd:enumeration value="gamma" />
          </xsd:restriction>
        </xsd:simpleType>
      </xsd:element>""", "Elemento"))

    client_named = tests.client_from_wsdl(tests.wsdl_input("""\
      <xsd:simpleType name="MyType">
        <xsd:restriction base="xsd:string">
          <xsd:enumeration value="alfa" />
          <xsd:enumeration value="beta" />
          <xsd:enumeration value="gamma" />
        </xsd:restriction>
      </xsd:simpleType>
      <xsd:element name="Elemento" type="ns:MyType" />""", "Elemento"))

    assert not _isInputWrapped(client_unnamed, "f")
    assert not _isInputWrapped(client_named, "f")


def test_disabling_automated_simple_interface_unwrapping():
    client = tests.client_from_wsdl(tests.wsdl_input("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="Elemento" type="xsd:string" />
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", "Wrapper"), nosend=True, prettyxml=True, unwrap=False)
    assert not _isInputWrapped(client, "f")
    wrapper = client.factory.create("Wrapper")
    wrapper.Elemento = "Wonderwall"
    _check_request(client.service.f(Wrapper=wrapper), """\
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
    _check_request(client.service.f(local="--L--", local_referenced="--LR--",
        external="--E--"), """\
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


def test_extra_parameters():
    """
    Extra input parameters should get silently ignored and not added to the
    constructed SOAP request.

    """
    service_from_wsdl = lambda wsdl : tests.client_from_wsdl(wsdl, nosend=True,
        prettyxml=True).service

    service = service_from_wsdl(tests.wsdl_input("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="aString" type="xsd:string" />
            <xsd:element name="anInteger" type="xsd:integer" />
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", "Wrapper"))

    # Unnamed parameters.
    _check_request(service.f("something", 0, "extra1", "extra2"), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper>
         <ns0:aString>something</ns0:aString>
         <ns0:anInteger>0</ns0:anInteger>
      </ns0:Wrapper>
   </ns1:Body>
</SOAP-ENV:Envelope>""")

    # Named parameters.
    _check_request(service.f("something", extra="1", anInteger=7), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper>
         <ns0:aString>something</ns0:aString>
         <ns0:anInteger>7</ns0:anInteger>
      </ns0:Wrapper>
   </ns1:Body>
</SOAP-ENV:Envelope>""")


def test_invalid_argument_type_handling():
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
          <xsd:element name="freak1" type="xsd:string" />
          <xsd:element name="freak2" type="xsd:string" />
          <xsd:element name="freak3" type="xsd:string" />
        </xsd:sequence>
      </xsd:complexType>
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="p1" type="xsd:string" />
            <xsd:element name="anInteger" type="xsd:integer" />
            <xsd:element name="p2" type="xsd:string" />
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", "Wrapper"), nosend=True, prettyxml=True)

    # Passing an unrelated Python type value.
    class SomeType:
        def __str__(self):
            return "Some string representation."
    _check_request(client.service.f(anInteger=SomeType()), """\
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
    _check_request(client.service.f(anInteger=value), """\
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
    service_from_wsdl = lambda wsdl : tests.client_from_wsdl(wsdl, nosend=True,
        prettyxml=True).service

    service = service_from_wsdl(tests.wsdl_input("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="aString" type="xsd:string" />
            <xsd:element name="anInteger" type="xsd:integer" />
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", "Wrapper"))

    _check_request(service.f(), """\
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

    _check_request(service.f(u"Pero Ždero"), """\
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

    _check_request(service.f(anInteger=666), """\
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
    _check_request(service.f(aString=None, anInteger=666), """\
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
    _check_request(service.f(aString="Omega", anInteger=None), """\
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
    service_from_wsdl = lambda wsdl : tests.client_from_wsdl(wsdl, nosend=True,
        prettyxml=True).service

    class Tester:
        def __init__(self, service, expected_xml):
            self.service = service
            self.expected_xml = expected_xml

        def test(self, *args, **kwargs):
            _check_request(self.service.f(*args, **kwargs), self.expected_xml)

    # Test different ways to make the same web service operation call.
    service = service_from_wsdl(tests.wsdl_input("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="uno" type="xsd:string" />
            <xsd:element name="due" type="xsd:string" />
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
    service = service_from_wsdl(tests.wsdl_input("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="due" type="xsd:string" />
            <xsd:element name="uno" type="xsd:string" />
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
    service_from_wsdl = lambda wsdl : tests.client_from_wsdl(wsdl, nosend=True,
        prettyxml=True).service

    service = service_from_wsdl(tests.wsdl_input("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="aString" type="xsd:string" minOccurs="0" />
            <xsd:element name="anInteger" type="xsd:integer" minOccurs="0" />
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", "Wrapper"))

    _check_request(service.f(), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper/>
   </ns1:Body>
</SOAP-ENV:Envelope>""")

    # None is treated as an undefined value.
    _check_request(service.f(None), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper/>
   </ns1:Body>
</SOAP-ENV:Envelope>""")

    # Empty string values are treated as well defined values.
    _check_request(service.f(""), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper>
         <ns0:aString></ns0:aString>
      </ns0:Wrapper>
   </ns1:Body>
</SOAP-ENV:Envelope>""")

    _check_request(service.f("Kiflica"), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper>
         <ns0:aString>Kiflica</ns0:aString>
      </ns0:Wrapper>
   </ns1:Body>
</SOAP-ENV:Envelope>""")

    _check_request(service.f(anInteger=666), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper>
         <ns0:anInteger>666</ns0:anInteger>
      </ns0:Wrapper>
   </ns1:Body>
</SOAP-ENV:Envelope>""")

    _check_request(service.f("Alfa", 9), """\
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
                  <xsd:element name="Elemento" type="xsd:string" />
                </xsd:sequence>
              </xsd:complexType>
            </xsd:element>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", "Wrapper1"), nosend=True, prettyxml=True)

    assert _isInputWrapped(client, "f")

    #   The following calls are actually illegal and result in incorrectly
    # generated SOAP requests.
    _check_request(client.service.f("A B C"), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper1>
         <ns0:Wrapper2>A B C</ns0:Wrapper2>
      </ns0:Wrapper1>
   </ns1:Body>
</SOAP-ENV:Envelope>""")
    _check_request(client.service.f(Elemento="A B C"), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper1>
         <ns0:Wrapper2/>
      </ns0:Wrapper1>
   </ns1:Body>
</SOAP-ENV:Envelope>""")
    _check_request(client.service.f(Wrapper2="A B C"), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper1>
         <ns0:Wrapper2>A B C</ns0:Wrapper2>
      </ns0:Wrapper1>
   </ns1:Body>
</SOAP-ENV:Envelope>""")
    _check_request(client.service.f(Wrapper1="A B C"), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper1>
         <ns0:Wrapper2/>
      </ns0:Wrapper1>
   </ns1:Body>
</SOAP-ENV:Envelope>""")


def test_wrapped_parameter():
    # Prepare web service proxies.
    client = lambda *args : tests.client_from_wsdl(tests.wsdl_input(*args),
        nosend=True, prettyxml=True)
    client_bare_single = client("""\
      <xsd:element name="Elemento" type="xsd:string" />""", "Elemento")
    client_bare_multiple_simple = client("""\
      <xsd:element name="Elemento1" type="xsd:string" />
      <xsd:element name="Elemento2" type="xsd:string" />""", "Elemento1",
        "Elemento2")
    client_bare_multiple_wrapped = client("""\
      <xsd:complexType name="Wrapper">
        <xsd:sequence>
          <xsd:element name="Elemento" type="xsd:string" />
        </xsd:sequence>
      </xsd:complexType>
      <xsd:element name="Elemento1" type="ns:Wrapper" />
      <xsd:element name="Elemento2" type="ns:Wrapper" />""", "Elemento1",
        "Elemento2")
    client_wrapped_unnamed = client("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="Elemento" type="xsd:string" />
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", "Wrapper")
    client_wrapped_named = client("""\
      <xsd:complexType name="WrapperType">
        <xsd:sequence>
          <xsd:element name="Elemento" type="xsd:string" />
        </xsd:sequence>
      </xsd:complexType>
      <xsd:element name="Wrapper" type="ns:WrapperType" />""", "Wrapper")

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

    _check_request(call_single(client_bare_single), """\
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
    _check_request(call_single(client_wrapped_unnamed), expected_xml)
    _check_request(call_single(client_wrapped_named), expected_xml)

    #   Suds library's automatic structure unwrapping prevents us from
    # specifying the external wrapper structure directly.
    _check_request(client_wrapped_unnamed.service.f(Wrapper="A"), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper>
         <ns0:Elemento/>
      </ns0:Wrapper>
   </ns1:Body>
</SOAP-ENV:Envelope>""")

    #   Multiple parameter web service operations are never automatically
    # unwrapped.
    data = ("Unga", "Bunga")
    call_multiple = lambda c : c.service.f(*data)

    _check_request(call_multiple(client_bare_multiple_simple), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Elemento1>%s</ns0:Elemento1>
      <ns0:Elemento2>%s</ns0:Elemento2>
   </ns1:Body>
</SOAP-ENV:Envelope>""" % data)

    _check_request(call_multiple(client_bare_multiple_wrapped), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Elemento1>%s</ns0:Elemento1>
      <ns0:Elemento2>%s</ns0:Elemento2>
   </ns1:Body>
</SOAP-ENV:Envelope>""" % data)


def _check_request(request, expected_xml):
    tests.compare_xml_to_string(request.original_envelope, expected_xml)


def _isInputWrapped(client, method_name):
    assert len(client.wsdl.bindings) == 1
    operation = client.wsdl.bindings.values()[0].operations[method_name]
    return operation.soap.input.body.wrapped
