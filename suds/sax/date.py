# This program is free software; you can redistribute it and/or modify
# it under the terms of the (LGPL) GNU Lesser General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Library Lesser General Public License for more details at
# ( http://www.gnu.org/licenses/lgpl.html ).
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
# written by: Nathan Van Gheem (vangheem@gmail.com)

"""Classes for conversion between XML dates and Python objects."""

from logging import getLogger
from suds import UnicodeMixin

import datetime
import re
import time

log = getLogger(__name__)


class Date(UnicodeMixin):
    """
    An XML date object.
    Supported formats:
        - YYYY-MM-DD
        - YYYY-MM-DD(z|Z)
        - YYYY-MM-DD+06:00
        - YYYY-MM-DD-06:00
    @ivar date: The object value.
    @type date: B{datetime}.I{date}

    """

    def __init__(self, value):
        """
        @param value: The date value of the object.
        @type value: (datetime.date|str)
        @raise ValueError: When I{value} is invalid.

        """
        if isinstance(value, datetime.datetime):
            self.date = value.date()
        elif isinstance(value, datetime.date):
            self.date = value
        elif isinstance(value, basestring):
            self.date = self.__parse(value)
        else:
            raise ValueError, type(value)

    def __parse(self, s):
        """
        Parse the string date.
        Supported formats:
            - YYYY-MM-DD
            - YYYY-MM-DD(z|Z)
            - YYYY-MM-DD+06:00
            - YYYY-MM-DD-06:00
        Although, the TZ is ignored because it's meaningless
        without the time, right?
        @param s: A date string.
        @type s: str
        @return: A date object.
        @rtype: B{datetime}.I{date}

        """
        try:
            year, month, day = s[:10].split('-', 2)
            year = int(year)
            month = int(month)
            day = int(day)
            return datetime.date(year, month, day)
        except:
            log.debug(s, exec_info=True)
            raise ValueError, 'Invalid format "%s"' % s

    def __unicode__(self):
        return self.date.isoformat()


class Time(UnicodeMixin):
    """
    An XML time object.
    Supported formats:
        - HH:MI:SS
        - HH:MI:SS(z|Z)
        - HH:MI:SS.ms
        - HH:MI:SS.ms(z|Z)
        - HH:MI:SS(+|-)06:00
        - HH:MI:SS.ms(+|-)06:00
    @ivar tz: The timezone
    @type tz: L{Timezone}
    @ivar time: The object value.
    @type time: B{datetime}.I{time}

    """

    def __init__(self, value, adjusted=True):
        """
        @param value: The time value of the object.
        @type value: (datetime.time|str)
        @param adjusted: Adjust for I{local} Timezone.
        @type adjusted: boolean
        @raise ValueError: When I{value} is invalid.

        """
        self.tz = Timezone()
        if isinstance(value, datetime.time):
            self.time = value
        elif isinstance(value, basestring):
            self.time = self.__parse(value)
            if adjusted:
                self.__adjust()
        else:
            raise ValueError, type(value)

    def __adjust(self):
        """Adjust for TZ offset."""
        if hasattr(self, 'offset'):
            today = datetime.date.today()
            delta = self.tz.adjustment(self.offset)
            d = datetime.datetime.combine(today, self.time)
            d = ( d + delta )
            self.time = d.time()

    def __parse(self, s):
        """
        Parse the string date.
        Patterns:
            - HH:MI:SS
            - HH:MI:SS(z|Z)
            - HH:MI:SS.ms
            - HH:MI:SS.ms(z|Z)
            - HH:MI:SS(+|-)06:00
            - HH:MI:SS.ms(+|-)06:00
        @param s: A time string.
        @type s: str
        @return: A time object.
        @rtype: B{datetime}.I{time}

        """
        try:
            offset = None
            part = Timezone.split(s)
            hour, minute, second = part[0].split(':', 2)
            hour = int(hour)
            minute = int(minute)
            second, ms = self.__second(second)
            if len(part) == 2:
                self.offset = self.__offset(part[1])
            return datetime.time(hour, minute, second, ms)
        except:
            log.debug(s, exec_info=True)
            raise ValueError, 'Invalid format "%s"' % s

    @staticmethod
    def __second(s):
        """
        Parse the seconds and microseconds.
        The microseconds are truncated to 999999 due to a restriction in
        the python datetime.datetime object.
        @param s: A string representation of the seconds.
        @type s: str
        @return: Tuple of (sec, ms)
        @rtype: tuple.

        """
        part = s.split('.')
        seconds = int(part[0])
        microseconds = 0
        if len(part) > 1:
            microseconds = int(part[1][:6])
        return seconds, microseconds

    def __offset(self, s):
        """
        Parse the TZ offset.
        @param s: A string representation of the TZ offset.
        @type s: str
        @return: The signed offset in hours.
        @rtype: str

        """
        if len(s) == len('-00:00'):
            return int(s[:3])
        if len(s) == 0:
            return self.tz.local
        if len(s) == 1:
            return 0
        raise Exception()

    def __unicode__(self):
        time = self.time.isoformat()
        if self.tz.local:
            return '%s%+.2d:00' % (time, self.tz.local)
        return '%sZ' % time


