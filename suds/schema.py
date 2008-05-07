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
from suds.sudsobject import Object
from sax import Parser, splitPrefix, defns
from urlparse import urljoin


def qualified_reference(ref, resolvers, tns=defns):
    """
    Get type reference I{qualified} by pnamespace.
    @param ref: A referenced type name such as <person type="tns:person"/>
    @type ref: str
    @param resolvers: A list of objects to be used to resolve types.
    @type resolvers: [L{sax.Element},]
    @param tns: An optional target namespace used to qualify references
        when no prefix is specified.
    @type tns: A namespace I{tuple: (prefix,uri)}
    @return: A qualified reference.
    @rtype: (name, ns)
    @note: Suds namespaces are tuples: I{(prefix,URI)}.  An example
        qualified reference would be: ("myname",("tns", "http://..."))
    """
    ns = tns
    p, n = splitPrefix(ref)
    if p is not None:
        if not isinstance(resolvers, (list, tuple)):
            resolvers = (resolvers,)
        for r in resolvers:
            resolved = r.resolvePrefix(p)
            if resolved[1] is not None:
                ns = resolved
                break 
    return (n, ns)

def isqref(object):
    """
    Get whether the object is a qualified reference.
    @param object: An object to be tested.
    @type object: I{any}
    @rtype: boolean
    """
    return (\
        isinstance(object, tuple) and \
        len(object) == 2 and \
        isinstance(object[0], basestring) and \
        isinstance(object[1], tuple) and \
        len(object[1]) == len(defns))


class SchemaCollection:
    
    """
    A collection of schema objects.  This class is needed because WSDLs may contain
    more then one <schema/> node.
    @ivar root: A root node used for ns prefix resolution (set to WSDL's root).
    @type root: L{Element}
    @ivar tns: The target namespace (set to WSDL's target namesapce)
    @type tns: (prefix,URI)
    """
    
    def __init__(self, wsdl):
        """
        @param wsdl: A WSDL object.
        @type wsdl: L{wsdl.WSDL}
        """
        self.root = wsdl.root
        self.tns = wsdl.tns
        self.baseurl = wsdl.url
        self.children = []
        self.namespaces = {}
        self.log = logger('schema')
        
    def add(self, node):
        """
        Add a schema node to the collection.
        @param node: A <schema/> root node.
        @type node: L{Element}
        """
        child = [node, None]
        self.children.append(child)
        tns = node.get('targetNamespace')
        self.namespaces[tns] = child
        
    def load(self):
        """
        Load the schema objects for the root nodes.
        """
        for child in self.children:
            self.build(child)
        
    def imported(self, ns):
        """
        Find an imported schema by namespace.  Only the URI portion of
        the namespace is compared to each schema's I{targetNamespace}
        @param ns: A namespace.
        @type ns: (prefix,URI)
        @return: The schema matching the namesapce, else None.
        @rtype: L{Schema}
        """
        child = self.namespaces.get(ns[1], None)
        if child is not None:
            return self.build(child)
        else:
            return None

    def find(self, path, history=None, resolved=True):
        """ @see: L{Schema.find()} """
        if history is None:
            history = []
        for s in [c[1] for c in self.children]:
            result = s.find(path, history, resolved)
            if result is not None:
                return result
        return None
    
    def build(self, child):
        """
        Build a L{Schema} object for each node for which one has not already
        been built.
        @param child: A child.
        @type child: [L{Element}, L{Schema}]
        @return: child[1]
        @rtype: L{Schema}
        """
        if child[1] is None:
            schema = Schema(child[0], self.baseurl, self)
            child[1] = schema
        return child[1]
    
    def __len__(self):
        return len(self.children)
    
    def __str__(self):
        return unicode(self).encode('utf-8')
    
    def __unicode__(self):
        result = ['\nschema collection']
        for s in [c[1] for c in self.children]:
            result.append(s.str(1))
        return '\n'.join(result)


