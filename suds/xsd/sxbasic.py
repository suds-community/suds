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
The I{sxbasic} module provides classes that represent
I{basic} schema objects.
"""

from logging import getLogger
from suds import *
from suds.xsd import *
from suds.xsd.sxbase import *
from suds.xsd.query import *
from suds.sax import splitPrefix, Namespace
from suds.sax.parser import Parser
from suds.transport import TransportError
from urlparse import urljoin


log = getLogger(__name__)


class Factory:
    """
    @cvar tags: A factory to create object objects based on tag.
    @type tags: {tag:fn,}
    """

    tags =\
    {
        'import' : lambda x,y: Import(x,y),
        'include' : lambda x,y: Include(x,y), 
        'complexType' : lambda x,y: Complex(x,y),
        'group' : lambda x,y: Group(x,y),
        'attributeGroup' : lambda x,y: AttributeGroup(x,y), 
        'simpleType' : lambda x,y: Simple(x,y), 
        'element' : lambda x,y: Element(x,y),
        'attribute' : lambda x,y: Attribute(x,y),
        'sequence' : lambda x,y: Sequence(x,y),
        'all' : lambda x,y: All(x,y),
        'choice' : lambda x,y: Choice(x,y),
        'complexContent' : lambda x,y: ComplexContent(x,y),
        'simpleContent' : lambda x,y: SimpleContent(x,y),
        'restriction' : lambda x,y: Restriction(x,y),
        'enumeration' : lambda x,y: Enumeration(x,y),
        'extension' : lambda x,y: Extension(x,y),
        'any' : lambda x,y: Any(x,y),
    }
    
    @classmethod
    def create(cls, root, schema):
        """
        Create an object based on the root tag name.
        @param root: An XML root element.
        @type root: L{Element}
        @param schema: A schema object.
        @type schema: L{schema.Schema}
        @return: The created object.
        @rtype: L{SchemaObject} 
        """
        fn = cls.tags.get(root.name)
        if fn is not None:
            return fn(schema, root)
        else:
            return None

    @classmethod
    def build(cls, root, schema, filter=('*',)):
        """
        Build an xsobject representation.
        @param root: An schema XML root.
        @type root: L{sax.element.Element}
        @param filter: A tag filter.
        @type filter: [str,...]
        @return: A schema object graph.
        @rtype: L{sxbase.SchemaObject}
        """
        children = []
        for node in root.getChildren(ns=Namespace.xsdns):
            if '*' in filter or node.name in filter:
                child = cls.create(node, schema)
                if child is None:
                    continue
                children.append(child)
                c = cls.build(node, schema, child.childtags())
                child.rawchildren = c
        return children
    
    @classmethod
    def collate(cls, children):
        imports = []
        elements = {}
        attributes = {}
        types = {}
        groups = {}
        agrps = {}
        for c in children:
            if isinstance(c, (Import, Include)):
                imports.append(c)
                continue
            if isinstance(c, Attribute):
                attributes[c.qname] = c
                continue
            if isinstance(c, Element):
                elements[c.qname] = c
                continue
            if isinstance(c, Group):
                groups[c.qname] = c
                continue
            if isinstance(c, AttributeGroup):
                agrps[c.qname] = c
                continue
            types[c.qname] = c
        for i in imports:
            children.remove(i)
        return (children, imports, attributes, elements, types, groups, agrps)
    

class TypedContent(Content):

    def resolve(self, nobuiltin=False):
        """
        Resolve and return the nodes true self.
        @param nobuiltin: Flag indicates that resolution must
            not continue to include xsd builtins.
        @return: The resolved (true) type.
        @rtype: L{SchemaObject}
        """
        if self.type is None:
            return self
        cached = self.cache.get(nobuiltin)
        if cached is not None:
            return cached
        result = self
        defns = self.root.defaultNamespace()
        qref = qualify(self.type, self.root, defns)
        query = TypeQuery(qref)
        query.history = [self]
        log.debug('%s, resolving: %s\n using:%s', self.id, qref, query)
        resolved = query.execute(self.schema)
        if resolved is None:
            log.debug(self.schema)
            raise TypeNotFound(qref)
        if resolved.builtin():
            if nobuiltin:
                result = self
            else:
                result = resolved
        else:
            result = resolved.resolve(nobuiltin)
        return result



class Complex(SchemaObject):
    """
    Represents an (xsd) schema <xs:complexType/> node.
    @cvar childtags: A list of valid child node names
    @type childtags: (I{str},...)
    """
        
    def childtags(self):
        """
        Get a list of valid child tag names.
        @return: A list of child tag names.
        @rtype: [str,...]
        """
        return (
            'attribute', 
            'attributeGroup', 
            'sequence', 
            'all', 
            'choice', 
            'complexContent',
            'simpleContent', 
            'any', 
            'group')

    def description(self):
        """
        Get the names used for str() and repr() description.
        @return:  A dictionary of relavent attributes.
        @rtype: [str,...]
        """
        return ('name',)
    
    def extension(self):
        """
        Get whether the object contains an extension/restriction
        @return: True if a restriction, else False.
        @rtype: boolean
        """
        for c in self.rawchildren:
            if c.extension():
                return True
        return False


class Group(SchemaObject):
    """
    Represents an (xsd) schema <xs:group/> node.
    @cvar childtags: A list of valid child node names
    @type childtags: (I{str},...)
    """
    
    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{schema.Schema}
        @param root: The xml root node.
        @type root: L{sax.element.Element}
        """
        SchemaObject.__init__(self, schema, root)
        self.min = root.get('minOccurs', default='1')
        self.max = root.get('maxOccurs', default='1')
        
    def childtags(self):
        """
        Get a list of valid child tag names.
        @return: A list of child tag names.
        @rtype: [str,...]
        """
        return ('sequence', 'all', 'choice')
    
    def unbounded(self):
        """
        Get whether this node is unbounded I{(a collection)}.
        @return: True if unbounded, else False.
        @rtype: boolean
        """
        if self.max.isdigit():
            return (int(self.max) > 1)
        else:
            return ( self.max == 'unbounded' )
        
    def optional(self):
        """
        Get whether this type is optional.
        @return: True if optional, else False
        @rtype: boolean
        """
        return ( self.min == '0' )
        
    def dependencies(self):
        """
        Get a list of dependancies for dereferencing.
        @return: A merge dependancy index and a list of dependancies.
        @rtype: (int, [L{SchemaObject},...])
        """
        deps = []
        midx = None
        if self.ref is not None:     
            defns = self.default_namespace()
            qref = qualify(self.ref, self.root, defns)
            query = GroupQuery(qref)
            g = query.execute(self.schema)
            if g is None:
                log.debug(self.schema)
                raise TypeNotFound(qref)
            deps.append(g)
            midx = 0
        return (midx, deps)
    
    def merge(self, g):
        """
        Merge the referenced object.
        @param g: A resoleve reference.
        @type g: L{Group}
        """
        self.name = g.name
        self.qname = g.qname
        self.rawchildren = g.rawchildren

    def description(self):
        """
        Get the names used for str() and repr() description.
        @return:  A dictionary of relavent attributes.
        @rtype: [str,...]
        """
        return ('name', 'ref',)
    

