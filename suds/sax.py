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

from urllib import urlopen
from xml.sax import parse, parseString, ContentHandler

def splitPrefix(name):
    """ split the name into a tuple (prefix, name) """
    if name is not None and ':' in name:
        return tuple(name.split(':', 1))
    else:
        return (None, name)

class Attribute:
    """ simple attribute """
    def __init__(self, name, value=None):
        self.parent = None
        self.prefix, self.name = splitPrefix(name)
        self.value = encode(value)
        
    def resolvePrefix(self, prefix):
        """ resolve the specified prefix to a known namespace """
        ns = (None,None)
        if self.parent is not None:
            ns = self.parent.resolvePrefix(prefix)
        return ns
    
    def qname(self):
        """ get the fully qualified name """
        if self.prefix is None:
            return self.name
        else:
            return ':'.join((self.prefix, self.name))
        
    def setValue(self, value):
        """ set the attributes value """
        self.value = encode(value)
        
    def getValue(self, default=None):
        """ get the attributes value with optional default """
        result = decode(self.value)
        if result is None:
            result = default
        return result
        
    def namespace(self):
        """ get the attributes namespace """
        if self.prefix is None:
            return (None,None)
        else:
            return self.resolvePrefix(self.prefix)
    
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
        return '%s="%s"' % (self.qname(), self.value)


