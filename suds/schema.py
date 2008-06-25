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
The I{schema} module provides a intelligent representation of
an XSD schema.  The I{raw} model is the XML tree and the I{model}
is the denormalized, objectified and intelligent view of the schema.
Most of the I{value-add} provided by the model is centered around
tranparent referenced type resolution and targeted denormalization.
"""

from suds import *
from suds.sudsobject import Factory, Object
from sax import Parser, splitPrefix, Namespace
from sax import Element as Node
from urlparse import urljoin
import logging

log = logger(__name__)


def qualified_reference(ref, resolvers, defns=Namespace.default):
    """
    Get type reference I{qualified} by pnamespace.
    @param ref: A referenced type name such as <person type="tns:person"/>
    @type ref: str
    @param resolvers: A list of objects to be used to resolve types.
    @type resolvers: [L{sax.Element},]
    @param tns: An optional target namespace used to qualify references
        when no prefix is specified.
    @type defns: A default namespace I{tuple: (prefix,uri)} used when ref not prefixed.
    @return: A qualified reference.
    @rtype: (name, ns)
    @note: Suds namespaces are tuples: I{(prefix,URI)}.  An example
        qualified reference would be: ("myname",("tns", "http://..."))
    """
    ns = None
    p, n = splitPrefix(ref)
    if p is not None:
        if not isinstance(resolvers, (list, tuple)):
            resolvers = (resolvers,)
        for r in resolvers:
            resolved = r.resolvePrefix(p)
            if resolved[1] is not None:
                ns = resolved
                break
        if ns is None:
            raise Exception('prefix (%s) not resolved' % p)
    else:
        ns = defns
    return (n, ns)

def isqref(object):
    """
    Get whether the object is a I{qualified reference}.
    @param object: An object to be tested.
    @type object: I{any}
    @rtype: boolean
    @see: L{qualified_reference()}
    """
    return (\
        isinstance(object, tuple) and \
        len(object) == 2 and \
        isinstance(object[0], basestring) and \
        Namespace.isns(object[1]))


class SchemaCollection:
    """
    A collection of schema objects.  This class is needed because WSDLs may contain
    more then one <schema/> node.
    @ivar root: A root node used for ns prefix resolution (set to WSDL's root).
    @type root: L{Element}
    @ivar tns: The target namespace (set to WSDL's target namesapce)
    @type tns: (prefix,URI)
    @ivar baseurl: The I{base} URL for this schema.
    @type baseurl: str
    @ivar children: A list contained schemas.
    @type children: [L{Schema},...]
    @ivar impfilter: A list of namespaces B{not} to import.
    @type impfilter: set
    """
    
    def __init__(self, wsdl, impfilter=None):
        """
        @param wsdl: A WSDL object.
        @type wsdl: L{wsdl.WSDL}
        @param impfilter: A list of namespaces B{not} to import.
        @type impfilter: set
        """
        self.root = wsdl.root
        self.id = objid(self)
        self.tns = wsdl.tns
        self.baseurl = wsdl.url
        self.children = []
        self.impfilter = impfilter
        self.namespaces = {}
        
    def add(self, node):
        """
        Add a schema node to the collection.
        @param node: A <schema/> root node.
        @type node: L{Element}
        """
        child = Schema(node, self.baseurl, self, self.impfilter)
        self.children.append(child)
        self.namespaces[child.tns[1]] = child
        
    def load(self):
        """
        Load the schema objects for the root nodes.
        """
        for stage in Schema.init_stages:
            for child in self.children:
                child.init(stage)
        if log.isEnabledFor(logging.DEBUG):
            log.debug('schema (%s):\n%s', self.baseurl, str(self))
        
    def schemabyns(self, ns):
        """
        Find a schema by namespace.  Only the URI portion of
        the namespace is compared to each schema's I{targetNamespace}
        @param ns: A namespace.
        @type ns: (prefix,URI)
        @return: The schema matching the namesapce, else None.
        @rtype: L{Schema}
        """
        return self.namespaces.get(ns[1], None)

    def find(self, query):
        """ @see: L{Schema.find()} """
        result = None
        self.start(query)
        while result is None:
            for s in self.children:
                log.debug('%s, finding (%s) in %s', self.id, query.name, repr(s))
                result = s.find(query)
                if result is not None:
                    break
            if result is None and \
                query.increment(self.id):
                    continue
            else:
                break
        return result
    
    def start(self, query):
        """
        Start the query by setting myself as the owner and
        qualifying the query.
        @param query: A query.
        @type query: L{Query}
        """
        if query.owner is None:
            query.owner = self.id
        query.qualify(self.root, self.tns)
        
    def namedtypes(self):
        """
        Get a list of top level named types.
        @return: A list of types.
        @rtype: [L{SchemaProperty},...]
        """
        result = {}
        for s in self.flattened_children():
            for c in s.children:
                name = c.get_name()
                if name is None:
                    continue
                resolved = c.resolve()
                if isinstance(resolved, XBuiltin):
                    result[name] = c
                else:
                    result[name] = resolved           
        return result.values()
    
    def flattened_children(self):
        result = []
        for s in self.children:
            if s not in result:
                result.append(s)
            for gc in s.grandchildren():
                if gc not in result:
                    result.append(gc)
        return result
    
    def __len__(self):
        return len(self.children)
    
    def __str__(self):
        return unicode(self).encode('utf-8')
    
    def __unicode__(self):
        result = ['\nschema collection']
        for s in self.children:
            result.append(s.str(1))
        return '\n'.join(result)


class Schema:
    """
    The schema is an objectification of a <schema/> (xsd) definition.
    It provides inspection, lookup and type resolution.
    @ivar root: The root node.
    @type root: L{sax.Element}
    @ivar tns: The target namespace.
    @type tns: (prefix,URI)
    @ivar efdq: The @B{e}lementB{F}ormB{D}efault="B{q}ualified" flag. 
    @type efdq: boolean
    @ivar baseurl: The I{base} URL for this schema.
    @type baseurl: str
    @ivar container: A schema collection containing this schema.
    @type container: L{SchemaCollection}
    @ivar types: A schema types cache.
    @type types: {name:L{SchemaProperty}}
    @ivar children: A list of child properties.
    @type children: [L{SchemaProperty},...]
    @ivar factory: A property factory.
    @type factory: L{PropertyFactory}
    @ivar impfilter: A list of namespaces B{not} to import.
    @type impfilter: set
    """
    
    init_stages = range(0,4)
    
    def __init__(self, root, baseurl, container=None, impfilter=None):
        """
        @param root: The xml root.
        @type root: L{sax.Element}
        @param baseurl: The base url used for importing.
        @type baseurl: basestring
        @param container: An optional container.
        @type container: L{SchemaCollection}
        @param impfilter: A list of namespaces B{not} to import.
        @type impfilter: set
        """
        self.root = root
        self.id = objid(self)
        self.tns = self.__tns()
        self.stage = -1
        self.baseurl = baseurl
        self.container = container
        self.types = {}
        self.children = []
        self.factory = PropertyFactory(self)
        self.impfilter = impfilter
        self.form_qualified = self.__form_qualified()
        if container is None:
            self.init(3)
                    
    def __form_qualified(self):
        """ get @elementFormDefault = (qualified) """
        form = self.root.get('elementFormDefault')
        if form is None:
            return False
        else:
            return ( form.lower() == 'qualified' )
                
    def __tns(self):
        """ get the target namespace """
        tns = [None, self.root.get('targetNamespace')]
        if tns[1] is not None:
            tns[0] = self.root.findPrefix(tns[1])
        return tuple(tns)
            
    def init(self, stage):
        """
        Perform I{stage} initialization.
        @param stage: The init stage to complete.
        """
        for n in range(0, (stage+1)):
            if self.stage < n:
                m = '__init%s__' % n
                self.stage = n
                log.debug('%s, init (%d)', self.id, n)
                if not hasattr(self, m): continue
                method = getattr(self, m)
                method()
                for s in self.grandchildren():
                    s.init(n)
                
    def __init0__(self):
        """ create children """
        for node in self.root.children:
            try:
                child = self.factory.create(node)
                self.children.append(child)
            except:
                pass

    def __init1__(self):
        """ run children through depsolving and child promotion """
        for stage in SchemaProperty.init_stages:
            for c in self.children:
                c.init(stage)
        self.children.sort()

    def __init2__(self):
        pass
        
    def schemabyns(self, ns):
        """ find schema by namespace """
        if self.container is not None:
            return self.container.schemabyns(ns)
        else:
            return None
        
    def grandchildren(self):
        """ get I{grandchild} schemas that have been imported """
        for c in self.children:
            if isinstance(c, Import) and \
                c.imp.schema is not None:
                    yield c.imp.schema
        
    def find(self, query):
        """
        Find a I{type} defined in one of the contained schemas.
        @param query: A query.
        @type query: L{Query}
        @return: The found schema type. 
        @rtype: L{qualified_reference()}
        """
        self.start(query)
        key = query.key()
        cached = self.types.get(key, None)
        if cached is not None and \
            not query.filter(cached):
                return cached
        if self.builtin(query.qname):
            b = self.factory.create(builtin=query.name)
            log.debug(
                '%s, found (%s)\n%s\n%s',
                self.id, query.name, query, tostr(b))
            return b
        result = None
        while result is None:
            result = self.__find(query)
            if result is None and query.increment(self.id):
                continue
            else:
                break
        if result is not None:
            if query.resolved:
                result = result.resolve()
            self.types[key] = result
            query.history.append(result)
            log.debug(
                '%s, found (%s)\n%s\n%s', self.id, query.name, query, tostr(result))
        else:
            log.debug('%s, (%s) not-found:\n%s', self.id, query.name, query)
        return result
    
    def start(self, query):
        """
        Start the query by setting myself as the owner and
        qualifying the query.
        """
        if query.owner is None:
            query.owner = self.id
        query.qualify(self.root, self.tns)

    def custom(self, ref, context=None):
        """ get whether specified type reference is custom """
        if ref is None:
            return True
        else:
            return (not self.builtin(ref, context))
    
    def builtin(self, ref, context=None):
        """ get whether the specified type reference is an (xsd) builtin """
        w3 = 'http://www.w3.org'
        try:
            if isqref(ref):
                ns = ref[1]
                return ns[1].startswith(w3)
            if context is None:
                context = self.root    
            prefix = splitPrefix(ref)[0]
            prefixes = context.findPrefixes(w3, 'startswith')
            return (prefix in prefixes)
        except:
            return False

    def str(self, indent=0):
        tab = '%*s'%(indent*3, '')
        result = []
        result.append('%s%s' % (tab, self.id))
        result.append('%s(raw)' % tab)
        result.append(self.root.str(indent+1))
        result.append('%s(model {%d})' % (tab, self.stage))
        for c in self.children:
            result.append(c.str(indent+1))
        result.append('')
        return '\n'.join(result) 
    
    def __find(self, query):
        """ find a schema object by name. """
        result = None
        query.qualify(self.root, self.tns)
        ref, ns = query.qname
        log.debug('%s, finding (%s)\n%s', self.id, query.name, query)
        for child in self.children:
            if isinstance(child, Import):
                log.debug(
                    '%s, searching (import): %s\nfor:\n%s', 
                    self.id, repr(child), query)
                result = child.xsfind(query)
                if result is not None:
                    break
            name = child.get_name()
            if name is None:
                log.debug(
                    '%s, searching (child): %s\nfor:\n%s',
                    self.id, repr(child), query)
                result = child.get_child(ref, ns)
                if query.filter(result):
                    result = None
                    continue
                if result is not None:
                    break
            else:
                log.debug(
                    '%s, matching: %s\nfor:\n%s',
                    self.id, repr(child), query)
                if child.match(ref, ns):
                    result = child
                    if query.filter(result):
                        result = None
                    else:
                        break
        return result
        
    def __repr__(self):
        myrep = \
            '<%s {%d} tns="%s"/>' % (self.id, self.stage, self.tns[1])
        return myrep.encode('utf-8')
    
    def __str__(self):
        return unicode(self).encode('utf-8')
    
    def __unicode__(self):
        return self.str()
    
    
class PropertyFactory:
    """
    @cvar tags: A factory to create property objects based on tag.
    @type tags: {tag:fn,}
    @cvar builtins: A factory to create property objects based on tag.
    @type builtins: {tag:fn,}
    """

    tags =\
    {
        'import' : lambda x,y=None: Import(x,y), 
        'complexType' : lambda x,y=None: Complex(x,y), 
        'simpleType' : lambda x,y=None: Simple(x,y), 
        'element' : lambda x,y=None: Element(x,y),
        'attribute' : lambda x,y=None: Attribute(x,y),
        'sequence' : lambda x,y=None: Sequence(x,y),
        'complexContent' : lambda x,y=None: ComplexContent(x,y),
        'enumeration' : lambda x,y=None: Enumeration(x,y),
        'extension' : lambda x,y=None: Extension(x,y),
        'any' : lambda x,y=None: Any(x,y),
    }

    builtins =\
    {
        'anyType' : lambda x,y=None: Any(x,y),
        'boolean' : lambda x,y=None: XBoolean(x,y),
    }
    
    def __init__(self, schema):
        """
        @param schema: A schema object.
        @type schema: L{Schema} 
        """
        self.schema = schema
    
    def create(self, root=None, builtin=None):
        """
        Create an xsd property object
        @param root: A root node.  When specified, a property is created.
        @type root: L{Element}
        @param builtin: The name of an xsd builtin type.  When specified, a 
            property is created.
        @type builtin: basestring
        @return: A I{basic} property when I{root} is specified; An
            XSD builtin when I{builtin} name is specified.
        @rtype: L{SchemaProperty}
        """
        if root is not None:
            return self.__create(root)
        elif builtin is not None:
            return self.__builtin(builtin)

    def __create(self, root):
        if root.name in PropertyFactory.tags:
            fn = PropertyFactory.tags[root.name]
            return fn(self.schema, root)
        else:
            raise Exception('tag (%s) not-found' % root.name)
        
    def __builtin(self, name):
        if name in PropertyFactory.builtins:
            fn = PropertyFactory.builtins[name]
            return fn(self.schema, name)
        else:
            return XBuiltin(self.schema, name)


class SchemaProperty:
    """
    A schema property is an extension to property object with
    with schema awareness.
    @ivar root: The XML root element.
    @type root: L{sax.Element}
    @ivar schema: The schema containing this object.
    @type schema: L{Schema}
    @ivar state: The transient states for the property
    @type state: L{sudsobject.Object}
    @ivar state.depsolve: The dependancy resolved flag.
    @type state.depsolve: boolean
    @ivar state.promoted: The child promoted flag.
    @type state.promoted: boolean
    @ivar form_qualified: A flag that inidcates that @elementFormDefault
        has a value of I{qualified}.
    @type form_qualified: boolean
    @ivar nillable: A flag that inidcates that @nillable
        has a value of I{true}.
    @type nillable: boolean
    @ivar children: A list of child xsd I{(non-attribute)} nodes
    @type children: [L{SchemaProperty},...]
    @ivar attributes: A list of child xsd I{(attribute)} nodes
    @type attributes: [L{SchemaProperty},...]
    @ivar derived: Derived type flag.
    @type derived: boolean
    @ivar resolve_result: The cached result of L{resolve()}
    @type resolve_result: L{SchemaProperty}
    """
    
    init_stages = range(0,4)

    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{Schema}
        @param root: The xml root node.
        @type root: L{sax.Element}
        """
        self.schema = schema
        self.root = root
        self.id = objid(self)
        self.stage = -1
        self.form_qualified = schema.form_qualified
        self.nillable = False
        self.children = []
        self.attributes = []
        self.derived = False
        self.resolve_cache = {}
        
    def init(self, stage):
        """
        Perform I{stage} initialization.
        @param stage: The init stage to complete.
        """
        for n in range(0, (stage+1)):  
            if self.stage < n:
                m = '__init%s__' % n
                self.stage = n
                log.debug('%s, init (%d)', self.id, n)
                if not hasattr(self, m): continue
                method = getattr(self, m)
                method()
                for c in self.children:
                    c.init(n)
        
    def match(self, name, ns=None, classes=()):
        """
        Match by name, optional namespace and list of classes.  When a list of
        classes is specified, this object must be in the list.  Otherwise, the
        class list is ignored.
        @param name: The name of the property
        @type name: basestring
        @param ns: An optional namespace
        @type ns: (I{prefix},I{URI})
        @param classes: A list of classes used to qualify the match.
        @type classes: [I{class},...]
        @return: True on match, else False
        @rtype: boolean
        """
        myns = self.namespace()
        myname = self.get_name()
        if ns is None:
            matched = ( myname == name )
        else:
            matched = ( myns[1] == ns[1] and myname == name )
        if matched and len(classes):
            matched = ( self.__class__ in classes )
        return matched
        
    def namespace(self):
        """
        Get this properties namespace
        @return: The schema's target namespace
        @rtype: (I{prefix},I{URI})
        """
        return self.schema.tns
        
    def get_name(self):
        """
        Get the object's name
        @return: The object's name
        @rtype: basestring
        """
        return None
    
    def get_qname(self):
        """
        Get a fully qualified name.
        @return: A qualified name as I{prefix}:I{name}.
        @rtype: basestring
        """
        prefix = self.namespace()[0]
        name = self.get_name()
        if name is not None:
            return ':'.join((prefix, name))
        else:
            return None
    
    def typed(self):
        """
        Get whether this type references another type.
        @return: True if @type="" is specified
        @rtype: boolean
        """
        return ( self.ref() is not None )
    
    def ref(self):
        """
        Get the referenced (xsi) type as defined by the schema.
        This is usually the value of the I{type} attribute.
        @return: The object's type reference
        @rtype: basestring
        """
        return None
        
    def qref(self):
        """
        Get the B{qualified} referenced (xsi) type as defined by the schema.
        This is usually the value of the I{type} attribute that has been
        qualified by L{qualified_reference()}.
        @return: The object's (qualified) type reference
        @rtype: I{qualified reference}
        @see: L{qualified_reference()}
        """
        ref = self.ref()
        if ref is not None:
            qref = qualified_reference(ref, self.root, self.root.namespace())
            name = qref[0]
            ns = qref[1]
            return (':'.join((ns[0], name)), ns)
        else:
            return None
    
    def get_children(self, empty=None):
        """
        Get child (nested) schema definition nodes (excluding attributes).
        @param empty: An optional value to be returned when the
        list of children is empty.
        @type empty: I{any}
        @return: A list of children.
        @rtype: [L{SchemaProperty},...]
        """ 
        list = self.children
        if len(list) == 0 and empty is not None:
            list = empty
        return list
    
    def get_child(self, name, ns=None):
        """
        Get (find) a I{non-attribute} child by name and namespace.
        @param name: A child name.
        @type name: basestring
        @param ns: The child's namespace.
        @type ns: (I{prefix},I{URI})
        @return: The requested child.
        @rtype: L{SchemaProperty}
        """
        for child in self.get_children():
            if child.match(name, ns):
                return child
        return None
    
    def get_attributes(self):
        """
        Get a list of schema attribute nodes.
        @return: A list of attributes.
        @rtype: [L{Attribute},...]
        """ 
        return self.attributes
    
    def get_attribute(self, name, ns=None):
        """
        Get (find) a I{non-attribute} child by name and namespace.
        @param name: A child name.
        @type name: basestring
        @param ns: The child's namespace.
        @type ns: (I{prefix},I{URI})
        @return: The requested child.
        @rtype: L{SchemaProperty}
        """
        for a in self.get_attributes():
            if a.match(name, ns):
                return a
        return None
    
    def unbounded(self):
        """
        Get whether this node is unbounded I{(a collection)}
        @return: True if unbounded, else False.
        @rtype: boolean
        """
        return False
    
    def resolve(self, depth=1024, nobuiltin=False):
        """
        Resolve and return the nodes true type when another
        named type is referenced.
        @param depth: The resolution depth.
        @type depth: int
        @param nobuiltin: Flag indicates that resolution must
            not continue to xsd builtins.
        @return: The resolved (true) type.
        @rtype: L{SchemaProperty}
        """
        cachekey = '%d.%s' % (depth, nobuiltin)
        cached = self.resolve_cache.get(cachekey, None)
        if cached is not None:
            return cached
        history = [self]
        result = self
        for n in range(0, depth):
            resolved = self.__resolve(result, history)
            if resolved != result and \
                not (nobuiltin and isinstance(resolved, XBuiltin)):
                    result = resolved
            else:
                break
        if result is not None:
            self.resolve_cache[cachekey] = result
        return result
        
    def any(self):
        """
        Get whether this is an xs:any
        @return: True if any, else False
        @rtype: boolean
        """
        return False
        
    def find(self, ref, classes=()):
        """
        Find a referenced type in self or children.
        @param ref: Either a I{qualified reference} or the
                name of a referenced type.
        @type ref: (I{str}|I{qualified reference})
        @param classes: A list of classes used to qualify the match.
        @type classes: [I{class},...] 
        @return: The referenced type.
        @rtype: L{SchemaProperty}
        @see: L{qualified_reference()}
        @see: L{Schema.find()}
        """
        if isqref(ref):
            n, ns = ref
        else:
            n, ns = qualified_reference(ref, self.root, self.namespace())
        if self.match(n, ns, classes=classes):
            return self
        qref = (n, ns)
        for c in self.children:
            p = c.find(qref, classes)
            if p is not None:
                return p
        return None
    
    def add_children(self, *paths):
        """
        Add (sax) children at the specified paths as child
        schema property objects.  Each path is a I{simple} XML
        string containing element names separated by (/) and is not
        to be confused with an XPATH expression.  Children are stored
        in either the I{children} collection of the I{attributes} collection.
        @param paths: A I{vararg} list of paths.
        @type paths: basestring
        @see: L{PropertyFactory}
        """
        factory = PropertyFactory(self.schema)
        for path in paths:
            for root in self.root.childrenAtPath(path):
                child = factory.create(root)
                if child.isattr():
                    self.attributes.append(child)
                else:
                    self.children.append(child)
                
    def replace_child(self, child, replacements):
        """
        Replace a (child) with specified replacement objects.
        @param child: A child of this property.
        @type child: L{SchemaProperty}
        @param replacements: A list of replacement properties.
        @type replacements: [L{SchemaProperty},...]
        """
        index = self.children.index(child)
        self.children.remove(child)
        for c in replacements:
            self.children.insert(index, c)
            index += 1
            
    def promote_grandchildren(self):
        """
        Promote grand-children as direct children.  Promoted children
        replace their parents.
        @see: replace_child()
        """
        children = list(self.children)
        for c in children:
            c.init(self.stage)
            self.attributes += c.attributes
            self.replace_child(c, c.children)
        
    def str(self, indent=0):
        """
        Get a string representation of this property.
        @param indent: The indent.
        @type indent: int
        @return: A string.
        @rtype: str
        """
        tab = '%*s'%(indent*3, '')
        result  = []
        result.append('%s<%s' % (tab, self.id))
        result.append(' {%s}' % self.stage)
        result.append(' name="%s"' % self.get_name())
        ref = self.ref()
        if ref is not None:
            result.append(' type="%s"' % ref)
        if len(self):
            for c in ( self.attributes + self.children ):
                result.append('\n')
                result.append(c.str(indent+1))
            result.append('\n%s' % tab)
            result.append('</%s>' % self.__class__.__name__)
        else:
            result.append(' />')
        return ''.join(result)
    
    def isattr(self):
        """
        Get whether the property is a schema I{attribute} definition.
        @return: True if an attribute, else False.
        @rtype: boolean
        """
        return False
    
    def translate(self, value, topython=True):
        """
        Translate a value (type) to/from a python type.
        @param value: A value to translate.
        @return: The converted I{language} type.
        """
        return value
    
    def __resolve(self, t, history):
        """ resolve the specified type """
        result = t
        if t.typed():
            ref = qualified_reference(t.ref(), t.root, t.root.namespace())
            query = Query(ref)
            query.history = history
            log.debug('%s, resolving: %s\n using:%s', self.id, ref, query)
            resolved = t.schema.find(query)
            if resolved is None:
                raise TypeNotFound(ref)
            else:
                result = resolved
        return result
            
    def __init0__(self):
        """
        Load
        @precondition: The model must be initialized.
        @note: subclasses override here!
        """
        pass   
    
    def __init1__(self):
        """
        Perform dependancy solving.
        Dependancies are resolved to their I{true} types during
        schema loading.
        @precondition: The model must be initialized.
        @precondition: I{__init0__()} have been invoked.
        @note: subclasses override here!
        """
        pass
    
    def __init2__(self):
        """
        Promote children.
        @precondition: The model must be initialized.
        @precondition: I{__init1__()} have been invoked.
        """
        pass
        
    def __str__(self):
        return unicode(self).encode('utf-8')
            
    def __unicode__(self):
        return unicode(self.str())
    
    def __repr__(self):
        myrep = \
            '<%s {%d} name="%s"/>' % (self.id, self.stage, self.get_name())
        return myrep.encode('utf-8')
    
    def __len__(self):
        return len(self.children)
    
    def __getitem__(self, index):
        return self.children[index]
    

class Polymorphic(SchemaProperty):
    
    """
    Represents a polymorphic property which is an xsd construct
    that may reference another by name.  Once the reference is
    resolved, the object transforms into the referenced property.
    """
    
    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{Schema}
        @param root: The xml root node.
        @type root: L{sax.Element}
        """
        SchemaProperty.__init__(self, schema, root)
        self.referenced = None
        
    def __init1__(self):
        """
        Resolve based on @ref (reference) found
        @see: L{SchemaProperty.__init1__()}
        """
        ref = self.root.get('ref')
        if ref is not None:
            self.__find_referenced(ref)
        
    def __find_referenced(self, ref):
        """ 
        find the referenced property in top level elements
        first, then look deeper.
        """
        classes = (self.__class__,)
        for c in self.schema.children:
            if c.match(ref, classes=classes):
                self.referenced = c
                return
        for c in self.schema.children:
            p = c.find(ref, classes)
            if p is not None:
                self.referenced = p
                return
        raise TypeNotFound(ref)


class Complex(SchemaProperty):
    """
    Represents an (xsd) schema <xs:complexType/> node.
    @cvar valid_children: A list of valid child node names
    @type valid_children: (I{str},...)
    """
    
    valid_children =\
        ('attribute',
          'sequence', 
          'complexContent',
          'any')
    
    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{Schema}
        @param root: The xml root node.
        @type root: L{sax.Element}
        """
        SchemaProperty.__init__(self, schema, root)
        self.add_children(*Complex.valid_children)
        
    def get_name(self):
        """ gets the <xs:complexType name=""/> attribute value """
        return self.root.get('name')
    
    def __init0__(self):
        """ update derived flag """
        for c in self.children:
            if c.__class__ in (Extension, ComplexContent):
                self.derived = True
                break
        
    def __init2__(self):
        """ promote grand-children """
        self.promote_grandchildren()
    
    def __lt__(self, other):
        """ <element/> first """
        return ( not isinstance(other, Element) )


class Simple(SchemaProperty):
    """
    Represents an (xsd) schema <xs:simpleType/> node
    """
    
    valid_children =\
        ('restriction/enumeration',
          'any',)
    
    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{Schema}
        @param root: The xml root node.
        @type root: L{sax.Element}
        """
        SchemaProperty.__init__(self, schema, root)
        self.add_children(*Simple.valid_children)

    def get_name(self):
        """ gets the <xs:simpleType name=""/> attribute value """
        return self.root.get('name')

    def ref(self):
        """ gets the <xs:simpleType xsi:type=""/> attribute value """
        return self.root.get('type')


class Sequence(SchemaProperty):
    """
    Represents an (xsd) schema <xs:sequence/> node.
    """
    
    valid_children =\
        ('element',
          'any',)
    
    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{Schema}
        @param root: The xml root node.
        @type root: L{sax.Element}
        """
        SchemaProperty.__init__(self, schema, root)
        self.add_children(*Sequence.valid_children)


class ComplexContent(SchemaProperty):
    """
    Represents an (xsd) schema <xs:complexContent/> node.
    """
    
    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{Schema}
        @param root: The xml root node.
        @type root: L{sax.Element}
        """
        SchemaProperty.__init__(self, schema, root)
        self.add_children('extension')

    def __init2__(self):
        """ promote grand-children """
        self.promote_grandchildren()


class Enumeration(SchemaProperty):
    """
    Represents an (xsd) schema <xs:enumeration/> node
    """

    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{Schema}
        @param root: The xml root node.
        @type root: L{sax.Element}
        """
        SchemaProperty.__init__(self, schema, root)
        
    def get_name(self):
        """ gets the <xs:enumeration value=""/> attribute value """
        return self.root.get('value')

    
class Element(Polymorphic):
    """
    Represents an (xsd) schema <xs:element/> node.
    @cvar valid_children: A list of valid child node names
    @type valid_children: (I{str},...)
    """
    
    valid_children = \
        ('attribute', 
        'complexType',
        'any',)
    
    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{Schema}
        @param root: The xml root node.
        @type root: L{sax.Element}
        """
        Polymorphic.__init__(self, schema, root)
        form = root.get('form')
        self.form_qualified = self.__form_qualified()
        self.nillable = self.__nillable()
        self.add_children(*Element.valid_children)
        
    def get_name(self):
        """ gets the <xs:element name=""/> attribute value """
        return self.root.get('name')
    
    def ref(self):
        """ gets the <xs:element type=""/> attribute value """
        return self.root.get('type')
    
    def unbounded(self):
        """ get whether the element has a maxOccurs > 1 or unbounded """
        max = self.root.get('maxOccurs', default=1)
        return (max > 1 or max == 'unbounded')
    
    def __form_qualified(self):
        """ get @form = (qualified) """
        form = self.root.get('form')
        if form is None:
            return self.form_qualified
        else:
            return ( form.lower() == 'qualified' )
        
    def __nillable(self):
        """ get @nillable = (1|true) """
        nillable = self.root.get('nillable')
        if nillable is None:
            return self.nillable
        else:
            return ( nillable.lower() in ('1', 'true') )

    def __lt__(self, other):
        """ <simpleType/> first """
        return ( not isinstance(other, Simple) )
    
    def __init2__(self):
        """
        if referenced (@ref) then promote the referenced
        node; then replace my children with those of the
        referenced node; otherwise, promote my grand-children
        @see: L{SchemaProperty.__init2__()}
        """
        if self.referenced is not None:
            self.referenced.init(self.stage)
            self.root = self.referenced.root
            self.children = self.referenced.children
        else:
            self.promote_grandchildren()
        self.derived = self.resolve().derived


class Extension(Complex):
    """
    Represents an (xsd) schema <xs:extension/> node.
    """
    
    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{Schema}
        @param root: The xml root node.
        @type root: L{sax.Element}
        """
        Complex.__init__(self, schema, root)
        self.super = None
        
    def __init1__(self):
        """ lookup superclass  """
        Complex.__init1__(self)
        base = self.root.get('base')
        ref = qualified_reference(base, self.root, self.root.namespace())
        query = Query(ref)
        self.super = self.schema.find(query)
        if self.super is None:
            raise TypeNotFound(base)
        
    def __init2__(self):
        """ add base type's children as my own """
        Complex.__init2__(self)
        index = 0
        self.super.init(self.stage)
        super = self.super.resolve()
        for c in super.children:
            self.children.insert(index, c)
            index += 1


class Import(SchemaProperty):
    """
    Represents an (xsd) schema <xs:import/> node
    """
    
    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{Schema}
        @param root: The xml root node.
        @type root: L{sax.Element}
        """
        SchemaProperty.__init__(self, schema, root)
        self.imp = Factory.object('import')
        self.imp.schema = None
        self.imp.ns = (None, root.get('namespace'))
        self.imp.location = root.get('schemaLocation')
        self.imp.external = False
        
    def find(self, ref, classes=()):
        """
        Find a referenced type in the imported schema.
        @param ref: Either a I{qualified reference} or the
                name of a referenced type.
        @type ref: (I{str}|I{qualified reference})
        @param classes: A list of classes used to qualify the match.
        @type classes: [I{class},...] 
        @return: The referenced type.
        @rtype: L{SchemaProperty}
        @see: L{qualified_reference()}
        @see: L{Schema.find()}
        """
        result = None
        if self.imp.schema is not None:
            query = Query(ref)
            query.clsfilter = classes
            query.qualify(self.root, self.schema.tns)
            result = self.imp.schema.find(query)
        return result
    
    def xsfind(self, query):
        """
        Find a I{type} defined in one of the contained schemas.
        @param query: A query.
        @type query: L{Query}
        @return: The found schema type. 
        @rtype: L{qualified_reference()}
        """
        if self.imp.schema is None:
            return None
        marker = self.marker(query)
        if marker in query.history:
            return None
        query.history.append(marker)
        result = None
        log.debug('%s, finding (%s) in:\n%s',
            self.id, 
            query.name,
            repr(self.imp.schema))
        result = self.imp.schema.find(query)
        if result is not None:
            log.debug('%s, found (%s) as %s',
                self.id, 
                query.qname, 
                repr(result))
        return result
    
    def marker(self, query):
        """ get unique search marker """
        name, ns = query.qname
        marker = tostr(name) \
            + tostr(ns[1]) \
            + objid(self.imp.schema)
        return marker

    def namespace(self):
        """ get this properties namespace """
        result = self.schema.tns
        if self.imp.schema is not None:
            result = self.imp.schema.tns
        return result
    
    def skip(self):
        """ skip this namespace """
        return \
            Namespace.xs(self.imp.ns) or \
            self.imp.ns[1] == self.schema.tns or \
            self.imp.ns[1] in self.schema.impfilter
            
    def str(self, indent=0):
        """
        Get a string representation of this property.
        @param indent: The indent.
        @type indent: int
        @return: A string.
        @rtype: str
        """
        tab = '%*s'%(indent*3, '')
        result  = []
        result.append('%s<%s' % (tab, self.id))
        result.append(' {%d}' % self.stage)
        result.append(' location="%s"' % self.imp.location)
        if self.imp.schema is None:
            result.append(' schema="n/r"')
        else:
            result.append(' schema="%s"' % self.imp.schema.id)
        result.append('/>')
        return ''.join(result)
            
    def __init0__(self):
        log.debug('%s, import (%s) at: (%s)', self.id, self.imp.ns[1], self.imp.location)
        if self.skip():
            log.debug('%s, import (%s) skipped', self.id, self.imp.ns[1])
            return
        schema = self.schema.schemabyns(self.imp.ns)
        if schema is not None:
            self.imp.schema = schema
            self.__import_succeeded()
        else:
            self.imp.external = True
            self.__import()

    def __import(self):
        """ import the xsd content at the specified url """
        if self.imp.location is None:
            url = self.imp.ns[1]
        else:
            url = self.imp.location
        try:
            if '://' not in url:
                url = urljoin(self.schema.baseurl, url)
            p = Parser()
            root = p.parse(url=url).root()
            self.imp.schema = Schema(root, url, impfilter=self.schema.impfilter)
            self.__import_succeeded()
        except Exception:
            self.__import_failed(url)
            
    def __import_failed(self, url):
        """ import failed """
        self.schema.impfilter.add(self.imp.ns[1])
        msg = \
            'imported schema (%s) at (%s), not-found' \
            (self.imp.ns[1], url)
        log.debug('%s, %s', self.id, msg, exc_info=True)
        if self.imp.location is not None:
            raise Exception(msg)
            
    def __import_succeeded(self):
        """ process the imported schema """
        self.imp.schema.init(0)
        if self.imp.ns[0] is not None:
            ns = self.imp.ns
            self.schema.root.addPrefix(ns[0], ns[1])
            
    def __repr__(self):
        result  = []
        result.append('<%s' % self.id)
        result.append(' {%s}' % self.stage)
        if self.imp.schema is None:
            result.append(' schema="n/r"')
        else:
            result.append(' schema="%s"' % self.imp.schema.id)
            result.append(' tns="%s"' % self.imp.schema.tns[1])
        result.append('/>')
        return ''.join(result)
            
    def __lt__(self, other):
        """ everything else first """
        return False


class XBuiltin(SchemaProperty):
    """
    Represents an (xsd) schema <xs:*/> node
    """
    
    def __init__(self, schema, name):
        """
        @param schema: The containing schema.
        @type schema: L{Schema}
        """
        root = Node('xsd-builtin')
        root.set('name', name)
        SchemaProperty.__init__(self, schema, root)
        
    def get_name(self):
        return self.root.get('name')
            
    def namespace(self):
        return Namespace.xsdns
    
    def resolve(self, depth=1024, nobuiltin=False):
        return self
    

class Any(XBuiltin):
    """
    Represents an (xsd) <any/> node
    """

    def __init__(self, schema, name):
        """
        @param schema: The containing schema.
        @type schema: L{Schema}
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
        @type schema: L{Schema}
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

   
class Attribute(Polymorphic):
    """
    Represents an (xsd) <attribute/> node
    """

    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{Schema}
        @param root: The xml root node.
        @type root: L{sax.Element}
        """
        Polymorphic.__init__(self, schema, root)
        
    def isattr(self):
        """ get whether the property is an attribute """
        return True
        
    def get_name(self):
        """ gets the <xs:attribute name=""/> attribute value """
        return self.root.get('name')
    
    def ref(self):
        """ gets the <xs:attribute type=""/> attribute value """
        return self.root.get('type')

    def get_default(self):
        """ gets the <xs:attribute default=""/> attribute value """
        return self.root.get('default', default='')
    
    def required(self):
        """ gets the <xs:attribute use="required"/> attribute value """
        use = self.root.get('use', default='')
        return ( use.lower() == 'required' )

    def __init2__(self):
        """
        Replace the root with the referenced root 
        while preserving @use.
        @see: L{SchemaProperty.__init2__()}
        """
        if self.referenced is not None:
            myuse = self.root.get('use')
            self.root = self.referenced.root
            if myuse is not None:
                self.root.set('use', myuse)

              
class Query(Object):
    
    clsorder = \
        ((XBuiltin, Simple, Element),
         (Complex,))
    
    def __init__(self, name):
        Object.__init__(self)
        self.id = objid(self)
        self.name = name
        if isqref(name):
            self.name = name[0]
            self.qname = name
        else:
            self.name = name  
            self.qname = None
        self.history = []
        self.resolved = False
        self.cidx = 0
        self.classes = self.clsorder[self.cidx]
        self.clsfilter = ()
        self.owner = None
        
    def increment(self, owner):
        max = len(self.clsorder)-1
        if self.owner == owner and \
            self.cidx < max:
                self.cidx += 1
                self.classes = self.clsorder[self.cidx]
                log.debug('%s, targeting %s', self.id, self.classes)
                self.history = []
                return True
        else:
            return False
        
    def filter(self, result):
        if result is None:
            return True
        cls = result.__class__
        reject = \
            ( cls  not in self.classes or \
              ( len(self.clsfilter) and cls not in self.clsfilter ) or \
              result in self.history )
        if reject:
            log.debug('result %s, rejected by\n%s', repr(result), tostr(self))
        return reject
    
    def qualify(self, resolvers, tns):
        """ convert the name a qualified reference """
        if self.qname is None:
            if isinstance(self.name, basestring):
                self.qname = qualified_reference(self.name, resolvers, tns)
            elif isqref(self.name):
                self.qname = name
                self.name = self.qname[0]
            else:
                raise Exception('name must be (str|qref)')
        
    def key(self):
        return \
            str(self.resolved) \
            + tostr(self.qname) \
            + tostr(self.clsfilter)

