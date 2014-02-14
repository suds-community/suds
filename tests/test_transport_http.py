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
import sys
import urllib2

if sys.version_info >= (3, 0):
    urllib_request = urllib.request
else:
    urllib_request = urllib2


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


def test_sending_non_ascii_data_to_unicode_URL(monkeypatch):
    """
    Regression test: Original suds HttpTransport implementation passed its
    request URL to the underlying httplib HTTP request object as-is, and since
    suds Client passes its target location URL to its HttpTransport as a
    unicode string, this was causing problems on Python implementations
    expecting a non-unicode URL in their httplib HTTP requests.

    Under Python 2.4 this was causing no problems as that implementation simply
    sends all the request data over the network as-is (and treats all unicode
    data as bytes internally anyway).

    Under Python 2.7 this was causing the httplib HTTP request implementation
    to convert all of its data to unicode, and do so by simply assuming that
    data contains only ASCII characters. If any other characters are
    encountered, it fails with an exception like "UnicodeDecodeError: 'ascii'
    codec can't decode byte 0xd0 in position 290: ordinal not in range(128)".

    Under Python 3.x the httplib HTTP request implementation automatically
    converts its received URL to a bytes object (assuming it contains only
    ASCII characters), thus avoiding the need to convert all the other request
    data.

    In order to trigger the problematic httplib behaviour we need to make suds
    attempt to send a HTTP request over the network. On the other hand, we want
    this test to work even on computers not connected to a network so we
    monkey-patch the underlying network socket APIs, log all the data suds
    attempts to send over the network and consider the test run successful once
    suds attempts to read back data from the network.

    """
    def call_once(f):
        """Method decorator making sure its function only gets called once."""
        def wrapper(self, *args, **kwargs):
            f_tag = "_%s__%s_called" % (self.__class__.__name__, f.__name__)
            assert not hasattr(self, f_tag)
            setattr(self, f_tag, True)
            return f(self, *args, **kwargs)
        return wrapper

    class Mocker:
        def __init__(self, expected_host, expected_port):
            self.expected_host = expected_host
            self.expected_port = expected_port
            self.sent_data = suds.byte_str()
            self.host_address = object()
        @call_once
        def getaddrinfo(self, host, port, *args, **kwargs):
            assert host == self.expected_host
            assert port == self.expected_port
            return [(None, None, None, None, self.host_address)]
        @call_once
        def socket(self, *args, **kwargs):
            self.socket = MockSocket(self)
            return self.socket

    class MockSocketReader:
        @call_once
        def readline(self, *args, **kwargs):
            raise MyException

    class MockSocket:
        def __init__(self, mocker):
            self.__mocker = mocker
        @call_once
        def connect(self, address):
            assert address is self.__mocker.host_address
        @call_once
        def makefile(self, *args, **kwargs):
            return MockSocketReader()
        def sendall(self, data):
            # Python 2.4 urllib implementation calls this function twice - once
            # for sending the HTTP request headers and once for its body.
            self.__mocker.sent_data += data
        @call_once
        def settimeout(self, *args, **kwargs):
            assert not hasattr(self, "settimeout_called")
            self.settimeout_called = True

    host = "an-easily-recognizable-host-name-214894932"
    port = 9999
    mocker = Mocker(host, port)
    monkeypatch.setattr("socket.getaddrinfo", mocker.getaddrinfo)
    monkeypatch.setattr("socket.socket", mocker.socket)
    host_port = "%s:%s" % (host, port)
    # It is important for this URL to be unicode in order to trigger the
    # problematic httplib behaviour described in the main test description.
    # Setting it to a simple byte-string avoids Python 2.7 httplib's unicode +
    # string concatenation causing the final sent data to be unicode. This
    # matches regular HttpTransport usage in suds as suds.client.Client always
    # passes its target location URL as a unicode value.
    unicode_URL = u"http://%s/svc" % (host_port,)
    non_ascii_byte_data = u"Дмитровский район".encode("utf-8")
    request = suds.transport.Request(unicode_URL, non_ascii_byte_data)
    transport = suds.transport.http.HttpTransport()
    pytest.raises(MyException, transport.send, request)
    assert mocker.sent_data.__class__ is suds.byte_str_class
    assert mocker.sent_data.endswith(non_ascii_byte_data)
    assert host_port.encode("utf-8") in mocker.sent_data


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


def test_sending_to_non_ascii_URL():
    """
    Suds should refuse to send HTTP requests with a target URL string
    containing non-ASCII characters. URLs are supposed to consist of ASCII
    characters only.

    """
    class MockURLOpener:
        def open(self, request, timeout=None):
            raise MyException
    transport = suds.transport.http.HttpTransport()
    transport.urlopener = MockURLOpener()
    unicode_URL = u"http://Дмитровский-район-152312306:9999/svc"
    request_data = "any data type will do here as we do not actually send it"
    request = suds.transport.Request(unicode_URL, request_data)
    pytest.raises(UnicodeEncodeError, transport.open, request)
    pytest.raises(UnicodeEncodeError, transport.send, request)


@pytest.mark.skipif(sys.version_info >= (3, 0),
    reason="Python 2 specific functionality")
@pytest.mark.parametrize(("url_string", "expected_exception"), (
    ("http://jorgula", MyException),
    ("http://jorgula_\xe7", UnicodeDecodeError)))
def test_sending_to_py2_bytes_URL(url_string, expected_exception):
    """
    Suds should accept single-byte string URL values under Python 2, but should
    still report an error if those strings contain any non-ASCII characters.

    """
    class MockURLOpener:
        def open(self, request, timeout=None):
            raise MyException
    transport = suds.transport.http.HttpTransport()
    transport.urlopener = MockURLOpener()
    request_data = u"any data type will do here as we do not actually send it"
    request = suds.transport.Request(suds.byte_str(url_string), request_data)
    pytest.raises(expected_exception, transport.open, request)
    pytest.raises(expected_exception, transport.send, request)


@pytest.mark.skipif(sys.version_info < (3, 0),
    reason="requires at least Python 3")
@pytest.mark.parametrize("url_string", (
    "http://jorgula",
    "http://jorgula_\xe7"))
@pytest.mark.parametrize("url_type_name", (
    "bytes",
    "bytearray"))
def test_sending_to_py3_bytes_URL(url_string, url_type_name):
    """
    Suds should refuse to send HTTP requests using target URL specified as
    either a Python 3 bytes or bytearray object.

    """
    class MockURLOpener:
        def open(self, request, timeout=None):
            raise MyException
    transport = suds.transport.http.HttpTransport()
    transport.urlopener = MockURLOpener()
    expected_exception = AssertionError
    if sys.flags.optimize:
        expected_exception = AttributeError
    import builtins
    url_type = getattr(builtins, url_type_name)
    url = url_type(url_string, encoding="utf-8")
    content = len("any data type will do here as we do not actually send it")
    request = suds.transport.Request(url, content)
    pytest.raises(expected_exception, transport.open, request)
    pytest.raises(expected_exception, transport.send, request)


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
