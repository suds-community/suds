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
# written by: Jeff Ortel ( jortel@redhat.com )

"""
Date & time related suds Python library unit tests.

Implemented using the 'pytest' testing framework.

"""

if __name__ == "__main__":
    try:
        import pytest
        pytest.main(["--pyargs", __file__])
    except ImportError:
        print("'py.test' unit testing framework not available. Can not run "
            "'{}' directly as a script.".format(__file__))
    import sys
    sys.exit(-2)


from suds.sax.date import Date, DateTime, Time, Timezone
from suds.xsd.sxbuiltin import XDate, XDateTime, XTime
import tests

import pytest

import datetime

tests.setup_logging()

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
        "1900-01-01-25:00",  # Invalid time zone indicator.
        "1900-01-01-24:00",  # Invalid time zone indicator.
        "1900-01-01+25:00",  # Invalid time zone indicator.
        "1900-01-01+24:00")  # Invalid time zone indicator.

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
        "T23:59:6")

class TestDate:
    """Tests for the suds.sax.date.Date class."""

    @pytest.mark.parametrize(("string", "y", "m", "d"), (
        ("1900-01-01", 1900, 1, 1),
        ("1900-1-1", 1900, 1, 1),
        ("1900-01-01z", 1900, 1, 1),
        ("1900-01-01Z", 1900, 1, 1),
        ("1900-01-01+02:00", 1900, 1, 1),
        ("1900-01-01-21:13", 1900, 1, 1),
        ("2000-02-29", 2000, 2, 29)))  # Leap year.
    def testStringToValue(self, string, y, m, d):
        assert Date(string).date == datetime.date(y, m, d)

    @pytest.mark.parametrize("string", _invalid_date_strings)
    def testStringToValue_failure(self, string):
        pytest.raises(ValueError, Date, string)


class TestDateTime:
    """Tests for the suds.sax.date.DateTime class."""

    @pytest.mark.parametrize(
        ("string", "y", "M", "d", "h", "m", "s", "micros"), (
        ("2013-11-19T14:05:23.428068", 2013, 11, 19, 14, 5, 23, 428068),
        ("2013-11-19 14:05:23.428068", 2013, 11, 19, 14, 5, 23, 428068),
        ("2013-11-19T14:05:23.428068-02:00", 2013, 11, 19, 14, 5, 23, 428068),
        ("2013-11-19T14:05:23.428068+02:00", 2013, 11, 19, 14, 5, 23, 428068)))
    def testStringToValue(self, string, y, M, d, h, m, s, micros):
        assert DateTime(string).datetime == datetime.datetime(y, M, d, h, m, s,
            micros)

    @pytest.mark.parametrize(
        ("string", "y", "M", "d", "h", "m", "s", "micros"), (
        ("2000-2-28T23:59:59.9999995", 2000, 2, 29, 0, 0, 0, 0),
        ("2000-2-29T23:59:59.9999995", 2000, 3, 1, 0, 0, 0, 0),
        ("2013-12-31T23:59:59.9999994", 2013, 12, 31, 23, 59, 59, 999999),
        ("2013-12-31T23:59:59.99999949", 2013, 12, 31, 23, 59, 59, 999999),
        ("2013-12-31T23:59:59.9999995", 2014, 1, 1, 0, 0, 0, 0)))
    def testStringToValue_subsecondRounding(self, string, y, M, d, h, m, s,
        micros):
        assert DateTime(string).datetime == datetime.datetime(y, M, d, h, m, s,
            micros)

    @pytest.mark.parametrize("string",
        [x + "T00:00:00" for x in _invalid_date_strings] +
        ["2000-12-31T" + x for x in _invalid_time_strings] + [
        "2013-11-19T14:05:23.428068-25:00",  # Invalid time zone indicator.
        "2013-11-19T14:05:23.428068-24:00",  # Invalid time zone indicator.
        "2013-11-19T14:05:23.428068+24:00",  # Invalid time zone indicator.
        "2013-11-19T14:05:23.428068+25:00"])  # Invalid time zone indicator.
    def testStringToValue_failure(self, string):
        pytest.raises(ValueError, Date, string)


