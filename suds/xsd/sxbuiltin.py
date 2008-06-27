# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
# written by: Jeff Ortel ( jortel@redhat.com )

"""
The I{sxbuiltin} module provides classes that represent
XSD I{builtin} schema objects.
"""

from suds import *
from suds.xsd import *
from suds.sax import Element
from suds.xsd.sxbase import SchemaObject
from suds.sax import Namespace

log = logger(__name__)


class XBuiltin(SchemaObject):
    """
    Represents an (xsd) schema <xs:*/> node
    """
    
    def __init__(self, schema, name):
        """
        @param schema: The containing schema.
        @type schema: L{schema.Schema}
        """
        root = Element('sxbuiltin')
        root.set('name', name)
        SchemaObject.__init__(self, schema, root)
        
    def get_name(self):
        return self.root.get('name')
            
    def namespace(self):
        return Namespace.xsdns
    
    def builtin(self):
        return True
    
    def resolve(self, depth=1024, nobuiltin=False):
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
        
    def match(self, name, ns=None, classes=()):
        """ match anything """
        return True
    
    def get_child(self, name, ns=None):
        """ get any child """
        return Any(self.schema, name)
    
    def any(self):
        return True

    
class XBoolean(XBuiltin):
    """
    Represents an (xsd) boolean builtin type.
    """
    
    translation = (
        { '1':True, 'true':True, '0':False, 'false':False },
        { True: 'true', False: 'false' },)

    def __init__(self, schema, name):
        """
        @param schema: The containing schema.
        @type schema: L{schema.Schema}
        """
        XBuiltin.__init__(self, schema, name)
        
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
