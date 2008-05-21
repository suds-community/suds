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
The sax module contains a collection of classes that provide a
(D)ocument (O)bject (M)odel representation of an XML document.
The goal is to provide an easy, intuative interface for managing XML
documents.  Although, the term, DOM, is used above, this model is
B{far} better.

XML namespaces in suds are represented using a (2) element tuple
containing the prefix and the URI.  Eg: I{('tns', 'http://myns')}

@var defns: The default namespace
@type defns: namespace : (I{prefix},I{URI})
@var xsdns: The I{schema} namespace
@type xsdns: namespace : (I{prefix},I{URI})
@var xsins: The I{schema-instance} namespace.
@type xsins: namespace : (I{prefix},I{URI})
"""

from suds import *
from urllib import urlopen
from xml.sax import parse, parseString, ContentHandler

log = logger(__name__)

def splitPrefix(name):
    """
    Split the name into a tuple (I{prefix}, I{name}).  The first element in
    the tuple is I{None} when the name does't have a prefix.
    @param name: A node name containing an optional prefix.
    @type name: basestring
    @return: A tuple containing the (2) parts of I{name}
    @rtype: (I{prefix}, I{name}) 
    """
    if isinstance(name, basestring) \
        and ':' in name:
            return tuple(name.split(':', 1))
    else:
        return (None, name)


defns = (None, None)
xsdns = ('xs', 'http://www.w3.org/2001/XMLSchema')
xsins = ('xsi', 'http://www.w3.org/2001/XMLSchema-instance')


class Attribute:
    """
    An XML attribute object.
    @ivar parent: The node containing this attribute
    @type parent: L{Element}
    @ivar prefix: The I{optional} namespace prefix.
    @type prefix: basestring
    @ivar name: The I{unqualified} name of the attribute
    @type name: basestring
    @ivar value: The attribute's value
    @type value: basestring
    """
    def __init__(self, name, value=None):
        """
        @param name: The attribute's name with I{optional} namespace prefix -OR-
            a tuple as: (I{prefix},I{name})
        @type name: basestring
        @param value: The attribute's value
        @type value: basestring 
        """
        self.parent = None
        if isinstance(name, basestring):
            self.prefix, self.name = splitPrefix(name)
        else:
            self.prefix = name[0]
            self.name = name[1]
        self.value = encode(value)
        
    def clone(self, parent=None):
        """
        Clone this object.
        @param parent: The parent for the clone.
        @type parent: L{Element}
        @return: A copy of this object assigned to the new parent.
        @rtype: L{Attribute}
        """
        a = Attribute(self.qname(), self.value)
        a.parent = parent
        return a
    
    def qname(self):
        """
        Get the B{fully} qualified name of this attribute
        @return: The fully qualified name.
        @rtype: basestring
        """
        if self.prefix is None:
            return self.name
        else:
            return ':'.join((self.prefix, self.name))
        
    def setValue(self, value):
        """
        Set the attributes value
        @param value: The new value (may be None)
        @type value: basestring
        """
        self.value = encode(value)
        
    def getValue(self, default=''):
        """
        Get the attributes value with optional default.
        @param default: An optional value to be return when the
            attribute's has not been set.
        @type default: basestring
        @return: The attribute's value, or I{default}
        @rtype: basestring
        """
        result = decode(self.value)
        if result is None:
            result = default
        return result
        
    def namespace(self):
        """
        Get the attributes namespace.  This may either be the namespace
        defined by an optional prefix, or its parent's namespace.
        @return: The attribute's namespace
        @rtype: (I{prefix}, I{name})
        """
        if self.prefix is None:
            return defns
        else:
            return self.resolvePrefix(self.prefix)
        
    def resolvePrefix(self, prefix):
        """
        Resolve the specified prefix to a known namespace.
        @param prefix: A declared prefix
        @type prefix: basestring
        @return: The namespace that has been mapped to I{prefix}
        @rtype: (I{prefix}, I{name})
        """
        ns = defns
        if self.parent is not None:
            ns = self.parent.resolvePrefix(prefix)
        return ns
    
    def __eq__(self, rhs):
        """ equals operator """
        return rhs is not None and \
            isinstance(rhs, Attribute) and \
            self.prefix == rhs.name and \
            self.name == rhs.name
            
    def __repr__(self):
        """ get a string representation """
        return \
            'attr (prefix=%s, name=%s, value=(%s))' %\
                (self.prefix, self.name, self.value)

    def __str__(self):
        """ get an xml string representation """
        return unicode(self).encode('utf-8')
    
    def __unicode__(self):
        """ get an xml string representation """
        return u'%s="%s"' % (self.qname(), self.value)


class Element:
    
    """
    An XML element object.
    @ivar parent: The node containing this attribute
    @type parent: L{Element}
    @ivar prefix: The I{optional} namespace prefix.
    @type prefix: basestring
    @ivar name: The I{unqualified} name of the attribute
    @type name: basestring
    @ivar expns: An explicit namespace (xmlns="...").
    @type expns: (I{prefix}, I{name})
    @ivar nsprefixes: A mapping of prefixes to namespaces.
    @type nsprefixes: dict
    @ivar attributes: A list of XML attributes.
    @type attributes: [I{Attribute},]
    @ivar text: The element's I{text} content.
    @type text: basestring
    @ivar children: A list of child elements.
    @type children: [I{Element},]
    @cvar matcher: A collection of I{lambda} for string matching.
    """

    matcher = \
    {
        'eq': lambda a,b: a == b,
        'startswith' : lambda a,b: a.startswith(b),
        'endswith' : lambda a,b: a.endswith(b),
        'contains' : lambda a,b: b in a 
    }
    
    @classmethod
    def buildPath(self, parent, path):
        """
        Build the specifed pat as a/b/c where missing intermediate nodes are built
        automatically.
        @param parent: A parent element on which the path is built.
        @type parent: I{Element}
        @param path: A simple path separated by (/).
        @type path: basestring
        @return: The leaf node of I{path}.
        @rtype: L{Element}
        """
        for tag in path.split('/'):
            child = parent.getChild(tag)
            if child is None:
                child = Element(tag, parent)
            parent = child
        return child

    def __init__(self, name, parent=None, ns=None):
        """
        @param name: The element's (tag) name.  May cotain a prefix.
        @type name: basestring
        @param parent: An optional parent element.
        @type parent: I{Element}
        @param ns: An optional namespace
        @type ns: (I{prefix}, I{name})
        """
        
        self.rename(name)
        self.expns = None
        self.nsprefixes = {}
        self.attributes = []
        self.text = None
        if parent is not None:
            if isinstance(parent, Element):
                self.parent = parent
            else:
                raise Exception('parent (%s) not-valid', parent.__class__.__name__)
        else:
            self.parent = None
        self.children = []
        self.applyns(ns)
        
    def rename(self, name):
        """
        Rename the element.
        @param name: A new name for the element.
        @type name: basestring 
        """
        if name is None:
            raise Exception('name (%s) not-valid' % name)
        else:
            self.prefix, self.name = splitPrefix(name)

    def qname(self):
        """
        Get the B{fully} qualified name of this element
        @return: The fully qualified name.
        @rtype: basestring
        """
        if self.prefix is None:
            return self.name
        else:
            return '%s:%s' % (self.prefix, self.name)
        
    def getRoot(self):
        """
        Get the root (top) node of the tree.
        @return: The I{top} node of this tree.
        @rtype: I{Element}
        """
        if self.parent is None:
            return self
        else:
            return self.parent.getRoot()
        
    def clone(self, parent=None):
        """
        Deep clone of this element and children.
        @param parent: An optional parent for the copied fragment.
        @type parent: I{Element}
        @return: A deep copy parented by I{parent}
        @rtype: I{Element}
        """
        root = Element(self.qname(), parent, self.namespace())
        for a in self.attributes:
            root.append(a.clone(self))
        for c in self.children:
            root.append(c.clone(self))
        for item in self.nsprefixes.items():
            root.addPrefix(item[0], item[1])
        return root
    
    def detach(self):
        """
        Detach from parent.
        @return: This element removed from its parent's
            child list and I{parent}=I{None}
        @rtype: L{Element}
        """
        if self.parent is not None:
            if self in self.parent.children:
                self.parent.children.remove(self)
            self.parent = None
        return self
        
    def set(self, name, value, ns=None):
        """
        Set an attribute's value.
        @param name: The name of the attribute.
        @type name: basestring
        @param value: The attribute value.
        @type value: basestring
        @param ns: The optional attribute's namespace.
        @type ns: (I{prefix}, I{name})
        @see: __setitem__()
        """
        attr = self.attrib(name, ns)
        if attr is None:
            attr = Attribute(name, value)
            self.append(attr)
        else:
            attr.setValue(value)
            
    def get(self, name, ns=None, default=None):
        """
        Get the value of an attribute by name.
        @param name: The name of the attribute.
        @type name: basestring
        @param ns: The optional attribute's namespace.
        @type ns: (I{prefix}, I{name})
        @param default: An optional value to be returned when either
            the attribute does not exist of has not value.
        @type default: basestring
        @return: The attribute's value or I{default}
        @rtype: basestring
        @see: __getitem__()
        """
        attr = self.attrib(name, ns)
        if attr is None or attr.value is None:
            return default
        else:
            return attr.getValue()   

    def setText(self, value):
        """
        Set the element's text content.
        @param value: The element's text value.
        @type value: basestring
        @return: self
        @rtype: I{Element}
        """
        self.text = encode(value)
        return self
        
    def getText(self, default=None):
        """
        Get the element's text content with optional default
        @param default: A value to be returned when no text content exists.
        @type default: basestring
        @return: The text content, or I{default}
        @rtype: basestring
        """
        result = decode(self.text)
        if result is None:
            result = default
        return result
    
    def attrib(self, name, ns=None):
        """
        Get an attribute by name and (optional) namespace
        @param name: The name of a contained attribute (may contain prefix).
        @type name: basestring
        @param ns: An optional namespace
        @type ns: (I{prefix}, I{name})
        @return: The requested attribute object.
        @rtype: L{Attribute}
        """
        result = None
        if len(self.attributes) == 0:
            return result
        if ns is None:
            p, n = splitPrefix(name)
            p = [p]
        else:
            prefixes = self.findPrefixes(ns[1])
            p, n = (prefixes, name)
        for a in self.attributes:
            if a.prefix in p and a.name == n:
                result = a
                break
        return result
        
    def namespace(self):
        """
        Get the element's namespace.
        @return: The element's namespace by resolving the prefix, the explicit 
            namespace or the inherited namespace.
        @rtype: (I{prefix}, I{name})
        """
        if self.prefix is None:
            p = self.parent
            while p is not None:
                if p.expns is not None:
                    return (None, p.expns)
                else:
                    p = p.parent
        else:
            return self.resolvePrefix(self.prefix)
            
    def append(self, objects):
        """
        Append the specified child based on whether it is an
        element or an attrbuite.
        @param objects: A (single|collection) of attribute(s) or element(s)
            to be added as children.
        @return: self
        @rtype: L{Element}
        """
        if not isinstance(objects, (list, tuple)):
            objects = (objects,)
        for child in objects:
            if isinstance(child, Element):
                self.children.append(child)
                child.parent = self
                continue
            if isinstance(child, Attribute):
                self.attributes.append(child)
                child.parent = self
                continue
            raise Exception('append %s not-valid', child.__class__.__name__)
        return self
    
    def removeChild(self, child):
        """
        Remove the specified child element.
        @param child: A child.
        @type child: L{Element}
        @return: The I{child} that has been removed.
        @rtype: L{Element}
        """
        return child.detach()
            
    def replaceChild(self, child, content):
        """
        Replace I{child} with the specified I{content}.
        @param child: A child element.
        @type child: L{Element}
        @param content: An element or collection of elements.
        @type content: L{Element} or [L{Element},]
        """
        if child not in self.children:
            raise Exception('child not-found')
        index = self.children.index(child)
        self.removeChild(child)
        if not isinstance(content, list) and not isinstance(content, tuple):
            content = (content,)
        for node in content:
            self.children.insert(index, node.detach())
            node.parent = self
            index += 1

    def getChild(self, name, ns=None, default=None):
        """
        Get a child by name and (optional) namespace.
        @param name: The name of a child element (may contain prefix).
        @type name: basestring
        @param ns: An optional namespace used to match the child.
        @type ns: (I{prefix}, I{name})
        @param default: Returned when child not-found.
        @type default: L{Element}
        @return: The requested child, or I{default} when not-found.
        @rtype: L{Element}
        """
        prefix, name = splitPrefix(name)
        if prefix is not None:
            ns = self.resolvePrefix(prefix)
        for c in self.children:
            if c.name == name and \
                ( ns is None or c.namespace()[1] == ns[1] ):
                return c
        return default
    
    def childAtPath(self, path):
        """
        Get a child at I{path} where I{path} is a (/) separated
        list of element names that are expected to be children.
        @param path: A (/) separated list of element names.
        @type path: basestring
        @return: The leaf node at the end of I{path}
        @rtype: L{Element}
        """
        result = None
        node = self
        for name in [p for p in path.split('/') if len(p) > 0]:
            ns = None
            prefix, name = splitPrefix(name)
            if prefix is not None:
                ns = node.resolvePrefix(prefix)
            result = node.getChild(name, ns)
            if result is None:
                break;
            else:
                node = result
        return result

    def childrenAtPath(self, path):
        """
        Get a list of children at I{path} where I{path} is a (/) separated
        list of element names that are expected to be children.
        @param path: A (/) separated list of element names.
        @type path: basestring
        @return: The collection leaf nodes at the end of I{path}
        @rtype: [L{Element},...]
        """
        parts = [p for p in path.split('/') if len(p) > 0]
        if len(parts) == 1:
            result = self.getChildren(path)
        else:
            result = self.__childrenAtPath(parts)
        return result
        
    def getChildren(self, name=None, ns=None):
        """
        Get a list of children by name and (optional) namespace.
        @param name: The name of a child element (may contain prefix).
        @type name: basestring
        @param ns: An optional namespace used to match the child.
        @type ns: (I{prefix}, I{name})
        @return: The list of matching children.
        @rtype: [L{Element},...]
        """
        result = []
        prefix, name = splitPrefix(name)
        if prefix is not None:
            ns = self.resolvePrefix(prefix)
        if name is None and ns is None:
            return self.children
        for c in self.children:
            if c.name == name and \
                ( ns is None or c.namespace()[1] == ns[1] ):
                result.append(c)
        return result
    
    def detachChildren(self):
        """
        Detach and return this element's children.
        @return: The element's children (detached).
        @rtype: [L{Element},...]
        """
        detached = self.children
        self.children = []
        for child in detached:
            child.parent = None
        return detached
    
    def flattenedTree(self, addSelf=True):
        """
        Get I{flattened} list of elements for this branch in the tree.
        @param addSelf: A flag that indicates that the result 
            contains B{this} element.
        @type addSelf: boolean
        @return: A I{flattened} list of all elements.
        @rtype: [L{Element},...]
        """
        result = []
        if addSelf:
            result.append(self)
        for c in self.children:
            result.append(c, False)
        return result
    
    def flattenedPrefixes(self):
        """
        Get a I{flattened} list of all namespace prefixes 
        mappings for this branch in the tree.  This includes mapping in this
        element and those mapped by child elements.  Mapping is: (I{prefix},I{URI})
        @return: A list of B{all} prefix => URI mappings in this branch.
        @rtype: [I{item},...]
        """
        result = []
        for item in self.nsprefixes.items():
            if item in result:
                continue
            result.append((item[0], item[1]))
        for c in self.children:
            cp = c.flattenedPrefixes()
            result += [item for item in cp if item not in result]
        return result
        
    def resolvePrefix(self, prefix, default=defns):
        """
        Resolve the specified prefix to a namespace.  The I{nsprefixes} is
        searched.  If not found, it walks up the tree until either resolved or
        the top of the tree is reached.  Searching up the tree provides for
        inherited mappings.
        @param prefix: A namespace prefix to resolve.
        @type prefix: basestring
        @param default: An optional value to be returned when the prefix
            cannot be resolved.
        @type default: (I{prefix},I{URI})
        @return: The namespace that is mapped to I{prefix} in this context.
        @rtype: (I{prefix},I{URI})
        """
        n = self
        while n is not None:
            if prefix in n.nsprefixes:
                return (prefix, n.nsprefixes[prefix])
            else:
                n = n.parent
        return default
    
    def addPrefix(self, p, u):
        """
        Add or update a prefix mapping.
        @param p: A prefix.
        @type p: basestring
        @param u: A namespace URI.
        @type u: basestring
        @return: self
        @rtype: L{Element}
        """
        self.nsprefixes[p] = u
        return self
 
    def updatePrefix(self, p, u):
        """
        Update (redefine) a prefix mapping for the branch. 
        @param p: A prefix.
        @type p: basestring
        @param u: A namespace URI.
        @type u: basestring
        @return: self
        @rtype: L{Element}
        @note: This method traverses down the entire branch!
        """
        if p in self.nsprefixes:
            self.nsprefixes[p] = u
        for c in self.children:
            c.updatePrefix(p, u)
        return self
            
    def clearPrefix(self, prefix):
        """
        Clear the specified prefix from the prefix mappings.
        @param prefix: A prefix to clear.
        @type prefix: basestring
        @return: self
        @rtype: L{Element}
        """
        if prefix in self.nsprefixes:
            del self.nsprefixes[prefix]
        return self
    
    def findPrefix(self, uri):
        """
        Find the first prefix that has been mapped to a namespace URI.
        The local mapping is searched, then it walks up the tree until
        it reaches the top or finds a match.
        @param uri: A namespace URI.
        @type uri: basestring
        @return: A mapped prefix.
        @rtype: basestring
        """
        for item in self.nsprefixes.items():
            if item[1] == uri:
                prefix = item[0]
                return prefix
        if self.parent is not None:
            return self.parent.findPrefix(uri)
        else:
            return None

    def findPrefixes(self, uri, match='eq'):
        """
        Find all prefixes that has been mapped to a namespace URI.
        The local mapping is searched, then it walks up the tree until
        it reaches the top collecting all matches.
        @param uri: A namespace URI.
        @type uri: basestring
        @param match: A matching function L{Element.matcher}.
        @type match: basestring
        @return: A list of mapped prefixes.
        @rtype: [basestring,...]
        """
        result = []
        for item in self.nsprefixes.items():
            if self.matcher[match](item[1], uri):
                prefix = item[0]
                result.append(prefix)
        if self.parent is not None:
            result += self.parent.findPrefixes(uri, match)
        return result
    
    def promotePrefixes(self):
        """
        Push prefix declarations up the tree as far as possible.  Prefix
        mapping are pushed to its parent unless the parent has the
        prefix mapped to another URI or the parent has the prefix.
        This is propagated up the tree until the top is reached.
        """
        for c in self.children:
            c.promotePrefixes()
        if self.parent is None:
            return
        for p,u in self.nsprefixes.items():
            if p in self.parent.nsprefixes:
                pu = self.parent.nsprefixes[p]
                if pu == u:
                    del self.nsprefixes[p]
                continue
            if p != self.parent.prefix:
                self.parent.nsprefixes[p] = u
                del self.nsprefixes[p]       

    def isempty(self):
        """
        Get whether the element has no children.
        @return: True when element has not children.
        @rtype: boolean
        """
        return len(self.children) == 0 and \
            self.text is None
            
    def isnil(self):
        """
        Get whether the element is I{nil} as defined by having
        an attribute in the I{xsi:nil="true"}
        @return: True if I{nil}, else False
        @rtype: boolean
        """
        nilattr = self.attrib('nil', ns=xsins)
        if nilattr is None:
            return False
        else:
            return ( nilattr.getValue().lower() == 'true' )
        
    def trim(self):
        """
        Trim the formatting characters.
        @return: self
        @rtype: L{Element}
        """
        if self.text is not None:
            self.text = self.text.strip()
        return self
        
    def setnil(self, flag=True):
        """
        Set this node to I{nil} as defined by having an
        attribute I{xsi:nil}=I{flag}.
        @param flag: A flag inidcating how I{xsi:nil} will be set.
        @type flag: boolean
        @return: self
        @rtype: L{Element}
        """
        self.set('%s:nil' % xsins[0], flag)
        self.addPrefix(xsins[0], xsins[1])
        if flag:
            self.text = None
        return self
            
    def applyns(self, ns):
        """
        Apply the namespace to this node.  If the prefix is I{None} then
        this element's explicit namespace I{expns} is set to the
        URI defined by I{ns}.  Otherwise, the I{ns} is simply mapped.
        @param ns: A namespace.
        @type ns: (I{prefix},I{URI})
        """
        if ns is None:
            return
        if not isinstance(ns, (tuple,list)):
            raise Exception('namespace must be tuple')
        if ns[0] is None:
            self.expns = ns[1]
        else:
            self.prefix = ns[0]
            self.nsprefixes[ns[0]] = ns[1]
            
    def str(self, indent=0):
        """
        Get a string representation of this XML fragment.
        @param indent: The indent to be used in formatting the output.
        @type indent: int
        @return: A I{pretty} string.
        @rtype: basestring
        """
        tab = '%*s'%(indent*3,'')
        result = []
        result.append('%s<%s' % (tab, self.qname()))
        result.append(self.nsdeclarations())
        for a in [unicode(a) for a in self.attributes]:
            result.append(' %s' % a)
        if self.isempty():
            result.append('/>')
            return ''.join(result)
        result.append('>')
        if self.text is not None:
            result.append(self.text)
        for c in self.children:
            result.append('\n')
            result.append(c.str(indent+1))
        if len(self.children):
            result.append('\n%s' % tab)
        result.append('</%s>' % self.qname())
        result = ''.join(result)
        return result

    def nsdeclarations(self):
        """
        Get a string representation for all namespace declarations
        as xmlns="" and xmlns:p="".
        @return: A separated list of declarations.
        @rtype: basestring
        """
        result = ''
        if self.expns is not None:
            result += ' xmlns="%s"' % self.expns
        for (p,u) in self.nsprefixes.items():
            if self.parent is not None:
                ns = self.parent.resolvePrefix(p)
                if ns[1] == u: # already declared
                    continue
            result += ' xmlns:%s="%s"' % (p, u)
        return result
            
    def __childrenAtPath(self, parts):
        result = []
        node = self
        last = len(parts)-1
        ancestors = parts[:last]
        leaf = parts[last]
        for name in ancestors:
            ns = None
            prefix, name = splitPrefix(name)
            if prefix is not None:
                ns = node.resolvePrefix(prefix)
            child = node.getChild(name, ns)
            if child is None:
                break
            else:
                node = child
        if child is not None:
            ns = None
            prefix, leaf = splitPrefix(leaf)
            if prefix is not None:
                ns = node.resolvePrefix(prefix)
            result = child.getChildren(leaf)
        return result
                
    def __getitem__(self, index):
        if isinstance(index, basestring):
            return self.get(index)
        else:
            if index < len(self.children):
                return self.children[index]
            else:
                return None
        
    def __setitem__(self, index, value):
        if isinstance(index, basestring):
            self.set(index, value)
        else:
            if index < len(self.children) and \
                isinstance(value, Element):
                self.children.insert(index, value)

    def __eq__(self, rhs):
        return  rhs is not None and \
            isinstance(rhs, Element) and \
            self.name == rhs.name and \
            self.namespace()[1] == rhs.namespace()[1]
        
    def __repr__(self):
        return \
            'element (prefix=%s, name=%s)' % (self.prefix, self.name)
    
    def __str__(self):
        return unicode(self).encode('utf-8')
    
    def __unicode__(self):
        return self.str()
        

class Document(Element):
    """ simple document """

    def __init__(self):
        Element.__init__(self, 'document')
        
    def root(self):
        if len(self.children) > 0:
            return self.children[0]
        else:
            return None
        
    def flattened_nsprefixes(self):
        result = {}
        
        return result
        
    def __str__(self):
        return unicode(self).encode('utf-8')
    
    def __unicode__(self):
        result = '<?xml version="1.0" encoding="UTF-8"?>'
        root = self.root()
        if root is not None:
            result += '\n'
            result += root.str()
        return unicode(result)


class Handler(ContentHandler):
    """ sax hanlder """
    
    def __init__(self):
        self.nodes = [Document()]
 
    def startElement(self, name, attrs):
        top = self.top()
        node = Element(unicode(name), parent=top)
        for a in attrs.getNames():
            n = unicode(a)
            v = unicode(attrs.getValue(a))
            attribute = Attribute(n,v)
            if self.mapPrefix(node, attribute):
                continue
            node.append(attribute)
        top.append(node)
        self.push(node)
        
    def mapPrefix(self, node, attribute):
        skip = False
        if attribute.name == 'xmlns':
            node.expns = attribute.value
            skip = True
        elif attribute.prefix == 'xmlns':
            prefix = attribute.name
            node.nsprefixes[prefix] = attribute.value
            skip = True
        return skip
 
    def endElement(self, name):
        name = unicode(name)
        current = self.top()
        current.trim()
        currentqname = current.qname()
        if name == currentqname:
            self.pop()
        else:
            raise Exception('malformed document')
 
    def characters(self, content):
        text = unicode(content)
        node = self.top()
        if node.text is None:
            node.text = text
        else:
            node.text += text

    def push(self, node):
        self.nodes.append(node)

    def pop(self):
        self.nodes.pop()
 
    def top(self):
        return self.nodes[len(self.nodes)-1]


class Parser:
    """ simple parser """
        
    def parse(self, file=None, url=None, string=None):
        """ parse a document """
        handler = Handler()
        if file is not None:
            parse(file, handler)
            return handler.nodes[0]
        if url is not None:
            parse(urlopen(url), handler)
            return handler.nodes[0]
        if string is not None:
            parseString(string, handler)
            return handler.nodes[0]



encodings = \
(( '&', '&amp;' ),( '<', '&lt;' ),( '>', '&gt;' ),( '"', '&quot;' ),("'", '&apos;' ))

def encode(s):
    if isinstance(s, basestring):
        for x in encodings:
            s = s.replace(x[0], x[1])
    return s

def decode(s):
    if isinstance(s, basestring):
        for x in encodings:
            s = s.replace(x[1], x[0])
    return s
