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


from suds.sax.date import Timezone
import suds.xsd.sxbuiltin
import tests

import datetime

tests.setup_logging()


class TestDate:
    def testSimple(self):
        ref = datetime.date(1941, 12, 7)
        s = '%.4d-%.2d-%.2d' % (ref.year, ref.month, ref.day)
        assert _XDate().translate(s) == ref

    def testTimezoneNegative(self):
        self.__equalsTimezone(-6)

    def testTimezonePositive(self):
        self.__equalsTimezone(6)

    def testUtcTimezone(self):
        Timezone.LOCAL = lambda tz: 0
        ref = datetime.date(1941, 12, 7)
        s = '%.4d-%.2d-%.2dZ' % (ref.year, ref.month, ref.day)
        assert _XDate().translate(s) == ref

    @staticmethod
    def __equalsTimezone(tz):
        Timezone.LOCAL = lambda x: tz
        ref = datetime.date(1941, 12, 7)
        s = '%.4d-%.2d-%.2d%+.2d:00' % (ref.year, ref.month, ref.day, tz)
        assert _XDate().translate(s) == ref


class TestDateTime:
    def testConvertNegativeToGreaterNegative(self):
        Timezone.LOCAL = lambda tz: -6
        ref = datetime.datetime(1941, 12, 7, 10, 30, 22)
        s = self.__strDateTime(ref.year, ref.month, ref.day, ref.hour,
            ref.minute, ref.second, -5)
        t = _XDateTime().translate(s)
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
        t = _XDateTime().translate(s)
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
        t = _XDateTime().translate(s)
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
        t = _XDateTime().translate(s)
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
        t = _XDateTime().translate(s)
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
        t = _XDateTime().translate(s)
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
        t = _XDateTime().translate(s)
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
        t = _XDateTime().translate(s)
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
        t = _XDateTime().translate(s)
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
        t = _XDateTime().translate(s)
        assert ref.year == t.year
        assert ref.month == t.month
        assert ref.day == t.day
        assert ref.hour - 3 == t.hour
        assert ref.minute == t.minute
        assert ref.second == t.second

    def testConvertUtcToNegative(self):
        Timezone.LOCAL = lambda tz: -6
        ref = datetime.datetime(1941, 12, 7, 10, 30, 22)
        s = '%.4d-%.2d-%.2dT%.2d:%.2d:%.2dZ' % (ref.year, ref.month, ref.day,
            ref.hour, ref.minute, ref.second)
        t = _XDateTime().translate(s)
        assert ref.year == t.year
        assert ref.month == t.month
        assert ref.day == t.day
        assert ref.hour - 6 == t.hour
        assert ref.minute == t.minute
        assert ref.second == t.second

    def testConvertUtcToPositive(self):
        Timezone.LOCAL = lambda tz: 3
        ref = datetime.datetime(1941, 12, 7, 10, 30, 22)
        s = '%.4d-%.2d-%.2dT%.2d:%.2d:%.2dZ' % (ref.year, ref.month, ref.day,
            ref.hour, ref.minute, ref.second)
        t = _XDateTime().translate(s)
        assert ref.year == t.year
        assert ref.month == t.month
        assert ref.day == t.day
        assert ref.hour + 3 == t.hour
        assert ref.minute == t.minute
        assert ref.second == t.second

    def testOverflow(self):
        Timezone.LOCAL = lambda tz: -2
        ref = datetime.datetime(1, 1, 1, 0, 0, 0)
        s = '%.4d-%.2d-%.2dT%.2d:%.2d:%.2dZ' % (ref.year, ref.month, ref.day,
            ref.hour, ref.minute, ref.second)
        assert _XDateTime().translate(s) == ref

    def testSimple(self):
        Timezone.LOCAL = lambda tz: 0
        ref = datetime.datetime(1941, 12, 7, 10, 30, 22)
        s = '%.4d-%.2d-%.2dT%.2d:%.2d:%.2d' % (ref.year, ref.month, ref.day,
            ref.hour, ref.minute, ref.second)
        assert _XDateTime().translate(s) == ref

    def testSimpleWithMicrosecond(self):
        Timezone.LOCAL = lambda tz: 0
        ref = datetime.datetime(1941, 12, 7, 10, 30, 22, 454)
        s = '%.4d-%.2d-%.2dT%.2d:%.2d:%.2d.%.4d' % (ref.year, ref.month,
            ref.day, ref.hour, ref.minute, ref.second, ref.microsecond)
        assert _XDateTime().translate(s) == ref

    def testTimezoneNegative(self):
        self.__equalsTimezone(-6)

    def testTimezonePositive(self):
        self.__equalsTimezone(6)

    def testUtcTimezone(self):
        Timezone.LOCAL = lambda tz: 0
        ref = datetime.datetime(1941, 12, 7, 10, 30, 22)
        s = '%.4d-%.2d-%.2dT%.2d:%.2d:%.2d' % (ref.year, ref.month, ref.day,
            ref.hour, ref.minute, ref.second)
        assert _XDateTime().translate(s) == ref

    def __equalsTimezone(self, tz):
        Timezone.LOCAL = lambda x: tz
        ref = datetime.datetime(1941, 12, 7, 10, 30, 22)
        s = self.__strDateTime(ref.year, ref.month, ref.day, ref.hour,
            ref.minute, ref.second, tz)
        assert _XDateTime().translate(s) == ref

    @staticmethod
    def __strDateTime(Y, M, D, h, m, s, offset):
        return '%.4d-%.2d-%.2dT%.2d:%.2d:%.2d%+.2d:00' % (Y, M, D, h, m, s,
            offset)


