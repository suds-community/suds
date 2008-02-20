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



from suds.property import Property
from suds.sax import Parser

class Hint:
    """
    the hint class provides XML schema-like information that allows
    greater precision in generating the data structures.
    sequences are the bull path to the element.  The path can have
    (...) prefix and/or suffix wildcards.
    """
    
    def __init__(self):
        self.atpfx = '_'
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

    def __init__(self, hint=Hint()):
        """
        hint -- a hit object used to interpret the document.   
        """
        self.handlers = {}
        self.hint = hint
        self.basichandler = BasicHandler(self)
        self.parser = Parser()
        
    def set_hint(self, hint):
        """ set the parsing hint """
        self.hint = hint

    def read(self, file=None, url=None, string=None):
        """open and process the specified file|url|string"""
        if file is not None:
            root = self.parser.parse(file=file).root()
        elif url is not None:
            root = self.parser.parse(url=url).root()
        elif string is not None:
            root = self.parser.parse(string=string).root()
        else:
            raise Exception('(file|url|string) must be specified')
        return self.process(root)
    
    def process(self, node):
        """
        process the specified node and convert the XML document into
        a data structure (python dictionary).  the element is examined for attributes and children.
        Attributes are added to the dictionary then the children are processed using recursion.  
        the child dictionary is added to the result using the child's tag as the key.
        """
        handler = self.handlers.get(node.name, self.basichandler)
        return handler.process(node)
    
    def set_handler(self, tag, handler):
        """set a custom tag handler for the specified tag"""
        if isinstance(handler, TagHandler):
            self.handlers[tag] = handler
        else:
            raise TypeError, 'handler must be TagHandler'


class TagHandler:
    """abstract tag handler"""
    reserved = {'class':'cls', 'def':'dfn', }
    booleans = {'true':True, 'false':False}
    
    def __init__(self, p):
        """initialize with the specified processor"""
        self.p = p
        
    def process(self, node):
        """process the specified node and convert into a dictionary"""
        raise NotImplementedError

    def clean(self, key):
        """decode python reserved words"""
        return self.reserved.get(key, key)


class BasicHandler(TagHandler):
    
    """basic tag handler"""
    
    def __init__(self, p):
        TagHandler.__init__(self, p)
        self.path = []
            
    def process(self, node):
        """
        process the specified node and convert the XML document into
        a python dictionary.  the element is examined for attributes and children.
        attributes are added to the dictionary then the children are processed using recursion.  
        the child dictionary is added to the result using the child's tag as the key.
        """
        data = Property()
        md = data.get_metadata()
        md.prefix = node.prefix
        md.expns = node.expns
        md.nsprefixes = node.nsprefixes.items()
        self.path.append(node.name)
        self.import_attrs(data, node)
        self.import_children(data, node)
        self.import_text(data, node)
        self.path.pop()
        return self.result(data, node)
    
    def import_attrs(self, data, node):
        """import attribute nodes into the data structure"""
        for attr in node.attributes:
            key = attr.name
            key = '%s%s' % (self.p.hint.atpfx, self.clean(key))
            md = data.get_metadata(key)
            md.prefix = attr.prefix
            value = attr.getValue()
            value = self.booleans.get(value.lower(), value)
            data[key] = value

    def import_children(self, data, node):
        """import child nodes into the data structure"""
        for child in node.children:
            cdata = self.p.process(child)
            key = child.name
            key = self.clean(key)
            md = data.get_metadata(key)
            md.prefix = child.prefix
            md.expns = child.expns
            md.nsprefixes = child.nsprefixes.items()
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
    
    def import_text(self, data, node):
        """import text nodes into the data structure"""
        if node.text is None: return
        if len(node.text):
            value = node.getText()
            value = self.booleans.get(value.lower(), value)
            data['text'] = value
            
    def result(self, data, node):
        """
        perform final processing of the resulting data structure as follows:
        simple elements (not attrs or children) with text nodes will have a string 
        result equal to the value of the text node.
        """
        try:
            if len(data) == 0:
                return None
            if len(data) == 1 and self.p.hint.nonsequence(node.name):
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


