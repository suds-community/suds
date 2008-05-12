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
from suds.sudsobject import Object
from sax import *
from urlparse import urljoin
import logging

log = logger(__name__)


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
        @param importfilter: A list of namespaces B{not} to import.
        @type importfilter: set
        """
        self.root = wsdl.root
        self.tns = wsdl.tns
        self.baseurl = wsdl.url
        self.children = []
        if impfilter is None:
            self.impfilter = set([xsdns[1], xsins[1]])
        else:
            self.impfilter = impfilter
        self.namespaces = {}
        
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
        if log.isEnabledFor(logging.DEBUG):
            log.debug('schema (%s):\n%s', self.baseurl, str(self))
        
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
            schema = \
                Schema(child[0], self.baseurl, self, self.impfilter)
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
    @ivar efdq: The @B{e}lementB{F}ormB{D}efault="B{q}ualified" flag. 
    @type efdq: boolean
    @ivar baseurl: The I{base} URL for this schema.
    @type baseurl: str
    @ivar container: A schema collection containing this schema.
    @type container: L{SchemaCollection}
    @ivar types: A schema types cache.
    @type types: {path:L{SchemaProperty}}
    @ivar children: A list of child properties.
    @type children: [L{SchemaProperty},...]
    @ivar impfilter: A list of namespaces B{not} to import.
    @type impfilter: set
    """

    factory =\
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
    }
    
    def __init__(self, root, baseurl=None, container=None, impfilter=None):
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
        self.tns = self.__tns()
        self.efdq = self.__efdq()
        self.baseurl = baseurl
        self.container = container
        self.types = {}
        self.children = []
        if impfilter is None:
            self.impfilter = set([xsdns[1], xsins[1]])
        else:
            self.impfilter = impfilter
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
    
    def __efdq(self):
        """ get whether @elementFromDefualt = \"qualified\" """
        efd = self.root.get('elementFormDefault')
        if efd is None:
            return False
        else:
            return ( efd.lower() == 'qualified' )
    
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
        log.debug('finding (%s)', ref)
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
            log.debug('found (%s) as:\n%s', ref, result)
            history.append(result)
            if resolved or len(parts) > 1:
                result = result.resolve(history)
                log.debug('resolved (%s) as:\n%s', ref, result)
            for part in parts[1:]:
                ref, ns = part
                log.debug('find-child (%s)', ref)
                result = result.get_child(ref, ns)
                if result is None:
                    break
                log.debug('found (%s) as:\n%s', ref, result)
                if resolved:
                    result = result.resolve(history)
                log.debug('resolved (%s) as:\n%s', ref, result)
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
    @ivar root: The XML root element.
    @type root: L{sax.Element}
    @ivar schema: The schema containing this object.
    @type schema: L{Schema}
    @ivar state: The transient states for the property
    @type state: L{Object}
    @ivar state.depsolve: The dependancy resolved flag.
    @type state.depsolve: boolean
    @ivar state.promoted: The child promoted flag.
    @type state.promoted: boolean
    @ivar children: A list of child xsd I{(non-attribute)} nodes
    @type children: [L{SchemaProperty},...]
    @ivar attributes: A list of child xsd I{(attribute)} nodes
    @type attributes: [L{SchemaProperty},...]
    """

    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{Schema}
        @param root: The xml root node.
        @type root: L{sax.Element}
        """
        self.schema = schema
        self.root = root
        self.state = Object()
        self.state.depsolved = False
        self.state.promoted = False
        self.children = []
        self.attributes = []
        
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
        qualified by L{qualified_reference()}
        @return: The object's (qualified) type reference
        @rtype: I{qualified reference}
        @see: L{qualified_reference()}
        """
        ref = self.ref()
        if ref is not None:
            return qualified_reference(ref, self.root, self.schema.tns)
        else:
            return (None, defns)
        
    def asref(self):
        """
        Get the B{qualified} referenced (xsi) type as defined by the schema.
        This is usually the value of the I{type} attribute that has been
        qualified by L{qualified_reference()}.  The diffrerence between this
        method and L{qref()} is the first element in the returned tuple has a
        namespace prefix.
        @return: The object's (qualified) type reference
        @rtype: I{qualified reference}
        @see: L{qualified_reference()}
        """
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
    
    def get_attributes(self):
        """
        Get a list of schema attribute nodes.
        @return: A list of attributes.
        @rtype: [L{Attribute},...]
        """ 
        return self.attributes
    
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
    
    def unbounded(self):
        """
        Get whether this node is unbounded I{(a collection)}
        @return: True if unbounded, else False.
        @rtype: boolean
        """
        return False
    
    def resolve(self, history=None):
        """
        Resolve and return the nodes true type when another
        named type is referenced.
        @param history: The history of matched items.
        @type history: [L{SchemaProperty},...]
        @return: The resolved (true) type.
        @rtype: L{SchemaProperty}
        """
        if history is None:
            history = [self]
        result = self
        if self.custom():
            ref = qualified_reference(self.ref(), self.root, self.namespace())
            resolved = self.schema.find(ref, history)
            if resolved is not None:
                result = resolved
        return result
    
    def custom(self):
        """
        Get whether this object's schema type is a I{custom} type.
        Custom types are those types that are not I{built-in}.
        The result is based on the value of get_type() and not
        on the object's class.
        @return: True if custom, else False.
        @rtype: boolean
        """
        ref = self.ref()
        if ref is not None:
            return self.schema.custom(ref)
        else:
            return False
    
    def builtin(self):
        """
        Get whether this object's schema type is a I{built-in} type.
        The result is based on the value of get_type() and not
        on the object's class.
        @return: True if built-in, else False.
        @rtype: boolean
        """
        ref = self.ref()
        if ref is None:
            return self.schema.builtin(ref)
        else:
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
        if self.match(n, ns, classes):
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
        @see: L{Schema.factory}
        """
        for path in paths:
            for root in self.root.childrenAtPath(path):
                fn = Schema.factory[root.name]
                child = fn(self.schema, root)
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
            c.promote()
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
            for c in ( self.attributes + self.children ):
                result.append('\n')
                result.append(c.str(indent+1))
            result.append('\n%s' % tab)
            result.append('</%s>' % tag)
        else:
            result.append(' />')
        return ''.join(result)
    
    def depsolve(self):
        """
        Perform dependancy solving.
        Dependancies are resolved to their I{true} types during
        schema loading.
        @note: Propagated to children.
        @see: L{__depsolve__()}
        """
        if not self.state.depsolved:
            self.__depsolve__()
            self.state.depsolved = True
        for c in self.children:
            c.depsolve()
        return self

    def promote(self):
        """
        Promote grand-children as need for proper denormalization
        of the object model.
        @note: Propagated to children.
        @see: L{__promote__()}
        """
        if not self.state.promoted:
            self.__promote__()
            self.state.promoted = True
        for c in self.children:
            c.promote()
        return self
    
    def isattr(self):
        """
        Get whether the property is a schema I{attribute} definition.
        @return: True if an attribute, else False.
        @rtype: boolean
        """
        return False
    
    def must_qualify(self):
        """
        Get whether the schema specifies that the
        default element form is (qualified).
        @return: True, if qualified
        @rtype: boolean
        """
        return self.schema.efdq
    
    def __depsolve__(self):
        """
        Perform dependancy solving.
        Dependancies are resolved to their I{true} types during
        schema loading.  Should only be invoked by L{depsolve()}
        @precondition: The model must be initialized.
        @note: subclasses override here!
        @see: L{depsolve()}
        """
        pass
    
    def __promote__(self):
        """
        Perform dependancy solving.
        Dependancies are resolved to their I{true} types during
        schema loading.  Should only be invoked by L{promote()}
        @precondition: The model must be initialized.
        @precondition: L{__depsolve__()} have been invoked.
        @note: subclasses override here!
        @see: L{promote()}
        """
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
        
    def __depsolve__(self):
        """
        Resolve based on @ref (reference) found
        @see: L{SchemaProperty.__depsolve__()}
        """
        ref = self.root.get('ref')
        if ref is not None:
            self.__find_referenced(ref)
        
    def __find_referenced(self, ref):
        """ find the referenced property """
        for c in self.schema.children:
            p = c.find(ref, (self.__class__,))
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
          'complexContent')
    
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
        
    def __promote__(self):
        """ promote grand-children """
        self.promote_grandchildren()


