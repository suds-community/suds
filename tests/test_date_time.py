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
# written by: Jeff Ortel ( jortel@redhat.com )

"""
Date & time related suds Python library unit tests.

Implemented using the 'pytest' testing framework.

"""

if __name__ == "__main__":
    import testutils
    testutils.run_using_pytest(globals())

from suds.sax.date import (FixedOffsetTimezone, Date, DateTime, Time,
    UtcTimezone)

import pytest

import datetime


class _Dummy:
    """Class for testing unknown object class handling."""
    pass


"""Invalid date strings reused for both date & datetime testing."""
_invalid_date_strings = (
    "",
    "abla",
    "12",
    "12-01",
    "-12-01",
    "1900-01",
    "+1900-10-01",  # Plus sign not allowed.
    "1900-13-01",  # Invalid month.
    "1900-02-30",  # Invalid day.
    "2001-02-29",  # Not a leap year.
    "2100-02-29",  # Not a leap year.
    " 1900-01-01",
    "1900- 01-01",
    "1900-01 -01",
    "1900-01-01 ",
    "1900-13-011",
    "1900-01-01X",
    "1900-01-01T",  # 'T' is a date/time separator for DateTime.
    # Invalid time zone indicators.
        "1900-01-01 +17:00",
        "1900-01-01+ 17:00",
        "1900-01-01*17:00",
        "1900-01-01 17:00",
        "1900-01-01+17:",
        "1900-01-01+170",
        "1900-01-01+1730",
        "1900-01-01+170:00",
        "1900-01-01+17:00:00",
        "1900-01-01-:4",
        "1900-01-01-2a:00",
        "1900-01-01-222:00",
        "1900-01-01-12:000"
        "1900-01-01+00:60",
        "1900-01-01-00:99")

"""Invalid date strings reused for both time & datetime testing."""
_invalid_time_strings = (
    "",
    "bunga",
    "12",
    "::",
    "12:",
    "12:01",
    "12:01:",
    "12:01: 00",
    "12:01:  00",
    "23: 01:00",
    " 23:01:00",
    "23 :01:00",
    "23::00",
    "23:000:00",
    "023:00:00",
    "23:00:000",
    "25:01:00",
    "-1:01:00",
    "24:01:00",
    "23:-1:00",
    "23:61:00",
    "23:60:00",
    "23:59:-1",
    "23:59:61",
    "23:59:60",
    "7.59.13",
    "7-59-13",
    "-0:01:00",
    "23:-0:00",
    "23:59:-0",
    "23:59:6.a",
    "23:59:6.",
    "23:59:6:0",
    "23:59:6.12x",
    "23:59:6.12x45",
    "23:59:6.999999 ",
    "23:59:6.999999x",
    "T23:59:6",
    # Invalid time zone indicators.
        "13:27:04 -10:00",
        "13:27:04- 10:00",
        "13:27:04*17:00",
        "13:27:04 17:00",
        "13:27:04-003",
        "13:27:04-003:00",
        "13:27:04+00:002",
        "13:27:04-13:60",
        "13:27:04-121",
        "13:27:04-1210",
        "13:27:04-121:00",
        "13:27:04+12:",
        "13:27:04+12:00:00",
        "13:27:04-:13"
        "13:27:04-24:00"
        "13:27:04+99:00")


