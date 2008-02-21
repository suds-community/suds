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

from suds import *
from suds.property import Property


class Schema:
    """
    The schema is an objectification of a <schema/> (xsd) definition.
    It provides inspection, lookup and type resolution. 
    """
    
    def __init__(self, schema):
        """ construct the sequence object with a schema """
        self.root = schema
        self.log = logger('schema')
        self.hints = {}
        self.types = {}
        
    def get_type(self, path):
        """
        get the definition object for the schema type located at the specified path.
        The path may contain (.) dot notation to specify nested types.
        The cached type is returned, else find_type() is used.
        """
        type = self.types.get(path, None)
        if type is None:
            type = self.find_type(path)
            self.types[path] = type
        return type
    
    def find_type(self, path):
        """
        get the definition object for the schema type located at the specified path.
        The path may contain (.) dot notation to specify nested types.
        """
        result = None
        parts = path.split('.')
        if result is None:
            for type in self.root.getChildren('complexType'):
                if type.attribute('name') == parts[0]:
                    result = Complex(self, type)
                    break
        if result is None:
            for type in self.root.getChildren('simpleType'):
                if type.attribute('name') == parts[0]:
                    result = Simple(self, type)
                    break
        if result is None:
            for type in self.root.getChildren('element'):
                if type.attribute('name') == parts[0]:
                    result = Element(self, type)
                    break
        if result is not None:
            for name in parts[1:]:
                result = result.get_child(name)
                if result is None:
                    break
                result = result.resolve()
        return result


class SchemaProperty:
    """
    A schema property is an extension to property object with
    with schema awareness.
    """
    
    __protected__ = ( 'root', 'schema')
    
    def __init__(self, schema, root):
        """ create the object with a schema and root node """
        self.root = root
        self.schema = schema
        
    def get_name(self):
        """ get the object's name """
        return None
    
    def get_type(self):
        """ get the node's (xsi) type as defined by the schema """
        return '_'
    
    def get_children(self, empty=None):
        """ get child (nested) schema definition nodes """ 
        list = []
        self.add_children(list)
        if len(list) == 0 and empty is not None:
            list = empty
        return list
    
    def get_child(self, name):
        """ get a child by name """
        for child in self.get_children():
            if child.get_name() == name:
                return child
        return None
    
    def add_children(self, list):
        """ abstract: add  children to the list.  should be overridden """
        pass
    
    def unbounded(self):
        """ get whether this node's specifes that it is unbounded (collection) """
        return False
    
    def resolve(self):
        """ return the nodes true type when another named type is referenced. """
        result = self
        type = self.get_type()
        if self.custom():
            resolved = self.schema.get_type(type)
            if resolved is not None:
                result = resolved
        return result
    
    def custom(self):
        """ get whether this object schema type is custom """
        if self.get_type() is None:
            return False
        else:
            return (not self.builtin())
    
    def builtin(self):
        """ get whether this object schema type is an (xsd) builtin """
        try:
            prefix = self.get_type().split()[0]
            return prefix.startswith('xs')
        except:
            return False


class Complex(SchemaProperty):
    
    """ Represents an (xsd) schema <xs:complexType/> node """
    
    def __init__(self, schema, root):
        """ create the object with a schema and root node """
        SchemaProperty.__init__(self, schema, root)
        
    def get_name(self):
        """ gets the <xs:complexType name=""/> attribute value """
        return self.root.attribute('name')
        
    def add_children(self, list):
        """ add <xs:sequence/> and <xs:complexContent/> nested types """
        for s in self.root.getChildren('sequence'):
            seq = Sequence(self.schema, s)
            seq.add_children(list)
        for s in self.root.getChildren('complexContent'):
            cont = ComplexContent(self.schema, s)
            cont.add_children(list)


class Simple(SchemaProperty):
    
    """ Represents an (xsd) schema <xs:simpleType/> node """
    
    def __init__(self, schema, root):
        """ create the object with a schema and root node """
        SchemaProperty.__init__(self, schema, root)

    def get_name(self):
        """ gets the <xs:simpleType name=""/> attribute value """
        return self.root.attribute('name')

    def get_type(self):
        """ gets the <xs:simpleType xsi:type=""/> attribute value """
        return self.root.attribute('type')
        
    def add_children(self, list):
        """ add <xs:enumeration/> nested types """
        for e in self.root.childrenAtPath('restriction/enumeration'):
            list.append(Enumeration(self.schema, e))
        return list


class Sequence(SchemaProperty):
    
    """ Represents an (xsd) schema <xs:sequence/> node """
    
    def __init__(self, schema, root):
        """ create the object with a schema and root node """
        SchemaProperty.__init__(self, schema, root)

    def add_children(self, list):
        """ add <xs:element/> nested types """
        for e in self.root.getChildren('element'):
            list.append(Element(self.schema, e))


class ComplexContent(SchemaProperty):
    
    """ Represents an (xsd) schema <xs:complexContent/> node """
    
    def __init__(self, schema, root):
        """ create the object with a schema and root node """
        SchemaProperty.__init__(self, schema, root)

    def add_children(self, list):
        """ add <xs:extension/> nested types """
        for e in self.root.getChildren('extension'):
            extension = Extension(self.schema, e)
            extension.add_children(list)


class Enumeration(SchemaProperty):
    
    """ Represents an (xsd) schema <xs:enumeration/> node """

    def __init__(self, schema, root):
        """ create the object with a schema and root node """
        SchemaProperty.__init__(self, schema, root)
        
    def get_name(self):
        """ gets the <xs:enumeration value=""/> attribute value """
        return self.root.attribute('attribute')

    
class Element(SchemaProperty):
    
    """ Represents an (xsd) schema <xs:element/> node """
    
    def __init__(self, schema, root):
        """ create the object with a schema and root node """
        SchemaProperty.__init__(self, schema, root)
        
    def get_name(self):
        """ gets the <xs:element name=""/> attribute value """
        return self.root.attribute('name')
    
    def get_type(self):
        """ gets the <xs:element type=""/> attribute value """
        return self.root.attribute('type')
    
    def add_children(self, list):
        """ add <complexType/>/* nested nodes """
        for c in self.root.getChildren('complexType'):
            complex = Complex(self.schema, c)
            complex.add_children(list)
    
    def unbounded(self):
        """ get whether the element has a maxOccurs > 1 or unbounded """
        max = self.root.attribute('maxOccurs', default=1)
        return ( max > 1 or max == 'unbounded' )


class Extension(Complex):
    
    """ Represents an (xsd) schema <xs:extension/> node """
    
    def __init__(self, schema, root):
        """ create the object with a schema and root node """
        Complex.__init__(self, schema, root)

    def add_children(self, list):
        """ lookup extended type and add its children then add nested types """
        super = self.schema.get_type(self.root.attribute('base'))
        if super is not None:
            super.add_children(list)
        Complex.add_children(self, list)

