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
# written by: Nathan Van Gheem (vangheem@gmail.com)

"""
The I{xdate} module provides classes for converstion
between XML dates and python objects.
"""

from logging import getLogger
from suds import *
from suds.xsd import *
import time
import datetime as dt
import re


class Date:
    """
    An XML date object (YYYY-MM-DD).
    @ivar date: The object value.
    @type date: L{dt.date}
    """
    def __init__(self, date):
        """
        @param date: The value of the object.
        @type date: ( L{dt.date}| L{dt.datetime} | L{str} )
        @raise ValueError: When I{date} is invalid.
        """
        if isinstance(date, dt.date):
            self.date = date
            return
        if isinstance(date, dt.datetime):
            self.date = date.date()
            return
        if isinstance(date, basestring):
            self.date = self.__parse(date)
            return
        raise ValueError, type(date)
    
    def native(self):
        """
        Get the native I{python} representation.
        @return: The python date object.
        @rtype: L{dt.date}
        """
        return self.date
    
    def year(self):
        """
        Get the I{year} component.
        @return: The year.
        @rtype: int
        """
        return self.date.year
    
    def month(self):
        """
        Get the I{month} component.
        @return: The month.
        @rtype: int
        """
        return self.date.month
    
    def day(self):
        """
        Get the I{day} component.
        @return: The day.
        @rtype: int
        """
        return self.date.day
        
    def __parse(self, s):
        """
        Parse the string date format: "YYYY-MM-DD".
        @param s: A date string.
        @type s: str
        @return: A date object.
        @rtype: L{dt.date}
        """
        try:
            year, month, day = s[:10].split('-', 2)
            year = int(year)
            month = int(month)
            day = int(day)
            return dt.date(year, month, day)
        except Exception, e:
            raise ValueError, 'Invalid format "%s"' % s
        
    def __str__(self):
        return unicode(self)
    
    def __unicode__(self):
        return self.date.isoformat()

class Time:
    """
    An XML time object (HH:MM:SS(Z|z|(-|+)[0-9]+)).
    @ivar date: The object value.
    @type date: L{dt.date}
    """
    def __init__(self, tm):
        """
        @param tm: The value of the object.
        @type tm: ( L{dt.time}| L{dt.datetime} | L{str} )
        @raise ValueError: When I{tm} is invalid.
        """
        if isinstance(tm, dt.time):
            self.tm = tm
            return
        if isinstance(tm, dt.datetime):
            self.tm = tm.time()
            return
        if isinstance(tm, basestring):
            self.tm = self.__parse(tm)
            return
        raise ValueError, type(tm)
    
    def native(self):
        """
        Get the native I{python} representation.
        @return: The python date object.
        @rtype: L{dt.time}
        """
        return self.tm
    
    def hour(self):
        """
        Get the I{hour} component.
        @return: The hour.
        @rtype: int
        """
        return self.tm.hour
    
    def minute(self):
        """
        Get the I{minute} component.
        @return: The minute.
        @rtype: int
        """
        return self.tm.minute
    
    def second(self):
        """
        Get the I{seconds} component.
        @return: The seconds.
        @rtype: int
        """
        return self.tm.second
    
    def microsecond(self):
        """
        Get the I{microsecond} component.
        @return: The microsecond.
        @rtype: int
        """
        return self.tm.microsecond
    
    def adjust(self, day):
        """
        Adjust the day based on TZ.
        @param day: The (+|-) days to adjust.
        @type day: int
        """
        pass
        
    def __parse(self, s):
        """
        Parse the string date.
        Format:"HH:MM:SS(Z|z|(-|+)[0-9]+)?".
        @param s: A time string.
        @type s: str
        @return: A time object.
        @rtype: L{dt.time}
        """
        try:
            part = self.__split(s)
            hour, minute, second = part[0].split(':', 2)
            hour = int(hour)
            minute = int(minute)
            second, ms = self.__second(second)
            if len(part) == 2:
                offset = self.__offset(part[1])
                tz = Timezone(offset)
                day, hour = tz.adjusted(hour)
                self.adjust(day)
            if ms is None:
                return dt.time(hour, minute, second)
            else:
                return dt.time(hour, minute, second, ms)
        except:
            raise ValueError, 'Invalid format "%s"' % s
        
    def __split(self, s):
        m = re.search('[zZ\-\+]', s)
        if m is None:
            return (s,)
        x = (m.end(0)-1)
        return (s[:x], s[x:])
        
    def __second(self, s):
        part = s.split('.')
        if len(part) == 1:
            return (int(part[0]), None)
        else:
            return (int(part[0]), int(part[1]))
        
    def __offset(self, s):
        if len(s) == len('-00:00'):
            return int(s[:3])
        if len(s) == 0:
            return Timezone.local
        if len(s) == 1:
            return 0
        raise Exception()

    def __str__(self):
        return unicode(self)
    
    def __unicode__(self):
        return '%s%+.2d:00' % (self.tm.isoformat(), Timezone.local)