class TestDate:
    """Tests for the suds.sax.date.Date class."""

    def testConstructFromDate(self):
        date = datetime.date(2001, 12, 10)
        assert Date(date).value is date

    def testConstructFromDateTime_naive(self):
        date = datetime.datetime(2001, 12, 10, 10, 50, 21, 32132)
        assert Date(date).value == datetime.date(2001, 12, 10)

    @pytest.mark.parametrize("hours", (5, 20))
    def testConstructFromDateTime_tzAware(self, hours):
        tz = FixedOffsetTimezone(10)
        date = datetime.datetime(2001, 12, 10, hours, 50, 21, 32132, tzinfo=tz)
        assert Date(date).value == datetime.date(2001, 12, 10)

    @pytest.mark.parametrize(("string", "y", "m", "d"), (
        ("1900-01-01", 1900, 1, 1),
        ("1900-1-1", 1900, 1, 1),
        ("1900-01-01z", 1900, 1, 1),
        ("1900-01-01Z", 1900, 1, 1),
        ("1900-01-01-02", 1900, 1, 1),
        ("1900-01-01+2", 1900, 1, 1),
        ("1900-01-01+02:00", 1900, 1, 1),
        ("1900-01-01+99:59", 1900, 1, 1),
        ("1900-01-01-21:13", 1900, 1, 1),
        ("2000-02-29", 2000, 2, 29)))  # Leap year.
    def testConstructFromString(self, string, y, m, d):
        assert Date(string).value == datetime.date(y, m, d)

    @pytest.mark.parametrize("string", _invalid_date_strings)
    def testConstructFromString_failure(self, string):
        pytest.raises(ValueError, Date, string)

    @pytest.mark.parametrize("source", (
        None,
        object(),
        _Dummy(),
        datetime.time(10, 10)))
    def testConstructFromUnknown(self, source):
        pytest.raises(ValueError, Date, source)

    @pytest.mark.parametrize(("input", "output"), (
        ("1900-01-01", "1900-01-01"),
        ("2000-02-29", "2000-02-29"),
        ("1900-1-1", "1900-01-01"),
        ("1900-01-01z", "1900-01-01"),
        ("1900-01-01Z", "1900-01-01"),
        ("1900-01-01-02", "1900-01-01"),
        ("1900-01-01+2", "1900-01-01"),
        ("1900-01-01+02:00", "1900-01-01"),
        ("1900-01-01+99:59", "1900-01-01"),
        ("1900-01-01-21:13", "1900-01-01")))
    def testConvertToString(self, input, output):
        assert str(Date(input)) == output