class TestTime:
    """Tests for the suds.sax.date.Time class."""

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
        ("1:13:50.0", 1, 13, 50, 0),
        ("18:0:09.2139z", 18, 0, 9, 213900),
        ("18:0:09.2139Z", 18, 0, 9, 213900),
        ("18:0:09.2139+10:31", 18, 0, 9, 213900),
        ("18:0:09.2139-10:31", 18, 0, 9, 213900)))
    def testStringToValue(self, string, h, m, s, micros):
        assert Time(string).time == datetime.time(h, m, s, micros)

    @pytest.mark.parametrize(("string", "h", "m", "s", "micros"), (
        ("0:0:0.0000000", 0, 0, 0, 0),
        ("0:0:0.0000001", 0, 0, 0, 0),
        ("0:0:0.0000004", 0, 0, 0, 0),
        ("0:0:0.0000005", 0, 0, 0, 1),
        ("0:0:0.0000006", 0, 0, 0, 1),
        ("0:0:0.0000009", 0, 0, 0, 1),
        ("0:0:0.5", 0, 0, 0, 500000),
        ("0:0:0.5000004", 0, 0, 0, 500001),
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
    def testStringToValue_subsecondRounding(self, string, h, m, s, micros):
        assert Time(string).time == datetime.time(0, 0, 0, micros)

    @pytest.mark.parametrize("string", _invalid_time_strings)
    def testStringToValue_failure(self, string):
        pytest.raises(ValueError, Time, string)


class TestXDate:
    """Tests for the suds.xsd.sxbuiltin.XDate class."""

    def testSimple(self):
        ref = datetime.date(1941, 12, 7)
        s = "%.4d-%.2d-%.2d" % (ref.year, ref.month, ref.day)
        assert XDate.translate(s) == ref

    def testTimezoneNegative(self):
        self.__equalsTimezone(-6)

    def testTimezonePositive(self):
        self.__equalsTimezone(6)

    def testTranslateToString(self):
        translated = self.__toString(datetime.date(2013, 7, 24))
        assert isinstance(translated, str)
        assert translated == "2013-07-24"

    def testTranslateToString_datetime(self):
        translated = self.__toString(datetime.datetime(2013, 7, 24, 11, 59, 4))
        assert isinstance(translated, str)
        assert translated == "2013-07-24"

    def testTranslateToString_failed(self):
        dummy = _Dummy()
        assert self.__toString(dummy) is dummy
        time = datetime.time()
        assert self.__toString(time) is time

    def testUtcTimezone(self):
        Timezone.LOCAL = lambda tz: 0
        ref = datetime.date(1941, 12, 7)
        s = "%.4d-%.2d-%.2dZ" % (ref.year, ref.month, ref.day)
        assert XDate.translate(s) == ref

    @staticmethod
    def __toString(value):
        return XDate.translate(value, topython=False)

    @staticmethod
    def __equalsTimezone(tz):
        Timezone.LOCAL = lambda x: tz
        ref = datetime.date(1941, 12, 7)
        s = "%.4d-%.2d-%.2d%+.2d:00" % (ref.year, ref.month, ref.day, tz)
        assert XDate.translate(s) == ref


class TestXDateTime:
    """Tests for the suds.xsd.sxbuiltin.XDateTime class."""

    def testConvertNegativeToGreaterNegative(self):
        Timezone.LOCAL = lambda tz: -6
        ref = datetime.datetime(1941, 12, 7, 10, 30, 22)
        s = self.__strDateTime(ref.year, ref.month, ref.day, ref.hour,
            ref.minute, ref.second, -5)
        t = XDateTime.translate(s)
        assert ref.year == t.year
        assert ref.month == t.month
        assert ref.day == t.day
        assert ref.hour - 1 == t.hour
        assert ref.minute == t.minute
        assert ref.second == t.second

    def testConvertNegativeToGreaterNegativeAndPreviousDay(self):
        Timezone.LOCAL = lambda tz: -6
        ref = datetime.datetime(1941, 12, 7, 0, 30, 22)
        s = self.__strDateTime(ref.year, ref.month, ref.day, ref.hour,
            ref.minute, ref.second, -5)
        t = XDateTime.translate(s)
        assert ref.year == t.year
        assert ref.month == t.month
        assert 6 == t.day
        assert 23 == t.hour
        assert ref.minute == t.minute
        assert ref.second == t.second

    def testConvertNegativeToLesserNegative(self):
        Timezone.LOCAL = lambda tz: -5
        ref = datetime.datetime(1941, 12, 7, 10, 30, 22)
        s = self.__strDateTime(ref.year, ref.month, ref.day, ref.hour,
            ref.minute, ref.second, -6)
        t = XDateTime.translate(s)
        assert ref.year == t.year
        assert ref.month == t.month
        assert ref.day == t.day
        assert ref.hour + 1 == t.hour
        assert ref.minute == t.minute
        assert ref.second == t.second

    def testConvertNegativeToLesserNegativeAndNextDay(self):
        Timezone.LOCAL = lambda tz: -5
        ref = datetime.datetime(1941, 12, 7, 23, 30, 22)
        s = self.__strDateTime(ref.year, ref.month, ref.day, ref.hour,
            ref.minute, ref.second, -6)
        t = XDateTime.translate(s)
        assert ref.year == t.year
        assert ref.month == t.month
        assert 8 == t.day
        assert 0 == t.hour
        assert ref.minute == t.minute
        assert ref.second == t.second

    def testConvertNegativeToPositive(self):
        Timezone.LOCAL = lambda tz: 3
        ref = datetime.datetime(1941, 12, 7, 10, 30, 22)
        s = self.__strDateTime(ref.year, ref.month, ref.day, ref.hour,
            ref.minute, ref.second, -6)
        t = XDateTime.translate(s)
        assert ref.year == t.year
        assert ref.month == t.month
        assert ref.day == t.day
        assert ref.hour + 9 == t.hour
        assert ref.minute == t.minute
        assert ref.second == t.second

    def testConvertNegativeToUtc(self):
        Timezone.LOCAL = lambda tz: 0
        ref = datetime.datetime(1941, 12, 7, 10, 30, 22)
        s = self.__strDateTime(ref.year, ref.month, ref.day, ref.hour,
            ref.minute, ref.second, -6)
        t = XDateTime.translate(s)
        assert ref.year == t.year
        assert ref.month == t.month
        assert ref.day == t.day
        assert ref.hour + 6 == t.hour
        assert ref.minute == t.minute
        assert ref.second == t.second

    def testConvertPositiveToGreaterPositive(self):
        Timezone.LOCAL = lambda tz: 3
        ref = datetime.datetime(1941, 12, 7, 10, 30, 22)
        s = self.__strDateTime(ref.year, ref.month, ref.day, ref.hour,
            ref.minute, ref.second, 2)
        t = XDateTime.translate(s)
        assert ref.year == t.year
        assert ref.month == t.month
        assert ref.day == t.day
        assert ref.hour + 1 == t.hour
        assert ref.minute == t.minute
        assert ref.second == t.second

    def testConvertPositiveToLesserPositive(self):
        Timezone.LOCAL = lambda tz: 2
        ref = datetime.datetime(1941, 12, 7, 10, 30, 22)
        s = self.__strDateTime(ref.year, ref.month, ref.day, ref.hour,
            ref.minute, ref.second, 3)
        t = XDateTime.translate(s)
        assert ref.year == t.year
        assert ref.month == t.month
        assert ref.day == t.day
        assert ref.hour - 1 == t.hour
        assert ref.minute == t.minute
        assert ref.second == t.second

    def testConvertPositiveToNegative(self):
        Timezone.LOCAL = lambda tz: -6
        ref = datetime.datetime(1941, 12, 7, 10, 30, 22)
        s = self.__strDateTime(ref.year, ref.month, ref.day, ref.hour,
            ref.minute, ref.second, 3)
        t = XDateTime.translate(s)
        assert ref.year == t.year
        assert ref.month == t.month
        assert ref.day == t.day
        assert ref.hour - 9 == t.hour
        assert ref.minute == t.minute
        assert ref.second == t.second

    def testConvertPositiveToUtc(self):
        Timezone.LOCAL = lambda tz: 0
        ref = datetime.datetime(1941, 12, 7, 10, 30, 22)
        s = self.__strDateTime(ref.year, ref.month, ref.day, ref.hour,
            ref.minute, ref.second, 3)
        t = XDateTime.translate(s)
        assert ref.year == t.year
        assert ref.month == t.month
        assert ref.day == t.day
        assert ref.hour - 3 == t.hour
        assert ref.minute == t.minute
        assert ref.second == t.second

    def testConvertUtcToNegative(self):
        Timezone.LOCAL = lambda tz: -6
        ref = datetime.datetime(1941, 12, 7, 10, 30, 22)
        s = "%.4d-%.2d-%.2dT%.2d:%.2d:%.2dZ" % (ref.year, ref.month, ref.day,
            ref.hour, ref.minute, ref.second)
        t = XDateTime.translate(s)
        assert ref.year == t.year
        assert ref.month == t.month
        assert ref.day == t.day
        assert ref.hour - 6 == t.hour
        assert ref.minute == t.minute
        assert ref.second == t.second

    def testConvertUtcToPositive(self):
        Timezone.LOCAL = lambda tz: 3
        ref = datetime.datetime(1941, 12, 7, 10, 30, 22)
        s = "%.4d-%.2d-%.2dT%.2d:%.2d:%.2dZ" % (ref.year, ref.month, ref.day,
            ref.hour, ref.minute, ref.second)
        t = XDateTime.translate(s)
        assert ref.year == t.year
        assert ref.month == t.month
        assert ref.day == t.day
        assert ref.hour + 3 == t.hour
        assert ref.minute == t.minute
        assert ref.second == t.second

    def testOverflow(self):
        Timezone.LOCAL = lambda tz: -2
        ref = datetime.datetime(1, 1, 1, 0, 0, 0)
        s = "%.4d-%.2d-%.2dT%.2d:%.2d:%.2dZ" % (ref.year, ref.month, ref.day,
            ref.hour, ref.minute, ref.second)
        assert XDateTime.translate(s) == ref

    def testSimple(self):
        Timezone.LOCAL = lambda tz: 0
        ref = datetime.datetime(1941, 12, 7, 10, 30, 22)
        s = "%.4d-%.2d-%.2dT%.2d:%.2d:%.2d" % (ref.year, ref.month, ref.day,
            ref.hour, ref.minute, ref.second)
        assert XDateTime.translate(s) == ref

    def testSimpleWithMicrosecond(self):
        Timezone.LOCAL = lambda tz: 0
        ref = datetime.datetime(1941, 12, 7, 10, 30, 22, 454)
        s = "%.4d-%.2d-%.2dT%.2d:%.2d:%.2d.%.4d" % (ref.year, ref.month,
            ref.day, ref.hour, ref.minute, ref.second, ref.microsecond)
        assert XDateTime.translate(s) == ref

    def testTimezoneNegative(self):
        self.__equalsTimezone(-6)

    def testTimezonePositive(self):
        self.__equalsTimezone(6)

    def testTranslateToString(self):
        Timezone.LOCAL = lambda tz: 0
        translated = self.__toString(datetime.datetime(2021, 12, 31, 11, 25))
        assert isinstance(translated, str)
        assert translated == "2021-12-31T11:25:00Z"

        Timezone.LOCAL = lambda tz: 4
        translated = self.__toString(datetime.datetime(2021, 1, 1, 16, 53, 9))
        assert isinstance(translated, str)
        assert translated == "2021-01-01T16:53:09+04:00"

        Timezone.LOCAL = lambda tz: -4
        translated = self.__toString(datetime.datetime(2021, 1, 1, 16, 53, 59))
        assert isinstance(translated, str)
        assert translated == "2021-01-01T16:53:59-04:00"

    def testTranslateToString_failed(self):
        dummy = _Dummy()
        assert self.__toString(dummy) is dummy
        time = datetime.time(22, 47, 9, 981)
        assert self.__toString(time) is time
        date = datetime.date(2101, 1, 1)
        assert self.__toString(date) is date

    def testUtcTimezone(self):
        Timezone.LOCAL = lambda tz: 0
        ref = datetime.date(1941, 12, 7)
        s = "%.4d-%.2d-%.2dZ" % (ref.year, ref.month, ref.day)
        assert XDate.translate(s) == ref

    def testUtcTimezone(self):
        Timezone.LOCAL = lambda tz: 0
        ref = datetime.datetime(1941, 12, 7, 10, 30, 22)
        s = "%.4d-%.2d-%.2dT%.2d:%.2d:%.2d" % (ref.year, ref.month, ref.day,
            ref.hour, ref.minute, ref.second)
        assert XDateTime.translate(s) == ref

    def __equalsTimezone(self, tz):
        Timezone.LOCAL = lambda x: tz
        ref = datetime.datetime(1941, 12, 7, 10, 30, 22)
        s = self.__strDateTime(ref.year, ref.month, ref.day, ref.hour,
            ref.minute, ref.second, tz)
        assert XDateTime.translate(s) == ref

    @staticmethod
    def __strDateTime(Y, M, D, h, m, s, offset):
        return "%.4d-%.2d-%.2dT%.2d:%.2d:%.2d%+.2d:00" % (Y, M, D, h, m, s,
            offset)

    @staticmethod
    def __toString(value):
        return XDateTime.translate(value, topython=False)


class TestXTime:
    """Tests for the suds.xsd.sxbuiltin.XTime class."""

    def testConvertNegativeToGreaterNegative(self):
        Timezone.LOCAL = lambda tz: -6
        ref = datetime.time(10, 30, 22)
        s = self.__strTime(ref.hour, ref.minute, ref.second, -5)
        t = XTime.translate(s)
        assert ref.hour - 1 == t.hour
        assert ref.minute == t.minute
        assert ref.second == t.second

    def testConvertNegativeToLesserNegative(self):
        Timezone.LOCAL = lambda tz: -5
        ref = datetime.time(10, 30, 22)
        s = self.__strTime(ref.hour, ref.minute, ref.second, -6)
        t = XTime.translate(s)
        assert ref.hour + 1 == t.hour
        assert ref.minute == t.minute
        assert ref.second == t.second

    def testConvertNegativeToPositive(self):
        Timezone.LOCAL = lambda tz: 3
        ref = datetime.time(10, 30, 22)
        s = self.__strTime(ref.hour, ref.minute, ref.second, -6)
        t = XTime.translate(s)
        assert ref.hour + 9 == t.hour
        assert ref.minute == t.minute
        assert ref.second == t.second

    def testConvertNegativeToUtc(self):
        Timezone.LOCAL = lambda tz: 0
        ref = datetime.time(10, 30, 22)
        s = self.__strTime(ref.hour, ref.minute, ref.second, -6)
        t = XTime.translate(s)
        assert ref.hour + 6 == t.hour
        assert ref.minute == t.minute
        assert ref.second == t.second

    def testConvertPositiveToGreaterPositive(self):
        Timezone.LOCAL = lambda tz: 3
        ref = datetime.time(10, 30, 22)
        s = self.__strTime(ref.hour, ref.minute, ref.second, 2)
        t = XTime.translate(s)
        assert ref.hour + 1 == t.hour
        assert ref.minute == t.minute
        assert ref.second == t.second

    def testConvertPositiveToLesserPositive(self):
        Timezone.LOCAL = lambda tz: 2
        ref = datetime.time(10, 30, 22)
        s = self.__strTime(ref.hour, ref.minute, ref.second, 3)
        t = XTime.translate(s)
        assert ref.hour - 1 == t.hour
        assert ref.minute == t.minute
        assert ref.second == t.second

    def testConvertPositiveToNegative(self):
        Timezone.LOCAL = lambda tz: -6
        ref = datetime.time(10, 30, 22)
        s = self.__strTime(ref.hour, ref.minute, ref.second, 3)
        t = XTime.translate(s)
        assert ref.hour - 9 == t.hour
        assert ref.minute == t.minute
        assert ref.second == t.second

    def testConvertPositiveToUtc(self):
        Timezone.LOCAL = lambda tz: 0
        ref = datetime.time(10, 30, 22)
        s = self.__strTime(ref.hour, ref.minute, ref.second, 3)
        t = XTime.translate(s)
        assert ref.hour - 3 == t.hour
        assert ref.minute == t.minute
        assert ref.second == t.second

    def testConvertUtcToNegative(self):
        Timezone.LOCAL = lambda tz: -6
        ref = datetime.time(10, 30, 22)
        s = "%.2d:%.2d:%.2dZ" % (ref.hour, ref.minute, ref.second)
        t = XTime.translate(s)
        assert ref.hour - 6 == t.hour
        assert ref.minute == t.minute
        assert ref.second == t.second

    def testConvertUtcToPositive(self):
        Timezone.LOCAL = lambda tz: 3
        ref = datetime.time(10, 30, 22)
        s = "%.2d:%.2d:%.2dZ" % (ref.hour, ref.minute, ref.second)
        t = XTime.translate(s)
        assert ref.hour + 3 == t.hour
        assert ref.minute == t.minute
        assert ref.second == t.second

    def testNegativeTimezone(self):
        self.__equalsTimezone(-6)

    def testPositiveTimezone(self):
        self.__equalsTimezone(6)

    def testSimple(self):
        ref = datetime.time(10, 30, 22)
        s = "%.2d:%.2d:%.2d" % (ref.hour, ref.minute, ref.second)
        assert XTime.translate(s) == ref

    def testSimpleWithLongMicrosecond(self):
        ref = datetime.time(10, 30, 22, 999999)
        s = "%.2d:%.2d:%.2d.%4.d" % (ref.hour, ref.minute, ref.second,
            int("999999999"))
        assert XTime.translate(s) == ref

    def testSimpleWithMicrosecond(self):
        ref = datetime.time(10, 30, 22, 999999)
        s = "%.2d:%.2d:%.2d.%4.d" % (ref.hour, ref.minute, ref.second,
            ref.microsecond)
        assert XTime.translate(s) == ref

    def testSimpleWithShortMicrosecond(self):
        ref = datetime.time(10, 30, 22, 34)
        s = "%.2d:%.2d:%.2d.%4.d" % (ref.hour, ref.minute, ref.second,
            ref.microsecond)
        assert XTime.translate(s) == ref

    def testTranslateToString(self):
        Timezone.LOCAL = lambda tz: 0
        translated = self.__toString(datetime.time(11, 25))
        assert isinstance(translated, str)
        assert translated == "11:25:00Z"

        Timezone.LOCAL = lambda tz: 4
        translated = self.__toString(datetime.time(16, 53, 12))
        assert isinstance(translated, str)
        assert translated == "16:53:12+04:00"

        Timezone.LOCAL = lambda tz: -4
        translated = self.__toString(datetime.time(16, 53, 12))
        assert isinstance(translated, str)
        assert translated == "16:53:12-04:00"

    def testTranslateToString_failed(self):
        dummy = _Dummy()
        assert self.__toString(dummy) is dummy
        date = datetime.date(2001, 1, 1)
        assert self.__toString(date) is date
        aDateTime = datetime.datetime(1997, 2, 13)
        assert self.__toString(aDateTime) is aDateTime

    def testUtcTimezone(self):
        Timezone.LOCAL = lambda tz: 0
        ref = datetime.time(10, 30, 22)
        s = "%.2d:%.2d:%.2dZ" % (ref.hour, ref.minute, ref.second)
        assert XTime.translate(s) == ref

    def __equalsTimezone(self, tz):
        Timezone.LOCAL = lambda x: tz
        ref = datetime.time(10, 30, 22)
        s = self.__strTime(ref.hour, ref.minute, ref.second, tz)
        assert XTime.translate(s) == ref

    @staticmethod
    def __strTime(h, m, s, offset):
        return "%.2d:%.2d:%.2d%+.2d:00" % (h, m, s, offset)

    @staticmethod
    def __toString(value):
        return XTime.translate(value, topython=False)


class _Dummy:
    """Class for testing unknown object class handling."""
    pass