class DateTime(Date,Time):
    """
    An XML time object (HH:MM:SS(Z|z|(-|+)[0-9]+)).
    @ivar date: The object value.
    @type date: L{dt.date}
    """
    def __init__(self, dtm):
        """
        @param tm: The value of the object.
        @type tm: ( L{dt.time}| L{dt.datetime} | L{str} )
        @raise ValueError: When I{tm} is invalid.
        """
        if isinstance(dtm, dt.datetime):
            Date.__init__(self, dtm.date())
            Time.__init__(self, dtm.time())
            return
        if isinstance(dtm, basestring):
            part = dtm.split('T')
            Date.__init__(self, part[0])
            Time.__init__(self, part[1])
            return
        raise ValueError, type(dtm)
    
    def native(self):
        """
        Get the native I{python} representation.
        @return: The python datetime object.
        @rtype: L{dt.datetime}
        """
        return dt.datetime.combine(self.date, self.tm)
    
    def adjust(self, day):
        """
        Adjust the day based on TZ.
        @param day: The (+|-) days to adjust.
        @type day: int
        """
        d = ( self.day() + day )
        self.date = self.date.replace(day=d)
        
    def __str__(self):
        return unicode(self)
    
    def __unicode__(self):
        s = []
        s.append(Date.__unicode__(self))
        s.append(Time.__unicode__(self))
        return 'T'.join(s)
    
    
class Timezone:
    """
    Timezone object used to do TZ conversions
    @cvar local: The (A) local TZ offset.
    @type local: int
    @ivar offset: The (B) offset to convert.
    @type offset: int
    """
    local = ( 0-time.timezone/60/60 )
    
    def __init__(self, offset):
        """
        @param offset: The (B) offset to convert.
        @type offset: int
        """
        self.offset = offset
        
    def adjusted(self, hour):
        """
        Adjust the I{hour} to the local TZ.
        @param hour: The hour to convert.
        @type hour: int
        @return: The adjusted hour.
        @rtype: int
        """
        day = 0
        adj = (self.local-self.offset)
        hour += adj
        if hour < 0:
            day = -1
            hour = (24+hour)
        if hour > 23:
            day = 1
            hour = (24-hour)
        return (day, hour)
    

def DT(s):
    t = DateTime(s)
    print '\n"%s"\n %s' % (s, t)


if __name__ == '__main__':
    print 'TIME'
    t = Time(dt.datetime.now())
    print t
    t = Time(dt.datetime.now().time())
    print t
    t = Time('10:30:22.445')
    print t
    t = Time('10:30:32z')
    print t
    t = Time('10:30:42-02:00')
    print t
    print 'DATE'
    d = Date(dt.datetime.now())
    print d
    d = Date(dt.datetime.now().date())
    print d
    d = Date('2009-07-28')
    print d
    print 'DATETIME'
    t = DateTime(dt.datetime.now())
    print t
    
    DT('2009-07-28T10:10:22')
    DT('2009-07-28T10:20:22+02:00')
    DT('2009-07-28T10:30:22Z')
    DT('2009-07-28T10:40:22-05:00')
    DT('2009-07-28T00:50:22-05:00')
    DT('2009-07-28T10:11:22-07:00')
    
    Timezone.local = 4
    print '\nTZ=4'

    DT('2009-07-28T10:10:22')
    DT('2009-07-28T10:20:22+02:00')
    DT('2009-07-28T10:30:22Z')
    DT('2009-07-28T10:40:22-05:00')
    DT('2009-07-28T00:50:22-05:00')
    DT('2009-07-28T10:11:22-07:00')