class AttributeGroup(SchemaObject):
    """
    Represents an (xsd) schema <xs:attributeGroup/> node.
    @cvar childtags: A list of valid child node names
    @type childtags: (I{str},...)
    """
    
    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{schema.Schema}
        @param root: The xml root node.
        @type root: L{sax.element.Element}
        """
        SchemaObject.__init__(self, schema, root)
        self.min = root.get('minOccurs', default='1')
        self.max = root.get('maxOccurs', default='1')
        
    def childtags(self):
        """
        Get a list of valid child tag names.
        @return: A list of child tag names.
        @rtype: [str,...]
        """
        return ('attribute', 'attributeGroup')

    def dependencies(self):
        """
        Get a list of dependancies for dereferencing.
        @return: A merge dependancy index and a list of dependancies.
        @rtype: (int, [L{SchemaObject},...])
        """
        deps = []
        midx = None
        if self.ref is not None:
            defns = self.default_namespace()
            qref = qualify(self.ref, self.root, defns)
            query = AttrGroupQuery(qref)
            ag = query.execute(self.schema)
            if ag is None:
                log.debug(self.schema)
                raise TypeNotFound(qref)
            deps.append(ag)
            midx = 0
        return (midx, deps)
    
    def merge(self, ag):
        """
        Merge the referenced object.
        @param ag: A resoleve reference.
        @type ag: L{AttributeGroup}
        """
        self.name = ag.name
        self.qname = ag.qname
        self.rawchildren = ag.rawchildren

    def description(self):
        """
        Get the names used for str() and repr() description.
        @return:  A dictionary of relavent attributes.
        @rtype: [str,...]
        """
        return ('name', 'ref',)
    

class Simple(SchemaObject):
    """
    Represents an (xsd) schema <xs:simpleType/> node
    """

    def childtags(self):
        """
        Get a list of valid child tag names.
        @return: A list of child tag names.
        @rtype: [str,...]
        """
        return ('restriction', 'any',)
    
    def enum(self):
        """
        Get whether this is a simple-type containing an enumeration.
        @return: True if any, else False
        @rtype: boolean
        """
        for child, ancestry in self.children():
            if isinstance(child, Enumeration):
                return True
        return False

    def description(self):
        """
        Get the names used for str() and repr() description.
        @return:  A dictionary of relavent attributes.
        @rtype: [str,...]
        """
        return ('name',)
    
    def extension(self):
        """
        Get whether the object contains a restriction
        @return: True if a restriction, else False.
        @rtype: boolean
        """
        for c in self.rawchildren:
            if c.extension():
                return True
        return False

   
class Restriction(SchemaObject):
    """
    Represents an (xsd) schema <xs:restriction/> node
    """
    
    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{schema.Schema}
        @param root: The xml root node.
        @type root: L{sax.element.Element}
        """
        SchemaObject.__init__(self, schema, root)
        self.ref = root.get('base')

    def childtags(self):
        """
        Get a list of valid child tag names.
        @return: A list of child tag names.
        @rtype: [str,...]
        """
        return ('enumeration', 'attribute', 'attributeGroup')
    
    def dependencies(self):
        """
        Get a list of dependancies for dereferencing.
        @return: A merge dependancy index and a list of dependancies.
        @rtype: (int, [L{SchemaObject},...])
        """
        deps = []
        midx = None
        if self.ref is not None:
            defns = self.default_namespace()
            qref = qualify(self.ref, self.root, defns)
            query = TypeQuery(qref)
            super = query.execute(self.schema)
            if super is None:
                log.debug(self.schema)
                raise TypeNotFound(qref)
            if not super.builtin():
                deps.append(super)
                midx = 0
        return (midx, deps)

    def merge(self, b):
        """
        Merge the resolved I{base} object with myself.
        @param b: A resolved base object.
        @type b: L{SchemaObject}
        """
        filter = Filter(False, self.rawchildren)
        self.prepend(self.rawchildren, b.rawchildren, filter)
        
    def extension(self):
        """
        Get whether the object is an extension/restriction
        @return: True if an extension/restriction, else False.
        @rtype: boolean
        """
        return ( self.ref is not None )
        
    def description(self):
        """
        Get the names used for str() and repr() description.
        @return:  A dictionary of relavent attributes.
        @rtype: [str,...]
        """
        return ('ref',)
    
    
