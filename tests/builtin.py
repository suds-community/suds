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


from suds.sax.date import Timezone as Tz
from suds.xsd.sxbuiltin import *
from unittest import TestCase


class Date(XDate):
    def __init__(self):
        pass
class Time(XTime):
    def __init__(self):
        pass
class DateTime(XDateTime):
    def __init__(self):
        pass
    
class DateTest(TestCase):
    
    def testSimple(self):
        ref = dt.date(1941, 12, 7)
        s = '%.4d-%.2d-%.2d' % (ref.year, ref.month, ref.day)
        xdate = Date()
        d = xdate.translate(s)
        self.assertEqual(d, ref)
        
    def testNegativeTimezone(self):
        self.equalsTimezone(-6)
        
    def testPositiveTimezone(self):
        self.equalsTimezone(6)
        
    def testUtcTimezone(self):
        Timezone.local = 0
        ref = dt.date(1941, 12, 7)
        s = '%.4d-%.2d-%.2dZ' % (ref.year, ref.month, ref.day)
        xdate = Date()
        d = xdate.translate(s)
        self.assertEqual(d, ref)
        
    def equalsTimezone(self, tz):
        Timezone.local = tz
        ref = dt.date(1941, 12, 7)
        s = '%.4d-%.2d-%.2d%+.2d:00' % (ref.year, ref.month, ref.day, tz)
        xdate = Date()
        d = xdate.translate(s)
        self.assertEqual(d, ref)


  
