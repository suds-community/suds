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
The I{sxbase} module provides I{base} classes that represent
schema objects.
"""

from logging import getLogger
from suds import *
from suds.xsd import *
from copy import copy, deepcopy

log = getLogger(__name__)


class SchemaObject:
    """
    A schema object is an extension to object object with
    with schema awareness.
    @ivar root: The XML root element.
    @type root: L{sax.element.Element}
    @ivar schema: The schema containing this object.
    @type schema: L{schema.Schema}
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
    @ivar container: The <sequence/>,<all/> or <choice/> 
        containing this object.
    @type container: L{SchemaObject}
    """

    @classmethod
    def prepend(cls, d, s, filter=None):
        """
        Prepend schema object's from B{s}ource list to 
        the B{d}estination list while applying the filter.
        @param d: The destination list.
        @type d: list
        @param s: The source list.
        @type s: list
        @param filter: A filter that allows items to be prepended.
        @type filter: L{ListFilter}
        """
        if filter is None:
            filter = ListFilter()
        i = 0
        for x in s:
            if filter.permit(x):
                d.insert(i, x)
                i += 1
    
    @classmethod
    def append(cls, d, s, filter=None):
        """
        Append schema object's from B{s}ource list to 
        the B{d}estination list while applying the filter.
        @param d: The destination list.
        @type d: list
        @param s: The source list.
        @type s: list
        @param filter: A filter that allows items to be appended.
        @type filter: L{ListFilter}
        """
        if filter is None:
            filter = ListFilter()
        for item in s:
            if filter.permit(item):
                d.append(item)

    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{schema.Schema}
        @param root: The xml root node.
        @type root: L{sax.element.Element}
        """
        self.schema = schema
        self.root = root
        self.id = objid(self)
        self.name = root.get('name')
        self.qname = (self.name, schema.tns[1])
        self.type = root.get('type')
        self.ref = [root.get('ref'), False]
        self.ref[1] = ( self.ref[0] is not None )
        self.form_qualified = schema.form_qualified
        self.nillable = False
        self.inherited = False
        self.children = []
        self.attributes = []
        self.container = None
        self.cache = {}
        self.flattened = False

    def namespace(self):
        """
        Get this properties namespace
        @return: The schema's target namespace
        @rtype: (I{prefix},I{URI})
        """
        return self.schema.tns
    
    def default_namespace(self):
        return self.root.defaultNamespace()
    
    def unbounded(self):
        """
        Get whether this node is unbounded I{(a collection)}
        @return: True if unbounded, else False.
        @rtype: boolean
        """
        return False
    
    def optional(self):
        """
        Get whether this type is optional.
        @return: True if optional, else False
        @rtype: boolean
        """
        return False
    
    def resolve(self, nobuiltin=False):
        """
        Resolve and return the nodes true self.
        @param nobuiltin: Flag indicates that resolution must
            not continue to include xsd builtins.
        @return: The resolved (true) type.
        @rtype: L{SchemaObject}
        """
        return self.cache.get(nobuiltin, self)
    
    def get_child(self, name):
        """
        Get (find) a I{non-attribute} child by name.
        @param name: A child name.
        @type name: str
        @return: The requested child.
        @rtype: L{SchemaObject}
        """
        for child in self.children:
            if child.any() or child.name == name:
                return child
        return None
    
    def get_attribute(self, name):
        """
        Get (find) a I{non-attribute} attribute by name.
        @param name: A attribute name.
        @type name: str
        @return: The requested child.
        @rtype: L{SchemaObject}
        """
        for child in self.attributes:
            if child.name == name:
                return child
        return None
    
    def sequence(self):
        """
        Get whether this is an <xs:sequence/>
        @return: True if any, else False
        @rtype: boolean
        """
        return False
    
    def all(self):
        """
        Get whether this is an <xs:all/>
        @return: True if any, else False
        @rtype: boolean
        """
        return False
    
    def choice(self):
        """
        Get whether this is an <xs:choice/>
        @return: True if any, else False
        @rtype: boolean
        """
        return False
        
    def any(self):
        """
        Get whether this is an <xs:any/>
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
    
    def containedbychoice(self):
        """
        Get whether this type is contained by a <choice/>.
        @return: True if contained by choice.
        @rtype: boolean
        """
        return False
    
    def isattr(self):
        """
        Get whether the object is a schema I{attribute} definition.
        @return: True if an attribute, else False.
        @rtype: boolean
        """
        return False
    
    def derived(self):
        """
        Get whether the object is derived in the it is an extension
        of another type.
        @return: True if derived, else False.
        @rtype: boolean
        """
        return False
        
    def find(self, qref, classes=()):
        """
        Find a referenced type in self or children.
        @param qref: A qualified reference.
        @type qref: qref
        @param classes: A list of classes used to qualify the match.
        @type classes: [I{class},...] 
        @return: The referenced type.
        @rtype: L{SchemaObject}
        @see: L{qualify()}
        """
        if not len(classes):
            classes = (self.__class__,)
        if self.qname == qref and self.__class__ in classes:
            return self
        for c in self.children:
            p = c.find(qref, classes)
            if p is not None:
                return p
        return None

    def translate(self, value, topython=True):
        """
        Translate a value (type) to/from a python type.
        @param value: A value to translate.
        @return: The converted I{language} type.
        """
        return value
    
    def childtags(self):
        """
        Get a list of valid child tag names.
        @return: A list of child tag names.
        @rtype: [str,...]
        """
        return ()
    
    def flatten(self, parent=None):
        """
        Walk the tree and invoke promote() on each node.  This gives each
        node the opportunity to flatten the tree as needed to remote
        uninteresting nodes.  Nodes that don't directly contribute to the
        structure of the data are omitted.
        """
        pa, pc = [],[]
        if not self.flattened:
            self.flattened = True
            log.debug(Repr(self))
            for c in self.children:
                a, c = c.flatten(self)
                pa += a
                pc += c
            if parent is None:
                self.attributes += pa
                self.children = pc
            else:
                self.promote(pa, pc)
        return (pa, pc)
            
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
        log.debug(Repr(self))
        filter = PromoteFilter()
        self.append(pa, self.attributes)
        self.append(pc, self.children, filter)
            
    def dereference(self):
        """
        Walk the tree and invoke mutate() on each node.  This gives each
        node the opportunity to resolve references to other types
        and mutate as needed.
        """
        if not self.ref[1]: return
        log.debug(Repr(self))
        self.ref[1] = False
        self.mutate()
            
    def mutate(self):
        """
        Mutate into a I{true} type as defined by a reference to
        another object.
        """
        pass

    def mark_inherited(self):
        """
        Mark this branch in the tree as inherited = true.
        """
        self.inherited = True
        for c in self.children:
            c.mark_inherited()
            
    def contents(self, collection):
        """
        Get a I{flattened} list of this nodes contents.
        @param collection: A list to fill.
        @type collection: list
        @return: The filled list.
        @rtype: list
        """
        collection.append(self)
        for a in self.attributes:
            collection.append(a)
        for c in self.children:
            c.contents(collection)
        return collection
    
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
        for n in self.description():
            if not hasattr(self, n):
                continue
            v = getattr(self, n)
            if v is None:
                continue
            result.append(' %s="%s"' % (n, v))
        if len(self):
            result.append('>')
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
    
    def description(self):
        """
        Get the names used for str() and repr() description.
        @return:  A dictionary of relavent attributes.
        @rtype: [str,...]
        """
        return ()
        
    def __str__(self):
        return unicode(self).encode('utf-8')
            
    def __unicode__(self):
        return unicode(self.str())
    
    def __repr__(self):
        s = []
        s.append('<%s' % self.id)
        for n in self.description():
            if not hasattr(self, n):
                continue
            v = getattr(self, n)
            if v is None:
                continue
            s.append(' %s="%s"' % (n, v))
        s.append(' />')
        myrep = ''.join(s)
        return myrep.encode('utf-8')
    
    def __len__(self):
        return len(self.children)+len(self.attributes)
    
    def __getitem__(self, index):
        return self.children[index]

    def __deepcopy__(self, memo={}):
        clone = copy(self)
        clone.attributes = deepcopy(self.attributes)
        clone.children = deepcopy(self.children)
        return clone


class Promotable(SchemaObject):
    """
    Represents I{promotable} schema objects.  They are objects that
    should be promoted during the flattening process.
    """
    
    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{schema.Schema}
        @param root: The xml root node.
        @type root: L{sax.element.Element}
        """
        SchemaObject.__init__(self, schema, root)


class ListFilter:
    def permit(self, x):
        return True        

class PromoteFilter(ListFilter):
    def permit(self, x):
        return isinstance(x, Promotable)
    
class UniqueFilter(ListFilter):
    def __init__(self, d):
        self.ids = [m.id for m in d]
    def permit(self, x):
        return ( x.id not in self.ids )