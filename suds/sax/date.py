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
# written by: Jurko Gospodnetić ( jurko.gospodnetic@pke.hr )
# based on code by: Glen Walker
# based on code by: Nathan Van Gheem ( vangheem@gmail.com )

"""Classes for conversion between XML dates and Python objects."""

from logging import getLogger
from suds import UnicodeMixin

import datetime
import re
import time

log = getLogger(__name__)


SNIPPET_DATE =  \
    r"(?P<year>\d{1,})-(?P<month>\d{1,2})-(?P<day>\d{1,2})"
SNIPPET_TIME =  \
    r"(?P<hour>\d{1,2}):(?P<minute>\d{1,2}):(?P<second>\d{1,2})"  \
    r"(?:\.(?P<subsecond>\d+))?"
SNIPPET_ZONE =  \
    r"(?:(?P<tz_sign>[-+])(?P<tz_hour>\d{1,2})"  \
    r"(?::(?P<tz_minute>\d{1,2})(?::(?P<tz_second>\d{1,2}))?)?)"  \
    r"|(?P<tz_utc>[Zz])"

PATTERN_DATE = r"^%s(?:%s)?$" % (SNIPPET_DATE, SNIPPET_ZONE)
PATTERN_TIME = r"^%s(?:%s)?$" % (SNIPPET_TIME, SNIPPET_ZONE)
PATTERN_DATETIME = r"^%s[T ]%s(?:%s)?$" % (SNIPPET_DATE, SNIPPET_TIME,
                                           SNIPPET_ZONE)

RE_DATE = re.compile(PATTERN_DATE)
RE_TIME = re.compile(PATTERN_TIME)
RE_DATETIME = re.compile(PATTERN_DATETIME)


class Date(UnicodeMixin):
    """
    An XML date object supporting the xsd:date datatype.

    @ivar value: The object value.
    @type value: B{datetime}.I{date}

    """

    def __init__(self, value):
        """
        @param value: The date value of the object.
        @type value: (datetime.date|str)
        @raise ValueError: When I{value} is invalid.

        """
        if isinstance(value, datetime.datetime):
            self.value = value.date()
        elif isinstance(value, datetime.date):
            self.value = value
        elif isinstance(value, basestring):
            self.value = self.__parse(value)
        else:
            raise ValueError("invalid type for Date(): %s" % type(value))

    @staticmethod
    def __parse(value):
        """
        Parse the string date.

        Supports the subset of ISO8601 used by xsd:date, but is lenient with
        what is accepted, handling most reasonable syntax.

        Any timezone is parsed but ignored because a) it is meaningless without
        a time and b) B{datetime}.I{date} does not support timezone
        information.

        @param value: A date string.
        @type value: str
        @return: A date object.
        @rtype: B{datetime}.I{date}

        """
        match_result = RE_DATE.match(value)
        if match_result is None:
            raise ValueError("date data has invalid format '%s'" % (value,))
        return _date_from_match(match_result)

    def __unicode__(self):
        return self.value.isoformat()


class DateTime(UnicodeMixin):
    """
    An XML datetime object supporting the xsd:dateTime datatype.

    @ivar value: The object value.
    @type value: B{datetime}.I{datetime}

    """

    def __init__(self, value):
        """
        @param value: The datetime value of the object.
        @type value: (datetime.datetime|str)
        @raise ValueError: When I{value} is invalid.

        """
        self.tz = Timezone()
        if isinstance(value, datetime.datetime):
            self.value = value
        elif isinstance(value, basestring):
            self.value = self.__parse(value)
            self.__adjust()
        else:
            raise ValueError("invalid type for DateTime(): %s" % type(value))

    def __adjust(self):
        """Adjust for TZ offset."""
        if not hasattr(self, "offset"):
            return
        delta = self.tz.adjustment(self.offset)
        try:
            self.value = ( self.value + delta )
        except OverflowError:
            log.warn("'%s' caused overflow, not-adjusted", self.value)

    def __parse(self, value):
        """
        Parse the string datetime.

        Supports the subset of ISO8601 used by xsd:dateTime, but is lenient
        with what is accepted, handling most reasonable syntax.

        Subsecond information is rounded to microseconds due to a restriction
        in the python datetime.datetime/time implementation.

        @param value: A datetime string.
        @type value: str
        @return: A datetime object.
        @rtype: B{datetime}.I{datetime}

        """
        match_result = RE_DATETIME.match(value)
        if match_result is None:
           raise ValueError("date data has invalid format '%s'" % (value,))

        date = _date_from_match(match_result)
        time, round_up = _time_from_match(match_result)
        result = datetime.datetime.combine(date, time)
        if round_up:
            result += datetime.timedelta(microseconds=1)
        offset = _offset_from_match(match_result)
        if offset is not None:
            self.offset = offset
        return result

    def __unicode__(self):
        datetime = self.value.isoformat()
        if self.tz.local:
            return "%s%+.2d:00" % (datetime, self.tz.local)
        return "%sZ" % datetime


