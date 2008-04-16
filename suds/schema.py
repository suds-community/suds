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
from sax import Parser, splitPrefix
from urlparse import urljoin


class SchemaCollection(list):
    
    """ a collection of schemas providing a wrapper """

    def get_type(self, path, history=None):
        """ see Schema.get_type() """
        if history is None:
            history = []
        for s in self:
            result = s.get_type(path, history)
            if result is not None:
                return result
        return None

    def custom(self, ref, context=None):
        """ get whether specified type reference is custom """
        return self[0].custom(ref, context)
    
    def builtin(self, ref, context=None):
        """ get whether the specified type reference is an (xsd) builtin """
        return self[0].builtin(ref, context)


class Schema:
    
    """
    The schema is an objectification of a <schema/> (xsd) definition.
    It provides inspection, lookup and type resolution. 
    """

    factory =\
    {
        'import' : lambda x, y: Import(x, y),
        'complexType' : lambda x,y: Complex(x, y),
        'simpleType' : lambda x,y: Simple(x, y),
        'element' : lambda x,y: Element(x, y)
    }
    
    def __init__(self, root, baseurl=None):
        """ construct the sequence object with a schema """
        self.root = root
        self.tns = self.get_tns()
        self.baseurl = baseurl
        self.log = logger('schema')
        self.hints = {}
        self.types = {}
        self.children = []
        self.__add_children()
                
    def __add_children(self):
        """ populate the list of children """
        for node in self.root.children:
            if node.name in self.factory:
                cls = self.factory[node.name]
                child = cls(self, node)
                self.children.append(child)
        self.children.sort()
                
    def get_tns(self):
        """ get the target namespace """
        tns = [None, self.root.attribute('targetNamespace')]
        if tns[1] is not None:
            tns[0] = self.root.findPrefix(tns[1])
        return tuple(tns)
        
    def get_type(self, path, history=None):
        """
        get the definition object for the schema type located at the specified path.
        The path may contain (.) dot notation to specify nested types.
        The cached type is returned, else find_type() is used.  The history prevents
        cyclic graphs.
        """
        if history is None:
            history = []   
        result = self.types.get(path, None)
        if result is None or result in history:
            result = self.__find_path(path, history)
            if result is not None:
                self.types[path] = result
        return result

    def custom(self, ref, context=None):
        """ get whether specified type reference is custom """
        if ref is None:
            return False
        else:
            return ( not self.builtin(ref, context) )
    
    def builtin(self, ref, context=None):
        """ get whether the specified type reference is an (xsd) builtin """
        try:
            if context is None:
                context = self.root
            prefix = splitPrefix(ref)[0]
            prefixes = context.findPrefixes('http://www.w3.org', 'startswith')
            return ( prefix in prefixes )
        except:
            return False
    
    def __find_path(self, path, history):
        """
        get the definition object for the schema type located at the specified path.
        The path may contain (.) dot notation to specify nested types.
        """
        result = None
        parts = path.split('.')
        ref, ns = self.qualified_reference(parts[0])
        for child in self.children:           
            name = child.get_name()
            if name is None:
                result = child.get_child(ref, ns)
                if result in history:
                    continue
                if result is not None:
                    break
            else:
                if child.match(ref, ns):
                    result = child
                    if result not in history:
                        break
        if result is not None:
            history.append(result)
            result = result.resolve(history)
            for name in parts[1:]:
                ref, ns = self.qualified_reference(name)
                result = result.get_child(ref, ns)
                if result is None:
                    break
                result = result.resolve(history)
        return result
    
    def qualified_reference(self, ref):
        """ get type reference *qualified* by namespace w/ prefix stripped """
        prefix, name = splitPrefix(ref)
        if prefix is None:
            ns = self.tns
        else:
            ns = self.root.resolvePrefix(prefix, None)
        return (name, ns)
    
    def __str__(self):
        return unicode(self).encode('utf-8')
    
    def __unicode__(self):
        return unicode(self.root.str())


