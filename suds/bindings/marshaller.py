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
from suds.sudsobject import Factory, Object, Property, items
from suds.resolver import GraphResolver
from suds.sax import Document, Element, Attribute, splitPrefix, xsins

log = logger(__name__)


class Marshaller:
    """
    A marshaller object.
    @ivar basic: A basic I{plain} (untyped) marshaller.
    @type basic: L{Basic}
    @ivar literal: A I{literal} style marshaller.
    @type literal: L{Literal}
    @ivar encoded: A soap section 5 I{encoded} marshaller.
    @type encoded: L{Encoded} 
    """

    def __init__(self, schema):
        """
        @param schema: A schema object
        @type schema: L{schema.Schema}
        """
        self.basic = Basic()
        self.literal =  Literal(schema)
        self.encoded = Encoded(schema)


class Content(Object):
    """ marshalled content """
    def __init__(self, tag, value, type=None):
        Object.__init__(self)
        self.tag = tag
        self.type = type
        self.value = value


class Basic:
    """
    A I{basic} (untyped) marshaller.
    """

    def __init__(self, schema=None):
        """
        @param schema: A schema object
        @type schema: L{schema.Schema}
        """
        self.schema = schema

    def process(self, tag, value, type=None):
        """
        Process (marshal) the tag with the specified value using the
        optional type information.
        @param tag: The XML tag name for the value.
        @type tag: basestring
        @param value: The value (content) of the XML node.
        @type value: (L{Object}|any)
        @param type: The schema type.
        @type type: L{schema.SchemaProperty}
        """
        log.debug('processing tag=(%s) value:\n%s', tag, value)
        self.reset()
        document = Document()
        content = Content(tag, value, type)
        if value is None:
            self.append(document, content)
            return document.root()
        if isinstance(value, dict):
            value = Factory.object(dict=value)  
        elif isinstance(value, Property):
            root = self.node(tag, type)
            document.append(root)
            self.append(root, content)
        elif isinstance(value, Object):
            self.append(document, content)
        else:
            root = self.node(tag, type)
            document.append(root)
            root.setText(tostr(value))
        return document.root()
    
    def append(self, parent, content):
        """
        Append the specified L{content} to the I{parent}.
        @param content: The content to append.
        @type content: L{Object}
        """
        log.debug('appending parent:\n%s\ncontent:\n%s', parent, content)
        self.start(content)
        self.__append(parent, content)
        self.end(content)         
       
    def __append(self, parent, content):
        """
        Append the specified L{content} to the I{parent}.
        @param content: The content to append.
        @type content: L{Object}
        """
        log.debug('appending parent:\n%s\ncontent:\n%s', parent, content)
        if content.value is None:
            child = self.node(content.tag, content.type)
            self.setnil(child, content.type)
            parent.append(child)
            return
        if isinstance(content.value, dict):
            content.value = \
                Facotry.object(dict=content.value)
        if isinstance(content.value, Property):
            p = content.value
            parent.setText(p.get())
            for item in p.items():
                cont = Content(item[0], item[1])
                self.append(parent, cont)
            return
        if isinstance(content.value, Object):
            object = content.value
            child = self.node(content.tag, content.type)
            parent.append(child)
            for item in items(object):
                cont = Content(item[0], item[1])
                self.append(child, cont)
            return
        if isinstance(content.value, (list,tuple)):
            collection = content.value
            if len(collection):
                self.suspend(content)
                for item in collection:
                    cont = Content(content.tag, item)
                    self.append(parent, cont)
                self.resume(content)
            return
        if content.tag.startswith('_'):
            parent.set(content.tag[1:], tostr(content.value))
            return
        child = self.node(content.tag, content.type)
        child.setText(unicode(content.value))
        parent.append(child)

    def reset(self):
        """
        Reset the marshaller.
        """
        pass

    def node(self, tag, type):
        """
        Create and return an XML node.
        @param tag: The node name.
        @type tag: basestring
        @param type: The schema type.
        @type type: L{schema.SchemaProperty}
        """
        return Element(tag)
    
    def start(self, content):
        """
        Appending this content has started.
        @param content: The content for which proccessing has started.
        @type content: L{Object}
        """
        pass
    
    def suspend(self, content):
        """
        Appending this content has suspended.
        @param content: The content for which proccessing has been suspended.
        @type content: L{Object}
        """
        pass
    
    def resume(self, content):
        """
        Appending this content has resumed.
        @param content: The content for which proccessing has been resumed.
        @type content: L{Object}
        """
        pass

    def end(self, content):
        """
        Appending this content has ended.
        @param content: The content for which proccessing has ended.
        @type content: L{Object}
        """
        pass
    
    def setnil(self, node, type):
        """
        Set the value of the I{node} to nill.
        @param node: A I{nil} node.
        @type node: L{Element}
        @param type: The node's schema type
        @type type: L{schema.SchemaProperty}
        """
        pass

       