class TestTime:
    def testConvertNegativeToGreaterNegative(self):
        Timezone.LOCAL = lambda tz: -6
        ref = datetime.time(10, 30, 22)
        s = self.__strTime(ref.hour, ref.minute, ref.second, -5)
        t = _XTime().translate(s)
        assert ref.hour - 1 == t.hour
        assert ref.minute == t.minute
        assert ref.second == t.second

    def testConvertNegativeToLesserNegative(self):
        Timezone.LOCAL = lambda tz: -5
        ref = datetime.time(10, 30, 22)
        s = self.__strTime(ref.hour, ref.minute, ref.second, -6)
        t = _XTime().translate(s)
        assert ref.hour + 1 == t.hour
        assert ref.minute == t.minute
        assert ref.second == t.second

    def testConvertNegativeToPositive(self):
        Timezone.LOCAL = lambda tz: 3
        ref = datetime.time(10, 30, 22)
        s = self.__strTime(ref.hour, ref.minute, ref.second, -6)
        t = _XTime().translate(s)
        assert ref.hour + 9 == t.hour
        assert ref.minute == t.minute
        assert ref.second == t.second

    def testConvertNegativeToUtc(self):
        Timezone.LOCAL = lambda tz: 0
        ref = datetime.time(10, 30, 22)
        s = self.__strTime(ref.hour, ref.minute, ref.second, -6)
        t = _XTime().translate(s)
        assert ref.hour + 6 == t.hour
        assert ref.minute == t.minute
        assert ref.second == t.second

    def testConvertPositiveToGreaterPositive(self):
        Timezone.LOCAL = lambda tz: 3
        ref = datetime.time(10, 30, 22)
        s = self.__strTime(ref.hour, ref.minute, ref.second, 2)
        t = _XTime().translate(s)
        assert ref.hour + 1 == t.hour
        assert ref.minute == t.minute
        assert ref.second == t.second

    def testConvertPositiveToLesserPositive(self):
        Timezone.LOCAL = lambda tz: 2
        ref = datetime.time(10, 30, 22)
        s = self.__strTime(ref.hour, ref.minute, ref.second, 3)
        t = _XTime().translate(s)
        assert ref.hour - 1 == t.hour
        assert ref.minute == t.minute
        assert ref.second == t.second

    def testConvertPositiveToNegative(self):
        Timezone.LOCAL = lambda tz: -6
        ref = datetime.time(10, 30, 22)
        s = self.__strTime(ref.hour, ref.minute, ref.second, 3)
        t = _XTime().translate(s)
        assert ref.hour - 9 == t.hour
        assert ref.minute == t.minute
        assert ref.second == t.second

    def testConvertPositiveToUtc(self):
        Timezone.LOCAL = lambda tz: 0
        ref = datetime.time(10, 30, 22)
        s = self.__strTime(ref.hour, ref.minute, ref.second, 3)
        t = _XTime().translate(s)
        assert ref.hour - 3 == t.hour
        assert ref.minute == t.minute
        assert ref.second == t.second

    def testConvertUtcToNegative(self):
        Timezone.LOCAL = lambda tz: -6
        ref = datetime.time(10, 30, 22)
        s = '%.2d:%.2d:%.2dZ' % (ref.hour, ref.minute, ref.second)
        t = _XTime().translate(s)
        assert ref.hour - 6 == t.hour
        assert ref.minute == t.minute
        assert ref.second == t.second

    def testConvertUtcToPositive(self):
        Timezone.LOCAL = lambda tz: 3
        ref = datetime.time(10, 30, 22)
        s = '%.2d:%.2d:%.2dZ' % (ref.hour, ref.minute, ref.second)
        t = _XTime().translate(s)
        assert ref.hour + 3 == t.hour
        assert ref.minute == t.minute
        assert ref.second == t.second

    def testNegativeTimezone(self):
        self.__equalsTimezone(-6)

    def testPositiveTimezone(self):
        self.__equalsTimezone(6)

    def testSimple(self):
        ref = datetime.time(10, 30, 22)
        s = '%.2d:%.2d:%.2d' % (ref.hour, ref.minute, ref.second)
        assert _XTime().translate(s) == ref

    def testSimpleWithLongMicrosecond(self):
        ref = datetime.time(10, 30, 22, 999999)
        s = '%.2d:%.2d:%.2d.%4.d' % (ref.hour, ref.minute, ref.second,
            int('999999999'))
        assert _XTime().translate(s) == ref

    def testSimpleWithMicrosecond(self):
        ref = datetime.time(10, 30, 22, 999999)
        s = '%.2d:%.2d:%.2d.%4.d' % (ref.hour, ref.minute, ref.second,
            ref.microsecond)
        assert _XTime().translate(s) == ref

    def testSimpleWithShortMicrosecond(self):
        ref = datetime.time(10, 30, 22, 34)
        s = '%.2d:%.2d:%.2d.%4.d' % (ref.hour, ref.minute, ref.second,
            ref.microsecond)
        assert _XTime().translate(s) == ref

    def testUtcTimezone(self):
        Timezone.LOCAL = lambda tz: 0
        ref = datetime.time(10, 30, 22)
        s = '%.2d:%.2d:%.2dZ' % (ref.hour, ref.minute, ref.second)
        assert _XTime().translate(s) == ref

    def __equalsTimezone(self, tz):
        Timezone.LOCAL = lambda x: tz
        ref = datetime.time(10, 30, 22)
        s = self.__strTime(ref.hour, ref.minute, ref.second, tz)
        assert _XTime().translate(s) == ref

    @staticmethod
    def __strTime(h, m, s, offset):
        return '%.2d:%.2d:%.2d%+.2d:00' % (h, m, s, offset)


class _XDate(suds.xsd.sxbuiltin.XDate):
    """Mock XDate not connected to an actual schema."""
    def __init__(self):
        pass


class _XDateTime(suds.xsd.sxbuiltin.XDateTime):
    """Mock XDateTime not connected to an actual schema."""
    def __init__(self):
        pass


class _XTime(suds.xsd.sxbuiltin.XTime):
    """Mock XTime not connected to an actual schema."""
    def __init__(self):
        pass