class TestDateTime:
    """Tests for the suds.sax.date.DateTime class."""

    def testConstructFromDateTime(self):
        dt = datetime.datetime(2001, 12, 10, 1, 1)
        assert DateTime(dt).value is dt
        dt.replace(tzinfo=UtcTimezone())
        assert DateTime(dt).value is dt

    @pytest.mark.parametrize(
        ("string", "y", "M", "d", "h", "m", "s", "micros"), (
        ("2013-11-19T14:05:23.428068", 2013, 11, 19, 14, 5, 23, 428068),
        ("2013-11-19 14:05:23.4280", 2013, 11, 19, 14, 5, 23, 428000)))
    def testConstructFromString(self, string, y, M, d, h, m, s, micros):
        assert DateTime(string).value == datetime.datetime(y, M, d, h, m, s,
            micros)

    @pytest.mark.parametrize("string",
        [x + "T00:00:00" for x in _invalid_date_strings] +
        ["2000-12-31T" + x for x in _invalid_time_strings] + [
        # Invalid date/time separator characters.
            "2013-11-1914:05:23.428068",
            "2013-11-19X14:05:23.428068"])
    def testConstructFromString_failure(self, string):
        pytest.raises(ValueError, DateTime, string)

    @pytest.mark.parametrize(
        ("string", "y", "M", "d", "h", "m", "s", "micros"), (
        ("2000-2-28T23:59:59.9999995", 2000, 2, 29, 0, 0, 0, 0),
        ("2000-2-29T23:59:59.9999995", 2000, 3, 1, 0, 0, 0, 0),
        ("2013-12-31T23:59:59.9999994", 2013, 12, 31, 23, 59, 59, 999999),
        ("2013-12-31T23:59:59.99999949", 2013, 12, 31, 23, 59, 59, 999999),
        ("2013-12-31T23:59:59.9999995", 2014, 1, 1, 0, 0, 0, 0)))
    def testConstructFromString_subsecondRounding(self, string, y, M, d, h, m,
            s, micros):
        ref = datetime.datetime(y, M, d, h, m, s, micros)
        assert DateTime(string).value == ref

    @pytest.mark.parametrize(
        ("string", "y", "M", "d", "h", "m", "s", "micros", "tz_h", "tz_m"), (
        ("2013-11-19T14:05:23.428068-3",
            2013, 11, 19, 14, 5, 23, 428068, -3, 0),
        ("2013-11-19T14:05:23.068+03",
            2013, 11, 19, 14, 5, 23, 68000, 3, 0),
        ("2013-11-19T14:05:23.428068-02:00",
            2013, 11, 19, 14, 5, 23, 428068, -2, 0),
        ("2013-11-19T14:05:23.428068+02:00",
            2013, 11, 19, 14, 5, 23, 428068, 2, 0),
        ("2013-11-19T14:05:23.428068-23:59",
            2013, 11, 19, 14, 5, 23, 428068, -23, -59)))
    def testConstructFromString_timezone(self, string, y, M, d, h, m, s,
            micros, tz_h, tz_m):
        tzdelta = datetime.timedelta(hours=tz_h, minutes=tz_m)
        tzinfo = FixedOffsetTimezone(tzdelta)
        ref = datetime.datetime(y, M, d, h, m, s, micros, tzinfo=tzinfo)
        assert DateTime(string).value == ref

    @pytest.mark.parametrize("source", (
        None,
        object(),
        _Dummy(),
        datetime.date(2010, 10, 27),
        datetime.time(10, 10)))
    def testConstructFromUnknown(self, source):
        pytest.raises(ValueError, DateTime, source)

    @pytest.mark.parametrize(("input", "output"), (
        ("2013-11-19T14:05:23.428068", "2013-11-19T14:05:23.428068"),
        ("2013-11-19 14:05:23.4280", "2013-11-19T14:05:23.428000"),
        ("2013-12-31T23:59:59.9999995", "2014-01-01T00:00:00"),
        ("2013-11-19T14:05:23.428068-3", "2013-11-19T14:05:23.428068-03:00"),
        ("2013-11-19T14:05:23.068+03", "2013-11-19T14:05:23.068000+03:00"),
        ("2013-11-19T14:05:23.4-02:00", "2013-11-19T14:05:23.400000-02:00"),
        ("2013-11-19T14:05:23.410+02:00", "2013-11-19T14:05:23.410000+02:00"),
        ("2013-11-19T14:05:23.428-23:59", "2013-11-19T14:05:23.428000-23:59")))
    def testConvertToString(self, input, output):
        assert str(DateTime(input)) == output