class SchemaProperty:
    
    """
    A schema property is an extension to property object with
    with schema awareness.
    """   

    def __init__(self, schema, root):
        """ create the object with a schema and root node """
        self.root = root
        self.schema = schema
        self.log = schema.log
        self.children = []
        
    def match(self, name, ns=None):
        """ match by name and optional namespace """
        myns = self.namespace()
        myname = self.get_name()
        if ns is None:
            return ( myname == name )
        else:
            return ( myns[1] == ns[1] and myname == name )
        
    def namespace(self):
        """ get this properties namespace """
        return self.schema.tns
        
    def get_name(self):
        """ get the object's name """
        return None
    
    def get_type(self):
        """ get the node's (xsi) type as defined by the schema """
        return None
    
    def get_children(self, empty=None):
        """ get child (nested) schema definition nodes """ 
        list = self.children
        if len(list) == 0 and empty is not None:
            list = empty
        return list
    
    def get_child(self, name, ns):
        """ get a child by name """
        for child in self.get_children():
            if child.match(name, ns):
                return child
        return None
    
    def unbounded(self):
        """ get whether this node's specifes that it is unbounded (collection) """
        return False
    
    def resolve(self, history):
        """ return the nodes true type when another named type is referenced. """
        if history is None:
            history = []
        result = self
        reftype = self.get_type()
        if self.custom():
            resolved = self.schema.get_type(reftype, history)
            if resolved is not None:
                result = resolved
        return result
    
    def custom(self):
        """ get whether this object schema type is custom """
        ref = self.get_type()
        return self.schema.custom(ref)
    
    def builtin(self):
        """ get whether this object schema type is an (xsd) builtin """
        ref = self.get_type()
        return self.schema.builtin(ref)
        
    def __str__(self):
        return unicode(self).encode('utf-8')
            
    def __unicode__(self):
        return u'ns=%s, name=(%s), type=(%s)' \
            % (self.namespace(),
                  self.get_name(),
                  self.get_type())
    
    def __repr__(self):
        return unicode(self).encode('utf-8')


class Complex(SchemaProperty):
    
    """ Represents an (xsd) schema <xs:complexType/> node """
    
    def __init__(self, schema, root):
        """ create the object with a schema and root node """
        SchemaProperty.__init__(self, schema, root)
        self.__add_children()
        
    def get_name(self):
        """ gets the <xs:complexType name=""/> attribute value """
        return self.root.attribute('name')
        
    def __add_children(self):
        """ add <xs:sequence/> and <xs:complexContent/> nested types """
        for s in self.root.getChildren('sequence'):
            seq = Sequence(self.schema, s)
            for sc in seq.children:
                self.children.append(sc)
        for s in self.root.getChildren('complexContent'):
            cont = ComplexContent(self.schema, s)
            for cc in cont.children:
                self.children.append(cc)


class Simple(SchemaProperty):
    
    """ Represents an (xsd) schema <xs:simpleType/> node """
    
    def __init__(self, schema, root):
        """ create the object with a schema and root node """
        SchemaProperty.__init__(self, schema, root)
        self.__add_children()

    def get_name(self):
        """ gets the <xs:simpleType name=""/> attribute value """
        return self.root.attribute('name')

    def get_type(self):
        """ gets the <xs:simpleType xsi:type=""/> attribute value """
        return self.root.attribute('type')
        
    def __add_children(self):
        """ add <xs:enumeration/> nested types """
        for e in self.root.childrenAtPath('restriction/enumeration'):
            enum = Enumeration(self.schema, e)
            self.children.append(enum)


class Sequence(SchemaProperty):
    
    """ Represents an (xsd) schema <xs:sequence/> node """
    
    def __init__(self, schema, root):
        """ create the object with a schema and root node """
        SchemaProperty.__init__(self, schema, root)
        self.__add_children()

    def __add_children(self):
        """ add <xs:element/> nested types """
        for e in self.root.getChildren('element'):
            element = Element(self.schema, e)
            self.children.append(element)


class ComplexContent(SchemaProperty):
    
    """ Represents an (xsd) schema <xs:complexContent/> node """
    
    def __init__(self, schema, root):
        """ create the object with a schema and root node """
        SchemaProperty.__init__(self, schema, root)
        self.__add_children()

    def __add_children(self):
        """ add <xs:extension/> nested types """
        for e in self.root.getChildren('extension'):
            extension = Extension(self.schema, e)
            for ec in extension.children:
                self.children.append(ec)


