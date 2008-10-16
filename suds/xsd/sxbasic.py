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
from suds.xsd.query import Query
from suds.sax import splitPrefix
from suds.sax.parser import Parser
from urlparse import urljoin
from copy import copy, deepcopy
from urllib2 import URLError, HTTPError

log = getLogger(__name__)


class Factory:
    """
    @cvar tags: A factory to create object objects based on tag.
    @type tags: {tag:fn,}
    """

    tags =\
    {
        'import' : lambda x,y: Import(x,y), 
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
        attributes = []
        for node in root.children:
            if '*' in filter or node.name in filter:
                child = cls.create(node, schema)
                if child is None:
                    continue
                if child.isattr():
                    attributes.append(child)
                else:
                    children.append(child)
                child.attributes, child.children = \
                    cls.build(node, schema, child.childtags())
        return (attributes, children)
    
    @classmethod
    def collate(cls, children):
        imports = []
        elements = {}
        attributes = {}
        types = {}
        groups = {}
        agrps = {}
        for c in children:
            if isinstance(c, Import):
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


class Complex(SchemaObject):
    """
    Represents an (xsd) schema <xs:complexType/> node.
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
        
    def childtags(self):
        """
        Get a list of valid child tag names.
        @return: A list of child tag names.
        @rtype: [str,...]
        """
        return ('attribute', 'attributeGroup', 'sequence', 'all', 'choice', 'complexContent', 'any', 'group')
    
    def derived(self):
        """
        Get whether the object is derived in the it is an extension
        of another type.
        @return: True if derived, else False.
        @rtype: boolean
        """
        try:
            return self.__derived
        except:
            self.__derived = False
            for c in self.children:
                if c.inherited:
                    self.__derived = True
                    break
        return self.__derived

    def description(self):
        """
        Get the names used for str() and repr() description.
        @return:  A dictionary of relavent attributes.
        @rtype: [str,...]
        """
        return ('name',)


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
        self.ref = root.get('ref')
        self.min = root.get('minOccurs', default='1')
        self.max = root.get('maxOccurs', default='1')
        self.mutated = ( self.ref is None )
        
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
        if self.container_unbounded():
            return True
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
        return ( self.container_optional() or self.min == '0' )
    
    def container_unbounded(self):
        """ get whether container is unbounded """
        if self.container is None:
            return False
        else:
            return self.container.unbounded()
        
    def container_optional(self):
        """ get whether container is optional """
        if self.container is None:
            return False
        else:
            return self.container.optional()
        
    def mutate(self):
        """
        Mutate into a I{true} type as defined by a reference to
        another object.
        """
        if self.mutated:
            return
        self.mutated = True
        classes = (Group,)
        defns = self.default_namespace()
        qref = qualify(self.ref, self.root, defns)
        e = self.schema.groups.get(qref)
        if e is not None:
            self.merge(deepcopy(e))
            return
        for c in self.schema.children:
            p = c.find(qref, classes)
            if p is not None:
                self.merge(deepcopy(p))
                return
        raise TypeNotFound(self.ref)
    
    def merge(self, e):
        """
        Merge the referenced object.
        @param e: A resoleve reference.
        @type e: L{Element}
        """
        self.name = e.name
        self.qname = e.qname
        self.children = e.children

    def description(self):
        """
        Get the names used for str() and repr() description.
        @return:  A dictionary of relavent attributes.
        @rtype: [str,...]
        """
        return ('name',)
    

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
        self.ref = root.get('ref')
        self.min = root.get('minOccurs', default='1')
        self.max = root.get('maxOccurs', default='1')
        self.mutated = ( self.ref is None )
        
    def childtags(self):
        """
        Get a list of valid child tag names.
        @return: A list of child tag names.
        @rtype: [str,...]
        """
        return ('attribute', 'attributeGroup')

    def mutate(self):
        """
        Mutate into a I{true} type as defined by a reference to
        another object.
        """
        if self.mutated:
            return
        self.mutated = True
        classes = (AttributeGroup,)
        defns = self.default_namespace()
        qref = qualify(self.ref, self.root, defns)
        e = self.schema.agrps.get(qref)
        if e is not None:
            self.merge(deepcopy(e))
            return
        for c in self.schema.children:
            p = c.find(qref, classes)
            if p is not None:
                self.merge(deepcopy(p))
                return
        raise TypeNotFound(self.ref)
    
    def merge(self, e):
        """
        Merge the referenced object.
        @param e: A resoleve reference.
        @type e: L{Element}
        """
        self.name = e.name
        self.qname = e.qname
        self.children = e.children

    def description(self):
        """
        Get the names used for str() and repr() description.
        @return:  A dictionary of relavent attributes.
        @rtype: [str,...]
        """
        return ('name',)
    

class Simple(SchemaObject):
    """
    Represents an (xsd) schema <xs:simpleType/> node
    """
    
    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{schema.Schema}
        @param root: The xml root node.
        @type root: L{sax.element.Element}
        """
        SchemaObject.__init__(self, schema, root)

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
        for c in self.children:
            if isinstance(c, Enumeration):
                return True
        return False

    def description(self):
        """
        Get the names used for str() and repr() description.
        @return:  A dictionary of relavent attributes.
        @rtype: [str,...]
        """
        return ('name',)

   
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
        self.base = root.get('base')
        self.mutated = ( self.base is None )

    def childtags(self):
        """
        Get a list of valid child tag names.
        @return: A list of child tag names.
        @rtype: [str,...]
        """
        return ('enumeration', 'attribute', 'attributeGroup')
    
    def mutate(self):
        """
        Mutate into a I{true} type as defined by a reference to
        another object.
        """
        if self.mutated:
            return
        self.mutated = True
        log.debug(Repr(self))
        defns = self.default_namespace()
        qref = qualify(self.base, self.root, defns)
        query = Query(type=qref)
        super = query.execute(self.schema)
        if super is None:
            log.error(self.schema)
            raise TypeNotFound(qref)
        if not super.builtin():
            self.merge(deepcopy(super))

    def merge(self, b):
        """
        Merge the resolved I{base} object with myself.
        @param b: A resolved base object.
        @type b: L{SchemaObject}
        """
        b.dereference()
        filter = UniqueFilter(self.attributes)
        self.prepend(self.attributes, b.attributes, filter)
        filter = UniqueFilter(self.children)
        for c in b.children:
            c.mark_inherited()
        self.prepend(self.children, b.children, filter)
    
    
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

    def promote(self, pa, pc):
        """
        Promote children during the flattening proess.  The object's
        attributes and children are added to the B{p}romoted B{a}ttributes
        and B{p}romoted B{c}hildren lists as they see fit.
        @param pa: List of attributes to promote.
        @type pa: [L{SchemaObject}]
        @param pc: List of children to promote.
        @type pc: [L{SchemaObject}]
        """
        for c in self.children:
            c.container = self
        SchemaObject.promote(self, pa, pc)
    
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
    
    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{schema.Schema}
        @param root: The xml root node.
        @type root: L{sax.element.Element}
        """
        SchemaObject.__init__(self, schema, root)
        
    def childtags(self):
        """
        Get a list of valid child tag names.
        @return: A list of child tag names.
        @rtype: [str,...]
        """
        return ('attribute', 'attributeGroup', 'extension', 'restriction')


class Enumeration(Promotable):
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
        Promotable.__init__(self, schema, root)
        self.name = root.get('value')

    
class Element(Promotable):
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
        Promotable.__init__(self, schema, root)
        self.ref = root.get('ref')
        a = root.get('form')
        if a is not None:
            self.form_qualified = ( a == 'qualified' )
        a = self.root.get('nillable')
        if a is not None:
            self.nillable = ( a in ('1', 'true') )
        self.min = root.get('minOccurs', default='1')
        self.max = root.get('maxOccurs', default='1')
        self.mutated = ( self.ref is None )
        
    def childtags(self):
        """
        Get a list of valid child tag names.
        @return: A list of child tag names.
        @rtype: [str,...]
        """
        return ('attribute', 'simpleType', 'complexType', 'any',)
    
    def unbounded(self):
        """
        Get whether this node is unbounded I{(a collection)}.
        @return: True if unbounded, else False.
        @rtype: boolean
        """
        if self.container_unbounded():
            return True
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
        return ( self.container_optional() or self.min == '0' )
            
    def derived(self):
        """
        Get whether the object is derived in the it is an extension
        of another type.
        @return: True if derived, else False.
        @rtype: boolean
        """
        try:
            return self.__derived
        except:
            resolved = self.resolve()
            if resolved is self:
                self.__derived = False
            else:
                self.__derived = resolved.derived()
        return self.__derived
    
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
        query = Query(type=qref)
        query.history = [self]
        log.debug('%s, resolving: %s\n using:%s', self.id, qref, query)
        resolved = query.execute(self.schema)
        if resolved is None:
            raise TypeNotFound(qref)
        if resolved.builtin():
            if nobuiltin:
                result = self
            else:
                result = resolved
        else:
            result = resolved.resolve(nobuiltin)
        return result
    
    def mutate(self):
        """
        Mutate into a I{true} type as defined by a reference to
        another object.
        """
        if self.mutated:
            return
        self.mutated = True
        classes = (Element,)
        defns = self.default_namespace()
        qref = qualify(self.ref, self.root, defns)
        e = self.schema.elements.get(qref)
        if e is not None:
            self.merge(deepcopy(e))
            return
        for c in self.schema.children:
            p = c.find(qref, classes)
            if p is not None:
                self.merge(deepcopy(p))
                return
        raise TypeNotFound(self.ref)
    
    def merge(self, e):
        """
        Merge the referenced object.
        @param e: A resoleve reference.
        @type e: L{Element}
        """
        self.name = e.name
        self.qname = e.qname
        self.type = e.type
        self.children = e.children
        self.attributes = e.attributes
        
    def promote(self, pa, pc):
        """
        Promote children during the flattening proess.  The object's
        attributes and children are added to the B{p}romoted B{a}ttributes
        and B{p}romoted B{c}hildren lists as they see fit.
        @param pa: List of attributes to promote.
        @type pa: [L{SchemaObject}]
        @param pc: List of children to promote.
        @type pc: [L{SchemaObject}]
        """
        if len(self):
            log.debug(Repr(self))
            self.attributes += pa
            self.children = copy(pc)
            del pa[:]
            del pc[:]

    def description(self):
        """
        Get the names used for str() and repr() description.
        @return:  A dictionary of relavent attributes.
        @rtype: [str,...]
        """
        return ('name', 'type', 'inherited')
    
    def container_unbounded(self):
        """ get whether container is unbounded """
        if self.container is None:
            return False
        else:
            return self.container.unbounded()
        
    def container_optional(self):
        """ get whether container is optional """
        if self.container is None:
            return False
        else:
            return self.container.optional()


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
        self.base = root.get('base')
        self.mutated = False
        
    def childtags(self):
        """
        Get a list of valid child tag names.
        @return: A list of child tag names.
        @rtype: [str,...]
        """
        return ('attribute', 'attributeGroup', 'sequence', 'all', 'choice', 'group')
        
    def mutate(self):
        """
        Mutate into a I{true} type as defined by a reference to
        another object.
        """
        if self.mutated:
            return
        self.mutated = True
        log.debug(Repr(self))
        defns = self.default_namespace()
        qref = qualify(self.base, self.root, defns)
        query = Query(type=qref)
        super = query.execute(self.schema)
        if super is None:
            log.error(self.schema)
            raise TypeNotFound(qref)
        self.merge(deepcopy(super))

    def merge(self, b):
        """
        Merge the resolved I{base} object with myself.
        @param b: A resolved base object.
        @type b: L{SchemaObject}
        """
        b.dereference()
        filter = UniqueFilter(self.attributes)
        self.prepend(self.attributes, b.attributes, filter)
        filter = UniqueFilter(self.children)
        for c in b.children:
            c.mark_inherited()
        self.prepend(self.children, b.children, filter)

    def description(self):
        """
        Get the names used for str() and repr() description.
        @return:  A dictionary of relavent attributes.
        @rtype: [str,...]
        """
        return ('base',)


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
        """
        if self.opened:
            return
        self.opened = True
        log.debug('%s, importing ns="%s", location="%s"', self.id, self.ns[1], self.location)
        result = self.schema.locate(self.ns)
        if result is None:
            if self.location is None:
                log.debug('imported schema (%s) not-found', self.ns[1])
            else:
                result = self.download()
        log.debug('imported:\n%s', result)
        return result

    def download(self):
            url = self.location
            try:
                if '://' not in url:
                    url = urljoin(self.schema.baseurl, url)
                root = Parser().parse(url=url).root()
                return self.schema.instance(root, url)
            except (URLError, HTTPError):
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

   
class Attribute(Promotable):
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
        Promotable.__init__(self, schema, root)
        self.ref = root.get('ref')
        self.mutated = ( self.ref is None )
        
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
        use = self.root.get('use', default='')
        return ( use == 'optional' )
    
    def merge(self, e):
        """
        Merge the referenced object.
        @param e: A resoleve reference.
        @type e: L{Attribute}
        """
        self.name = e.name
        self.qname = e.qname
        self.type = e.type

    def mutate(self):
        """
        Mutate into a I{true} type as defined by a reference to
        another object.
        """
        if self.mutated:
            return
        self.mutated = True
        classes = (Attribute,)
        defns = self.default_namespace()
        qref = qualify(self.ref, self.root, defns)
        a = self.schema.attributes.get(qref)
        if a is not None:
            self.merge(deepcopy(a))
            return
        for c in self.schema.children:
            p = c.find(qref, classes)
            if p is not None:
                self.merge(deepcopy(p))
                return
        raise TypeNotFound(self.ref)
    
    def description(self):
        """
        Get the names used for str() and repr() description.
        @return:  A dictionary of relavent attributes.
        @rtype: [str,...]
        """
        return ('name','type')


class Any(Promotable):
    """
    Represents an (xsd) <any/> node
    """

    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{schema.Schema}
        """
        Promotable.__init__(self, schema, root)
        
    def get_child(self, name):
        """
        Get (find) a I{non-attribute} child by name and namespace.
        @param name: A child name.
        @type name: basestring
        @return: The requested child.
        @rtype: L{SchemaObject}
        """
        return self
    
    def get_attribute(self, name):
        """
        Get (find) a I{non-attribute} attribute by name.
        @param name: A attribute name.
        @type name: str
        @return: The requested attribute.
        @rtype: L{SchemaObject}
        """
        return self
    
    def any(self):
        """
        Get whether this is an xs:any
        @return: True if any, else False
        @rtype: boolean
        """
        return True