class Simple(SchemaProperty):
    """
    Represents an (xsd) schema <xs:simpleType/> node
    """
    
    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{Schema}
        @param root: The xml root node.
        @type root: L{sax.Element}
        """
        SchemaProperty.__init__(self, schema, root)
        self.add_children('restriction/enumeration')

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
    
    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{Schema}
        @param root: The xml root node.
        @type root: L{sax.Element}
        """
        SchemaProperty.__init__(self, schema, root)
        self.add_children('element')


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

    def __promote__(self):
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
    
    valid_children = ('attribute', 'complexType',)
    
    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{Schema}
        @param root: The xml root node.
        @type root: L{sax.Element}
        """
        Polymorphic.__init__(self, schema, root)
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
    
    def __promote__(self):
        """
        if referenced (@ref) then promote the referenced
        node; then replace my children with those of the
        referenced node; otherwise, promote my grand-children
        @see: L{SchemaProperty.__promote__()}
        """
        if self.referenced is not None:
            self.referenced.promote()
            self.root = self.referenced.root
            self.children = self.referenced.children
        else:
            self.promote_grandchildren()


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
        self.imported = None
        ns = (None, root.get('namespace'))
        location = root.get('schemaLocation')
        log.debug('import (%s) at: (%s)', ns[1], location)
        if self.skip(ns):
            log.debug('import (%s) skipped', ns[1])
            return
        self.__import(ns, location)
        self.__add_children()

    def namespace(self):
        """ get this properties namespace """
        return self.imported.tns
    
    def skip(self, ns):
        """ skip this namespace """
        return \
            ns[1] == self.schema.tns or \
            ns[1] in self.schema.impfilter

    def __add_children(self):
        """ add imported children """
        if self.imported is not None:
            for c in self.imported.children:
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
        except:
            self.schema.impfilter.add(ns[1])
            log.debug(
                'imported schema (%s) at (%s), not-found\n', 
                ns[1], location)
            
    def __process_import(self, imp_root, ns, location):
        """ process the imported schema """
        schema = \
            Schema(imp_root, location, impfilter=self.schema.impfilter)
        schema.reset_tns(ns)
        self.imported = schema


class XBuiltin(SchemaProperty):
    """
    Represents an (xsd) schema <xs:*/> node
    """
    
    def __init__(self, schema, name):
        """
        @param schema: The containing schema.
        @type schema: L{Schema}
        """
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

    def __promote__(self):
        """
        Replace the root with the referenced root 
        while preserving @use.
        @see: L{SchemaProperty.__promote__()}
        """
        if self.referenced is not None:
            myuse = self.root.get('use')
            self.root = self.referenced.root
            if myuse is not None:
                self.root.set('use', myuse)
