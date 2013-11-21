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


from suds.sax.date import (Date, DateTime, Time, UtcTimezone,
    FixedOffsetTimezone)
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
        # Invalid time zone indicators.
            "1900-01-01 +17:00",
            "1900-01-01+ 17:00",
            "1900-01-01*17:00",
            "1900-01-01 17:00",
            "1900-01-01+17:",
            "1900-01-01+170",
            "1900-01-01+170:00",
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
            "13:27:04-13:60",
            "13:27:04-121",
            "13:27:04-121:00",
            "13:27:04+12:",
            "13:27:04-:13"
            "13:27:04-24:00"
            "13:27:04+99:00")

class TestDate:
    """Tests for the suds.sax.date.Date class."""

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
    def testStringToValue(self, string, y, m, d):
        assert Date(string).value == datetime.date(y, m, d)

    @pytest.mark.parametrize("string", _invalid_date_strings)
    def testStringToValue_failure(self, string):
        pytest.raises(ValueError, Date, string)


class TestDateTime:
    """Tests for the suds.sax.date.DateTime class."""

    @pytest.mark.parametrize(
        ("string", "y", "M", "d", "h", "m", "s", "micros"), (
        ("2013-11-19T14:05:23.428068", 2013, 11, 19, 14, 5, 23, 428068),
        ("2013-11-19 14:05:23.4280", 2013, 11, 19, 14, 5, 23, 428000)))
    def testStringToValue(self, string, y, M, d, h, m, s, micros):
        assert DateTime(string).value == datetime.datetime(y, M, d, h, m, s,
            micros)

    @pytest.mark.parametrize("string",
        [x + "T00:00:00" for x in _invalid_date_strings] +
        ["2000-12-31T" + x for x in _invalid_time_strings] + [
        # Invalid date/time separator characters.
            "2013-11-1914:05:23.428068",
            "2013-11-19X14:05:23.428068",
        # Invalid time zone indicators.
            "2013-11-19T14:05:23.428068-225",
            "2013-11-19T14:05:23.428068-22:",
            "2013-11-19T14:05:23.428068-224:00",
            "2013-11-19T14:05:23.428068-014:00",
            "2013-11-19T14:05:23.428068-00:002",
            "2013-11-19T14:05:23.428068+224",
            "2013-11-19T14:05:23.428068+225:00",
            "2013-11-19T14:05:23.428068+015:00",
            "2013-11-19T14:05:23.428068+00:60",
            "2013-11-19T14:05:23.428068+24:00",
            "2013-11-19T14:05:23.428068-99:00"])
    def testStringToValue_failure(self, string):
        pytest.raises(ValueError, DateTime, string)

    @pytest.mark.parametrize(
        ("string", "y", "M", "d", "h", "m", "s", "micros"), (
        ("2000-2-28T23:59:59.9999995", 2000, 2, 29, 0, 0, 0, 0),
        ("2000-2-29T23:59:59.9999995", 2000, 3, 1, 0, 0, 0, 0),
        ("2013-12-31T23:59:59.9999994", 2013, 12, 31, 23, 59, 59, 999999),
        ("2013-12-31T23:59:59.99999949", 2013, 12, 31, 23, 59, 59, 999999),
        ("2013-12-31T23:59:59.9999995", 2014, 1, 1, 0, 0, 0, 0)))
    def testStringToValue_subsecondRounding(self, string, y, M, d, h, m, s,
        micros):
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
    def testStringToValue_timezone(self, string, y, M, d, h, m, s, micros,
        tz_h, tz_m):
        tzdelta = datetime.timedelta(hours=tz_h, minutes=tz_m)
        tzinfo = FixedOffsetTimezone(tzdelta)
        ref = datetime.datetime(y, M, d, h, m, s, micros, tzinfo=tzinfo)
        assert DateTime(string).value == ref


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
        ("1:13:50.0", 1, 13, 50, 0)))
    def testStringToValue(self, string, h, m, s, micros):
        assert Time(string).value == datetime.time(h, m, s, micros)

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
    def testStringToValue_subsecondRounding(self, string, h, m, s, micros):
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
    def testStringToValue_timezone(self, string, h, m, s, micros, tz_h, tz_m):
        tzdelta = datetime.timedelta(hours=tz_h, minutes=tz_m)
        tzinfo = FixedOffsetTimezone(tzdelta)
        ref = datetime.time(h, m, s, micros, tzinfo=tzinfo)
        assert Time(string).value == ref

    @pytest.mark.parametrize("string", _invalid_time_strings)
    def testStringToValue_failure(self, string):
        pytest.raises(ValueError, Time, string)


class TestXDate:
    """Tests for the suds.xsd.sxbuiltin.XDate class."""

    def testSimple(self):
        ref = datetime.date(1941, 12, 7)
        s = "%.4d-%.2d-%.2d" % (ref.year, ref.month, ref.day)
        assert XDate.translate(s) == ref

    @pytest.mark.parametrize("tz", (
        "Z",
        "-06:00",
        "-00:00",
        "+00:00",
        "+06:00"))
    def testTimezone(self, tz):
        ref = datetime.date(1941, 12, 7)
        s = "%.4d-%.2d-%.2d%s" % (ref.year, ref.month, ref.day, tz)
        assert XDate.translate(s) == ref

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
        ref = datetime.time()
        assert self.__toString(ref) is ref

    @staticmethod
    def __toString(value):
        return XDate.translate(value, topython=False)


