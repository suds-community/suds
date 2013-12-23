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
import sys
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


@pytest.mark.parametrize("url", (
    "http://my little URL",
    "https://my little URL",
    "xxx://my little URL",
    "xxx:my little URL",
    "xxx:"))
def test_http_request_URL(url):
    """Make sure suds makes a HTTP request targeted at an expected URL."""
    class MockURLOpener:
        def open(self, request, timeout=None):
            assert request.get_full_url() == url
            raise MyException
    transport = suds.transport.http.HttpTransport()
    transport.urlopener = MockURLOpener()
    store = suds.store.DocumentStore(wsdl=_wsdl_with_no_input_data(url))
    client = suds.client.Client("suds://wsdl", cache=None, documentStore=store,
        transport=transport)
    pytest.raises(MyException, client.service.f)


@pytest.mark.parametrize("url", (
    "my no-protocol URL",
    ":my no-protocol URL"))
def test_http_request_URL_with_a_missing_protocol_identifier(url):
    """
    Test suds reporting URLs with a missing protocol identifier.

    Python urllib library makes this check under Python 3.x, but does not under
    earlier Python versions.

    """
    class MockURLOpener:
        def open(self, request, timeout=None):
            raise MyException
    transport = suds.transport.http.HttpTransport()
    transport.urlopener = MockURLOpener()
    store = suds.store.DocumentStore(wsdl=_wsdl_with_no_input_data(url))
    client = suds.client.Client("suds://wsdl", cache=None, documentStore=store,
        transport=transport)
    exceptionClass = ValueError
    if sys.version_info < (3, 0):
        exceptionClass = MyException
    pytest.raises(exceptionClass, client.service.f)


def test_sending_unicode_data(monkeypatch):
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

    In order to trigger the problematic httplib behaviour we need to make suds
    attempt to send a HTTP request over the network. On the other hand, we want
    this test to work even on computers not connected to a network so we
    monkey-patch the underlying network socket APIs, log all the data suds
    attempt to send over the network and consider the test run successful once
    suds attempt to read back data from the network.

    """
    def callOnce(f):
        """Method decorator making sure its function only gets called once."""
        def wrapper(self, *args, **kwargs):
            fTag = "_%s__%s_called" % (self.__class__.__name__, f.__name__)
            assert not hasattr(self, fTag)
            setattr(self, fTag, True)
            return f(self, *args, **kwargs)
        return wrapper

    class Mocker:
        def __init__(self, expectedHost, expectedPort):
            self.expectedHost = expectedHost
            self.expectedPort = expectedPort
            self.sentData = suds.byte_str()
            self.hostAddress = object()
        @callOnce
        def getaddrinfo(self, host, port, *args, **kwargs):
            assert host == self.expectedHost
            assert port == self.expectedPort
            return [(None, None, None, None, self.hostAddress)]
        @callOnce
        def socket(self, *args, **kwargs):
            self.socket = MockSocket(self)
            return self.socket

    class MockSocketReader:
        @callOnce
        def readline(self, *args, **kwargs):
            raise MyException

    class MockSocket:
        def __init__(self, mocker):
            self.__mocker = mocker
        @callOnce
        def connect(self, address):
            assert address is self.__mocker.hostAddress
        @callOnce
        def makefile(self, *args, **kwargs):
            return MockSocketReader()
        def sendall(self, data):
            # Python 2.4 urllib implementation calls this function twice - once
            # for sending the HTTP request headers and once for its body.
            self.__mocker.sentData += data
        @callOnce
        def settimeout(self, *args, **kwargs):
            assert not hasattr(self, "settimeout_called")
            self.settimeout_called = True

    host = "an-easily-recognizable-host-name-214894932"
    port = 9999
    mocker = Mocker(host, port)
    monkeypatch.setattr("socket.getaddrinfo", mocker.getaddrinfo)
    monkeypatch.setattr("socket.socket", mocker.socket)
    url = "http://%s:%s/svc" % (host, port)
    store = suds.store.DocumentStore(wsdl=_wsdl_with_input_data(url))
    client = suds.client.Client("suds://wsdl", cache=None, documentStore=store)
    data = u"Дмитровский район"
    pytest.raises(MyException, client.service.f, data)
    assert data.encode("utf-8") in mocker.sentData


def test_sending_non_ascii_location():
    """
    Suds should refuse to send HTTP requests with a target location string
    containing non-ASCII characters. URLs are supposed to consist of
    characters only.

    """
    class MockURLOpener:
        def open(self, request, timeout=None):
            raise MyException
    url = u"http://Дмитровский-район-152312306:9999/svc"
    transport = suds.transport.http.HttpTransport()
    transport.urlopener = MockURLOpener()
    store = suds.store.DocumentStore(wsdl=_wsdl_with_no_input_data(url))
    client = suds.client.Client("suds://wsdl", cache=None, documentStore=store,
        transport=transport)
    pytest.raises(UnicodeEncodeError, client.service.f)


@pytest.mark.skipif(sys.version_info >= (3, 0),
    reason="Python 2 specific functionality")
@pytest.mark.parametrize(("urlString", "expectedException"), (
    ("http://jorgula", MyException),
    ("http://jorgula_\xe7", UnicodeDecodeError)))
def test_sending_py2_bytes_location(urlString, expectedException):
    """
    Suds should accept single-byte string URL values under Python 2, but should
    still report an error if those strings contain any non-ASCII characters.

    """
    class MockURLOpener:
        def open(self, request, timeout=None):
            raise MyException
    transport = suds.transport.http.HttpTransport()
    transport.urlopener = MockURLOpener()
    store = suds.store.DocumentStore(wsdl=_wsdl_with_no_input_data("http://x"))
    client = suds.client.Client("suds://wsdl", cache=None, documentStore=store,
        transport=transport)
    client.options.location = suds.byte_str(urlString)
    pytest.raises(expectedException, client.service.f)


@pytest.mark.skipif(sys.version_info < (3, 0),
    reason="requires at least Python 3")
@pytest.mark.parametrize("urlString", (
    "http://jorgula",
    "http://jorgula_\xe7"))
def test_sending_py3_bytes_location(urlString):
    """
    Suds should refuse to send HTTP requests with a target location specified
    as either a Python 3 bytes or bytearray object.

    """
    class MockURLOpener:
        def open(self, request, timeout=None):
            raise MyException
    transport = suds.transport.http.HttpTransport()
    transport.urlopener = MockURLOpener()
    store = suds.store.DocumentStore(wsdl=_wsdl_with_no_input_data("http://x"))
    client = suds.client.Client("suds://wsdl", cache=None, documentStore=store,
        transport=transport)

    expectedException = AssertionError
    if sys.flags.optimize:
        expectedException = AttributeError

    for url in (bytes(urlString, encoding="utf-8"),
        bytearray(urlString, encoding="utf-8")):
        # Under Python 3.x we can not use the client's 'location' option to set
        # a bytes URL as it accepts only strings and in Python 3.x all strings
        # are unicode strings. Therefore, we use an ugly hack, modifying suds's
        # internal web service description structure to force it to think it
        # has a bytes object specified as a location for its 'f' web service
        # operation.
        client.sd[0].ports[0][0].methods['f'].location = url
        pytest.raises(expectedException, client.service.f)


def _check_Authorization_header(request, username, password):
    assert len(request.headers) == 1
    header = request.headers["Authorization"]
    assert header == _encode_basic_credentials(username, password)


def _encode_basic_credentials(username, password):
    """
      Encodes user credentials as used in basic HTTP authentication.

      This is the value expected to be added to the 'Authorization' HTTP
    header.

    """
    data = suds.byte_str("%s:%s" % (username, password))
    return "Basic %s" % base64.b64encode(data).decode("utf-8")


def _wsdl_with_input_data(url):
    """
    Return a WSDL schema with a single operation f taking a single parameter.

    Included operation takes a single string parameter and returns no values.
    Externally specified URL is used as the web service location.

    """
    return suds.byte_str(u"""\
