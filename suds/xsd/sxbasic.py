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

from suds import *
from suds.xsd import *
from suds.xsd.sxbase import *
from suds.xsd.query import Query
from suds.sudsobject import Factory as SOFactory
from suds.sax import Parser, splitPrefix
from urlparse import urljoin
from copy import copy, deepcopy

log = logger(__name__)


class Factory:
    """
    @cvar tags: A factory to create object objects based on tag.
    @type tags: {tag:fn,}
    """

    tags =\
    {
        'import' : lambda x,y: Import(x,y), 
        'complexType' : lambda x,y: Complex(x,y), 
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
        @type root: L{sax.Element}
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
        types = {}
        for c in children:
            if isinstance(c, Element):
                elements[c.qname] = c
                continue
            if isinstance(c, Import):
                imports.append(c)
                continue
            types[c.qname] = c
        for i in imports:
            children.remove(i)
        return (children, imports,elements,types)


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
        @type root: L{sax.Element}
        """
        SchemaObject.__init__(self, schema, root)
        
    def childtags(self):
        """
        Get a list of valid child tag names.
        @return: A list of child tag names.
        @rtype: [str,...]
        """
        return ('attribute', 'sequence', 'all', 'choice', 'complexContent', 'any')
    
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
                if c.__class__ in (Extension, ComplexContent):
                    self.__derived = True
                    break
        return self.__derived


class Simple(SchemaObject):
    """
    Represents an (xsd) schema <xs:simpleType/> node
    """
    
    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{schema.Schema}
        @param root: The xml root node.
        @type root: L{sax.Element}
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

   
class Restriction(SchemaObject):
    """
    Represents an (xsd) schema <xs:restriction/> node
    """
    
    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{schema.Schema}
        @param root: The xml root node.
        @type root: L{sax.Element}
        """
        SchemaObject.__init__(self, schema, root)

    def childtags(self):
        """
        Get a list of valid child tag names.
        @return: A list of child tag names.
        @rtype: [str,...]
        """
        return ('enumeration',)
    
    def __repr__(self):
        myrep = '<%s />' % self.id
        return myrep.encode('utf-8')
    
    
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
        @type root: L{sax.Element}
        """
        SchemaObject.__init__(self, schema, root)
        
    def __repr__(self):
        myrep = '<%s />' % self.id
        return myrep.encode('utf-8')

    def childtags(self):
        """
        Get a list of valid child tag names.
        @return: A list of child tag names.
        @rtype: [str,...]
        """
        return ('element', 'sequence', 'all', 'choice', 'any')

class Sequence(Collection):
    """
    Represents an (xsd) schema <xs:sequence/> node.
    """
    pass

class All(Collection):
    """
    Represents an (xsd) schema <xs:all/> node.
    """
    pass

class Choice(Collection):
    """
    Represents an (xsd) schema <xs:choice/> node.
    """
    pass


class ComplexContent(SchemaObject):
    """
    Represents an (xsd) schema <xs:complexContent/> node.
    """
    
    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{schema.Schema}
        @param root: The xml root node.
        @type root: L{sax.Element}
        """
        SchemaObject.__init__(self, schema, root)
        
    def childtags(self):
        """
        Get a list of valid child tag names.
        @return: A list of child tag names.
        @rtype: [str,...]
        """
        return ('attribute', 'extension',)
    
    def __repr__(self):
        myrep = '<%s />' % self.id
        return myrep.encode('utf-8')


class Enumeration(Promotable):
    """
    Represents an (xsd) schema <xs:enumeration/> node
    """

    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{schema.Schema}
        @param root: The xml root node.
        @type root: L{sax.Element}
        """
        Promotable.__init__(self, schema, root)
        self.name = root.get('value')
        
    def __repr__(self):
        myrep = '<%s />' % self.id
        return myrep.encode('utf-8')

    
class Element(Promotable):
    """
    Represents an (xsd) schema <xs:element/> node.
    """
    
    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{schema.Schema}
        @param root: The xml root node.
        @type root: L{sax.Element}
        """
        Promotable.__init__(self, schema, root)
        self.ref = root.get('ref')
        self.referenced = None
        a = root.get('form')
        if a is not None:
            self.form_qualified = ( a == 'qualified' )
        a = self.root.get('nillable')
        if a is not None:
            self.nillable = ( a in ('1', 'true') )
        self.max = self.root.get('maxOccurs', default='1')
        
    def childtags(self):
        """
        Get a list of valid child tag names.
        @return: A list of child tag names.
        @rtype: [str,...]
        """
        return ('attribute', 'simpleType', 'complexType', 'any',)
    
    def unbounded(self):
        """
        Get whether this node is unbounded I{(a collection)}
        @return: True if unbounded, else False.
        @rtype: boolean
        """
        if self.max.isdigit():
            return (int(self.max) > 1)
        else:
            return ( self.max == 'unbounded' )
            
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
        qref = qualify(self.type, self.root, self.root.namespace())
        query = Query(type=qref)
        query.history = [self]
        log.debug('%s, resolving: %s\n using:%s', self.id, qref, query)
        resolved = query.execute(self.schema)
        if resolved is None:
            raise TypeNotFound(qref)
        else:
            result = resolved.resolve(nobuiltin)
        return result
    
    def mutate(self):
        """
        Mutate into a I{true} type as defined by a reference to
        another object.
        """
        if self.ref is None:
            return
        classes = (Element,)
        qref = qualify(self.ref, self.root, self.namespace())
        for e in self.schema.elements.values():
            if e.qname == qref:
                self.merge(e)
                return
        for c in self.schema.children:
            p = c.find(qref, classes)
            if p is not None:
                self.merge(p)
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
        self.children = deepcopy(e.children)
        self.attributes = deepcopy(e.attributes)
        
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
            del self.children[:]
            self.children += pc
            del pa[:]
            del pc[:]


class Extension(SchemaObject):
    """
    Represents an (xsd) schema <xs:extension/> node.
    """
    
    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{schema.Schema}
        @param root: The xml root node.
        @type root: L{sax.Element}
        """
        SchemaObject.__init__(self, schema, root)
        self.base = root.get('base')
        
    def childtags(self):
        """
        Get a list of valid child tag names.
        @return: A list of child tag names.
        @rtype: [str,...]
        """
        return ('attribute', 'sequence', 'all', 'choice', 'any')
        
    def mutate(self):
        """
        Mutate into a I{true} type as defined by a reference to
        another object.
        """
        log.debug(Repr(self))
        qref = qualify(self.base, self.root, self.namespace())
        query = Query(type=qref)
        super = query.execute(self.schema)
        if super is None:
            raise TypeNotFound(self.base)
        self.merge(super)

    def merge(self, b):
        """
        Merge the resolved I{base} object with myself.
        @param b: A resolved base object.
        @type b: L{SchemaObject}
        """
        self.prepend(self.attributes, deepcopy(b.attributes))
        self.prepend(self.children, deepcopy(b.children))
        
    def __repr__(self):
        myrep = '<%s base="%s"/>' % (self.id, self.base)
        return myrep.encode('utf-8')


class Import(SchemaObject):
    """
    Represents an (xsd) schema <xs:import/> node
    """
    
    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{schema.Schema}
        @param root: The xml root node.
        @type root: L{sax.Element}
        """
        SchemaObject.__init__(self, schema, root)
        self.imp = SOFactory.object('import')
        self.imp.ns = (None, root.get('namespace'))
        self.imp.location = root.get('schemaLocation')
        self.opened = False
        
    def open(self):
        """
        Open and import the refrenced schema.
        """
        if self.opened:
            return
        self.opened = True
        log.debug('%s, importing:\n%s', self.id, self.imp)
        if self.imp.location is None:
            result = self.schema.locate(self.imp.ns)
            if result is None:
                log.debug('imported schema (%s) not-found', self.imp.ns[1])
            return result
        else:
            url = self.imp.location
            try:
                if '://' not in url:
                    url = urljoin(self.schema.baseurl, url)
                root = Parser().parse(url=url).root()
                return self.schema.instance(root, url)
            except Exception:
                msg = 'imported schema (%s) at (%s), not-found' % (self.imp.ns[1], url)
                log.error('%s, %s', self.id, msg, exc_info=True)
                raise Exception(msg)
 
    def str(self, indent=0):
        """
        Get a string representation of this object.
        @param indent: The indent.
        @type indent: int
        @return: A string.
        @rtype: str
        """
        tab = '%*s'%(indent*3, '')
        result  = []
        result.append('%s<%s' % (tab, self.id))
        result.append(' ns="%s"' % self.imp.ns[1])
        result.append(' location="%s"' % self.imp.location)
        result.append('/>')
        return ''.join(result)

    def __repr__(self):
        repr = '<%s ns="%s" location="%s"/>' \
            % (self.id, self.imp.ns[1], self.imp.location)
        return repr.encode('utf-8')

   
class Attribute(Promotable):
    """
    Represents an (xsd) <attribute/> node
    """

    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{schema.Schema}
        @param root: The xml root node.
        @type root: L{sax.Element}
        """
        Promotable.__init__(self, schema, root)
        
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
    
    def required(self):
        """
        Gets the <xs:attribute use="required"/> attribute value
        @return: Whether the attribute is required.
        @rtype: bool
        """
        use = self.root.get('use', default='')
        return ( use.lower() == 'required' )


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
    
    def __repr__(self):
        myrep = '<%s />' % self.id
        return myrep.encode('utf-8')