class DateTime(Date, Time):
    """
    An XML time object.
    Supported formats:
        - YYYY-MM-DDB{T}HH:MI:SS
        - YYYY-MM-DDB{T}HH:MI:SS(z|Z)
        - YYYY-MM-DDB{T}HH:MI:SS.ms
        - YYYY-MM-DDB{T}HH:MI:SS.ms(z|Z)
        - YYYY-MM-DDB{T}HH:MI:SS(+|-)06:00
        - YYYY-MM-DDB{T}HH:MI:SS.ms(+|-)06:00
    @ivar datetime: The object value.
    @type datetime: B{datetime}.I{datetime}

    """

    def __init__(self, value):
        """
        @param value: The datetime value of the object.
        @type value: (datetime.datetime|str)
        @raise ValueError: When I{value} is invalid.

        """
        if isinstance(value, datetime.datetime):
            Date.__init__(self, value.date())
            Time.__init__(self, value.time())
            self.datetime = datetime.datetime.combine(self.date, self.time)
        elif isinstance(value, basestring):
            part = value.split('T')
            Date.__init__(self, part[0])
            Time.__init__(self, part[1], 0)
            self.datetime = datetime.datetime.combine(self.date, self.time)
            self.__adjust()
        else:
            raise ValueError, type(value)

    def __adjust(self):
        """Adjust for TZ offset."""
        if not hasattr(self, 'offset'):
            return
        delta = self.tz.adjustment(self.offset)
        try:
            d = ( self.datetime + delta )
            self.datetime = d
            self.date = d.date()
            self.time = d.time()
        except OverflowError:
            log.warn('"%s" caused overflow, not-adjusted', self.datetime)

    def __unicode__(self):
        s = []
        s.append(Date.__unicode__(self))
        s.append(Time.__unicode__(self))
        return 'T'.join(s)


class UTC(DateTime):
    """Represents current UTC time."""

    def __init__(self, date=None):
        if date is None:
            date = datetime.datetime.utcnow()
        DateTime.__init__(self, date)
        self.tz.local = 0


def get_local_timezone(tz):
    """
    Returns the local timezone offset based on local timezone and DST status.

    """
    if time.localtime().tm_isdst:
        offset_minutes = time.altzone
    else:
        offset_minutes = time.timezone
    return 0 - offset_minutes/60/60


class Timezone:
    """
    Timezone object used to do TZ conversions
    @cvar local: The (A) local TZ offset.
    @type local: int
    @cvar patten: The regex patten to match TZ.
    @type patten: re.Pattern

    """

    pattern = re.compile('([zZ])|([\-\+][0-9]{2}:[0-9]{2})')

    LOCAL = get_local_timezone

    def __init__(self, offset=None):
        if offset is None:
            offset = Timezone.LOCAL(self)
        self.local = offset

    @classmethod
    def split(cls, s):
        """
        Split the TZ from string.
        @param s: A string containing a timezone
        @type s: basestring
        @return: The split parts.
        @rtype: tuple

        """
        m = cls.pattern.search(s)
        if m is None:
            return (s,)
        x = m.start(0)
        return (s[:x], s[x:])

    def adjustment(self, offset):
        """
        Get the adjustment to the I{local} TZ.
        @return: The delta between I{offset} and local TZ.
        @rtype: B{datetime}.I{timedelta}

        """
        delta = ( self.local - offset )
        return datetime.timedelta(hours=delta)