class Schema:
    
    """
    The schema is an objectification of a <schema/> (xsd) definition.
    It provides inspection, lookup and type resolution.
    @cvar factory: A factory to create property objects based on tag.
    @type factory: {tag:fn,}
    @ivar root: The root node.
    @type root: L{sax.Element}
    @ivar tns: The target namespace.
    @type tns: (prefix,URI)
    @ivar baseurl: The I{base} URL for this schema.
    @type baseurl: str
    @ivar container: A schema collection containing this schema.
    @type container: L{SchemaCollection}
    @ivar types: A schema types cache.
    @type types: {path:L{SchemaProperty}}
    """

    factory =\
    {
        'import' : lambda x,y,z=None: Import(x,y,z), 
        'complexType' : lambda x,y,z=None: Complex(x,y,z), 
        'simpleType' : lambda x,y,z=None: Simple(x,y,z), 
        'element' : lambda x,y,z=None: Element(x,y,z),
        'sequence' : lambda x,y,z=None: Sequence(x,y,z),
        'complexContent' : lambda x,y,z=None: ComplexContent(x,y,z),
        'enumeration' : lambda x,y,z=None: Enumeration(x,y,z),
        'extension' : lambda x,y,z=None: Extension(x,y,z),
    }
    
    def __init__(self, root, baseurl=None, container=None):
        """
        """
        self.log = logger('schema')
        self.root = root
        self.tns = self.__tns()
        self.baseurl = baseurl
        self.container = container
        self.types = {}
        self.children = []
        self.__add_children()
        self.__load_children()
                
    def __add_children(self):
        """ populate the list of children """
        for node in self.root.children:
            if node.name in self.factory:
                fn = self.factory[node.name]
                child = fn(self, node)
                if isinstance(child, Import):
                    self.children += child.children
                else:
                    self.children.append(child)
                
    def __tns(self):
        """ get the target namespace """
        tns = [None, self.root.get('targetNamespace')]
        if tns[1] is not None:
            tns[0] = self.root.findPrefix(tns[1])
        return tuple(tns)
    
    def __load_children(self):
        """ run children through depsolving and child promotion """
        for c in self.children:
            c.depsolve()
        for c in self.children:
            c.promote()
        
    def imported(self, ns):
        """ find schema imported by namespace """
        if self.container is not None:
            return self.container.imported(ns)
        else:
            return None
        
    def find(self, path, history=None, resolved=True):
        """
        Find a I{type} defined in one of the contained schemas.
        @param path: The path to the requested type.
        @type path: (str|[qref,])
        @param history: A list of found path segments used to prevent either
            cyclic graphs and/or type self references.
        @type history: [L{SchemaProperty},]
        @param resolved: A flag that controls whether or not types are resolved
            automatically to their I{true} types.
        @type resolved: boolean
        @note: I{qref} = qualified reference
        @see: L{qualified_reference()}
        """
        key = None
        if history is None:
            history = []
        try:
            key = '/'.join((str(resolved), unicode(path)))
        except:
            pass
        if key is not None:
            cached = self.types.get(key, None)
            if cached is not None and \
                cached not in history:
                    return cached
        if self.builtin(path):
            b = XBuiltin(self, path)
            return b
        result = self.__find_path(path, history, resolved)
        if result is not None and \
            key is not None:
                self.types[key] = result
        return result

    def custom(self, ref, context=None):
        """ get whether specified type reference is custom """
        if ref is None:
            return False
        else:
            return (not self.builtin(ref, context))
    
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
            return (prefix in prefixes)
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

    def str(self, indent=0):
        tab = '%*s'%(indent*3, '')
        result = []
        result.append('%s(raw)' % tab)
        result.append(self.root.parent.str(indent+1))
        result.append('%s(model)' % tab)
        for c in self.children:
            result.append(c.str(indent+1))
        return '\n'.join(result) 
    
    def __find_path(self, path, history, resolved):
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
                    result = None
                    continue
                if result is not None:
                    break
            else:
                if child.match(ref, ns):
                    result = child
                    if result in history:
                        result = None
                    else:
                        break
        if result is not None:
            history.append(result)
            if resolved or len(parts) > 1:
                result = result.resolve(history)
            for part in parts[1:]:
                ref, ns = part
                result = result.get_child(ref, ns)
                if result is None:
                    break
                if resolved:
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
        return self.str()