class TestXDateTime:
    """Tests for the suds.xsd.sxbuiltin.XDateTime class."""

    def testSimple(self):
        ref = datetime.datetime(1941, 12, 7, 10, 30, 22)
        s = "%.4d-%.2d-%.2dT%.2d:%.2d:%.2d" % (ref.year, ref.month, ref.day,
            ref.hour, ref.minute, ref.second)
        assert XDateTime.translate(s) == ref

    def testSimpleWithMicrosecond(self):
        ref = datetime.datetime(1941, 12, 7, 10, 30, 22, 454000)
        assert XDateTime.translate("1941-12-7T10:30:22.454") == ref

    @pytest.mark.parametrize("tz", (-6, 0, 6))
    def testTimezone(self, tz):
        ref = datetime.datetime(1941, 12, 7, 10, 30, 22, tzinfo=UtcTimezone())
        s = "%.4d-%.2d-%.2dT%.2d:%.2d:%.2d%+.2d:00" % (ref.year, ref.month,
            ref.day, ref.hour + tz, ref.minute, ref.second, tz)
        assert XDateTime.translate(s) == ref

    def testTranslateToString(self):
        ref = datetime.datetime(2021, 12, 31, 11, 25)
        translated = self.__toString(ref)
        assert isinstance(translated, str)
        assert translated == "2021-12-31T11:25:00"

        ref = datetime.datetime(2021, 12, 31, 11, 25, tzinfo=UtcTimezone())
        translated = self.__toString(ref)
        assert isinstance(translated, str)
        assert translated == "2021-12-31T11:25:00+00:00"

        tzinfo = FixedOffsetTimezone(4)
        ref = datetime.datetime(2021, 1, 1, 16, 53, 9, tzinfo=tzinfo)
        translated = self.__toString(ref)
        assert isinstance(translated, str)
        assert translated == "2021-01-01T16:53:09+04:00"

        tzinfo = FixedOffsetTimezone(-4)
        ref = datetime.datetime(2021, 1, 1, 16, 53, 59, tzinfo=tzinfo)
        translated = self.__toString(ref)
        assert isinstance(translated, str)
        assert translated == "2021-01-01T16:53:59-04:00"

    def testTranslateToString_failed(self):
        dummy = _Dummy()
        assert self.__toString(dummy) is dummy
        time = datetime.time(22, 47, 9, 981)
        assert self.__toString(time) is time
        date = datetime.date(2101, 1, 1)
        assert self.__toString(date) is date

    @staticmethod
    def __toString(value):
        return XDateTime.translate(value, topython=False)


class TestXTime:
    """Tests for the suds.xsd.sxbuiltin.XTime class."""

    def testSimple(self):
        ref = datetime.time(10, 30, 22)
        s = "%.2d:%.2d:%d" % (ref.hour, ref.minute, ref.second)
        assert XTime.translate(s) == ref

    def testSimpleWithLongMicrosecond(self):
        ref = datetime.time(10, 30, 22, 999999)
        assert XTime.translate("10:30:22.9999991") == ref

    def testSimpleWithLongMicrosecondAndRounding(self):
        assert XTime.translate("10:30:22.9999995") == datetime.time(10, 30, 23)

    def testSimpleWithMicrosecond(self):
        ref = datetime.time(10, 30, 22, 999999)
        assert XTime.translate("10:30:22.999999") == ref

    def testSimpleWithShortMicrosecond(self):
        ref = datetime.time(10, 30, 22, 340000)
        assert XTime.translate("10:30:22.34") == ref

    @pytest.mark.parametrize("tz", (-6, 0, 6))
    def testTimezone(self, tz):
        ref = datetime.time(10, 30, 22, tzinfo=UtcTimezone())
        s = self.__strTime(ref.hour + tz, ref.minute, ref.second, tz)
        assert XTime.translate(s) == ref

    def testTranslateToString(self):
        ref = datetime.time(11, 25, tzinfo=UtcTimezone())
        translated = self.__toString(ref)
        assert isinstance(translated, str)
        assert translated == "11:25:00+00:00"

        ref = datetime.time(16, 53, 12, tzinfo=FixedOffsetTimezone(4))
        translated = self.__toString(ref)
        assert isinstance(translated, str)
        assert translated == "16:53:12+04:00"

        ref = datetime.time(16, 53, 12, tzinfo=FixedOffsetTimezone(-4))
        translated = self.__toString(ref)
        assert isinstance(translated, str)
        assert translated == "16:53:12-04:00"

    def testTranslateToString_failed(self):
        dummy = _Dummy()
        assert self.__toString(dummy) is dummy
        date = datetime.date(2001, 1, 1)
        assert self.__toString(date) is date
        aDateTime = datetime.datetime(1997, 2, 13)
        assert self.__toString(aDateTime) is aDateTime

    @staticmethod
    def __strTime(h, m, s, offset):
        return "%.2d:%.2d:%.2d%+.2d:00" % (h, m, s, offset)

    @staticmethod
    def __toString(value):
        return XTime.translate(value, topython=False)


class _Dummy:
    """Class for testing unknown object class handling."""
    pass
