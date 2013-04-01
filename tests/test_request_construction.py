# -*- coding: utf-8 -*-

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
    try:
        import pytest
        pytest.main(["--pyargs", __file__])
    except ImportError:
        print("'py.test' unit testing framework not available. Can not run "
            "'%s' directly as a script." % (__file__,))
    import sys
    sys.exit(-2)


import suds
import tests


def test_extra_parameters():
    """
    Extra input parameters should get silently ignored and not added to the
    constructed SOAP request.

    """
    service_from_wsdl = lambda wsdl : tests.client_from_wsdl(wsdl, nosend=True,
        prettyxml=True).service

    service = service_from_wsdl(_wsdl("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="aString" type="xsd:string" />
            <xsd:element name="anInteger" type="xsd:integer" />
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", "Wrapper"))

    # Unnamed parameters.
    assert service.f("something", 0, "extra1", "extra2").envelope ==  \
        suds.byte_str("""\
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
    assert service.f("something", extra="1", anInteger=7).envelope ==  \
        suds.byte_str("""\
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
    client_from_wsdl = lambda wsdl : tests.client_from_wsdl(wsdl, nosend=True,
        prettyxml=True).service

    client = tests.client_from_wsdl(_wsdl("""\
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
    assert client.service.f(anInteger=SomeType()).envelope ==  \
        suds.byte_str("""\
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
    assert client.service.f(anInteger=value).envelope ==  \
        suds.byte_str("""\
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

    service = service_from_wsdl(_wsdl("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="aString" type="xsd:string" />
            <xsd:element name="anInteger" type="xsd:integer" />
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", "Wrapper"))

    assert service.f().envelope == suds.byte_str("""\
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

    assert service.f(u"Pero Ždero").envelope == suds.byte_str("""\
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

    assert service.f(anInteger=666).envelope == suds.byte_str("""\
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
    assert service.f(aString=None, anInteger=666).envelope ==  \
        suds.byte_str("""\
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
    assert service.f(aString="Omega", anInteger=None).envelope ==  \
        suds.byte_str("""\
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

    # Test different ways to make the same web service operation call.
    service = service_from_wsdl(_wsdl("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="uno" type="xsd:string" />
            <xsd:element name="due" type="xsd:string" />
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", "Wrapper"))
    expected_request = suds.byte_str("""\
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
    assert expected_request == service.f("einz", "zwei").envelope
    assert expected_request == service.f(uno="einz", due="zwei").envelope
    assert expected_request == service.f(due="zwei", uno="einz").envelope
    assert expected_request == service.f("einz", due="zwei").envelope

    #   The order of parameters in the constructed SOAP request should depend
    # only on the initial WSDL schema.
    service = service_from_wsdl(_wsdl("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="due" type="xsd:string" />
            <xsd:element name="uno" type="xsd:string" />
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", "Wrapper"))
    expected_request = suds.byte_str("""\
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
    assert expected_request == service.f("zwei", "einz").envelope
    assert expected_request == service.f(uno="einz", due="zwei").envelope
    assert expected_request == service.f(due="zwei", uno="einz").envelope
    assert expected_request == service.f("zwei", uno="einz").envelope


def test_optional_parameter_handling():
    """Missing non-optional parameters should get passed as empty values."""
    service_from_wsdl = lambda wsdl : tests.client_from_wsdl(wsdl, nosend=True,
        prettyxml=True).service

    service = service_from_wsdl(_wsdl("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="aString" type="xsd:string" minOccurs="0" />
            <xsd:element name="anInteger" type="xsd:integer" minOccurs="0" />
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", "Wrapper"))

    assert service.f().envelope == suds.byte_str("""\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper/>
   </ns1:Body>
</SOAP-ENV:Envelope>""")

    # None is treated as an undefined value.
    assert service.f(None).envelope == suds.byte_str("""\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper/>
   </ns1:Body>
</SOAP-ENV:Envelope>""")

    # Empty string values are treated as well defined values.
    assert service.f("").envelope == suds.byte_str("""\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper>
         <ns0:aString></ns0:aString>
      </ns0:Wrapper>
   </ns1:Body>
</SOAP-ENV:Envelope>""")

    assert service.f("Kiflica").envelope == suds.byte_str("""\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper>
         <ns0:aString>Kiflica</ns0:aString>
      </ns0:Wrapper>
   </ns1:Body>
</SOAP-ENV:Envelope>""")

    assert service.f(anInteger=666).envelope == suds.byte_str("""\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper>
         <ns0:anInteger>666</ns0:anInteger>
      </ns0:Wrapper>
   </ns1:Body>
</SOAP-ENV:Envelope>""")

    assert service.f("Alfa", 9).envelope == suds.byte_str("""\
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


def test_wrapped_parameter():
    service_from_wsdl = lambda wsdl : tests.client_from_wsdl(wsdl, nosend=True,
        prettyxml=True).service

    # Prepare web service proxies.
    service_simple = service_from_wsdl(_wsdl("""\
      <xsd:element name="Elemento" type="xsd:string" />""", "Elemento"))
    service_complex = service_from_wsdl(_wsdl("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="Elemento" type="xsd:string" />
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", "Wrapper"))

    #   Both web service operations get called the same way even though the
    # complex one actually has an extra wrapper element around its input data.
    call = lambda s : s.f("Maestro").envelope
    assert call(service_simple) == suds.byte_str("""\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Elemento>Maestro</ns0:Elemento>
   </ns1:Body>
</SOAP-ENV:Envelope>""")
    assert call(service_complex) == suds.byte_str("""\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper>
         <ns0:Elemento>Maestro</ns0:Elemento>
      </ns0:Wrapper>
   </ns1:Body>
</SOAP-ENV:Envelope>""")


def _wsdl(schema_content, request_element_name):
    """
      Returns a WSDL schema used in different tests throughout this test
    module.

    """
    return suds.byte_str("""\
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
  </wsdl:types>
  <wsdl:message name="fRequestMessage">
    <wsdl:part name="parameters" element="ns:%s" />
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
    </wsdl:operation>
  </wsdl:binding>
  <wsdl:service name="dummy">
    <wsdl:port name="dummy" binding="ns:dummy">
      <soap:address location="unga-bunga-location" />
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>
""" % (schema_content, request_element_name))
