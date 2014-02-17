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
    __init__.run_using_pytest(globals())


import suds
import suds.transport
import suds.transport.http

import pytest

import base64
import re
import sys
import urllib2

if sys.version_info >= (3, 0):
    urllib_request = urllib.request
else:
    urllib_request = urllib2


class MyException(Exception):
    """Local exception used in this test module."""
    pass


class CountedMock(object):
    """
    Base mock object class supporting generic attribute access counting.

    Ignores attributes whose name starts with 'mock_' or '__mock_' or their
    transformed variant '_<className>__mock_'.

    Derived classes must call this class's __init__() or mock_reset()
    methods during their initialization, but both calls are not needed.
    Before this initialization, all counters will be reported as None.

    """

    def __init__(self):
        self.mock_reset()

    def __getattribute__(self, name):
        get = super(CountedMock, self).__getattribute__
        counter_name = "_CountedMock__mock_call_counter"
        has_counter = False
        try:
            counter = get(counter_name)
            has_counter = True
        except AttributeError:
            pass
        if has_counter:
            if name == counter_name:
                return counter
            if not re.match("(_.+__)?mock_", name):
                counter[name] = counter.get(name, 0) + 1
        return get(name)

    def mock_call_count(self, name):
        if self.__mock_call_counter:
            return self.__mock_call_counter.get(name, 0)

    def mock_reset(self):
        self.__mock_call_counter = {}


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

    def check_Authorization_header(request, username, password):
        assert len(request.headers) == 1
        header = request.headers["Authorization"]
        assert header == _encode_basic_credentials(username, password)

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
    check_Authorization_header(r, username, password)

    # Regression test: Extremely long username & password combinations must not
    # cause suds to add additional newlines in the constructed 'Authorization'
    # HTTP header.
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
    check_Authorization_header(r, username, password)


@pytest.mark.parametrize("url", (
    "my no-protocol URL",
    ":my no-protocol URL"))
def test_sending_to_URL_with_a_missing_protocol_identifier(url):
    """
    Test suds reporting URLs with a missing protocol identifier.

    Python urllib library makes this check under Python 3.x, but not under
    earlier Python versions.

    """
    class MockURLOpener:
        def open(self, request, timeout=None):
            raise MyException
    transport = suds.transport.http.HttpTransport()
    transport.urlopener = MockURLOpener()
    if sys.version_info < (3, 0):
        exception_class = MyException
        def check_exception(e):
            pass
    else:
        exception_class = ValueError
        def check_exception(e):
            assert "unknown url type" in str(e)
    request_data = object()
    request = suds.transport.Request(url, request_data)
    check_exception(pytest.raises(exception_class, transport.open, request))
    check_exception(pytest.raises(exception_class, transport.send, request))


@pytest.mark.parametrize(
    ("send_method", "expected_sent_data_start", "expect_request_data_send"), (
    (suds.transport.http.HttpTransport.open, "GET", False),
    (suds.transport.http.HttpTransport.send, "POST", True)))
