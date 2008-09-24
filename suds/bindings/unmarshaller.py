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
Provides classes for XML->object I{unmarshalling}.
"""

from logging import getLogger
from suds import *
from suds.sudsobject import Factory, Object, merge
from suds.sax import Namespace
from suds.resolver import NodeResolver

log = getLogger(__name__)


reserved = { 'class':'cls', 'def':'dfn', }


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
        @type schema: L{xsd.schema.Schema}
        """
        self.basic = Basic()
        self.typed = Typed(schema)

       
class Content(Object):
    """
    @ivar node: The content source node.
    @type node: L{sax.element.Element}
    @ivar data: The (optional) content data.
    @type data: L{Object}
    @ivar type: The (optional) content schema type.
    @type type: L{xsd.sxbase.SchemaObject}
    @ivar text: The (optional) content (xml) text.
    @type text: basestring
    """

    def __init__(self, node):
        Object.__init__(self)
        self.node = node
        self.data = None
        self.type = None
        self.text = None

    
class UMBase:
    """
    The abstract XML I{node} unmarshaller.  This class provides the
    I{core} unmarshalling functionality.
    """
        
    def process(self, content):
        """
        Process an object graph representation of the xml I{node}.
        @param content: The current content being unmarshalled.
        @type content: L{Content}
        @return: A suds object.
        @rtype: L{Object}
        """
        self.reset()
        data, result = self.append(content)
        return result
    
    def append(self, content):
        """
        Process the specified node and convert the XML document into
        a I{suds} L{object}.
        @param content: The current content being unmarshalled.
        @type content: L{Content}
        @return: A I{append-result} tuple as: (L{Object}, I{value})
        @rtype: I{append-result}
        @note: This is not the proper entry point.
        @see: L{process()}
        """
        self.start(content)
        self.append_attributes(content)
        self.append_children(content)
        self.append_text(content)
        self.end(content)
        return content.data, self.postprocess(content)
            
    def postprocess(self, content):
        """
        Perform final processing of the resulting data structure as follows:
          - Mixed values (children and text) will have a result of the I{content.node}.
          - Simi-simple values (attributes, no-children and text) will have a result of a
             property object.
          - Simple values (no-attributes, no-children with text nodes) will have a string 
             result equal to the value of the content.node.getText().
        @param content: The current content being unmarshalled.
        @type content: L{Content}
        @return: The post-processed result.
        @rtype: I{any}
        """
        node = content.node
        if len(node.children) and node.hasText():
            return node
        attributes = AttrList(node.attributes)
        if attributes.rlen() and \
            not len(node.children) and \
            node.hasText():
                p = Factory.property(node.name, node.getText())
                return merge(content.data, p)
        if len(content.data):
            return content.data
        lang = attributes.lang()
        if not len(node.children) and content.text is None:
            if self.nillable(content.data) and content.node.isnil():
                return None
            else:
                return xlstr.string('', lang)
        return xlstr.string(content.text, lang)
    
    def append_attributes(self, content):
        """
        Append attribute nodes into L{Content.data}.
        Attributes in the I{schema} or I{xml} namespaces are skipped.
        @param content: The current content being unmarshalled.
        @type content: L{Content}
        """
        attributes = AttrList(content.node.attributes)
        for attr in attributes.real():
            name = attr.name
            value = attr.value
            self.append_attribute(name, value, content)
            
    def append_attribute(self, name, value, content):
        """
        Append an attribute name/value into L{Content.data}.
        @param name: The attribute name
        @type name: basestring
        @param value: The attribute's value
        @type value: basestring
        @param content: The current content being unmarshalled.
        @type content: L{Content}
        """
        key = name
        key = '_%s' % reserved.get(key, key)
        setattr(content.data, key, value)
            
    def append_children(self, content):
        """
        Append child nodes into L{Content.data}
        @param content: The current content being unmarshalled.
        @type content: L{Content}
        """
        for child in content.node.children:
            cont = Content(child)
            cdata, cval = self.append(cont)
            key = reserved.get(child.name, child.name)
            if key in content.data:
                v = getattr(content.data, key)
                if isinstance(v, list):
                    v.append(cval)
                else:
                    setattr(content.data, key, [v, cval])
                continue
            if self.unbounded(cdata):
                if cval is None:
                    setattr(content.data, key, [])
                else:
                    setattr(content.data, key, [cval,])
            else:
                setattr(content.data, key, cval)
    
    def append_text(self, content):
        """
        Append text nodes into L{Content.data}
        @param content: The current content being unmarshalled.
        @type content: L{Content}
        """
        if content.node.hasText():
            content.text = content.node.getText()
        
    def reset(self):
        pass

    def start(self, content):
        """
        Processing on I{node} has started.  Build and return
        the proper object.
        @param content: The current content being unmarshalled.
        @type content: L{Content}
        @return: A subclass of Object.
        @rtype: L{Object}
        """
        content.data = Factory.object(content.node.name)
    
    def end(self, content):
        """
        Processing on I{node} has ended.
        @param content: The current content being unmarshalled.
        @type content: L{Content}
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
    
    
class Basic(UMBase):
    """
    A object builder (unmarshaller).
    """
        
    def process(self, node):
        """
        Process an object graph representation of the xml I{node}.
        @param node: An XML tree.
        @type node: L{sax.element.Element}
        @return: A suds object.
        @rtype: L{Object}
        """
        content = Content(node)
        return UMBase.process(self, content)


class Typed(UMBase):
    """
    A I{typed} XML unmarshaller
    @ivar resolver: A schema type resolver.
    @type resolver: L{NodeResolver}
    """
    
    def __init__(self, schema):
        """
        @param schema: A schema object.
        @type schema: L{xsd.schema.Schema}
        """
        self.resolver = NodeResolver(schema)
        
    def process(self, node, type):
        """
        Process an object graph representation of the xml L{node}.
        @param node: An XML tree.
        @type node: L{sax.element.Element}
        @param type: The I{optional} schema type.
        @type type: L{xsd.sxbase.SchemaObject}
        @return: A suds object.
        @rtype: L{Object}
        """
        content = Content(node)
        content.type = type
        return UMBase.process(self, content)

    def reset(self):
        """
        Reset the resolver.
        """
        log.debug('reset')
        self.resolver.reset()
    
    def start(self, content):
        """ 
        Resolve to the schema type; build an object and setup metadata.
        @param content: The current content being unmarshalled.
        @type content: L{Content}
        @return: A subclass of Object.
        @rtype: L{Object}
        """
        if content.type is None:
            found = self.resolver.find(content.node)
            if found is None:
                raise TypeNotFound(content.node.qname())
            content.type = found
        else:
            self.resolver.push(content.type)
        cls_name = content.type.name
        if cls_name is None:
            cls_name = content.node.name
        content.data = Factory.object(cls_name)
        md = content.data.__metadata__
        md.__type__ = content.type
        
    def end(self, content):
        """
        Backup (pop) the resolver.
        @param content: The current content being unmarshalled.
        @type content: L{Content}
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
            log.error('metadata error:\n%s', data, exc_info=True)
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
            log.error('metadata error:\n%s', data, exc_info=True)
        return False
    
    def append_attribute(self, name, value, content):
        """
        Append an attribute name/value into L{Content.data}.
        @param name: The attribute name
        @type name: basestring
        @param value: The attribute's value
        @type value: basestring
        @param content: The current content being unmarshalled.
        @type content: L{Content}
        """
        type = self.resolver.findattr(name)
        if type is None:
            log.warn('attribute (%s) type, not-found', name)
        else:
            resolved = type.resolve()
            value = type.translate(value)
        UMBase.append_attribute(self, name, value, content)
    
    def append_text(self, content):
        """
        Append text nodes into L{Content.data}
        @param content: The current content being unmarshalled.
        @type content: L{Content}
        """
        UMBase.append_text(self, content)
        resolved = content.type.resolve()
        content.text = resolved.translate(content.text)


