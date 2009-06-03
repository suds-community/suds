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
from suds.xsd.sxbase import XBuiltin
from suds.xsd.sxdate import *


log = getLogger(__name__)


class Factory:

    tags =\
    {
        'anyType' : lambda x,y: XAny(x,y),
        'string' : lambda x,y: XString(x,y),
        'boolean' : lambda x,y: XBoolean(x,y),
        'int' : lambda x,y: XInteger(x,y),
        'long' : lambda x,y: XInteger(x,y),
        'float' : lambda x,y: XFloat(x,y),
        'double' : lambda x,y: XFloat(x,y),
        'date' : lambda x,y: XDate(x,y),
        'time' : lambda x,y: XTime(x,y),
        'dateTime': lambda x,y: XDateTime(x,y),
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
        @rtype: L{XBuiltin} 
        """
        fn = cls.tags.get(name)
        if fn is not None:
            return fn(schema, name)
        else:
            return XBuiltin(schema, name)
    
    
class XString(XBuiltin):
    """
    Represents an (xsd) <xs:string/> node
    """
    pass

  
class XAny(XBuiltin):
    """
    Represents an (xsd) <any/> node
    """
    
    def __init__(self, schema, name):
        """
        @param schema: The containing schema.
        @type schema: L{schema.Schema}
        """
        XBuiltin.__init__(self, schema, name)
        self.nillable = False
    
    def get_child(self, name):
        """
        Get (find) a I{non-attribute} child by name and namespace.
        @param name: A child name.
        @type name: basestring
        @return: The requested child.
        @rtype: (L{XBuiltin}, [L{XBuiltin},..])
        """
        child = XAny(self.schema, name)
        return (child, [])
    
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
        { True: 'true', False: 'false' },
    )
        
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
            if isinstance(value, basestring) and len(value):
                return int(value)
            else:
                return None
        else:
            if isinstance(value, int):
                return str(value)
            else:
                return value

       
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
            if isinstance(value, basestring) and len(value):
                return float(value)
            else:
                return None
        else:
            if isinstance(value, float):
                return str(value)
            else:
                return value