class Element:
    """ simple xml element """
    def __init__(self, name, parent=None, ns=None):
        self.prefix, self.name = splitPrefix(name)
        self.expns = None
        self.nsprefixes = {}
        self.attributes = []
        self.text = None
        self.parent = parent
        self.children = []
        self.applyns(ns)
            
    def append(self, objects):
        """
        append the specified child based on whether it is an
        element or an attrbuite.
        """
        if not isinstance(objects, list) and not isinstance(objects, list):
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
            
    def detach(self):
        """ detach from parent """
        if self.parent is not None:
            if self in self.parent.children:
                self.parent.children.remove(self)
            self.parent = None
        return self

    def setText(self, value):
        """ set the element's text """
        self.text = encode(value)
        return self
        
    def getText(self, default=None):
        """ get the element's text with optional default """
        result = decode(self.text)
        if result is None:
            result = default
        return result
    
    def removeChild(self, child):
        """ remove the specified child """
        return child.detach()
            
    def replaceChild(self, child, content):
        """ replace the specified content (content may be a list|tuple) """
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
        """ get a child by name and (optional) namespace """
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
        get a child at the specifed path where path is a (/) separated
        list of element names.
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
        get a list of children at the specified path where path is a (/)
        separated list of element names.
        """
        result = []
        child = None
        parts = [p for p in path.split('/') if len(p) > 0]
        if len(parts) == 1:
            child = self.getChild(path)
            if child is not None:
                result.append(child)
        else:
            result = self.__childrenAtPath(parts)
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
        
    def getChildren(self, name=None, ns=None):
        """ get list of child elements by name and (optional) namespace """
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
        """ detach and return the list of children """
        detached = self.children
        self.children = []
        for child in detached:
            child.parent = None
        return detached
    
    def attrib(self, name):
        """ get an attribute by name """
        result = None
        for a in self.attributes:
            if a.name == name:
                result = a
                break
        return result
    
    def attribute(self, name, value=None, default=None):
        """ get/set an attribute by name """
        attr = self.attrib(name)
        if value is None:
            if attr is not None:
                if attr.value is None:
                    return default
                else:
                    return attr.getValue()
        else:
            if attr is None:
                attr = Attribute(name, value)
                self.append(attr)
            else:
                attr.setValue(value)
                
    def flattenedAttributes(self):
        """ get flattened list of attributes for branch in the tree """
        result = []
        for a in self.attributes:
            result.append(a)
        for c in self.children:
            result += c.flattenedAttributes()
        return result

    def flattenedTree(self, addSelf=True):
        """ get flattened list of attributes for branch in the tree """
        result = []
        if addSelf:
            result.append(self)
        for c in self.children:
            result.append(c, False)
        return result
        
    def qname(self):
        """ get the fully qualified name """
        if self.prefix is None:
            return self.name
        else:
            return '%s:%s' % (self.prefix, self.name)
        
    def namespace(self):
        """ get the namespace """
        if self.prefix is None:
            p = self.parent
            while p is not None:
                if p.expns is not None:
                    return (None, p.expns)
                else:
                    p = p.parent
        else:
            return self.resolvePrefix(self.prefix)
        
    def resolvePrefix(self, prefix):
        """ resolve the specified prefix into a namespace """
        n = self
        while n is not None:
            if prefix in n.nsprefixes:
                return (prefix, n.nsprefixes[prefix])
            else:
                n = n.parent
        return (None,None)
    
    def addPrefix(self, p, u):
        """ add/update a prefix mapping """
        self.nsprefixes[p] = u
 
    def updatePrefix(self, p, u):
        """ update a prefix mapping (recursive) """
        if p in self.nsprefixes:
            self.nsprefixes[p] = u
        for c in self.children:
            c.updatePrefix(p, u)
            
    def clearPrefix(self, prefix):
        """ clear the specified prefix from the mapping """
        if prefix in self.nsprefixes:
            del self.nsprefixes[prefix]     
    
    def findPrefix(self, uri):
        """ find a mapped prefix for the specified namespace URI """
        for item in self.nsprefixes.items():
            if item[1] == uri:
                prefix = item[0]
                return prefix
        if self.parent is not None:
            return self.parent.findPrefix(uri)
        else:
            return None
            
    def isempty(self):
        """ get whether the element has no children """
        return len(self.children) == 0 and \
            self.text is None
            
    def applyns(self, ns):
        """ apply the namespace to this node """
        if ns is not None:
            if ns[0] is None:
                self.expns = ns[1]
            else:
                self.nsprefixes[ns[0]] = ns[1]
                
    def __getitem__(self, index):
        if index < len(self.children):
            return self.children[index]
        else:
            return None
        
    def __setitem__(self, index, child):
        if index < len(self.children) and \
            isinstance(child, Element):
            self.children.insert(index, child)

    def __eq__(self, rhs):
        return  rhs is not None and \
            isinstance(rhs, Element) and \
            self.name == rhs.name and \
            self.namespace()[1] == rhs.namespace()[1]
        
    def __repr__(self):
        return \
            'element (prefix=%s, name=%s)' % (self.prefix, self.name)
    
    def nsdeclarations(self):
        """ get namespace declarations """
        result = ''
        if self.expns is not None:
            result += ' xmlns="%s"' % self.expns
        for (p,u) in self.nsprefixes.items():
            result += ' xmlns:%s="%s"' % (p, u)
        return result
    
    def __str__(self):
        return self.str()
        
    def str(self, indent=0):
        result = ''
        for i in range(0, indent):
            result += '  '
        result += '<%s' % self.qname()
        result += self.nsdeclarations()
        for a in [str(a) for a in self.attributes]:
            result += ' %s' % a
        if self.isempty():
            result += '/>'
            return result
        result += '>'
        if self.text is not None:
            result += self.text
        for c in self.children:
            result += '\n'
            result += c.str(indent+1)
        if len(self.children) > 0:
            result += '\n'
            for i in range(0, indent):
                result += '  '
        result += '</%s>' % self.qname()
        return result


class Document(Element):
    """ simple document """

    def __init__(self):
        Element.__init__(self, 'document')
        
    def root(self):
        if len(self.children) > 0:
            return self.children[0]
        else:
            return None
        
    def __str__(self):
        result = '<?xml version="1.0" encoding="UTF-8"?>'
        root = self.root()
        if root is not None:
            result += '\n'
            result += root.str()
        return result


class Handler(ContentHandler):
    """ sax hanlder """
    
    def __init__(self):
        self.nodes = [Document()]
 
    def startElement(self, name, attrs):
        top = self.top()
        node = Element(str(name), parent=top)
        for a in attrs.getNames():
            n = str(a)
            v = str(attrs.getValue(a))
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
        name = str(name)
        topqname = self.top().qname()
        if name == topqname:
            self.pop()
        else:
            raise Exception('malformed document')
 
    def characters(self, content):
        text = str(content).strip()
        if len(content) > 0:
            self.top().text = text;

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
    if s is None: return s
    for x in encodings:
        s = s.replace(x[0], x[1])
    return s

def decode(s):
    if s is None: return s
    for x in encodings:
        s = s.replace(x[1], x[0])
    return s
