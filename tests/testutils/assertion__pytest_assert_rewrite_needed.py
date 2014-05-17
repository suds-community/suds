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
Assertion test utility functions shared between multiple test modules.

Extracted into a separate module, named so pytest would apply its assertion
rewriting to it.

'pytest' assertion rewriting allows our assertion test utility functions to use
Python assertions and have them work even when run with Python assertions
disabled.

"""


def assert_no_output(pytest_capture_fixture):
    """
    Test utility asserting there was no captured stdout or stderr output.

    pytest_capture_fixture parameter may be one of pytest's output capture
    fixtures, e.g. capsys or capfd.

    """
    out, err = pytest_capture_fixture.readouterr()
    assert not out
    assert not err