class Collection(SchemaObject):
    """
    Represents an (xsd) schema collection node:
        - sequence
        - choice
        - all
    """

    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{schema.Schema}
        @param root: The xml root node.
        @type root: L{sax.element.Element}
        """
        SchemaObject.__init__(self, schema, root)
        self.min = root.get('minOccurs', default='1')
        self.max = root.get('maxOccurs', default='1')

    def childtags(self):
        """
        Get a list of valid child tag names.
        @return: A list of child tag names.
        @rtype: [str,...]
        """
        return ('element', 'sequence', 'all', 'choice', 'any', 'group')
    
    def unbounded(self):
        """
        Get whether this node is unbounded I{(a collection)}.
        @return: True if unbounded, else False.
        @rtype: boolean
        """
        if self.max.isdigit():
            return (int(self.max) > 1)
        else:
            return ( self.max == 'unbounded' )
        
    def optional(self):
        """
        Get whether this type is optional.
        @return: True if optional, else False
        @rtype: boolean
        """
        return ( self.min == '0' )


class Sequence(Collection):
    """
    Represents an (xsd) schema <xs:sequence/> node.
    """
    def sequence(self):
        """
        Get whether this is an <xs:sequence/>
        @return: True if any, else False
        @rtype: boolean
        """
        return True

class All(Collection):
    """
    Represents an (xsd) schema <xs:all/> node.
    """
    def all(self):
        """
        Get whether this is an <xs:all/>
        @return: True if any, else False
        @rtype: boolean
        """
        return True

class Choice(Collection):
    """
    Represents an (xsd) schema <xs:choice/> node.
    """
    def choice(self):
        """
        Get whether this is an <xs:choice/>
        @return: True if any, else False
        @rtype: boolean
        """
        return True


class ComplexContent(SchemaObject):
    """
    Represents an (xsd) schema <xs:complexContent/> node.
    """
        
    def childtags(self):
        """
        Get a list of valid child tag names.
        @return: A list of child tag names.
        @rtype: [str,...]
        """
        return ('attribute', 'attributeGroup', 'extension', 'restriction')
    
    def extension(self):
        """
        Get whether the object contains an extension/restriction
        @return: True if a restriction, else False.
        @rtype: boolean
        """
        for c in self.rawchildren:
            if c.extension():
                return True
        return False


class SimpleContent(SchemaObject):
    """
    Represents an (xsd) schema <xs:simpleContent/> node.
    """
        
    def childtags(self):
        """
        Get a list of valid child tag names.
        @return: A list of child tag names.
        @rtype: [str,...]
        """
        return ('extension', 'restriction')
    
    def extension(self):
        """
        Get whether the object contains a restriction
        @return: True if a restriction, else False.
        @rtype: boolean
        """
        for c in self.rawchildren:
            if c.extension():
                return True
        return False


class Enumeration(Content):
    """
    Represents an (xsd) schema <xs:enumeration/> node
    """

    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{schema.Schema}
        @param root: The xml root node.
        @type root: L{sax.element.Element}
        """
        Content.__init__(self, schema, root)
        self.name = root.get('value')
        
    def enum(self):
        """
        Get whether this is an enumeration.
        @return: True
        @rtype: boolean
        """
        return True

    
