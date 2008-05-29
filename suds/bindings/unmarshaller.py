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
from suds.sax import xsins
from suds.resolver import NodeResolver

log = logger(__name__)


reserved = \
    { 'class':'cls', 'def':'dfn', }
    
booleans = \
    { 'true':True, 'false':False }
    

class Unmarshaller:
    """
    An unmarshaller object.
    @ivar basic: A basic I{plain} (untyped) marshaller.
    @type basic: L{Basic}
    @ivar typed: A I{typed} marshaller.
    @type typed: L{Typed}
    """
    
    def __init__(self, schema):
        """
        @param schema: A schema object
        @type schema: L{schema.Schema}
        """
        self.basic = Basic(schema)
        self.typed = Typed(schema)

    
class Basic:
    """
    A object builder (unmarshaller).
    @ivar schema: A schema object
    @type schema: L{schema.Schema}
    """
    def __init__(self, schema):
        """
        @param schema: A schema object
        @type schema: L{schema.Schema}
        """
        self.schema = schema
        
    def process(self, node, type=None):
        """
        Process an object graph representation of the xml L{node}.
        @param node: An XML tree.
        @type node: L{sax.Element}
        @param type: The I{optional} schema type.
        @type type: L{schema.SchemaProperty}
        @return: A suds object.
        @rtype: L{Object}
        """
        self.reset()
        data, result = self.__process(node, type)
        return result
    
    def __process(self, node, type=None):
        """
        Process the specified node and convert the XML document into
        a L{suds} object.
        @param node: An XML fragment.
        @type node: L{sax.Element}
        @param type: The I{optional} schema type.
        @type type: L{schema.SchemaProperty}
        @return: A suds object.
        @rtype: L{Object}
        @note: This is not the proper entry point.
        @see: L{process()}
        """
        data = self.start(node, type)
        self.import_attrs(data, node)
        self.import_children(data, node)
        self.import_text(data, node)
        self.end(node, data)
        return data, self.result(data, node)
    
    def import_attrs(self, data, node):
        """
        Import attribute nodes into L{data}.
        @param data: The current object being built.
        @type data: L{Object}
        @param node: The current node being proecessed.
        @type node: L{sax.Element}
        """
        for attr in node.attributes:
            if attr.namespace()[1] == xsins[1]:
                continue
            key = attr.name
            key = '_%s' % reserved.get(key, key)
            value = attr.getValue()
            value = booleans.get(value.lower(), value)
            setattr(data, key, value)
            
    def import_children(self, data, node):
        """
        Import child nodes into L{data}
        @param data: The current object being built.
        @type data: L{Object}
        @param node: The current node being proecessed.
        @type node: L{sax.Element}
        """
        for child in node.children:
            cdata, cval = self.__process(child)
            key = reserved.get(child.name, child.name)
            if key in data:
                v = getattr(data, key)
                if isinstance(v, list):
                    v.append(cval)
                else:
                    setattr(data, key, [v, cval])
                continue
            if self.unbounded(cdata):
                if cval is None:
                    setattr(data, key, [])
                else:
                    setattr(data, key, [cval,])
            else:
                setattr(data, key, cval)
    
    def import_text(self, data, node):
        """
        Import text nodes into L{data}
        @param data: The current object being built.
        @type data: L{Object}
        @param node: The current node being proecessed.
        @type node: L{sax.Element}
        """
        if node.text is None: return
        if len(node.text):
            value = node.getText()
            value = booleans.get(value.lower(), value)
            md = data.__metadata__
            md.__xml__ = Object.__factory__.metadata()
            md.__xml__.text = value
            
    def result(self, data, node):
        """
        Perform final processing of the resulting data structure as follows:
        simple elements (not attrs or children) with text nodes will have a string 
        result equal to the value of the text node.
        @param data: The current object being built.
        @type data: L{Object}
        @param node: The current node being proecessed.
        @type node: L{sax.Element}
        @return: The post-processed result.
        @rtype: (L{Object}|I{list}|I{str}) 
        """
        if len(data): return data
        text = None
        try:
            md = data.__metadata__
            text = md.__xml__.text
        except AttributeError:
            pass
        if text is None:
            if self.nillable(data) and node.isnil():
                return None
            else:
                return ''
        return text
        
    def reset(self):
        pass

    def start(self, node, type=None):
        """
        Processing on I{node} has started.  Build and return
        the proper object.
        @param node: The current node being proecessed.
        @type node: L{sax.Element}
        @param type: The I{optional} schema type.
        @type type: L{schema.SchemaProperty}
        @return: A subclass of Object.
        @rtype: L{Object}
        """
        return Object()
    
    def end(self, node, data):
        """
        Processing on I{node} has ended.
        @param node: The current node being proecessed.
        @type node: L{sax.Element}
        @param data: The current object being built.
        @type data: L{Object}
        """
        pass
    
    def bounded(self, data):
        """
        Get whether the object is bounded (not a list).
        @param data: The current object being built.
        @type data: L{Object}
        @return: True if bounded, else False
        @rtype: boolean
        '"""
        return ( not self.unbounded(data) )
    
    def unbounded(self, data):
        """
        Get whether the object is unbounded (a list).
        @param data: The current object being built.
        @type data: L{Object}
        @return: True if unbounded, else False
        @rtype: boolean
        '"""
        return False
    
    def nillable(self, data):
        """
        Get whether the object is nillable.
        @param data: The current object being built.
        @type data: L{Object}
        @return: True if nillable, else False
        @rtype: boolean
        '"""
        return False


