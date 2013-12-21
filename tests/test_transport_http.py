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
Suds library HTTP transport related unit tests.

Implemented using the 'pytest' testing framework.

"""

if __name__ == "__main__":
    import __init__
    __init__.runUsingPyTest(globals())


import suds
import suds.client
import suds.store
import suds.transport.http

import pytest

import base64
import urllib2


class MyException(Exception):
    """Local exception used in this test module."""
    pass


def test_authenticated_http():
    t = suds.transport.http.HttpAuthenticated(username="Habul AfuFa",
        password="preCious")
    assert t.credentials() == ("Habul AfuFa", "preCious")

    t = suds.transport.http.HttpAuthenticated(username="macro")
    assert t.credentials() == ("macro", None)


def test_authenticated_http_add_credentials_to_request():
    class MockRequest:
        def __init__(self):
            self.headers = {}

    t = suds.transport.http.HttpAuthenticated(username="Humpty")
    r = MockRequest()
    t.addcredentials(r)
    assert len(r.headers) == 0

    t = suds.transport.http.HttpAuthenticated(password="Dumpty")
    r = MockRequest()
    t.addcredentials(r)
    assert len(r.headers) == 0

    username = "Habul Afufa"
    password = "preCious"
    t = suds.transport.http.HttpAuthenticated(username=username,
        password=password)
    r = MockRequest()
    t.addcredentials(r)
    _check_Authorization_header(r, username, password)

    #   Regression test: Extremely long username & password combinations must
    # not cause suds to add additional newlines in the constructed
    # 'Authorization' HTTP header.
    username = ("An Extremely Long Username that could be usable only to "
        "Extremely Important People whilst on Extremely Important Missions.")
    password = ("An Extremely Long Password that could be usable only to "
        "Extremely Important People whilst on Extremely Important Missions. "
        "And some extra 'funny' characters to improve security: "
        "!@#$%^&*():|}|{{.\nEven\nSome\nNewLines\n"
        "  and spaces at the start of a new line.   ")
    t = suds.transport.http.HttpAuthenticated(username=username,
        password=password)
    r = MockRequest()
    t.addcredentials(r)
    _check_Authorization_header(r, username, password)


def test_http_request_URL():
    """Make sure suds makes a HTTP request targeted at an expected URL."""

    class MockURLOpener:
        """
        Mock suds HTTP transport URL opener object asserting that it got passed
        a request with an expected URL and then raising an exception to
        interrupt the current network operation.

        """

        def __init__(self, expectedURL):
            self.expectedURL = expectedURL

        def open(self, request, timeout=None):
            assert request.get_full_url() == self.expectedURL
            raise MyException

    url = "http://my little URL"

    transport = suds.transport.http.HttpTransport()
    transport.urlopener = MockURLOpener(url)
    store = suds.store.DocumentStore(wsdl=_wsdl_with_url(url))
    client = suds.client.Client("suds://wsdl", cache=None, documentStore=store,
        transport=transport)
    pytest.raises(MyException, client.service.f)


def test_sending_unicode_data():
    """
    Original suds implementation passed its request location URL to the
    underlying HTTP request object as a unicode string.

    Under Python 2.4 this causes no problems as that implementation simply
    sends all the request data over the network as-is (and treats all unicode
    data as bytes anyway).

    Under Python 2.7 this causes the httplib HTTP request implementation to
    convert all of its data to unicode, and do so by simply assuming that data
    contains only ASCII characters. If any other characters are encountered, it
    fails with an exception like "UnicodeDecodeError: 'ascii' codec can't
    decode byte 0xd0 in position 290: ordinal not in range(128)".

    Under Python 3.x the httplib HTTP request implementation automatically
    converts its received URL to a bytes object (assuming it contains only
    ASCII characters), thus avoiding the need to convert all the other request
    data.

    Current test implementation can not trigger this httplib behaviour without
    actually attempting to send the request to some address. On the other hand,
    we want this test to pass even on computers not connected to a network so
    me mark it as passed if the test reaches the sending phase and fails. We
    also attempt to make the send fail on any computer by using an invalid
    server address and setting the network operation timeout to 0.

    IDEA: Use a custom transport which calls the underlying urllib library
    operation instead of suds's HttpTransport. Our transport would then use an
    additional handler in its urllib handler chain, collecting the prepared
    request data and aborting the whole operation just before that data gets
    sent over the network. This would allow us to test that this data both got
    constructed and that got constructed correctly and not require us to fake
    sending it over the network at all.

    """
    wsdl = suds.byte_str("""\