class AttrList:
    """
    A filtered attribute list.
    Items are included during iteration if they are in either the (xs) or
    (xml) namespaces.
    @ivar raw: The I{raw} attribute list.
    @type raw: list
    """
    def __init__(self, attributes):
        """
        @param attributes: A list of attributes
        @type attributes: list
        """
        self.raw = attributes
        
    def real(self):
        """
        Get list of I{real} attributes which exclude xs and xml attributes.
        @return: A list of I{real} attributes.
        @rtype: I{generator}
        """
        for a in self.raw:
            if self.skip(a): continue
            yield a
            
    def rlen(self):
        """
        Get the number of I{real} attributes which exclude xs and xml attributes.
        @return:A count of I{real} attributes. 
        @rtype: L{int}
        """
        n = 0
        for a in self.real():
            n += 1
        return n
            
    def lang(self):
        """
        Get list of I{filtered} attributes which exclude xs.
        @return: A list of I{filtered} attributes.
        @rtype: I{generator}
        """
        for a in self.raw:
            if a.qname() == 'xml:lang':
                return a.value
            return None

    def skip(self, attr):
        ns = attr.namespace()
        return ( Namespace.xs(ns) or ns[1] == Namespace.xmlns[1] )


class xlstr(unicode):
    """ language aware string """
    @classmethod
    def string(cls, s, lang=None):
        xls = xlstr(s)
        xls.lang = lang
        return xls
    def __init__(self, s):
        unicode.__init__(self, s)
        self.lang = None