class TestTime:
    """Tests for the suds.sax.date.Time class."""

    def testConstructFromTime(self):
        time = datetime.time(1, 1)
        assert Time(time).value is time
        time.replace(tzinfo=UtcTimezone())
        assert Time(time).value is time

    @pytest.mark.parametrize(("string", "h", "m", "s", "micros"), (
        ("10:59:47", 10, 59, 47, 0),
        ("9:9:13", 9, 9, 13, 0),
        ("18:0:09.2139", 18, 0, 9, 213900),
        ("18:0:09.02139", 18, 0, 9, 21390),
        ("18:0:09.002139", 18, 0, 9, 2139),
        ("0:00:00.00013", 0, 0, 0, 130),
        ("0:00:00.000001", 0, 0, 0, 1),
        ("0:00:00.000000", 0, 0, 0, 0),
        ("23:59:6.999999", 23, 59, 6, 999999),
        ("1:13:50.0", 1, 13, 50, 0)))
    def testConstructFromString(self, string, h, m, s, micros):
        assert Time(string).value == datetime.time(h, m, s, micros)

    @pytest.mark.parametrize("string", _invalid_time_strings)
    def testConstructFromString_failure(self, string):
        pytest.raises(ValueError, Time, string)

    @pytest.mark.parametrize(("string", "h", "m", "s", "micros"), (
        ("0:0:0.0000000", 0, 0, 0, 0),
        ("0:0:0.0000001", 0, 0, 0, 0),
        ("0:0:0.0000004", 0, 0, 0, 0),
        ("0:0:0.0000005", 0, 0, 0, 1),
        ("0:0:0.0000006", 0, 0, 0, 1),
        ("0:0:0.0000009", 0, 0, 0, 1),
        ("0:0:0.5", 0, 0, 0, 500000),
        ("0:0:0.5000004", 0, 0, 0, 500000),
        ("0:0:0.5000005", 0, 0, 0, 500001),
        ("0:0:0.50000050", 0, 0, 0, 500001),
        ("0:0:0.50000051", 0, 0, 0, 500001),
        ("0:0:0.50000055", 0, 0, 0, 500001),
        ("0:0:0.50000059", 0, 0, 0, 500001),
        ("0:0:0.5000006", 0, 0, 0, 500001),
        ("0:0:0.9999990", 0, 0, 0, 999999),
        ("0:0:0.9999991", 0, 0, 0, 999999),
        ("0:0:0.9999994", 0, 0, 0, 999999),
        ("0:0:0.99999949", 0, 0, 0, 999999),
        ("0:0:0.9999995", 0, 0, 1, 0),
        ("0:0:0.9999996", 0, 0, 1, 0),
        ("0:0:0.9999999", 0, 0, 1, 0)))
    def testConstructFromString_subsecondRounding(self, string, h, m, s,
            micros):
        assert Time(string).value == datetime.time(h, m, s, micros)

    @pytest.mark.parametrize(
        ("string", "h", "m", "s", "micros", "tz_h", "tz_m"), (
        ("18:0:09.2139z", 18, 0, 9, 213900, 0, 0),
        ("18:0:09.2139Z", 18, 0, 9, 213900, 0, 0),
        ("18:0:09.2139+3", 18, 0, 9, 213900, 3, 0),
        ("18:0:09.2139-3", 18, 0, 9, 213900, -3, 0),
        ("18:0:09.2139-03", 18, 0, 9, 213900, -3, 0),
        ("18:0:09.2139+9:3", 18, 0, 9, 213900, 9, 3),
        ("18:0:09.2139+10:31", 18, 0, 9, 213900, 10, 31),
        ("18:0:09.2139-10:31", 18, 0, 9, 213900, -10, -31)))
    def testConstructFromString_timezone(self, string, h, m, s, micros, tz_h,
            tz_m):
        tzdelta = datetime.timedelta(hours=tz_h, minutes=tz_m)
        tzinfo = FixedOffsetTimezone(tzdelta)
        ref = datetime.time(h, m, s, micros, tzinfo=tzinfo)
        assert Time(string).value == ref

    @pytest.mark.parametrize("source", (
        None,
        object(),
        _Dummy(),
        datetime.date(2010, 10, 27),
        datetime.datetime(2010, 10, 27, 10, 10)))
    def testConstructFromUnknown(self, source):
        pytest.raises(ValueError, Time, source)

    @pytest.mark.parametrize(("input", "output"), (
        ("14:05:23.428068", "14:05:23.428068"),
        ("14:05:23.4280", "14:05:23.428000"),
        ("23:59:59.9999995", "00:00:00"),
        ("14:05:23.428068-3", "14:05:23.428068-03:00"),
        ("14:05:23.068+03", "14:05:23.068000+03:00"),
        ("14:05:23.4-02:00", "14:05:23.400000-02:00"),
        ("14:05:23.410+02:00", "14:05:23.410000+02:00"),
        ("14:05:23.428-23:59", "14:05:23.428000-23:59")))
    def testConvertToString(self, input, output):
        assert str(Time(input)) == output