class Time(UnicodeMixin):
    """
    An XML time object supporting the xsd:time datatype.

    @ivar tz: The timezone
    @type tz: L{Timezone}
    @ivar value: The object value.
    @type value: B{datetime}.I{time}

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
            self.value = value
        elif isinstance(value, basestring):
            self.value = self.__parse(value)
            if adjusted:
                self.__adjust()
        else:
            raise ValueError("invalid type for Time(): %s" % type(value))

    def __adjust(self):
        """Adjust for TZ offset."""
        if hasattr(self, "offset"):
            today = datetime.date.today()
            delta = self.tz.adjustment(self.offset)
            d = datetime.datetime.combine(today, self.value)
            d = ( d + delta )
            self.value = d.time()

    def __parse(self, value):
        """
        Parse the string date.

        Supports the subset of ISO8601 used by xsd:time, but is lenient with
        what is accepted, handling most reasonable syntax.

        Subsecond information is rounded to microseconds due to a restriction
        in the python datetime.time implementation.

        @param value: A time string.
        @type value: str
        @return: A time object.
        @rtype: B{datetime}.I{time}

        """
        match_result = RE_TIME.match(value)
        if match_result is None:
           raise ValueError("date data has invalid format '%s'" % (value,))

        time, round_up = _time_from_match(match_result)
        if round_up:
            time = _bump_up_time_by_microsecond(time)
        offset = _offset_from_match(match_result)
        if offset is not None:
            self.offset = offset
        return time

    def __unicode__(self):
        time = self.value.isoformat()
        if self.tz.local:
            return "%s%+.2d:00" % (time, self.tz.local)
        return "%sZ" % time


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

    pattern = re.compile("([zZ])|([\-\+][0-9]{2}:[0-9]{2})")

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


def _bump_up_time_by_microsecond(time):
    """
    Helper function bumping up the given datetime.time by a microsecond,
    cycling around silently to 00:00:00.0 in case of an overflow.

    @param time: Time object.
    @type value: B{datetime}.I{time}
    @return: Time object.
    @rtype: B{datetime}.I{time}

    """
    dt = datetime.datetime(2000, 1, 1, time.hour, time.minute,
        time.second, time.microsecond)
    dt += datetime.timedelta(microseconds=1)
    return dt.time()


def _date_from_match(match_object):
    """
    Create a date object from a regular expression match.

    The regular expression match is expected to be from RE_DATE or RE_DATETIME.

    @param match_object: The regular expression match.
    @type value: B{re}.I{MatchObject}
    @return: A date object.
    @rtype: B{datetime}.I{date}

    """
    year = int(match_object.group("year"))
    month = int(match_object.group("month"))
    day = int(match_object.group("day"))
    return datetime.date(year, month, day)


def _time_from_match(match_object):
    """
    Create a time object from a regular expression match.

    Returns the time object and information whether the resulting time should
    be bumped up by one microsecond due to microsecond rounding.

    Subsecond information is rounded to microseconds due to a restriction in
    the python datetime.datetime/time implementation.

    The regular expression match is expected to be from RE_DATETIME or RE_TIME.

    @param match_object: The regular expression match.
    @type value: B{re}.I{MatchObject}
    @return: Time object + rounding flag.
    @rtype: tuple of B{datetime}.I{time} and bool

    """
    hour = int(match_object.group('hour'))
    minute = int(match_object.group('minute'))
    second = int(match_object.group('second'))
    subsecond = match_object.group('subsecond')

    round_up = False
    microsecond = 0
    if subsecond:
        round_up = len(subsecond) > 6 and int(subsecond[6]) >= 5
        subsecond = subsecond[:6]
        microsecond = int(subsecond + "0" * (6 - len(subsecond)))
    return datetime.time(hour, minute, second, microsecond), round_up


def _offset_from_match(match_object):
    """
    Calculates a timezone offset from a regular expression match.

    The regular expression match is expected to be from RE_DATE, RE_DATETIME or
    RE_TIME.

    @param match_object: The regular expression match.
    @type value: B{re}.I{MatchObject}
    @return: A timezone offset.
    @rtype: I(int)

    """
    tz_hour = match_object.group("tz_hour")
    if tz_hour:
        sign = 1
        if match_object.group("tz_sign") == "-":
            sign = -1
        return sign * int(tz_hour)
    if match_object.group("tz_utc"):
        return 0