def test_sending_using_network_sockets(monkeypatch, send_method,
        expected_sent_data_start, expect_request_data_send):
    """
    Test that telling HttpTransport to send a request actually causes it to
    send the expected data over the network.

    In order to test this we need to make suds attempt to send a HTTP request
    over the network. On the other hand, we want the test to work even on
    computers not connected to a network so we monkey-patch the underlying
    network socket APIs, log all the data suds attempts to send over the
    network and consider the test run successful once suds attempts to read
    back data from the network.

    """
    class Mocker(CountedMock):
        def __init__(self, expected_host, expected_port):
            self.expected_host = expected_host
            self.expected_port = expected_port
            self.host_address = object()
            self.mock_reset()
        def getaddrinfo(self, host, port, *args, **kwargs):
            assert host == self.expected_host
            assert port == self.expected_port
            return [(None, None, None, None, self.host_address)]
        def mock_reset(self):
            super(Mocker, self).mock_reset()
            self.mock_sent_data = suds.byte_str()
            self.mock_socket = None
        def socket(self, *args, **kwargs):
            assert self.mock_socket is None
            self.mock_socket = MockSocket(self)
            return self.mock_socket

    class MockSocket(CountedMock):
        def __init__(self, mocker):
            self.__mocker = mocker
            self.mock_reset()
        def connect(self, address):
            assert address is self.__mocker.host_address
        def makefile(self, *args, **kwargs):
            assert self.mock_reader is None
            self.mock_reader = MockSocketReader()
            return self.mock_reader
        def mock_reset(self):
            super(MockSocket, self).mock_reset()
            self.mock_reader = None
        def sendall(self, data):
            self.__mocker.mock_sent_data += data
        def settimeout(self, *args, **kwargs):
            pass

    class MockSocketReader(CountedMock):
        def __init__(self):
            super(MockSocketReader, self).__init__()
        def readline(self, *args, **kwargs):
            raise MyException

    host = "an-easily-recognizable-host-name-214894932"
    port = 9999
    host_port = "%s:%s" % (host, port)
    url_relative = "svc"
    url = "http://%s/%s" % (host_port, url_relative)
    partial_ascii_byte_data = suds.byte_str("Muka-laka-hiki")
    non_ascii_byte_data = u"Дмитровский район".encode("utf-8")
    non_ascii_byte_data += partial_ascii_byte_data
    mocker = Mocker(host, port)
    monkeypatch.setattr("socket.getaddrinfo", mocker.getaddrinfo)
    monkeypatch.setattr("socket.socket", mocker.socket)
    request = suds.transport.Request(url, non_ascii_byte_data)
    transport = suds.transport.http.HttpTransport()
    pytest.raises(MyException, send_method, transport, request)
    assert mocker.mock_call_count("getaddrinfo") == 1
    assert mocker.mock_call_count("socket") == 1
    assert mocker.mock_socket.mock_call_count("connect") == 1
    assert mocker.mock_socket.mock_call_count("makefile") == 1
    # With older Python versions, e.g. Python 2.4, urllib implementation calls
    # Socket's sendall() method twice - once for sending the HTTP request
    # headers and once for its body.
    assert mocker.mock_socket.mock_call_count("sendall") in (1, 2)
    # With older Python versions , e.g. Python 2.4, Socket class does not
    # implement the settimeout() method.
    assert mocker.mock_socket.mock_call_count("settimeout") in (0, 1)
    assert mocker.mock_socket.mock_reader.mock_call_count("readline") == 1
    assert mocker.mock_sent_data.__class__ is suds.byte_str_class
    expected_sent_data_start = "%s /%s HTTP/1.1\r\n" % (
        expected_sent_data_start, url_relative)
    expected_sent_data_start = suds.byte_str(expected_sent_data_start)
    assert mocker.mock_sent_data.startswith(expected_sent_data_start)
    assert host_port.encode("utf-8") in mocker.mock_sent_data
    if expect_request_data_send:
        assert mocker.mock_sent_data.endswith(non_ascii_byte_data)
    else:
        assert partial_ascii_byte_data not in mocker.mock_sent_data


@pytest.mark.parametrize("url", (
    "sudo://make-me-a-sammich",
    "http://my little URL",
    "https://my little URL",
    "xxx://my little URL",
    "xxx:my little URL",
    "xxx:"))
def test_urlopener_default(url, monkeypatch):
    """HttpTransport builds a new urlopener if not given an external one."""
    my_request = suds.transport.Request(url, u"Rumpelstiltskin")
    def mock_build_urlopener(*handlers):
        assert len(handlers) == 1
        assert handlers[0].__class__ is urllib2.ProxyHandler
        raise MyException
    monkeypatch.setattr(urllib_request, "build_opener", mock_build_urlopener)
    transport = suds.transport.http.HttpTransport()
    assert transport.urlopener is None
    pytest.raises(MyException, transport.open, my_request)
    pytest.raises(MyException, transport.send, my_request)


@pytest.mark.parametrize("url", (
    "sudo://make-me-a-sammich",
    "http://my little URL",
    "https://my little URL",
    "xxx://my little URL",
    "xxx:my little URL",
    "xxx:"))
def test_urlopener_indirection(url, monkeypatch):
    """
    HttpTransport may be configured with an external urlopener.

    In that case, a new urlopener is not built and the given urlopener is used
    as-is, without adding any extra handlers to it.

    """
    my_request = suds.transport.Request(url, u"Rumpelstiltskin")
    class MockURLOpener:
        def open(self, urllib_request, timeout=None):
            assert urllib_request.__class__ is urllib2.Request
            assert urllib_request.get_full_url() == url
            raise MyException
    def mock_build_urlopener(*args, **kwargs):
        pytest.fail("urllib2.build_opener() called when not expected.")
    monkeypatch.setattr(urllib_request, "build_opener", mock_build_urlopener)
    transport = suds.transport.http.HttpTransport()
    transport.urlopener = MockURLOpener()
    pytest.raises(MyException, transport.open, my_request)
    pytest.raises(MyException, transport.send, my_request)


def _encode_basic_credentials(username, password):
    """
    Encode user credentials as used in basic HTTP authentication.

    This is the value expected to be added to the 'Authorization' HTTP header.

    """
    data = suds.byte_str("%s:%s" % (username, password))
    return "Basic %s" % base64.b64encode(data).decode("utf-8")