class TimeTest(TestCase):

    def testSimple(self):
        ref = dt.time(10, 30, 22)
        s = '%.2d:%.2d:%.2d' % (ref.hour, ref.minute, ref.second)
        xtime = Time()
        t = xtime.translate(s)
        self.assertEqual(t, ref)
        
    def testSimpleWithShortMicrosecond(self):
        ref = dt.time(10, 30, 22, 34)
        s = '%.2d:%.2d:%.2d.%4.d' % (ref.hour, ref.minute, ref.second, ref.microsecond)
        xtime = Time()
        t = xtime.translate(s)
        self.assertEqual(t, ref)
        
    def testSimpleWithMicrosecond(self):
        ref = dt.time(10, 30, 22, 999999)
        s = '%.2d:%.2d:%.2d.%4.d' % (ref.hour, ref.minute, ref.second, ref.microsecond)
        xtime = Time()
        t = xtime.translate(s)
        self.assertEqual(t, ref)
        
    def testSimpleWithLongMicrosecond(self):
        ref = dt.time(10, 30, 22, 999999)
        s = '%.2d:%.2d:%.2d.%4.d' % (ref.hour, ref.minute, ref.second, int('999999999'))
        xtime = Time()
        t = xtime.translate(s)
        self.assertEqual(t, ref)
        
    def testPositiveTimezone(self):
        self.equalsTimezone(6)
        
    def testNegativeTimezone(self):
        self.equalsTimezone(-6)
        
    def testUtcTimezone(self):
        Timezone.local = 0
        ref = dt.time(10, 30, 22)
        s = '%.2d:%.2d:%.2dZ' % (ref.hour, ref.minute, ref.second)
        xtime = Time()
        t = xtime.translate(s)
        self.assertEqual(t, ref)
        
    def equalsTimezone(self, tz):
        Timezone.local = tz
        ref = dt.time(10, 30, 22)
        s = self.strTime(ref.hour, ref.minute, ref.second, tz)
        xtime = Time()
        t = xtime.translate(s)
        self.assertEqual(t, ref)
        
    def testConvertNegativeToGreaterNegative(self):
        Timezone.local = -6
        ref = dt.time(10, 30, 22)
        s = self.strTime(ref.hour, ref.minute, ref.second, -5)
        xtime = Time()
        t = xtime.translate(s)
        self.assertEqual(ref.hour-1, t.hour)
        self.assertEqual(ref.minute, t.minute)
        self.assertEqual(ref.second, t.second)
        
    def testConvertNegativeToLesserNegative(self):
        Timezone.local = -5
        ref = dt.time(10, 30, 22)
        s = self.strTime(ref.hour, ref.minute, ref.second, -6)
        xtime = Time()
        t = xtime.translate(s)
        self.assertEqual(ref.hour+1, t.hour)
        self.assertEqual(ref.minute, t.minute)
        self.assertEqual(ref.second, t.second)
        
    def testConvertPositiveToGreaterPositive(self):
        Timezone.local = 3
        ref = dt.time(10, 30, 22)
        s = self.strTime(ref.hour, ref.minute, ref.second, 2)
        xtime = Time()
        t = xtime.translate(s)
        self.assertEqual(ref.hour+1, t.hour)
        self.assertEqual(ref.minute, t.minute)
        self.assertEqual(ref.second, t.second)
        
    def testConvertPositiveToLesserPositive(self):
        Timezone.local = 2
        ref = dt.time(10, 30, 22)
        s = self.strTime(ref.hour, ref.minute, ref.second, 3)
        xtime = Time()
        t = xtime.translate(s)
        self.assertEqual(ref.hour-1, t.hour)
        self.assertEqual(ref.minute, t.minute)
        self.assertEqual(ref.second, t.second)
        
    def testConvertPositiveToNegative(self):
        Timezone.local = -6
        ref = dt.time(10, 30, 22)
        s = self.strTime(ref.hour, ref.minute, ref.second, 3)
        xtime = Time()
        t = xtime.translate(s)
        self.assertEqual(ref.hour-9, t.hour)
        self.assertEqual(ref.minute, t.minute)
        self.assertEqual(ref.second, t.second)
        
    def testConvertNegativeToPositive(self):
        Timezone.local = 3
        ref = dt.time(10, 30, 22)
        s = self.strTime(ref.hour, ref.minute, ref.second, -6)
        xtime = Time()
        t = xtime.translate(s)
        self.assertEqual(ref.hour+9, t.hour)
        self.assertEqual(ref.minute, t.minute)
        self.assertEqual(ref.second, t.second)
        
    def testConvertNegativeToUtc(self):
        Timezone.local = 0
        ref = dt.time(10, 30, 22)
        s = self.strTime(ref.hour, ref.minute, ref.second, -6)
        xtime = Time()
        t = xtime.translate(s)
        self.assertEqual(ref.hour+6, t.hour)
        self.assertEqual(ref.minute, t.minute)
        self.assertEqual(ref.second, t.second)
        
    def testConvertPositiveToUtc(self):
        Timezone.local = 0
        ref = dt.time(10, 30, 22)
        s = self.strTime(ref.hour, ref.minute, ref.second, 3)
        xtime = Time()
        t = xtime.translate(s)
        self.assertEqual(ref.hour-3, t.hour)
        self.assertEqual(ref.minute, t.minute)
        self.assertEqual(ref.second, t.second)
        
    def testConvertUtcToPositive(self):
        Timezone.local = 3
        ref = dt.time(10, 30, 22)
        s = '%.2d:%.2d:%.2dZ' % (ref.hour, ref.minute, ref.second)
        xtime = Time()
        t = xtime.translate(s)
        self.assertEqual(ref.hour+3, t.hour)
        self.assertEqual(ref.minute, t.minute)
        self.assertEqual(ref.second, t.second)
        
    def testConvertUtcToNegative(self):
        Timezone.local = -6
        ref = dt.time(10, 30, 22)
        s = '%.2d:%.2d:%.2dZ' % (ref.hour, ref.minute, ref.second)
        xtime = Time()
        t = xtime.translate(s)
        self.assertEqual(ref.hour-6, t.hour)
        self.assertEqual(ref.minute, t.minute)
        self.assertEqual(ref.second, t.second)
        
    def strTime(self, h, m, s, offset):
        return '%.2d:%.2d:%.2d%+.2d:00' % (h, m, s, offset)