<?xml version="1.0" encoding="utf-8"?>
<wsdl:definitions targetNamespace="myNamespace"
  xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
  xmlns:tns="myNamespace"
  xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
  xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <wsdl:types>
    <xsd:schema targetNamespace="myNamespace">
      <xsd:element name="fRequest" nillable="true" type="xsd:string"/>
      <xsd:element name="fResponse" nillable="true" type="xsd:string"/>
    </xsd:schema>
  </wsdl:types>
  <wsdl:message name="fInputMessage">
    <wsdl:part name="parameters" element="tns:fRequest"/>
  </wsdl:message>
  <wsdl:message name="fOutputMessage">
    <wsdl:part name="parameters" element="tns:fResponse"/>
  </wsdl:message>
  <wsdl:portType name="Port">
    <wsdl:operation name="f">
      <wsdl:input message="tns:fInputMessage"/>
      <wsdl:output message="tns:fOutputMessage"/>
    </wsdl:operation>
  </wsdl:portType>
  <wsdl:binding name="Binding" type="tns:Port">
    <soap:binding style="document"
      transport="http://schemas.xmlsoap.org/soap/http"/>
    <wsdl:operation name="f">
      <soap:operation/>
      <wsdl:input><soap:body use="literal"/></wsdl:input>
      <wsdl:output><soap:body use="literal"/></wsdl:output>
    </wsdl:operation>
  </wsdl:binding>
  <wsdl:service name="Service">
    <wsdl:port name="Port" binding="tns:Binding">
      <soap:address location="http://some-invalid-address-152312306:9999/svc"/>
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>""")

    store = suds.store.DocumentStore(wsdl=wsdl)
    client = suds.client.Client("suds://wsdl", cache=None, documentStore=store,
        timeout=0)
    # Expected to raise an exception complaining that a non-blocking socket
    # operation could not be completed immediately or, in case there is no
    # network, that the server's address could not be resolved.
    pytest.raises(urllib2.URLError, client.service.f, u"Дмитровский район")


def test_sending_unicode_location():
    """
    Suds should refuse to send HTTP requests with a target location string
    containing non-ASCII characters. URLs are supposed to consist of
    characters only.

    """
    wsdl = suds.byte_str(u"""\
<?xml version="1.0" encoding="utf-8"?>
<wsdl:definitions targetNamespace="myNamespace"
  xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
  xmlns:tns="myNamespace"
  xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
  xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <wsdl:types>
    <xsd:schema targetNamespace="myNamespace">
      <xsd:element name="fRequest" type="xsd:string"/>
      <xsd:element name="fResponse" type="xsd:string"/>
    </xsd:schema>
  </wsdl:types>
  <wsdl:message name="fInputMessage">
    <wsdl:part name="parameters" element="tns:fRequest"/>
  </wsdl:message>
  <wsdl:message name="fOutputMessage">
    <wsdl:part name="parameters" element="tns:fResponse"/>
  </wsdl:message>
  <wsdl:portType name="Port">
    <wsdl:operation name="f">
      <wsdl:input message="tns:fInputMessage"/>
      <wsdl:output message="tns:fOutputMessage"/>
    </wsdl:operation>
  </wsdl:portType>
  <wsdl:binding name="Binding" type="tns:Port">
    <soap:binding style="document"
      transport="http://schemas.xmlsoap.org/soap/http"/>
    <wsdl:operation name="f">
      <soap:operation/>
      <wsdl:input><soap:body use="literal"/></wsdl:input>
      <wsdl:output><soap:body use="literal"/></wsdl:output>
    </wsdl:operation>
  </wsdl:binding>
  <wsdl:service name="Service">
    <wsdl:port name="Port" binding="tns:Binding">
      <soap:address location="http://Дмитровский-район-152312306:9999/svc"/>
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>""")

    store = suds.store.DocumentStore(wsdl=wsdl)
    client = suds.client.Client("suds://wsdl", cache=None, documentStore=store,
        timeout=0)
    pytest.raises(UnicodeEncodeError, client.service.f, "plonker")


def _check_Authorization_header(request, username, password):
    assert len(request.headers) == 1
    assert request.headers["Authorization"] == _encode_basic_credentials(
        username, password)


def _encode_basic_credentials(username, password):
    """
      Encodes user credentials as used in basic HTTP authentication.

      This is the value expected to be added to the 'Authorization' HTTP
    header.

    """
    data = suds.byte_str("%s:%s" % (username, password))
    return "Basic %s" % base64.b64encode(data).decode("utf-8")


def _wsdl_with_url(url):
    """
    Return a WSDL schema with the given URL and a single operation f.

    Included operation takes no parameters and returns no values.

    """
    return suds.byte_str(u"""\
<?xml version="1.0" encoding="utf-8"?>
<wsdl:definitions targetNamespace="myNamespace"
  xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
  xmlns:tns="myNamespace"
  xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
  xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <wsdl:types>
    <xsd:schema/>
  </wsdl:types>
  <wsdl:portType name="Port">
    <wsdl:operation name="f"/>
  </wsdl:portType>
  <wsdl:binding name="Binding" type="tns:Port">
    <soap:binding style="document"
      transport="http://schemas.xmlsoap.org/soap/http"/>
    <wsdl:operation name="f"/>
  </wsdl:binding>
  <wsdl:service name="Service">
    <wsdl:port name="Port" binding="tns:Binding">
      <soap:address location="%s"/>
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>""" % (url,))