class SchemaProperty:
    
    """
    A schema property is an extension to property object with
    with schema awareness.
    """

    def __init__(self, schema, root, parent):
        """ create the object with a schema and root node """
        self.root = root
        self.schema = schema
        self.parent = parent
        self.log = schema.log
        self.state = Object()
        self.state.depsolved = False
        self.state.promoted = False
        self.children = []
        
    def match(self, name, ns=None, classes=()):
        """ match by name and optional namespace """
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
        """ get the true type as need for external qualified reference """
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
        
    def find(self, ref, classes=()):
        """ find a referenced type in self or child """
        if isqref(ref):
            n, ns = ref
        else:
            n, ns = qualified_reference(ref, self.root, self.namespace())
        if self.match(n, ns, classes):
            return self
        qref = (n, ns)
        for c in self.children:
            p = c.find(qref, classes)
            if p is not None:
                return p
        return None
    
    def add_children(self, *paths):
        """ add (sax) children at the specified paths as properties """
        for path in paths:
            for root in self.root.childrenAtPath(path):
                fn = Schema.factory[root.name]
                child = fn(self.schema, root, self)
                self.children.append(child)
                
    def replace_child(self, child, replacements):
        """ replace (child) with specified replacements """
        index = self.children.index(child)
        self.children.remove(child)
        for c in replacements:
            c.parent = self
            self.children.insert(index, c)
            index += 1
            
    def promote_grandchildren(self):
        """ promote grand-children to replace the parents """
        children = list(self.children)
        for c in children:
            c.promote()
            self.replace_child(c, c.children)
        
    def str(self, indent=0):
        tag = self.__class__.__name__
        tab = '%*s'%(indent*3, '')
        result  = []
        result.append('%s<%s ' % (tab, tag))
        result.append('name="%s"' % self.get_name())
        try:
            ref = self.asref()
        except: 
            ref = (None,(None,None))
        result.append(', type="%s (%s)"' % (ref[0], ref[1][1]))
        if len(self):
            for c in self.children:
                result.append('\n')
                result.append(c.str(indent+1))
            result.append('\n%s' % tab)
            result.append('</%s>' % tag)
        else:
            result.append(' />')
        return ''.join(result)
    
    def depsolve(self):
        if not self.state.depsolved:
            self.__depsolve__()
            self.state.depsolved = True
        for c in self.children:
            c.depsolve()
        return self

    def promote(self):
        if not self.state.promoted:
            self.__promote__()
            self.state.promoted = True
        for c in self.children:
            c.promote()
        return self
    
    def __depsolve__(self):
        """ overridden by subclasses """
        pass
    
    def __promote__(self):
        """ overridden by subclasses """
        pass
        
    def __str__(self):
        return unicode(self).encode('utf-8')
            
    def __unicode__(self):
        return unicode(self.str())
    
    def __repr__(self):
        return unicode(self).encode('utf-8')
    
    def __len__(self):
        return len(self.children)
    
    def __getitem__(self, index):
        return self.children[index]


class Complex(SchemaProperty):
    
    """ Represents an (xsd) schema <xs:complexType/> node """
    
    def __init__(self, schema, root, parent=None):
        SchemaProperty.__init__(self, schema, root, parent)
        self.add_children('sequence', 'complexContent')
        
    def get_name(self):
        """ gets the <xs:complexType name=""/> attribute value """
        return self.root.get('name')
        
    def __promote__(self):
        """ promote grand-children """
        self.promote_grandchildren()