class Typed(Basic):
    """
    A I{typed} XML unmarshaller
    @ivar resolver: A schema type resolver.
    @type resolver: L{NodeResolver}
    """
    
    def __init__(self, binding):
        """
        @param binding: A binding object.
        @type binding: L{binding.Binding}
        """
        Basic.__init__(self, binding)
        self.resolver = NodeResolver(self.schema)

    def reset(self):
        """
        Reset the resolver.
        """
        log.debug('reset')
        self.resolver.reset()
    
    def start(self, node, type=None):
        """ 
        Resolve to the schema type; build an object and setup metadata.
        @param node: The current node being proecessed.
        @type node: L{sax.Element}
        @param type: The I{optional} schema type.
        @type type: L{schema.SchemaProperty}
        @return: A subclass of Object.
        @rtype: L{Object}
        """
        if type is None:
            if node.name == 'pathmatches':
                pass
            found = self.resolver.find(node)
            if found is None:
                raise TypeNotFound(node.qname())
            type = found
        else:
            self.resolver.push(type.resolve())
        data = Object.__factory__.instance(type.get_name())
        md = data.__metadata__
        md.__type__ = type
        return data
        
    def end(self, node, data):
        """
        Backup (pop) the resolver.
        @param node: The current node being proecessed.
        @type node: L{sax.Element}
        @param data: The current object being built.
        @type data: L{Object}
        """
        self.resolver.pop()
        
    def unbounded(self, data):
        """
        Get whether the object is unbounded (a list) by looking at
        the type embedded in the data's metadata.
        @param data: The current object being built.
        @type data: L{Object}
        @return: True if unbounded, else False
        @rtype: boolean
        '"""
        try:
            if isinstance(data, Object):
                md = data.__metadata__
                type = md.__type__
                return type.unbounded()
        except:
            log.error('metadata error:\n%s', tostr(data), exc_info=True)
        return False
    
    def nillable(self, data):
        """
        Get whether the object is nillable.
        @param data: The current object being built.
        @type data: L{Object}
        @return: True if nillable, else False
        @rtype: boolean
        '"""
        try:
            if isinstance(data, Object):
                md = data.__metadata__
                type = md.__type__
                return type.nillable
        except:
            log.error('metadata error:\n%s', tostr(data), exc_info=True)
        return False