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
Suds library transport related unit tests.

Implemented using the 'pytest' testing framework.

"""

if __name__ == "__main__":
    import __init__
    __init__.runUsingPyTest(globals())


import suds
from suds.transport import Reply, Request

import pytest

import sys


@pytest.mark.parametrize("message", (
    u"",
    u"for a bitch it's haaaard...",
    u"I'm here to kick ass,\nand chew bubble gum...\nand I'm all out of gum.",
    u"šuć-muć pa ožeži.. za 100 €\n\nwith multiple\nlines...",
    u"\n\n\n\n\n\n",
    u"中原千军逐蒋"))
def test_reply_as_string(message):
    code = 17
    reply = Reply(code, {"aaa":1}, message)
    expected = u"""\
CODE: %s
HEADERS: %s
MESSAGE:
%s""" % (code, reply.headers, message)
    assert unicode(reply) == expected
    if sys.version_info < (3, 0):
        assert str(reply) == expected.encode("utf-8")


@pytest.mark.parametrize(("code", "headers", "message"), (
    (1, {}, "ola"),
    (2, {"semper":"fi"}, u"中原千军逐蒋\n城楼万众检阅")))
def test_reply_constructor(code, headers, message):
    reply = Reply(code, headers, message)
    assert reply.code == code
    assert reply.headers == headers
    assert reply.message == message


@pytest.mark.parametrize("message", (
    u"",
    u"for a bitch it's haaaard...",
    u"I'm here to kick ass,\nand chew bubble gum...\nand I'm all out of gum.",
    u"šuć-muć pa ožeži.. za 100 €\n\nwith multiple\nlines...",
    u"\n\n\n\n\n\n",
    u"中原千军逐蒋"))
def test_request_as_string(message):
    request = Request("my url", message)
    request.headers["aaa"] = 1
    expected = u"""\
URL: my url
HEADERS: %s
MESSAGE:
%s""" % (request.headers, message)
    assert unicode(request) == expected
    if sys.version_info < (3, 0):
        assert str(request) == expected.encode("utf-8")


@pytest.mark.parametrize(("url", "message"), (
    ("for a bitch it's haaaard...", "it's hard out here..."),
    (u"中原千军逐蒋", u"城楼万众检阅")))
def test_request_constructor(url, message):
    request = Request(url, message)
    assert request.url == url
    assert request.message == message
    assert request.headers == {}


def test_request_without_message():
    request = Request("for a bitch it's haaaard...")
    assert request.url == "for a bitch it's haaaard..."
    assert request.message is None
    assert request.headers == {}