class Literal(Basic):
    """
    A I{literal} marshaller.
    This marshaller is semi-typed as needed to support both
    document/literal and rpc/literal soap styles.
    """

    def __init__(self, schema):
        """
        @param schema: A schema object
        @type schema: L{schema.Schema}
        """
        Basic.__init__(self, schema)
        self.resolver = GraphResolver(self.schema)
    
    def reset(self):
        """
        Reset the resolver.
        """
        self.resolver.reset()
            
    def start(self, content):
        """
        Processing of I{content} has started, find and set the content's
        schema type using the resolver.
        @param content: The content for which proccessing has stated.
        @type content: L{Object}
        @note: This will I{push} the type in the resolver.
        """
        log.debug('starting content:\n%s', content)
        if isinstance(content.value, Object):
            content.type = self.__metatype(content)
        if content.type is None:
            name = content.tag
            if name.startswith('_'):
                name = '@'+name[1:]
            content.type = \
                self.resolver.find(name, content.value)
        else:
            self.resolver.push(content.type)
        if content.type is None:
            raise TypeNotFound(content.tag)
        
    def suspend(self, content):
        """
        Appending this content has suspended.
        @param content: The content for which proccessing has been suspended.
        @type content: L{Object}
        """
        content.suspended = True
        self.resolver.pop()
    
    def resume(self, content):
        """
        Appending this content has resumed.
        @param content: The content for which proccessing has been resumed.
        @type content: L{Object}
        """
        self.resolver.push(content.type)
        
    def end(self, content):
        """
        Processing of I{content} has ended, mirror the change
        in the resolver.
        @param content: The content for which proccessing has ended.
        @type content: L{Object}
        """
        log.debug('ending content:\n%s', content)
        current = self.resolver.top()[0]
        if current == content.type:
            self.resolver.pop()
        else:
            raise Exception(
                'content (end) mismatch: top=(%s) cont=(%s)' % \
                (current, content))
            
    def setnil(self, node, type):
        """
        Set the value of the I{node} to nill.
        @param node: A I{nil} node.
        @type node: L{Element}
        @param type: The node's schema type
        @type type: L{schema.SchemaProperty}
        """
        if type.nillable:
            node.setnil()
    
    def node(self, tag, type):
        """
        Create and return an XML node that is qualified
        using the I{type}.  Also, make sure all referenced namespace
        prefixes are declared.
        @param tag: The node name.
        @type tag: basestring
        @param type: The schema type.
        @type type: L{schema.SchemaProperty}
        @return: A new node.
        @rtype: L{Element}
        """
        ns = type.namespace()
        if type.form_qualified:
            node = Element(tag, ns=ns)
            node.addPrefix(ns[0], ns[1])
        else:
            node = Element(tag)
        self.encode(node, type)
        log.debug('created - node:\n%s', node)
        return node
    
    def encode(self, node, type):
        """
        Add (soap) encoding information
        @param node: The node to update.
        @type node: L{Element}
        @param type: The schema type use for the encoding.
        @type type: L{schema.SchemaProperty}
        """
        if not type.any() and \
            type.derived:
                name = type.get_name()
                node.set('xsi:type', name)
                log.debug('encoding name=(%s) on:\n\t%s', name, tostr(node))
                node.addPrefix(xsins[0], xsins[1])
    
    def __metatype(self, content):
        """
        Get the I{type} embedded in the content.I{value}.
        This makes the assumption that content.I{value} is an
        L{Object} and has I{type} metadata.
        @param content: The content for which proccessing has ended.
        @type content: L{Object}
        @return: The type found in the metadata.
        @rtype: L{schema.SchemaProperty}
        """
        result = None
        try:
            md = content.value.__metadata__
            result = md.__type__
            log.debug('type (%s) found in metadata', result.get_name())
        except AttributeError:
            pass
        return result



class Encoded(Literal):
    """
    A SOAP section (5) encoding marshaller.
    This marshaller supports rpc/encoded soap styles.
    """
    
    def __init__(self, schema):
        """
        @param schema: A schema object
        @type schema: L{schema.Schema}
        """
        Literal.__init__(self, schema)
        
    def encode(self, node, type):
        """
        Add (soap) encoding information
        @param node: The node to update.
        @type node: L{Element}
        @param type: The schema type use for the encoding.
        @type type: L{schema.SchemaProperty}
        """
        if not type.any():
            name, ns = type.qref()
            node.set('xsi:type', name)
            log.debug('encoding name=(%s)', name)
            node.addPrefix(ns[0], ns[1])
            node.addPrefix(xsins[0], xsins[1])