class DateTimeTest(TestCase):

    def testSimple(self):
        ref = dt.datetime(1941, 12, 7, 10, 30, 22)
        s = '%.4d-%.2d-%.2dT%.2d:%.2d:%.2d' \
            % (ref.year,
               ref.month, 
               ref.day, 
               ref.hour, 
               ref.minute, 
               ref.second)
        xdt = DateTime()
        t = xdt.translate(s)
        self.assertEqual(t, ref)
        
    def testSimpleWithMicrosecond(self):
        ref = dt.datetime(1941, 12, 7, 10, 30, 22, 454)
        s = '%.4d-%.2d-%.2dT%.2d:%.2d:%.2d.%.4d' \
            % (ref.year, 
               ref.month, 
               ref.day, 
               ref.hour, 
               ref.minute, 
               ref.second, 
               ref.microsecond)
        xdt = DateTime()
        t = xdt.translate(s)
        self.assertEqual(t, ref)
        
    def testPositiveTimezone(self):
        self.equalsTimezone(6)
        
    def testNegativeTimezone(self):
        self.equalsTimezone(-6)
        
    def testUtcTimezone(self):
        Timezone.local = 0
        ref = dt.datetime(1941, 12, 7, 10, 30, 22)
        s = '%.4d-%.2d-%.2dT%.2d:%.2d:%.2d' \
            % (ref.year,
               ref.month, 
               ref.day, 
               ref.hour, 
               ref.minute, 
               ref.second)
        xdt = DateTime()
        t = xdt.translate(s)
        self.assertEqual(t, ref)
        
    def equalsTimezone(self, tz):
        Timezone.local = tz
        ref = dt.datetime(1941, 12, 7, 10, 30, 22)
        s = self.strDateTime(
                ref.year,
                ref.month,
                ref.day,
                ref.hour,
                ref.minute,
                ref.second,
                tz)
        xdt = DateTime()
        t = xdt.translate(s)
        self.assertEqual(t, ref)
        
    def testConvertNegativeToGreaterNegative(self):
        Timezone.local = -6
        ref = dt.datetime(1941, 12, 7, 10, 30, 22)
        s = self.strDateTime(
                ref.year,
                ref.month,
                ref.day,
                ref.hour,
                ref.minute,
                ref.second,
                -5)
        xdt = DateTime()
        t = xdt.translate(s)
        self.assertEqual(ref.year, t.year)
        self.assertEqual(ref.month, t.month)
        self.assertEqual(ref.day, t.day)
        self.assertEqual(ref.hour-1, t.hour)
        self.assertEqual(ref.minute, t.minute)
        self.assertEqual(ref.second, t.second)
        
    def testConvertNegativeToLesserNegative(self):
        Timezone.local = -5
        ref = dt.datetime(1941, 12, 7, 10, 30, 22)
        s = self.strDateTime(
                ref.year,
                ref.month,
                ref.day,
                ref.hour,
                ref.minute,
                ref.second,
                -6)
        xdt = DateTime()
        t = xdt.translate(s)
        self.assertEqual(ref.year, t.year)
        self.assertEqual(ref.month, t.month)
        self.assertEqual(ref.day, t.day)
        self.assertEqual(ref.hour+1, t.hour)
        self.assertEqual(ref.minute, t.minute)
        self.assertEqual(ref.second, t.second)
        
    def testConvertPositiveToGreaterPositive(self):
        Timezone.local = 3
        ref = dt.datetime(1941, 12, 7, 10, 30, 22)
        s = self.strDateTime(
                ref.year,
                ref.month,
                ref.day,
                ref.hour,
                ref.minute,
                ref.second,
                2)
        xdt = DateTime()
        t = xdt.translate(s)
        self.assertEqual(ref.year, t.year)
        self.assertEqual(ref.month, t.month)
        self.assertEqual(ref.day, t.day)
        self.assertEqual(ref.hour+1, t.hour)
        self.assertEqual(ref.minute, t.minute)
        self.assertEqual(ref.second, t.second)
        
    def testConvertPositiveToLesserPositive(self):
        Timezone.local = 2
        ref = dt.datetime(1941, 12, 7, 10, 30, 22)
        s = self.strDateTime(
                ref.year,
                ref.month,
                ref.day,
                ref.hour,
                ref.minute,
                ref.second,
                3)
        xdt = DateTime()
        t = xdt.translate(s)
        self.assertEqual(ref.year, t.year)
        self.assertEqual(ref.month, t.month)
        self.assertEqual(ref.day, t.day)
        self.assertEqual(ref.hour-1, t.hour)
        self.assertEqual(ref.minute, t.minute)
        self.assertEqual(ref.second, t.second)
        
    def testConvertPositiveToNegative(self):
        Timezone.local = -6
        ref = dt.datetime(1941, 12, 7, 10, 30, 22)
        s = self.strDateTime(
                ref.year,
                ref.month,
                ref.day,
                ref.hour,
                ref.minute,
                ref.second,
                3)
        xdt = DateTime()
        t = xdt.translate(s)
        self.assertEqual(ref.year, t.year)
        self.assertEqual(ref.month, t.month)
        self.assertEqual(ref.day, t.day)
        self.assertEqual(ref.hour-9, t.hour)
        self.assertEqual(ref.minute, t.minute)
        self.assertEqual(ref.second, t.second)
        
    def testConvertNegativeToPositive(self):
        Timezone.local = 3
        ref = dt.datetime(1941, 12, 7, 10, 30, 22)
        s = self.strDateTime(
                ref.year,
                ref.month,
                ref.day,
                ref.hour,
                ref.minute,
                ref.second,
                -6)
        xdt = DateTime()
        t = xdt.translate(s)
        self.assertEqual(ref.year, t.year)
        self.assertEqual(ref.month, t.month)
        self.assertEqual(ref.day, t.day)
        self.assertEqual(ref.hour+9, t.hour)
        self.assertEqual(ref.minute, t.minute)
        self.assertEqual(ref.second, t.second)
        
    def testConvertNegativeToUtc(self):
        Timezone.local = 0
        ref = dt.datetime(1941, 12, 7, 10, 30, 22)
        s = self.strDateTime(
                ref.year,
                ref.month,
                ref.day,
                ref.hour,
                ref.minute,
                ref.second,
                -6)
        xdt = DateTime()
        t = xdt.translate(s)
        self.assertEqual(ref.year, t.year)
        self.assertEqual(ref.month, t.month)
        self.assertEqual(ref.day, t.day)
        self.assertEqual(ref.hour+6, t.hour)
        self.assertEqual(ref.minute, t.minute)
        self.assertEqual(ref.second, t.second)
        
    def testConvertPositiveToUtc(self):
        Timezone.local = 0
        ref = dt.datetime(1941, 12, 7, 10, 30, 22)
        s = self.strDateTime(
                ref.year,
                ref.month,
                ref.day,
                ref.hour,
                ref.minute,
                ref.second,
                3)
        xdt = DateTime()
        t = xdt.translate(s)
        self.assertEqual(ref.year, t.year)
        self.assertEqual(ref.month, t.month)
        self.assertEqual(ref.day, t.day)
        self.assertEqual(ref.hour-3, t.hour)
        self.assertEqual(ref.minute, t.minute)
        self.assertEqual(ref.second, t.second)
        
    def testConvertUtcToPositive(self):
        Timezone.local = 3
        ref = dt.datetime(1941, 12, 7, 10, 30, 22)
        s = '%.4d-%.2d-%.2dT%.2d:%.2d:%.2dZ' \
            % (ref.year,
               ref.month, 
               ref.day, 
               ref.hour, 
               ref.minute, 
               ref.second)
        xdt = DateTime()
        t = xdt.translate(s)
        self.assertEqual(ref.year, t.year)
        self.assertEqual(ref.month, t.month)
        self.assertEqual(ref.day, t.day)
        self.assertEqual(ref.hour+3, t.hour)
        self.assertEqual(ref.minute, t.minute)
        self.assertEqual(ref.second, t.second)
        
    def testConvertUtcToNegative(self):
        Timezone.local = -6
        ref = dt.datetime(1941, 12, 7, 10, 30, 22)
        s = '%.4d-%.2d-%.2dT%.2d:%.2d:%.2dZ' \
            % (ref.year,
               ref.month, 
               ref.day, 
               ref.hour, 
               ref.minute, 
               ref.second)
        xdt = DateTime()
        t = xdt.translate(s)
        self.assertEqual(ref.year, t.year)
        self.assertEqual(ref.month, t.month)
        self.assertEqual(ref.day, t.day)
        self.assertEqual(ref.hour-6, t.hour)
        self.assertEqual(ref.minute, t.minute)
        self.assertEqual(ref.second, t.second)
        
    def testConvertNegativeToGreaterNegativeAndPreviousDay(self):
        Timezone.local = -6
        ref = dt.datetime(1941, 12, 7, 0, 30, 22)
        s = self.strDateTime(
                ref.year,
                ref.month,
                ref.day,
                ref.hour,
                ref.minute,
                ref.second,
                -5)
        xdt = DateTime()
        t = xdt.translate(s)
        self.assertEqual(ref.year, t.year)
        self.assertEqual(ref.month, t.month)
        self.assertEqual(6, t.day)
        self.assertEqual(23, t.hour)
        self.assertEqual(ref.minute, t.minute)
        self.assertEqual(ref.second, t.second)
        
    def testConvertNegativeToLesserNegativeAndNextDay(self):
        Timezone.local = -5
        ref = dt.datetime(1941, 12, 7, 23, 30, 22)
        s = self.strDateTime(
                ref.year,
                ref.month,
                ref.day,
                ref.hour,
                ref.minute,
                ref.second,
                -6)
        xdt = DateTime()
        t = xdt.translate(s)
        self.assertEqual(ref.year, t.year)
        self.assertEqual(ref.month, t.month)
        self.assertEqual(8, t.day)
        self.assertEqual(0, t.hour)
        self.assertEqual(ref.minute, t.minute)
        self.assertEqual(ref.second, t.second)
        
    def strDateTime(self, Y, M, D, h, m, s, offset):
        s = '%.4d-%.2d-%.2dT%.2d:%.2d:%.2d%+.2d:00' \
            % (Y, M, D, h, m, s, offset)
        return s

        
if __name__ == '__main__':
    unittest.main()