class Enumeration(SchemaProperty):
    
    """ Represents an (xsd) schema <xs:enumeration/> node """

    def __init__(self, schema, root):
        """ create the object with a schema and root node """
        SchemaProperty.__init__(self, schema, root)
        
    def get_name(self):
        """ gets the <xs:enumeration value=""/> attribute value """
        return self.root.attribute('value')

    
class Element(SchemaProperty):
    
    """ Represents an (xsd) schema <xs:element/> node """
    
    def __init__(self, schema, root):
        """ create the object with a schema and root node """
        SchemaProperty.__init__(self, schema, root)
        self.__add_children()
        
    def get_name(self):
        """ gets the <xs:element name=""/> attribute value """
        return self.root.attribute('name')
    
    def get_type(self):
        """ gets the <xs:element type=""/> attribute value """
        return self.root.attribute('type')
    
    def __add_children(self):
        """ add <complexType/>/* nested nodes """
        for c in self.root.getChildren('complexType'):
            complex = Complex(self.schema, c)
            for cc in complex.children:
                self.children.append(cc)
    
    def unbounded(self):
        """ get whether the element has a maxOccurs > 1 or unbounded """
        max = self.root.attribute('maxOccurs', default=1)
        return ( max > 1 or max == 'unbounded' )
    
    def __cmp__(self, other):
        """ <element/> before types """
        if not isinstance(other, Import):
            return -1
        else:
            return 0


class Extension(Complex):
    
    """ Represents an (xsd) schema <xs:extension/> node """
    
    def __init__(self, schema, root):
        """ create the object with a schema and root node """
        Complex.__init__(self, schema, root)
        self.__add_children()

    def __add_children(self):
        """ lookup extended type and add its children then add nested types """
        super = self.schema.get_type(self.root.attribute('base'))
        if super is None:
            return
        index = 0
        for sc in super.children:
            self.children.insert(index, sc)
            index += 1


class Import(SchemaProperty):
    
    """ Represents an (xsd) schema <xs:import/> node """
    
    def __init__(self, schema, root):
        """ create the object with a schema and root node """
        SchemaProperty.__init__(self, schema, root)   
        self.imported = None
        location = root.attribute('schemaLocation')
        if location is not None:
            self.__import(location)
        self.__add_children()

    def namespace(self):
        """ get this properties namespace """
        return self.imported.tns

    def __add_children(self):
        """ add imported children """
        if self.imported is not None:
            for ic in self.imported.children:
                self.children.append(ic)

    def __import(self, uri):
        """ import the xsd content at the specified url """
        p = Parser()
        try:           
            if '://' not in uri:
                uri = urljoin(self.schema.baseurl, uri)
            imp_root = p.parse(url=uri).root()
            self.imported = Schema(imp_root, uri)
            self.__update_tns(imp_root)
            self.root.parent.replaceChild(self.root, imp_root)
            self.root = imp_root
            self.log.debug('schema at (%s)\n\timported with tns=%s', uri, self.namespace())
        except tuple, e:
            self.log.error('imported schema at (%s), not-found\n\t%s', uri, unicode(e))
            
    def __update_tns(self, imp_root):
        """
        update the target namespace when the schema is imported
        specifying another namespace
        """
        impuri = self.root.attribute('namespace')
        if impuri is None:
            return
        prefixes = (imp_root.findPrefix(impuri), self.root.findPrefix(impuri))
        if prefixes[1] is None:
            return
        self.log.debug('imported (%s), prefix remapped as (%s)', impuri, prefixes[1])
        self.imported.tns = (prefixes[1], impuri)
        if prefixes[0] is None:
            return
        if prefixes[0] == prefixes[1]:
            return
        imp_root.clearPrefix(prefixes[0])
        imp_root.addPrefix(prefixes[1], impuri)
        self.__update_references(imp_root, prefixes)
        
    def __update_references(self, imp_root, prefixes):
        """ update all attributes with references to the old prefix to the new prefix """
        for a in imp_root.flattenedAttributes():
            value = a.getValue()
            if value is None: continue
            if ':' in value:
                p = value.split(':')
                if p[0] == prefixes[0]:
                    value = ':'.join((prefixes[1], value[1]))
                    a.setValue(value)
        
    def __cmp__(self, other):
        """ <import/> first """
        return -1

        