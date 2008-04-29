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
from sax import Parser, splitPrefix, defns
from urlparse import urljoin


def qualified_reference(ref, resolvers, tns=defns):
    """ get type reference *qualified* by prefix and namespace """
    ns = tns
    p, n = splitPrefix(ref)
    if p is not None:
        if not isinstance(resolvers, (list,tuple)):
            resolvers = (resolvers,)
        for r in resolvers:
            resolved = r.resolvePrefix(p)
            if resolved[1] is not None:
                ns = resolved
                break 
    return (n, ns)

def isqref(object):
    """ get whether the object is a qualified reference """
    return (\
        isinstance(object, tuple) and \
        len(object) == len(defns) and \
        isinstance(object[0], basestring) and \
        isinstance(object[1], tuple) and \
        len(object[1]) == len(defns) )


class SchemaCollection(list):
    
    """ a collection of schemas providing a wrapper """
    
    def __init__(self, wsdl):
        self.root = wsdl.root
        self.tns = wsdl.tns
        self.log = logger('schema')
        
    def imported(self, ns):
        """ find schema imported by namespace """
        for s in self:
            if s.tns[1] == ns[1]:
                return s
        return None

    def find(self, path, history=None):
        """ see Schema.find() """
        if history is None:
            history = []
        for s in self:
            result = s.find(path, history)
            if result is not None:
                return result
        return None
    
    def __str__(self):
        return unicode(self).encode('utf-8')
    
    def __unicode__(self):
        result = []
        for s in self:
            result.append(unicode(s))
        return '\n'.join(result)


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
    
    def __init__(self, root, baseurl=None, container=None):
        """ construct the sequence object with a schema """
        self.log = logger('schema')
        self.root = root
        self.tns = self.__tns()
        self.baseurl = baseurl
        self.container = container
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
                if isinstance(child, Import):
                    self.children += child.children
                else:
                    self.children.append(child)
        self.children.sort()
                
    def __tns(self):
        """ get the target namespace """
        tns = [None, self.root.attribute('targetNamespace')]
        if tns[1] is not None:
            tns[0] = self.root.findPrefix(tns[1])
        return tuple(tns)
        
    def imported(self, ns):
        """ find schema imported by namespace """
        if self.container is not None:
            return self.container.imported(ns)
        else:
            return None
        
    def find(self, path, history=None):
        """
        get the definition object for the schema type located at the specified path.
        The path may contain (.) dot notation to specify nested types.
        The cached type is returned, else find_type() is used.  The history prevents
        cyclic graphs.
        """
        if history is None:
            history = []
        if isinstance(path, basestring):
            cached = self.types.get(path, None)
            if cached is not None:
                return cached
        if self.builtin(path):
            b = XBuiltin(self, path)
            return b
        result = self.__find_path(path, history)
        if result is not None and \
            isinstance(path, basestring):
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
        w3 = 'http://www.w3.org'
        try:
            if self.isqref(ref):
                ns = ref[1]
                return ns[1].startswith(w3)
            if context is None:
                context = self.root    
            prefix = splitPrefix(ref)[0]
            prefixes = context.findPrefixes(w3, 'startswith')
            return ( prefix in prefixes )
        except:
            return False
    
    def isqref(self, object):
        """ get whether the object is a qualified reference """
        return isqref(object)
    
    def reset_tns(self, ns):
        """ reset the target namespace """
        uA = self.tns[1]
        uB = ns[1]
        if uA != uB:
            self.root.replaceNamespace(uA, uB)
            self.tns = (None, uB)      
    
    def __find_path(self, path, history):
        """
        get the definition object for the schema type located at the specified path.
        The path may contain (.) dot notation to specify nested types.
        """
        result = None
        parts = self.__qualify(path)
        ref, ns = parts[0]
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
            for part in parts[1:]:
                ref, ns = part
                result = result.get_child(ref, ns)
                if result is None:
                    break
                result = result.resolve(history)
        return result
    
    def __qualify(self, path):
        """ convert the path into a list of qualified references """
        if isinstance(path, basestring):
            qualified = []
            for p in path.split('.'):
                if isinstance(p, basestring):
                    p = qualified_reference(p, self.root, self.tns)
                    qualified.append(p)
            return qualified
        if self.isqref(path):
            path = (path,)
        return path
    
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
    
    def ref(self):
        """ get the referenced (xsi) type as defined by the schema """
        return None
    
    def qref(self):
        """ get the qualified referenced (xsi) type as defined by the schema """
        ref = self.ref()
        if ref is not None:
            return qualified_reference(ref, self.root, self.schema.tns)
        else:
            return (None, defns)
        
    def asref(self):
        """ get the types true type as need for external qualified reference """
        ref = self.ref()
        if ref is None:
            name = self.get_name()
            ns = self.namespace()
        else:
            qref = qualified_reference(ref, self.root, self.schema.tns)
            name = qref[0]
            ns = qref[1]
        return (':'.join((ns[0], name)), ns)
    
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
        if self.custom():
            ref = qualified_reference(self.ref(), self.root, self.namespace())
            resolved = self.schema.find(ref, history)
            if resolved is not None:
                result = resolved
        return result
    
    def custom(self):
        """ get whether this object schema type is custom """
        ref = self.ref()
        if ref is not None:
            return self.schema.custom(ref)
        else:
            return False
    
    def builtin(self):
        """ get whether this object schema type is an (xsd) builtin """
        ref = self.ref()
        if ref is None:
            return self.schema.builtin(ref)
        else:
            return False
        
    def __str__(self):
        return unicode(self).encode('utf-8')
            
    def __unicode__(self):
        return u'ns=%s, name=(%s), qref=%s' \
            % (self.namespace(),
                  self.get_name(),
                  self.qref())
    
    def __repr__(self):
        return unicode(self).encode('utf-8')
    
    def __len__(self):
        return len(self.children)
    
    def __getitem__(self, index):
        return self.children[index]


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

    def ref(self):
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
    
    def ref(self):
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
        super = self.schema.find(self.root.attribute('base'))
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
        ns = (None, root.attribute('namespace'))
        location = root.attribute('schemaLocation')
        self.__import(ns, location)
        self.__add_children()

    def namespace(self):
        """ get this properties namespace """
        return self.imported.tns

    def __add_children(self):
        """ add imported children """
        if self.imported is not None:
            for ic in self.imported.children:
                self.children.append(ic)

    def __import(self, ns, location):
        """ import the xsd content at the specified url """
        try:
            if location is None:
                schema = self.schema.imported(ns)
                if schema is not None:
                    imp_root = schema.root.clone()
                    location = ns[1]
                    self.__process_import(imp_root, ns, location)
                    return
                else:
                    location = ns[1]
            if '://' not in location:
                location = urljoin(self.schema.baseurl, location)
            imp_root = Parser().parse(url=location).root()
            self.__process_import(imp_root, ns, location)
        except Exception, e:
            self.log.debug(
                'imported schema at (%s), not-found\n\t%s', 
                location, unicode(e))
            
    def __process_import(self, imp_root, ns, location):
        """ process the imported schema """
        schema = Schema(imp_root, location)
        schema.reset_tns(ns)
        self.imported = schema
        
    def __cmp__(self, other):
        """ <import/> first """
        return -1


class XBuiltin(SchemaProperty):
    
    """ Represents an (xsd) schema <xs:*/> node """
    
    def __init__(self, schema, name):
        SchemaProperty.__init__(self, schema, schema.root)
        if schema.isqref(name):
            ns = name[1]
            self.name = ':'.join((ns[0], name[0]))
        else:
            self.name = name
        
    def builtin(self):
        return False
    
    def custom(self):
        return False
        
    def ref(self):
        return self.name