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
Suds library HTTP transport related unit tests.

Implemented using the 'pytest' testing framework.

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
import suds.transport.http

import base64


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


def _encode_basic_credentials(username, password):
    """
      Encodes user credentials as used in basic HTTP authentication.

      This is the value expected to be added to the 'Authorization' HTTP
    header.

    """
    data = suds.byte_str('%s:%s' % (username, password))
    return "Basic %s" % base64.b64encode(data).decode('utf-8')


def _check_Authorization_header(request, username, password):
    assert len(request.headers) == 1
    assert request.headers['Authorization'] == _encode_basic_credentials(
        username, password)
