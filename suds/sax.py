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

class Attribute:
    """ simple attribute """
    def __init__(self, name, value=None):
        self.node = None
        self.prefix, self.name = self.splitPrefix(name)
        self.value = value
        
    def resolvePrefix(self, prefix):
        ns = (None,None)
        if node is not None:
            ns = self.node.resolvePrefix(prefix)
        return ns
    
    def qname(self):
        if self.prefix is None:
            return self.name
        else:
            return '%s:%s' % (self.prefix, self.name)
        
    def namespace(self):
        if self.prefix is None:
            return (None,None)
        else:
            return self.resolvePrefix(self.prefix)
        
    def splitPrefix(self, name):
        if ':' in name:
            return tuple(name.split(':'))
        else:
            return (None, name)
    
    def __eq__(self, rhs):
        return rhs is not None and \
            isinstance(rhs, Attribute) and \
            self.prefix == rhs.name and \
            self.name == rhs.name
            
    def __repr__(self):
        return \
            'attr (prefix=%s, name=%s, value=(%s))' %\
                (self.prefix, self.name, self.value)

    def __str__(self):
        return '%s="%s"' % (self.qname(), self.value)


class Node:
    """ simple xml node """
    def __init__(self, name, parent=None, ns=None):
        self.prefix, self.name = self.splitPrefix(name)
        self.expns = None
        self.nsprefixes = {}
        self.attributes = []
        self.text = None
        self.parent = parent
        self.children = []
        self.applyns(ns)
            
    def append(self, child):
        if isinstance(child, Node):
            self.children.append(child)
            child.parent = self
            return
        if isinstance(child, Attribute):
            self.attributes.append(child)
            child.node = self
            return

    def getChild(self, name, ns=None):
        for c in self.children:
            if c.name == name and \
                ( ns is None or c.namespace()[1] == ns[1] ):
                return c
        return None
    
    def find(self, path):
        result = None
        node = self
        for p in [p for p in path.split('/') if len(p) > 0]:
            result = node.getChild(p)
            if result is None:
                break;
            else:
                node = result
        return result

    def findAll(self, path):
        result = []
        child = None
        parts = [p for p in path.split('/') if len(p) > 0]
        if len(parts) == 1:
            child = self.getChild(path)
            if child is not None:
                result.append(child)
        else:
            node = self
            last = len(parts)-1
            ancestors = parts[:last]
            leaf = parts[last]
            for n in ancestors:
                child = node.getChild(n)
                if child is None:
                    break
                else:
                    node = child
            if child is not None:
                result = child.getChildren(leaf)
        return result
        
    def getChildren(self, name=None, ns=None):
        result = []
        if name is None and ns is None:
            return self.children
        for c in self.children:
            if c.name == name and \
                ( ns is None or c.namespace()[1] == ns[1] ):
                result.append(c)
        return result
    
    def attribute(self, name, value=None):
        attr = None
        for a in self.attributes:
            if a.name == name:
                attr = a
                break
        if value is None:
            if attr is not None:
                return attr.value
        else:
            if attr is None:
                attr = Attribute(name, value)
                self.append(attr)
            else:
                attr.value = value
        
    def qname(self):
        if self.prefix is None:
            return self.name
        else:
            return '%s:%s' % (self.prefix, self.name)
        
    def namespace(self):
        if self.prefix is None:
            p = self.parent
            while p is not None:
                if p.expns is not None:
                    return (None, p.expns)
                else:
                    p = p.parent
        else:
            return self.resolvePrefix(self.prefix)
        
    def splitPrefix(self, name):
        if ':' in name:
            return tuple(name.split(':'))
        else:
            return (None, name)
        
    def resolvePrefix(self, prefix):
        n = self
        while n is not None:
            if prefix in n.nsprefixes:
                return (prefix, n.nsprefixes[prefix])
            else:
                n = n.parent
        return (None,None)
            
    def isempty(self):
        return len(self.children) == 0 and \
            self.text is None
            
    def applyns(self, ns):
        if ns is not None:
            if ns[0] is None:
                self.expns = ns[1]
            else:
                self.nsprefixes[ns[0]] = ns[1]

    def __eq__(self, rhs):
        return  rhs is not None and \
            isinstance(rhs, Node) and \
            self.name == rhs.name and \
            self.namespace() == rhs.namespace()
        
    def __repr__(self):
        return \
            'node (prefix=%s, name=%s)' % (self.prefix, self.name)
    
    def nsdeclarations(self):
        result = ''
        if self.expns is not None:
            result += ' xmlns="%s"' % self.expns
        for (p,u) in self.nsprefixes.items():
            result += ' xmlns:%s="%s"' % (p, u)
        return result
    
    def qname(self):
        if self.prefix is None:
            return self.name
        else:
            return '%s:%s' % (self.prefix, self.name)
    
    def __str__(self):
        return self.str()
        
    def str(self, indent=0):
        result = ''
        for i in range(0, indent):
            result += '    '
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
                result += '    '
        result += '</%s>' % self.qname()
        return result


class Document(Node):
    """ simple document node """

    def __init__(self):
        Node.__init__(self, 'document')
        
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
        node = Node(str(name), parent=top)
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