<?xml version="1.0" encoding="utf-8"?>
<wsdl:definitions targetNamespace="myNamespace"
  xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
  xmlns:tns="myNamespace"
  xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
  xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <wsdl:types>
    <xsd:schema targetNamespace="myNamespace">
      <xsd:element name="fRequest" type="xsd:string"/>
    </xsd:schema>
  </wsdl:types>
  <wsdl:message name="fInputMessage">
    <wsdl:part name="parameters" element="tns:fRequest"/>
  </wsdl:message>
  <wsdl:portType name="Port">
    <wsdl:operation name="f">
      <wsdl:input message="tns:fInputMessage"/>
    </wsdl:operation>
  </wsdl:portType>
  <wsdl:binding name="Binding" type="tns:Port">
    <soap:binding style="document"
      transport="http://schemas.xmlsoap.org/soap/http"/>
    <wsdl:operation name="f">
      <soap:operation/>
      <wsdl:input><soap:body use="literal"/></wsdl:input>
    </wsdl:operation>
  </wsdl:binding>
  <wsdl:service name="Service">
    <wsdl:port name="Port" binding="tns:Binding">
      <soap:address location="%s"/>
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>""" % (url,))


def _wsdl_with_no_input_data(url):
    """
    Return a WSDL schema with a single operation f taking no parameters.

    Included operation returns no values. Externally specified URL is used as
    the web service location.

    """
    return suds.byte_str(u"""\
<?xml version="1.0" encoding="utf-8"?>
<wsdl:definitions targetNamespace="myNamespace"
  xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
  xmlns:tns="myNamespace"
  xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
  xmlns:xsd="http://www.w3.org/2001/XMLSchema">
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