class Element(TypedContent):
    """
    Represents an (xsd) schema <xs:element/> node.
    """
    
    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{schema.Schema}
        @param root: The xml root node.
        @type root: L{sax.element.Element}
        """
        TypedContent.__init__(self, schema, root)
        self.min = root.get('minOccurs', default='1')
        self.max = root.get('maxOccurs', default='1')
        a = root.get('form')
        if a is not None:
            self.form_qualified = ( a == 'qualified' )
        a = self.root.get('nillable')
        if a is not None:
            self.nillable = ( a in ('1', 'true') )
        if self.type is None and self.root.isempty():
            self.type = self.anytype()
        
    def childtags(self):
        """
        Get a list of valid child tag names.
        @return: A list of child tag names.
        @rtype: [str,...]
        """
        return ('attribute', 'simpleType', 'complexType', 'any',)
    
    def extension(self):
        """
        Get whether the object contains a restriction
        @return: True if a restriction, else False.
        @rtype: boolean
        """
        for c in self.rawchildren:
            if c.extension():
                return True
        return False
    
    def unbounded(self):
        """
        Get whether this node is unbounded I{(a collection)}.
        @return: True if unbounded, else False.
        @rtype: boolean
        """
        if self.max.isdigit():
            return (int(self.max) > 1)
        else:
            return ( self.max == 'unbounded' )
        
    def optional(self):
        """
        Get whether this type is optional.
        @return: True if optional, else False
        @rtype: boolean
        """
        return ( self.min == '0' )
    
    def dependencies(self):
        """
        Get a list of dependancies for dereferencing.
        @return: A merge dependancy index and a list of dependancies.
        @rtype: (int, [L{SchemaObject},...])
        """
        deps = []
        midx = None
        if self.ref is not None:
            defns = self.default_namespace()
            qref = qualify(self.ref, self.root, defns)
            query = ElementQuery(qref)
            e = query.execute(self.schema)
            if e is None:
                log.debug(self.schema)
                raise TypeNotFound(qref)
            deps.append(e)
            midx = 0
        return (midx, deps)
    
    def merge(self, e):
        """
        Merge the referenced object.
        @param e: A resoleve reference.
        @type e: L{Element}
        """
        self.name = e.name
        self.qname = e.qname
        self.type = e.type
        self.rawchildren = e.rawchildren


    def description(self):
        """
        Get the names used for str() and repr() description.
        @return:  A dictionary of relavent attributes.
        @rtype: [str,...]
        """
        return ('name', 'ref', 'type')
        
    def anytype(self):
        """ create an xsd:anyType reference """
        p,u = Namespace.xsdns
        mp = self.root.findPrefix(u)
        if mp is None:
            mp = p
            self.root.addPrefix(p, u)
        return ':'.join((mp, 'anyType'))


class Extension(SchemaObject):
    """
    Represents an (xsd) schema <xs:extension/> node.
    """
    
    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{schema.Schema}
        @param root: The xml root node.
        @type root: L{sax.element.Element}
        """
        SchemaObject.__init__(self, schema, root)
        self.ref = root.get('base')
        
    def childtags(self):
        """
        Get a list of valid child tag names.
        @return: A list of child tag names.
        @rtype: [str,...]
        """
        return ('attribute', 'attributeGroup', 'sequence', 'all', 'choice', 'group')
        
    def dependencies(self):
        """
        Get a list of dependancies for dereferencing.
        @return: A merge dependancy index and a list of dependancies.
        @rtype: (int, [L{SchemaObject},...])
        """
        deps = []
        midx = None
        if self.ref is not None:
            defns = self.default_namespace()
            qref = qualify(self.ref, self.root, defns)
            query = TypeQuery(qref)
            super = query.execute(self.schema)
            if super is None:
                log.debug(self.schema)
                raise TypeNotFound(qref)
            if not super.builtin():
                deps.append(super)
                midx = 0
        return (midx, deps)

    def merge(self, b):
        """
        Merge the resolved I{base} object with myself.
        @param b: A resolved base object.
        @type b: L{SchemaObject}
        """
        filter = Filter(False, self.rawchildren)
        self.prepend(self.rawchildren, b.rawchildren, filter)
        
    def extension(self):
        """
        Get whether the object is an extension/restriction
        @return: True if an extension/restriction, else False.
        @rtype: boolean
        """
        return ( self.ref is not None )

    def description(self):
        """
        Get the names used for str() and repr() description.
        @return:  A dictionary of relavent attributes.
        @rtype: [str,...]
        """
        return ('ref',)