class Simple(SchemaProperty):
    
    """ Represents an (xsd) schema <xs:simpleType/> node """
    
    def __init__(self, schema, root, parent=None):
        SchemaProperty.__init__(self, schema, root, parent)
        self.add_children('restriction/enumeration')

    def get_name(self):
        """ gets the <xs:simpleType name=""/> attribute value """
        return self.root.get('name')

    def ref(self):
        """ gets the <xs:simpleType xsi:type=""/> attribute value """
        return self.root.get('type')


class Sequence(SchemaProperty):
    
    """ Represents an (xsd) schema <xs:sequence/> node """
    
    def __init__(self, schema, root, parent=None):
        SchemaProperty.__init__(self, schema, root, parent)
        self.add_children('element')


class ComplexContent(SchemaProperty):
    
    """ Represents an (xsd) schema <xs:complexContent/> node """
    
    def __init__(self, schema, root, parent=None):
        SchemaProperty.__init__(self, schema, root, parent)
        self.add_children('extension')

    def __promote__(self):
        """ promote grand-children """
        self.promote_grandchildren()


class Enumeration(SchemaProperty):
    
    """ Represents an (xsd) schema <xs:enumeration/> node """

    def __init__(self, schema, root, parent=None):
        SchemaProperty.__init__(self, schema, root, parent)
        
    def get_name(self):
        """ gets the <xs:enumeration value=""/> attribute value """
        return self.root.get('value')

    
class Element(SchemaProperty):
    
    """ Represents an (xsd) schema <xs:element/> node """
    
    valid_children = ('complexType',)
    
    def __init__(self, schema, root, parent=None):
        SchemaProperty.__init__(self, schema, root, parent)
        self.add_children(*Element.valid_children)
        self.referenced = None
        
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

    def __depsolve__(self):
        """ load based on @ref (reference) found """
        ref = self.root.get('ref')
        if ref is not None:
            self.__find_referenced(ref)
    
    def __promote__(self):
        """
        if referenced (@ref) then promote the referenced
        node; then replace my children with those of the
        referenced node; otherwise, promote my grand-children
        """
        if self.referenced is not None:
            self.referenced.promote()
            self.root = self.referenced.root
            self.children = self.referenced.children
        else:
            self.promote_grandchildren()
        
    def __find_referenced(self, ref):
        """ find the referenced element """
        for c in self.schema.children:
            p = c.find(ref, (Element,))
            if p is not None:
                self.referenced = p
                return
        raise TypeNotFound(ref)


class Extension(Complex):
    
    """ Represents an (xsd) schema <xs:extension/> node """
    
    def __init__(self, schema, root, parent=None):
        Complex.__init__(self, schema, root, parent)
        self.super = None
        
    def __depsolve__(self):
        """ lookup superclass  """
        Complex.__depsolve__(self)
        base = self.root.get('base')
        self.super = self.schema.find(base)
        if self.super is None:
            raise TypeNotFound(base)
        
    def __promote__(self):
        """ add base type's children as my own """
        Complex.__promote__(self)
        index = 0
        self.super.promote()
        for c in self.super.children:
            self.children.insert(index, c)
            index += 1


class Import(SchemaProperty):
    
    """ Represents an (xsd) schema <xs:import/> node """
    
    def __init__(self, schema, root, parent=None):
        SchemaProperty.__init__(self, schema, root, parent)
        self.imported = None
        ns = (None, root.get('namespace'))
        location = root.get('schemaLocation')
        self.__import(ns, location)
        self.__add_children()

    def namespace(self):
        """ get this properties namespace """
        return self.imported.tns

    def __add_children(self):
        """ add imported children """
        if self.imported is not None:
            for c in self.imported.children:
                c.parent = self
                self.children.append(c)

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


class XBuiltin(SchemaProperty):
    
    """ Represents an (xsd) schema <xs:*/> node """
    
    def __init__(self, schema, name, parent=None):
        SchemaProperty.__init__(self, schema, schema.root, parent)
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
