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

import testutils
if __name__ == "__main__":
    testutils.run_using_pytest(globals())

import suds
import suds.transport
import suds.transport.http

import pytest
from six import u
from six.moves import http_client
from six.moves.urllib.error import HTTPError
from six.moves.urllib.request import ProxyHandler

import base64
import re
import sys
from email.message import Message

# We can not use six.moves modules for this since we want to monkey-patch the
# exact underlying urllib2/urllib.request module in our tests and not just
# their six.moves proxy module.
if sys.version_info < (3,):
    import urllib2 as urllib_request
else:
    import urllib.request as urllib_request


class MustNotBeCalled(Exception):
    """Local exception used in this test module."""
    pass


class MyException(Exception):
    """Local exception used in this test module."""
    pass


class Undefined:
    """Internal tag class indicating undefined function call parameters."""
    pass


class CountedMock(object):
    """
    Base mock object class supporting generic attribute access counting.

    Ignores attributes whose name starts with 'mock_' or '__mock_' or their
    transformed variant '_<className>__mock_'.

    Derived classes must call this class's __init__() or mock_reset() methods
    during their initialization, but both calls are not needed. Before this
    initialization, all counters will be reported as None.

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


class MockFP:
    """
    Mock FP 'File object' as stored inside Python's HTTPError exception.

    Must have several 'File object' methods defined on it as Python's HTTPError
    implementation expects them and stores references to them internally, at
    least with Python 2.4.

    """

    def read():
        raise MustNotBeCalled

    def readline():
        raise MustNotBeCalled

    def close(self):
        pass


class MockURLOpenerSaboteur:
    """
    Mock URLOpener raising an exception in its open() method.

    If no open_exception is given in its initializer, simply marks the current
    test as a failure if its open() method is called. Otherwise raises the
    given exception from that call.

    """

    def __init__(self, open_exception=None):
        self.__open_exception = open_exception
        self.args = None

    def open(self, *args, **kwargs):
        self.args = args
        if self.__open_exception:
            raise self.__open_exception
        pytest.fail("urllib urlopener.open() must not be called.")


class SendMethodFixture:
    """
    Instances of this class get returned by the send_method test fixture.

    Each instance is connected to a specific suds.transport.http.HttpTransport
    request sending method and may be used to call that method on a specific
    suds.transport.http.HttpTransport instance.

    """

    def __init__(self, name):
        self.name = name

    def __call__(self, transport, *args, **kwargs):
        assert isinstance(transport, suds.transport.http.HttpTransport)
        return getattr(transport, self.name)(*args, **kwargs)


# Test URL data used by several tests in this test module.
test_URL_data = (
    "sudo://make-me-a-sammich",
    "http://my little URL",
    "https://my little URL",
    "xxx://my little URL",
    "xxx:my little URL",
    "xxx:")


def assert_default_transport(transport):
    """Test utility verifying default constructed transport content."""
    assert isinstance(transport, suds.transport.http.HttpTransport)
    assert transport.urlopener is None


def create_request(url="protocol://default-url", data=u("Rumpelstiltskin")):
    """Test utility constructing a suds.transport.Request instance."""
    return suds.transport.Request(url, data)


@pytest.fixture(params=["open", "send"])
def send_method(request):
    """
    pytest testing framework based test fixture causing tests using that
    fixture to be called for each suds.transport.http.HttpTransport request
    sending method.

    """
    return SendMethodFixture(request.param)


@pytest.mark.parametrize("input", (
    dict(),
    dict(password="Humpty"),
    dict(username="Dumpty"),
    dict(username="Habul Afufa", password="preCious"),
    # Regression test: Extremely long username & password combinations must not
    # cause suds to add additional newlines in the constructed 'Authorization'
    # HTTP header.
    dict(username="An Extremely Long Username that could be usable only to "
        "Extremely Important People whilst on Extremely Important Missions.",
        password="An Extremely Long Password that could be usable only to "
        "Extremely Important People whilst on Extremely Important Missions. "
        "And some extra 'funny' characters to improve security: "
        "!@#$%^&*():|}|{{.\nEven\nSome\nNewLines\n"
        "  and spaces at the start of a new line.   ")))
def test_authenticated_http_add_credentials_to_request(input):
    class MockRequest:
        def __init__(self):
            self.headers = {}

    def assert_Authorization_header(request, username, password):
        if username is None or password is None:
            assert len(request.headers) == 0
        else:
            assert len(request.headers) == 1
            header = request.headers["Authorization"]
            assert header == _encode_basic_credentials(username, password)

    username = input.get("username", None)
    password = input.get("password", None)
    t = suds.transport.http.HttpAuthenticated(**input)
    r = MockRequest()
    t.addcredentials(r)
    assert_Authorization_header(r, username, password)


@pytest.mark.parametrize("input", (
    dict(password="riff raff..!@#"),
    dict(username="macro"),
    dict(username="Hab AfuFa", password="preCious")))
def test_construct_authenticated_http(input):
    expected_username = input.get("username", None)
    expected_password = input.get("password", None)
    transport = suds.transport.http.HttpAuthenticated(**input)
    assert transport.credentials() == (expected_username, expected_password)
    assert_default_transport(transport)


def test_request_headers_are_passed_to_urllib_when_opening_a_request():
    class MockRequest(object):
        url = "http://somewhere.far"
        headers = {'Key': 'value'}

    mock_request = MockRequest()

    transport = suds.transport.http.HttpTransport()
    transport.urlopener = MockURLOpenerSaboteur(MyException)

    pytest.raises(MyException, suds.transport.http.HttpTransport.open, transport, mock_request)

    assert transport.urlopener.args[0].headers == mock_request.headers


def test_construct_http():
    transport = suds.transport.http.HttpTransport()
    assert_default_transport(transport)


def test_sending_using_network_sockets(send_method, monkeypatch):
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
        def close(self):
            pass
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
        def setsockopt(self, *args, **kwargs):
            pass

    class MockSocketReader(CountedMock):
        def __init__(self):
            super(MockSocketReader, self).__init__()
        def readline(self, *args, **kwargs):
            raise MyException
        def close(self):
            pass
        def flush(self):
            pass

    # Setup.
    host = "an-easily-recognizable-host-name-214894932"
    port = 9999
    host_port = "%s:%s" % (host, port)
    url_relative = "svc"
    url = "http://%s/%s" % (host_port, url_relative)
    partial_ascii_byte_data = suds.byte_str("Muka-laka-hiki")
    non_ascii_byte_data = u("\u0414\u043C\u0438 \u0442\u0440").encode("utf-8")
    non_ascii_byte_data += partial_ascii_byte_data
    mocker = Mocker(host, port)
    monkeypatch.setattr("socket.getaddrinfo", mocker.getaddrinfo)
    monkeypatch.setattr("socket.socket", mocker.socket)
    request = suds.transport.Request(url, non_ascii_byte_data)
    transport = suds.transport.http.HttpTransport()
    expected_sent_data_start, expected_request_data_send = {
        "open": ("GET", False),
        "send": ("POST", True)}[send_method.name]

    # Execute.
    pytest.raises(MyException, send_method, transport, request)

    # Verify.
    assert mocker.mock_call_count("getaddrinfo") == 1
    assert mocker.mock_call_count("socket") == 1
    assert mocker.mock_socket.mock_call_count("connect") == 1
    assert mocker.mock_socket.mock_call_count("makefile") == 1
    # With older Python versions, e.g. Python 2.4, urllib implementation calls
    # Socket's sendall() method twice - once for sending the HTTP request
    # headers and once for its body.
    assert mocker.mock_socket.mock_call_count("sendall") in (1, 2)
    # Python versions prior to 3.4.2 do not explicitly close their HTTP server
    # connection socket in case of our custom exceptions, e.g. version 3.4.1.
    # closes it only on OSError exceptions.
    assert mocker.mock_socket.mock_call_count("close") in (0, 1)
    # With older Python versions, e.g. Python 2.4, Socket class does not
    # implement the settimeout() method.
    assert mocker.mock_socket.mock_call_count("settimeout") in (0, 1)
    assert mocker.mock_socket.mock_reader.mock_call_count("readline") == 1
    assert mocker.mock_sent_data.__class__ is suds.byte_str_class
    expected_sent_data_start = "%s /%s HTTP/1.1\r\n" % (
        expected_sent_data_start, url_relative)
    expected_sent_data_start = suds.byte_str(expected_sent_data_start)
    assert mocker.mock_sent_data.startswith(expected_sent_data_start)
    assert host_port.encode("utf-8") in mocker.mock_sent_data
    if expected_request_data_send:
        assert mocker.mock_sent_data.endswith(non_ascii_byte_data)
    else:
        assert partial_ascii_byte_data not in mocker.mock_sent_data


class TestSendingToURLWithAMissingProtocolIdentifier:
    """
    Test suds reporting URLs with a missing protocol identifier.

    Python urllib library makes this check under Python 3.x, but not under
    earlier Python versions.

    """

    # We can not set this 'url' fixture data using a class decorator since that
    # Python feature has been introduced in Python 2.6 and we need to keep this
    # code backward compatible with Python 2.4.
    invalid_URL_parametrization = pytest.mark.parametrize("url", (
        "my no-protocol URL",
        ":my no-protocol URL"))

    @pytest.mark.skipif(sys.version_info >= (3,), reason="Python 2 specific")
    @invalid_URL_parametrization
    def test_python2(self, url, send_method):
        transport = suds.transport.http.HttpTransport()
        transport.urlopener = MockURLOpenerSaboteur(MyException)
        request = create_request(url)
        pytest.raises(MyException, send_method, transport, request)

    @pytest.mark.skipif(sys.version_info < (3,), reason="Python 3+ specific")
    @invalid_URL_parametrization
    def test_python3(self, url, send_method, monkeypatch):
        monkeypatch.delitem(locals(), "e", False)
        transport = suds.transport.http.HttpTransport()
        transport.urlopener = MockURLOpenerSaboteur()
        request = create_request(url)
        e = pytest.raises(ValueError, send_method, transport, request)
        try:
            assert "unknown url type" in str(e.value)
        finally:
            del e  # explicitly break circular reference chain in Python 3


class TestURLOpenerUsage:
    """
    Test demonstrating how suds.transport.http.HttpTransport makes use of the
    urllib library to perform the actual network transfers.

    The main contact point with the urllib library are its OpenerDirector
    objects we refer to as 'urlopener'.

    """

    @staticmethod
    def create_HTTPError(url=Undefined, code=Undefined, msg=Undefined,
            hdrs=Undefined, fp=None):
        """
        Test utility method constructing a HTTPError instance. Allows callers
        to construct a HTTPError instance using input data they are interested
        in, with some built-in default values used for any input data they are
        not interested in.

        """
        if url is Undefined:
            url = object()
        if code is Undefined:
            code = object()
        if msg is Undefined:
            msg = object()
        if hdrs is Undefined:
            hdrs = object()
        return HTTPError(url=url, code=code, msg=msg, hdrs=hdrs, fp=fp)

    @pytest.mark.parametrize("status_code", (
        http_client.ACCEPTED,
        http_client.NO_CONTENT,
        http_client.RESET_CONTENT,
        http_client.MOVED_PERMANENTLY,
        http_client.BAD_REQUEST,
        http_client.PAYMENT_REQUIRED,
        http_client.FORBIDDEN,
        http_client.NOT_FOUND,
        http_client.INTERNAL_SERVER_ERROR,
        http_client.NOT_IMPLEMENTED,
        http_client.HTTP_VERSION_NOT_SUPPORTED))
    def test_open_propagating_HTTPError_exceptions(self, status_code,
            monkeypatch):
        """
        HttpTransport open() operation should transform HTTPError urlopener
        exceptions to suds.transport.TransportError exceptions.

        """
        # Setup.
        monkeypatch.delattr(locals(), "e", False)
        fp = MockFP()
        e_original = self.create_HTTPError(code=status_code, fp=fp)
        t = suds.transport.http.HttpTransport()
        t.urlopener = MockURLOpenerSaboteur(open_exception=e_original)
        request = create_request()

        # Execute.
        e = pytest.raises(suds.transport.TransportError, t.open, request).value
        try:
            # Verify.
            assert e.args == (str(e_original),)
            assert e.httpcode is status_code
            assert e.fp is fp
        finally:
            del e  # explicitly break circular reference chain in Python 3

    @pytest.mark.xfail(reason="original suds library bug")
    @pytest.mark.parametrize("status_code", (
        http_client.ACCEPTED,
        http_client.NO_CONTENT))
    def test_operation_invoke_with_urlopen_accept_no_content__data(self,
            status_code):
        """
        suds.client.Client web service operation invocation expecting output
        data, and for which a corresponding urlopen call raises a HTTPError
        with status code ACCEPTED or NO_CONTENT, should report this as a
        TransportError.

        """
        e = self.create_HTTPError(code=status_code)
        transport = suds.transport.http.HttpTransport()
        transport.urlopener = MockURLOpenerSaboteur(open_exception=e)
        wsdl = testutils.wsdl('<xsd:element name="o" type="xsd:string"/>',
            output="o", operation_name="f")
        client = testutils.client_from_wsdl(wsdl, transport=transport)
        pytest.raises(suds.transport.TransportError, client.service.f)

    @pytest.mark.xfail(reason="original suds library bug")
    @pytest.mark.parametrize("status_code", (
        http_client.ACCEPTED,
        http_client.NO_CONTENT))
    def test_operation_invoke_with_urlopen_accept_no_content__no_data(self,
            status_code):
        """
        suds.client.Client web service operation invocation expecting no output
        data, and for which a corresponding urlopen call raises a HTTPError
        with status code ACCEPTED or NO_CONTENT, should treat this as a
        successful invocation.

        """
        # We are not yet sure that the behaviour checked for in this test is
        # actually desired. The test is only an 'educated guess' prepared to
        # demonstrate a related problem in the original suds library
        # implementation. The original implementation is definitely buggy as
        # its web service operation invocation raises an AttributeError
        # exception by attempting to access a non-existing 'None.message'
        # attribute internally.
        e = self.create_HTTPError(code=status_code)
        transport = suds.transport.http.HttpTransport()
        transport.urlopener = MockURLOpenerSaboteur(open_exception=e)
        wsdl = testutils.wsdl('<xsd:element name="o" type="xsd:string"/>',
            output="o", operation_name="f")
        client = testutils.client_from_wsdl(wsdl, transport=transport)
        assert client.service.f() is None

    def test_propagating_non_HTTPError_exceptions(self, send_method):
        """
        HttpTransport data sending operations need to propagate non-HTTPError
        exceptions raised by the underlying urlopen call.

        """
        e = MyException()
        t = suds.transport.http.HttpTransport()
        t.urlopener = MockURLOpenerSaboteur(open_exception=e)
        assert pytest.raises(e.__class__, t.open, create_request()).value is e

    @pytest.mark.parametrize("status_code", (
        http_client.RESET_CONTENT,
        http_client.MOVED_PERMANENTLY,
        http_client.BAD_REQUEST,
        http_client.PAYMENT_REQUIRED,
        http_client.FORBIDDEN,
        http_client.NOT_FOUND,
        http_client.INTERNAL_SERVER_ERROR,
        http_client.NOT_IMPLEMENTED,
        http_client.HTTP_VERSION_NOT_SUPPORTED))
    def test_send_transforming_HTTPError_exceptions(self, status_code,
            monkeypatch):
        """
        HttpTransport send() operation should transform HTTPError urlopener
        exceptions with status codes other than ACCEPTED or NO_CONTENT to
        suds.transport.TransportError exceptions.

        """
        # Setup.
        monkeypatch.delattr(locals(), "e", False)
        msg = object()
        fp = MockFP()
        e_original = self.create_HTTPError(msg=msg, code=status_code, fp=fp)
        t = suds.transport.http.HttpTransport()
        t.urlopener = MockURLOpenerSaboteur(open_exception=e_original)
        request = create_request()

        # Execute.
        e = pytest.raises(suds.transport.TransportError, t.send, request).value
        try:
            # Verify.
            assert len(e.args) == 1
            assert e.args[0] is e_original.msg
            assert e.httpcode is status_code
            assert e.fp is fp
        finally:
            del e  # explicitly break circular reference chain in Python 3

    @pytest.mark.parametrize("status_code", (
        http_client.ACCEPTED,
        http_client.NO_CONTENT))
    def test_send_transforming_HTTPError_exceptions__accepted_no_content(self,
            status_code):
        """
        HttpTransport send() operation should return None when their underlying
        urlopen operation raises a HTTPError exception with status code
        ACCEPTED or NO_CONTENT.

        """
        e_original = self.create_HTTPError(code=status_code)
        t = suds.transport.http.HttpTransport()
        t.urlopener = MockURLOpenerSaboteur(open_exception=e_original)
        assert t.send(create_request()) is None

    def test_specify_timeout(self):
        """
        HttpTransport send() operation should pass a Request timeout parameter
        to urllib
        """
        t = suds.transport.http.HttpTransport()
        request = create_request()
        request.timeout = 10

        # Python 2 compatible object
        class CompatibleHeaders(dict):
            dict = {}

        class MockResponse:
            def info(self):
                message = Message()
                # Python 2 compatible response
                message.getheaders = lambda k: {}
                return message

            @property
            def headers(self):
                return CompatibleHeaders()

            def read(self):
                return ''

        class MockURLOpener:
            def open(self, urllib_request, timeout=None):
                assert timeout == request.timeout
                return MockResponse()

        t.urlopener = MockURLOpener()
        t.send(request)


    @pytest.mark.parametrize("url", test_URL_data)
    def test_urlopener_default(self, url, send_method, monkeypatch):
        """
        HttpTransport builds a new urlopener if not given an external one.

        """
        def my_build_urlopener(*handlers):
            assert len(handlers) == 1
            assert handlers[0].__class__ is ProxyHandler
            raise MyException
        monkeypatch.setattr(urllib_request, "build_opener", my_build_urlopener)
        transport = suds.transport.http.HttpTransport()
        request = create_request(url=url)
        pytest.raises(MyException, send_method, transport, request)

    @pytest.mark.parametrize("url", test_URL_data)
    def test_urlopener_indirection(self, url, send_method, monkeypatch):
        """
        HttpTransport may be configured with an external urlopener.

        In that case, when opening or sending a HTTP request, a new urlopener
        is not built and the given urlopener is used as-is, without adding any
        extra handlers to it.

        """
        class MockURLOpener:
            def open(self, request, timeout=None):
                assert request.__class__ is urllib_request.Request
                assert request.get_full_url() == url
                raise MyException
        transport = suds.transport.http.HttpTransport()
        transport.urlopener = MockURLOpener()
        def my_build_urlopener(*args, **kwargs):
            pytest.fail("urllib build_opener() called when not expected.")
        monkeypatch.setattr(urllib_request, "build_opener", my_build_urlopener)
        request = create_request(url=url)
        pytest.raises(MyException, send_method, transport, request)


def _encode_basic_credentials(username, password):
    """
    Encode user credentials as used in basic HTTP authentication.

    This is the value expected to be added to the 'Authorization' HTTP header.

    """
    data = suds.byte_str("%s:%s" % (username, password))
    return "Basic %s" % base64.b64encode(data).decode("utf-8")