class Import(SchemaObject):
    """
    Represents an (xsd) schema <xs:import/> node
    @cvar locations: A dictionary of namespace locations.
    @type locations: dict
    @ivar ns: The imported namespace.
    @type ns: str
    @ivar location: The (optional) location.
    @type location: namespace-uri
    @ivar opened: Opened and I{imported} flag.
    @type opened: boolean
    """
    
    locations = {}
    
    @classmethod
    def bind(cls, ns, location=None):
        """
        Bind a namespace to a schema location (URI).  
        This is used for imports that don't specify a schemaLocation.
        @param ns: A namespace-uri.
        @type ns: str
        @param location: The (optional) schema location for the
            namespace.  (default=ns).
        @type location: str
        """
        if location is None:
            location = ns
        cls.locations[ns] = location
    
    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{schema.Schema}
        @param root: The xml root node.
        @type root: L{sax.element.Element}
        """
        SchemaObject.__init__(self, schema, root)
        self.ns = (None, root.get('namespace'))
        self.location = root.get('schemaLocation')
        if self.location is None:
            self.location = self.locations.get(self.ns[1])
        self.opened = False
        
    def open(self):
        """
        Open and import the refrenced schema.
        @return: The referenced schema.
        @rtype: L{Schema}
        """
        if self.opened:
            return
        self.opened = True
        log.debug('%s, importing ns="%s", location="%s"', self.id, self.ns[1], self.location)
        result = self.locate()
        if result is None:
            if self.location is None:
                log.debug('imported schema (%s) not-found', self.ns[1])
            else:
                result = self.download()
        log.debug('imported:\n%s', result)
        return result
    
    def locate(self):
        """ find the schema locally """
        if self.ns[1] == self.schema.tns[1]:
            return None
        else:
            return self.schema.locate(self.ns)

    def download(self):
        """ download the schema """
        url = self.location
        try:
            if '://' not in url:
                url = urljoin(self.schema.baseurl, url)
            transport = self.schema.options.transport
            root = Parser(transport).parse(url=url).root()
            root.set('url', url)
            return self.schema.instance(root, url)
        except TransportError:
            msg = 'imported schema (%s) at (%s), failed' % (self.ns[1], url)
            log.error('%s, %s', self.id, msg, exc_info=True)
            raise Exception(msg)
 
    def description(self):
        """
        Get the names used for str() and repr() description.
        @return:  A dictionary of relavent attributes.
        @rtype: [str,...]
        """
        return ('ns', 'location')
    
    
class Include(Import):
    pass

   
class Attribute(TypedContent):
    """
    Represents an (xsd) <attribute/> node
    """

    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{schema.Schema}
        @param root: The xml root node.
        @type root: L{sax.element.Element}
        """
        TypedContent.__init__(self, schema, root)
        self.use = root.get('use', default='')
        
    def isattr(self):
        """
        Get whether the object is a schema I{attribute} definition.
        @return: True if an attribute, else False.
        @rtype: boolean
        """
        return True

    def get_default(self):
        """
        Gets the <xs:attribute default=""/> attribute value.
        @return: The default value for the attribute
        @rtype: str
        """
        return self.root.get('default', default='')
    
    def optional(self):
        """
        Get whether this type is optional.
        @return: True if optional, else False
        @rtype: boolean
        """
        return ( self.use != 'required' )

    def dependencies(self):
        """
        Get a list of dependancies for dereferencing.
        @return: A merge dependancy index and a list of dependancies.
        @rtype: (int, [L{SchemaObject},...])
        """
        deps = []
        midx = None
        if self.ref is not None:
            defns = self.default_namespace()
            qref = qualify(self.ref, self.root, defns)
            query = AttrQuery(qref)
            a = query.execute(self.schema)
            if a is None:
                log.debug(self.schema)
                raise TypeNotFound(qref)
            deps.append(a)
            midx = 0
        return (midx, deps)
        
    def merge(self, a):
        """
        Merge the referenced object.
        @param a: A resoleve reference.
        @type a: L{Attribute}
        """
        self.name = a.name
        self.qname = a.qname
        self.type = a.type
    
    def description(self):
        """
        Get the names used for str() and repr() description.
        @return:  A dictionary of relavent attributes.
        @rtype: [str,...]
        """
        return ('name', 'ref', 'type')


