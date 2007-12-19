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



from property import Property
from urllib import urlopen
import re
import sys

if sys.version_info < (2,5):
    from lxml.etree import ElementTree, XML
else:
    from xml.etree.ElementTree import ElementTree
    from xml.etree.ElementTree import XML

class Hint:
    
    """
    the hint class provides XML schema-like information that allows
    greater precision in generating the data structures.
    sequences are the bull path to the element.  The path can have
    (...) prefix and/or suffix wildcards.
    """
    
    def __init__(self, addtag=False):
        self.atpfx = '_'
        self.addtag = addtag
        self.sequences = []
        self.cache = {}
        
    def sequence(self, path):
        result = self.cache.get(path, None)
        if result is None:
            result = self.match_sequence(path)
            self.cache[path] = result
        return result
        
    def match_sequence(self, path):
        for s in self.sequences:
            if path == s:
                return True
            if s.startswith('...') and s.endswith('...'):
                if path.contains(s[3:-3]):
                    return True
                continue
            if s.startswith('...'):
                if path.endswith(s[3:]):
                    return True
                continue
            if s.endswith('...'):
                if path.startswith(s[:-3]):
                    return True
                continue
        return False
    
    def nonsequence(self, path):
        return not self.sequence(path)


class DocumentReader:
    
    """
    the property reader reads an XML file and generates a property object.   
    """

    def __init__(self, hint=Hint(), stripns=True):
        """
        hint -- a hit object used to interpret the document.
        stripns -- indicates whether to strip the namespace from tag names.     
        """
        self.handlers = {}
        self.hint = hint
        self._stripns = stripns
        self.basichandler = BasicHandler(self)
        
    def set_hint(self, hint):
        """ set the parsing hint """
        self.hint = hint

    def read(self, file=None, url=None, string=None):
        """open and process the specified file|url|string"""
        if file is not None:
            root = ElementTree(file=file).getroot()
        elif url is not None:
            root = ElementTree(file=urlopen(url)).getroot()
        elif string is not None:
            root = XML(string)
        else:
            raise Exception('(file|url|string) must be specified')
        return self.process(root)
    
    def process(self, e):
        """
        process the specified element and convert the XML document into
        a data structure (python dictionary).  the element is examined for attributes and children.
        Attributes are added to the dictionary then the children are processed using recursion.  
        the child dictionary is added to the result using the child's tag as the key.
        """
        handler = self.handlers.get(e.tag, self.basichandler)
        return handler.process(e)
    
    def set_handler(self, tag, handler):
        """set a custom tag handler for the specified tag"""
        if isinstance(handler, TagHandler):
            self.handlers[tag] = handler
        else:
            raise TypeError, 'handler must be TagHandler'
        
    def stripns(self, s):
        """strip the {} namespace used by etree and return (ns, s)"""
        ns = None
        if self._stripns:
            p = re.compile('({[^{]+})(.+)')
            m = p.match(s)
            if m:
                 ns = m.group(1)
                 s = m.group(2)
        if ns is not None:
            ns = ns[1:-1]
        return (ns, s)


class TagHandler:
    """abstract tag handler"""
    reserved = {'class':'cls', 'def':'dfn', }
    booleans = {'true':True, 'false':False}
    
    def __init__(self, p):
        """initialize with the specified processor"""
        self.p = p
        
    def process(self, e):
        """process the specified element and convert into a dictionary"""
        raise NotImplementedError

    def clean(self, key):
        """decode python reserved words"""
        return self.reserved.get(key, key)


class BasicHandler(TagHandler):
    
    """basic tag handler"""
    
    def __init__(self, p):
        TagHandler.__init__(self, p)
        self.path = []
            
    def process(self, e):
        """
        process the specified element and convert the XML document into
        a python dictionary.  the element is examined for attributes and children.
        attributes are added to the dictionary then the children are processed using recursion.  
        the child dictionary is added to the result using the child's tag as the key.
        """
        data = Property()
        if self.p.hint.addtag:
            data.__type__ = e.tag
        self.path.append(self.p.stripns(e.tag)[1])
        self.import_attrs(data, e)
        self.import_children(data, e)
        self.import_text(data, e)
        self.path.pop()
        return self.result(data, e)
    
    def import_attrs(self, data, e):
        """import attribute nodes into the data structure"""
        for attr in e.keys():
            ns, key = self.p.stripns(attr)
            key = '%s%s' % (self.p.hint.atpfx, self.clean(key))
            if ns is not None:
                data.get_metadata(key).namespace = ns
            value = e.get(attr).strip()
            value = self.booleans.get(value.lower(), value)
            data[key] = value

    def import_children(self, data, e):
        """import child nodes into the data structure"""
        for child in e.getchildren():
            cdata = self.p.process(child)
            ns, key = self.p.stripns(child.tag)
            key = self.clean(key)
            if ns is not None:
                data.get_metadata(key).namespace = ns
            if key in data:
                v = data[key]
                if isinstance(v, list):
                    data[key].append(cdata)
                else:
                    data[key] = [v, cdata]
                continue
            if self.p.hint.sequence(self.pathstring(key)):
                if cdata is None:
                    data[key] = []
                else:
                    data[key] = [cdata,]
            else:
                data[key] = cdata
    
    def import_text(self, data, e):
        """import text nodes into the data structure"""
        if e.text is None: return
        if len(e.text):
            value = e.text.strip()
            value = self.booleans.get(value.lower(), value)
            key = self.clean('text')
            data[key] = value
            
    def result(self, data, e):
        """
        perform final processing of the resulting data structure as follows:
        simple elements (not attrs or children) with text nodes will have a string 
        result equal to the value of the text node.
        """
        try:
            if len(data) == 0:
                return None
            if len(data) == 1 and self.p.hint.nonsequence(e.tag):
                return data['text']
        except:
            pass
        return data
    
    def pathstring(self, leaf=None):
        """construct a string representation of the current processing path"""
        s = ''
        for p in self.path:
            s += '/%s' % p
        if leaf is not None:
           s += '/%s' % leaf
        return s


