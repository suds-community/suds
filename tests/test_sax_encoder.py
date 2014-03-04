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
Suds SAX module's special character encoder unit tests.

Implemented using the 'pytest' testing framework.

"""

if __name__ == "__main__":
    import __init__
    __init__.run_using_pytest(globals())


import suds.sax.enc

import pytest


"""Data not affected by encode()/decode() operations."""
invariant_decoded_encoded_test_data = (
    # Empty text.
    "",
    # Pure text.
    "x",
    "xyz",
    "Devil take the hindmost",
    # Whitespace handling.
    "spaces    kept",
    " ",
    "  ",
    "\t",
    "\v",
    "\f",
    "\r",
    "\n",
    "  \t\t\v\v   \f\f  \v\v\f\r\n\n\r  \t \t\t",
    "  \t\f\v   something   \r\r\n\freal\f\f\r\n\f\t\f")

"""
Decoded/encoded data convertible in either direction using encode()/decode()
operations.

"""
symmetric_decoded_encoded_test_data = [
    # Simple replacements.
    ("<", "&lt;"),
    (">", "&gt;"),
    ("'", "&apos;"),
    ('"', "&quot;"),
    ("&", "&amp;"),
    # Mixed replacements.
    ("abcd&&<<", "abcd&amp;&amp;&lt;&lt;"),
    # Character reference lookalikes.
    ("& lt;", "&amp; lt;"),
    ("&gt ;", "&amp;gt ;"),
    ("&a pos;", "&amp;a pos;"),
    ("&walle;", "&amp;walle;"),
    ("&quot", "&amp;quot"),
    ("&quo", "&amp;quo"),
    ("amp;", "amp;"),
    # XML markup.
    ("<a>unga-bunga</a>", "&lt;a&gt;unga-bunga&lt;/a&gt;"),
    ("<a></b>", "&lt;a&gt;&lt;/b&gt;"),
    ("<&></\n>", "&lt;&amp;&gt;&lt;/\n&gt;"),
    ("<a id=\"fluffy's\"> && </a>",
        "&lt;a id=&quot;fluffy&apos;s&quot;&gt; &amp;&amp; &lt;/a&gt;")] + [
    # Invarant data.
    (x, x) for x in invariant_decoded_encoded_test_data]


@pytest.mark.parametrize(("input", "expected"), [
    (e, d) for d, e in symmetric_decoded_encoded_test_data] + [
    # Character reference lookalikes.
    (x, x) for x in (
        "& lt;",
        "&gt ;",
        "&a pos;",
        "&walle;",
        "&quot",
        "&quo",
        "amp;")] + [
    # Double decode.
    ("&amp;amp;", "&amp;"),
    ("&amp;lt;", "&lt;"),
    ("&amp;gt;", "&gt;"),
    ("&amp;apos;", "&apos;"),
    ("&amp;quot;", "&quot;")])
def test_decode(input, expected):
    assert suds.sax.enc.Encoder().decode(input) == expected


@pytest.mark.parametrize(("input", "expected"),
    symmetric_decoded_encoded_test_data + [
    # Double encoding.
    #TODO: See whether this 'avoid double encoding' behaviour is actually
    # desirable. That is how XML entity reference encoding has been implemented
    # in the original suds implementation, but it makes encode/decode
    # operations asymmetric and prevents the user from actually encoding data
    # like '&amp;' that should not be interpreted as '&'.
    ("&amp;", "&amp;"),
    ("&lt;", "&lt;"),
    ("&gt;", "&gt;"),
    ("&apos;", "&apos;"),
    ("&quot;", "&quot;")])
def test_encode(input, expected):
    assert suds.sax.enc.Encoder().encode(input) == expected