class Any(Content):
    """
    Represents an (xsd) <any/> node
    """
    
    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{schema.Schema}
        @param root: The xml root node.
        @type root: L{sax.element.Element}
        """
        Content.__init__(self, schema, root)
        self.min = root.get('minOccurs', default='0')
        self.max = root.get('maxOccurs', default='1')

    def get_child(self, name):
        """
        Get (find) a I{non-attribute} child by name and namespace.
        @param name: A child name.
        @type name: basestring
        @return: The requested (child, ancestry).
        @rtype: (L{SchemaObject}, [L{SchemaObject},..])
        """
        root = self.root.clone()
        root.set('minOccurs', '0')
        root.set('maxOccurs', '1')
        root.set('note', 'synthesized (any) child')
        child = Any(self.schema, root)
        return (child, [])
    
    def get_attribute(self, name):
        """
        Get (find) a I{non-attribute} attribute by name.
        @param name: A attribute name.
        @type name: str
        @return: The requested attribute.
        @rtype: L{SchemaObject}
        """
        root = self.root.clone()
        root.set('note', 'synthesized (any) attribute')
        attribute = Any(self.schema, root)
        return (attribute, [])
    
    def any(self):
        """
        Get whether this is an xs:any
        @return: True if any, else False
        @rtype: boolean
        """
        return True
    
    def unbounded(self):
        """
        Get whether this node is unbounded I{(a collection)}.
        @return: True if unbounded, else False.
        @rtype: boolean
        """
        if self.max.isdigit():
            return (int(self.max) > 1)
        else:
            return ( self.max == 'unbounded' )
        
    def optional(self):
        """
        Get whether this type is optional.
        @return: True if optional, else False
        @rtype: boolean
        """
        return ( self.min == '0' )
    


#######################################################
# Static Import Bindings :-(
#######################################################
Import.bind('http://schemas.xmlsoap.org/soap/encoding/')
Import.bind('http://www.w3.org/XML/1998/namespace', 'http://www.w3.org/2001/xml.xsd')
Import.bind('http://www.w3.org/2001/XMLSchema', 'http://www.w3.org/2001/XMLSchema.xsd')
