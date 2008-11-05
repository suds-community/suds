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
The I{sxbuiltin} module provides classes that represent
XSD I{builtin} schema objects.
"""

from logging import getLogger
from suds import *
from suds.xsd import *
from suds.sax.element import Element
from suds.xsd.sxbase import SchemaObject
from suds.sax import Namespace
import datetime
import time

log = getLogger(__name__)


class Factory:

    tags =\
    {
        'anyType' : lambda x,y=None: Any(x,y),
        'boolean' : lambda x,y=None: XBoolean(x,y),
        'int' : lambda x,y=None: XInteger(x,y),
        'long' : lambda x,y=None: XInteger(x,y),
        'float' : lambda x,y=None: XFloat(x,y),
        'double' : lambda x,y=None: XFloat(x,y),
        'date' : lambda x,y=None: XDate(x,y),
        'time' : lambda x,y=None: XTime(x,y),
        'dateTime': lambda x,y=None: XDateTime(x,y),
    }

    @classmethod
    def create(cls, schema, name):
        """
        Create an object based on the root tag name.
        @param schema: A schema object.
        @type schema: L{schema.Schema}
        @param name: The name.
        @type name: str
        @return: The created object.
        @rtype: L{SchemaObject} 
        """
        fn = cls.tags.get(name)
        if fn is not None:
            return fn(schema, name)
        else:
            return XBuiltin(schema, name)


class XBuiltin(SchemaObject):
    """
    Represents an (xsd) schema <xs:*/> node
    """
    
    def __init__(self, schema, name):
        """
        @param schema: The containing schema.
        @type schema: L{schema.Schema}
        """
        root = Element(name)
        SchemaObject.__init__(self, schema, root)
        self.name = name
            
    def namespace(self):
        return Namespace.xsdns
    
    def builtin(self):
        return True
    
    def resolve(self, nobuiltin=False):
        return self

  
class Any(XBuiltin):
    """
    Represents an (xsd) <any/> node
    """

    def __init__(self, schema, name):
        """
        @param schema: The containing schema.
        @type schema: L{schema.Schema}
        """
        XBuiltin.__init__(self, schema, name)
    
    def get_child(self, name):
        """
        Get (find) a I{non-attribute} child by name and namespace.
        @param name: A child name.
        @type name: basestring
        @return: The requested child.
        @rtype: L{SchemaObject}
        """
        return Any(self.schema, name)
    
    def any(self):
        """
        Get whether this is an xs:any
        @return: True if any, else False
        @rtype: boolean
        """
        return True


class XBoolean(XBuiltin):
    """
    Represents an (xsd) boolean builtin type.
    """
    
    translation = (
        { '1':True, 'true':True, '0':False, 'false':False },
        { True: 'true', False: 'false' },)
        
    def translate(self, value, topython=True):
        """
        Convert a value from a schema type to a python type.
        @param value: A value to convert.
        @return: The converted I{language} type.
        """
        if topython:
            table = XBoolean.translation[0]
        else:
            table = XBoolean.translation[1]
        return table.get(value, value)

   
class XInteger(XBuiltin):
    """
    Represents an (xsd) xs:int builtin type.
    """
        
    def translate(self, value, topython=True):
        """
        Convert a value from a schema type to a python type.
        @param value: A value to convert.
        @return: The converted I{language} type.
        """
        if topython:
            return int(value)
        else:
            return str(value)

       
class XFloat(XBuiltin):
    """
    Represents an (xsd) xs:float builtin type.
    """
        
    def translate(self, value, topython=True):
        """
        Convert a value from a schema type to a python type.
        @param value: A value to convert.
        @return: The converted I{language} type.
        """
        if topython:
            return float(value)
        else:
            return str(value)


class LocalTimezone(datetime.tzinfo):
    """
    This implements tzinfo
    python does not automatically support timezones for its date objects
    """
    def __init__(self):
        offset = time.timezone
        self.__offset = datetime.timedelta(seconds = offset)
        
        offset = offset/60/60
        offset = str(offset)
        if int(offset) >= 0:
            if len(offset) == 2:
                offset = "+%s:00" % offset
            else:
                offset = "+0%s:00" % offset
        else:
            if len(offset) == 2:
                offset = "-%s:00" % offset
            else:
                offset = "-0%s:00" % offset
                
        self.__name = offset
        
    def utcoffset(self, dt):
        return self.__offset
    def tzname(self, dt):
        return self.__name
    def dst(self, dt):
        return datetime.timedelta(hours=1)


class XDate(XBuiltin):
    """
    Represents an (xsd) date builtin type.
    <start>2002-09-24</start>
    <start>2002-09-24Z</start>
    <start>2002-09-24+06:00</start>
    <start>2002-09-24-06:00</start>
    """
    
    def get_offset(self, value):
        if len(value) == 0:
            return time.timezone
        elif value.lower() != "z":
            tz_hour, tz_min = value.rsplit(':', 2)
            return (int(tz_hour)*60+int(tz_min))*60
        else:
            return 0
    
    def toPython(self, value):
        if value is None or len(value) == 0:
            return None
            
        year, month, day = value.rsplit('-', 3)
        
        #if it has a tz set, convert to user's tz
        if len(day) > 2:
            try:
                date = datetime.datetime(
                                int(year), 
                                int(month), 
                                int(day[:2]), 
                                tzinfo=LocalTimezone())
                offset = time.timezone - self.get_offset(day[2:])
                return date - datetime.timedelta(seconds=offset)
            except:
                log.warn('date "%s", invalid-timezone', value)
        return datetime.datetime(int(year), int(month), int(day))
    
    def toString(self, value):
        if not isinstance(value, datetime.datetime):
            return value
        if value is None:
            return ''
        #if tz was used here or not
        if value.tzinfo is None:
            return value.strftime("%Y-%m-%d")
        else:
            return value.strftime("%Y-%m-%d") + value.tzinfo.tzname(None)                
    
    def translate(self, value, topython=True):
        if topython:
            return self.toPython(value)
        else:
            return self.toString(value)

      
class XTime(XDate):
    """
    Represents an (xsd) time builtin type.
    <xs:element name="start" type="xs:time"/>
    <start>09:00:00</start>
    <start>09:30:10.5</start>
    """
    
    def get_extras(self, value):
        leftover = value[2:]
        second = value[:2]
        microsec = 0
        
        if leftover.startswith("."):
            splitindex = len(leftover)
            for sub in ["+", "-", "Z", "z"]:
                if leftover.find(sub) != -1:
                    splitindex = leftover.find(sub)
                    break
                    
            microsec = int( float(leftover[:splitindex])*1000000 )
            leftover = leftover[splitindex:]
            
        return int(second), int(microsec), leftover
        
    def get_offset(self, value):
        """
        done differently from parent since datetime.timedelta does not work with the time object
        returns None, None if there is no tz set
        """
        if value is None or len(value) == 0:
            return None, None
        elif value.lower() == "z":
            return 0, 0
        else:
            tz_hour, tz_min = value.split(':', 1)
            return int(tz_hour), int(tz_min)
            
    def calculate_time(self, hour, minute, tz_hour, tz_min):
        if tz_hour == None:
            return hour, minute
        
        hour -= time.timezone/60/60 - tz_hour
        minute -= tz_min*60
        
        #in case hours or minutes wrap around
        # 0 <= hour < 24
        # 0 <= minute < 60
        if minute < 0:
            hour -= 1
            minute = 60 - (minute*-1)
        elif minute > 60:
            hour += 1
            minute -= 60
        if hour < 0:
            hour = 24 - (hour*-1)
        elif hour > 23:
            hour -= 24
            
        return hour, minute
            
    def get_time(self, value):
        hour, minute, extra = value.split(':', 2)
        second, microsec, leftover = self.get_extras(extra)
        
        #convert to local since you can use timedelta with time objects
        tz_hour, tz_min = self.get_offset(leftover)
        
        #if it has a tz set, convert to user's tz
        # if tz_hour is None, no tz was set
        if tz_hour is not None:
            hour, minute = self.calculate_time(int(hour), int(minute), tz_hour, tz_min)
                    
        return int(hour), int(minute), second, microsec, tz_hour

    def toPython(self, value):
        if len(value) == 0:
            return None
            
        hour, minute, second, microsec, has_tz_set = self.get_time(value)
        
        if has_tz_set is not None:
            return datetime.time(
                            hour=int(hour), 
                            minute=int(minute), 
                            second=int(second), 
                            microsecond=microsec, 
                            tzinfo=LocalTimezone())
        else:
            return datetime.time(
                            hour=int(hour), 
                            minute=int(minute), 
                            second=int(second), 
                            microsecond=microsec)
            
    def toString(self, value):
        if not isinstance(value, datetime.datetime):
            return value
        if value is None:
            return ''
            
        time = value.strftime("%H:%M:%S")
        
        if value.microsecond != 0:
            time += str(float(value.microsecond)/1000000)[1:]

        if value.tzinfo is not None:
            time += value.tzinfo.tzname(None)
            
        return time

    def translate(self, value, topython=True):
        if topython:
            return self.toPython(value)
        else:
            return self.toString(value)
            

class XDateTime(XTime, XDate):
    """
    Represents an (xsd) dateTime builtin type.
    <startdate>2002-05-30T09:00:00</startdate>
    <startdate>2002-05-30T09:30:10.5</startdate>
    """

    def get_offset(self, value):
        return XDate.get_offset(self, value)

    def get_extras(self, value):
        return XTime.get_extras(self, value)

    def get_time(self, value):
        hour, minute, extra = value.split(':', 2)
        second, microsec, leftover = self.get_extras(extra)
                    
        return int(hour), int(minute), second, microsec, leftover

    def toPython(self, value):
        if value is None or len(value) == 0:
            return None
            
        date, mytime = value.split('T')
        year, month, day = date.split('-', 2)

        hour, minute, second, microsec, leftover = self.get_time(mytime)
        
        #if it has a tz set, convert to user's tz
        if len(leftover) > 0:
            try:
                date = datetime.datetime(
                                int(year), 
                                int(month),
                                int(day), 
                                hour, 
                                minute, 
                                second, 
                                microsec, 
                                tzinfo=LocalTimezone())
                #best way to convert timezone
                offset = time.timezone - self.get_offset(leftover)
                return date - datetime.timedelta(seconds=offset)
            except:
                log.warn('datetime "%s", invalid-timezone', value)
        return datetime.datetime(
                        int(year), 
                        int(month),  
                        int(day), 
                        hour, 
                        minute, 
                        second, 
                        microsec)

    def toString(self, value):
        if not isinstance(value, datetime.datetime):
            return value
        if value is None:
            return ''
        
        dt = value.strftime("%Y-%m-%dT%H:%M:%S")
        
        if value.microsecond != 0:
            dt += str(float(value.microsecond)/1000000)[1:]
            
        if value.tzinfo is not None:
            dt += value.tzinfo.tzname(None)

        return dt

    def translate(self, value, topython=True):
        if topython:
            return self.toPython(value)
        else:
            return self.toString(value)