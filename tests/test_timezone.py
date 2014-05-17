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
Unit tests for Timezone modeling classes implemented in suds.

Implemented using the 'pytest' testing framework.

"""

if __name__ == "__main__":
    import testutils
    testutils.run_using_pytest(globals())

from suds.sax.date import FixedOffsetTimezone, UtcTimezone

import pytest

import datetime


class TestFixedOffsetTimezone:
    """Tests for the suds.sax.date.FixedOffsetTimezone class."""

    @pytest.mark.parametrize(("h", "m", "name"), (
        (-13, 0, "-13:00"),
        (-5, 0, "-05:00"),
        (0, 0, "+00:00"),
        (5, 0, "+05:00"),
        (13, 0, "+13:00"),
        (5, 50, "+05:50"),
        (-4, 31, "-04:31")))
    def test(self, h, m, name):
        tz_delta = datetime.timedelta(hours=h, minutes=m)
        tz = FixedOffsetTimezone(tz_delta)
        assert tz.utcoffset(None) is tz_delta
        assert tz.dst(None) == datetime.timedelta(0)
        assert tz.tzname(None) == name
        assert str(tz) == "FixedOffsetTimezone " + name

    @pytest.mark.parametrize(("h", "m", "s", "us"), (
        (-22, 10, 1, 0),
        (-5, 0, 59, 0),
        (0, 0, 0, 1),
        (12, 12, 0, 120120),
        (12, 12, 0, 999999)))
    def testTooPreciseOffset(self, h, m, s, us):
        o = datetime.timedelta(hours=h, minutes=m, seconds=s, microseconds=us)
        pytest.raises(ValueError, FixedOffsetTimezone, o)

    @pytest.mark.parametrize("hours", (-5, 0, 5))
    def testConstructFromInteger(self, hours):
        tz = FixedOffsetTimezone(hours)
        assert tz.utcoffset(None) == datetime.timedelta(hours=hours)


class TestUtcTimezone:
    """Tests for the suds.sax.date.UtcTimezone class."""

    def test(self):
        tz = UtcTimezone()
        assert tz.utcoffset(None) == datetime.timedelta(0)
        assert tz.dst(None) == datetime.timedelta(0)
        assert tz.tzname(None) == "UTC"
        assert str(tz) == "UtcTimezone"
