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
The I{sxbase} module provides I{base} classes that represent
schema objects.
"""

from suds import *
from suds.xsd import *

log = logger(__name__)


class SchemaObject:
    """
    A schema object is an extension to object object with
    with schema awareness.
    @ivar root: The XML root element.
    @type root: L{sax.Element}
    @ivar schema: The schema containing this object.
    @type schema: L{schema.Schema}
    @ivar state: The transient states for the object
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
    @type children: [L{SchemaObject},...]
    @ivar attributes: A list of child xsd I{(attribute)} nodes
    @type attributes: [L{SchemaObject},...]
    @ivar derived: Derived type flag.
    @type derived: boolean
    @ivar resolve_result: The cached result of L{resolve()}
    @type resolve_result: L{SchemaObject}
    """
    
    init_stages = range(0,4)

    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{schema.Schema}
        @param root: The xml root node.
        @type root: L{sax.Element}
        """
        self.schema = schema
        self.root = root
        self.id = objid(self)
        self.factory = None
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
        @param name: The name of the object
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
        @rtype: [L{SchemaObject},...]
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
        @rtype: L{SchemaObject}
        """
        for child in self.get_children():
            if child.match(name, ns):
                return child
        return None
    
    def get_attributes(self):
        """
        Get a list of schema attribute nodes.
        @return: A list of attributes.
        @rtype: [L{sxbasic.Attribute},...]
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
        @rtype: L{SchemaObject}
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
        @rtype: L{SchemaObject}
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
                not (nobuiltin and resolved.builtin()):
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
    
    def builtin(self):
        """
        Get whether this is a schema-instance (xs) type.
        @return: True if any, else False
        @rtype: boolean
        """
        return False
    
    def enum(self):
        """
        Get whether this is a simple-type containing an enumeration.
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
        @rtype: L{SchemaObject}
        @see: L{qualified_reference()}
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
                
    def replace_child(self, child, replacements):
        """
        Replace a (child) with specified replacement objects.
        @param child: A child of this object.
        @type child: L{SchemaObject}
        @param replacements: A list of replacement properties.
        @type replacements: [L{SchemaObject},...]
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
        Get a string representation of this object.
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
            for c in self.attributes:
                result.append('\n')
                result.append(c.str(indent+1))
                result.append('@')
            for c in self.children:
                result.append('\n')
                result.append(c.str(indent+1))
            result.append('\n%s' % tab)
            result.append('</%s>' % self.__class__.__name__)
        else:
            result.append(' />')
        return ''.join(result)
    
    def isattr(self):
        """
        Get whether the object is a schema I{attribute} definition.
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
    
    def valid_children(self):
        """
        Get a list of valid child tag names.
        @return: A list of child tag names.
        @rtype: [str,...]
        """
        return ()
    
    def __resolve(self, t, history):
        """ resolve the specified type """
        result = t
        if t.typed():
            ref = qualified_reference(t.ref(), t.root, t.root.namespace())
            query = t.factory.create(query=ref)
            query.history = history
            log.debug('%s, resolving: %s\n using:%s', self.id, ref, query)
            resolved = query.execute(t.schema)
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
    

class Polymorphic(SchemaObject):
    
    """
    Represents a polymorphic object which is an xsd construct
    that may reference another by name.  Once the reference is
    resolved, the object transforms into the referenced object.
    """
    
    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{schema.Schema}
        @param root: The xml root node.
        @type root: L{sax.Element}
        """
        SchemaObject.__init__(self, schema, root)
        self.referenced = None
        
    def __init1__(self):
        """
        Resolve based on @ref (reference) found
        @see: L{SchemaObject.__init1__()}
        """
        ref = self.root.get('ref')
        if ref is not None:
            self.__find_referenced(ref)
        
    def __find_referenced(self, ref):
        """ 
        find the referenced object in top level elements
        first, then look deeper.
        """
        classes = (self.__class__,)
        n, ns = qualified_reference(ref, self.root, self.namespace())
        for c in self.schema.children:
            if c.match(n, ns=ns, classes=classes):
                self.referenced = c
                return
        qref = (n, ns)
        for c in self.schema.children:
            p = c.find(qref, classes)
            if p is not None:
                self.referenced = p
                return
        raise TypeNotFound(ref)

