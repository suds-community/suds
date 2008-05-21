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
from suds.resolver import GraphResolver
from suds.sax import Element, Attribute, splitPrefix, xsins

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

    def __init__(self, schema, **kwargs):
        """
        @param schema: A schema object
        @type schema: L{schema.Schema}
        @param kwargs: keyword args
        """
        self.basic = Basic()
        self.literal = \
            Literal(schema, **kwargs)
        self.encoded = \
            Encoded(schema, **kwargs)


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

    def __init__(self, schema=None, **kwargs):
        """
        @param schema: A schema object
        @type schema: L{schema.Schema}
        @param kwargs: keyword args
        @keyword nil_supported: The bindings will set the xsi:nil="true" on nodes
                that have a value=None when this flag is True (default:True).
                Otherwise, an empty node <x/> is sent.
        @type nil_supported: boolean
        """
        self.schema = schema
        self.nil_supported = kwargs.get('nil_supported', True)

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
        self.reset(type)
        root = self.node(tag, type)
        if isinstance(value, dict):
            value = Object.__factory__.instance(dict=value)
        if isinstance(value, Object):
            for key in value:
                cont = Content(key, value[key])
                self.append(root, cont)
        else:
            root.setText(tostr(value))
        return root
    
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
            if self.nil_supported:
                child.setnil()
            parent.append(child)
            return
        if isinstance(content.value, dict):
            content.value = \
                Object.__factory__.instance(dict=content.value)
        if isinstance(content.value, Object):
            object = content.value
            child = self.node(content.tag, content.type)
            parent.append(child)
            for key in object:
                cont = Content(key, object[key])
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
            parent.set(content.tag[1:], unicode(content.value))
            return
        child = self.node(content.tag, content.type)
        child.setText(unicode(content.value))
        parent.append(child)

    def reset(self, type):
        """
        Reset the marshaller.
        Since this is a I{basic} resolver, nil is B{not} supported.
        @param type: A I{parent} schema type.
        @type type: L{schema.SchemaProperty}
        @return: A new node.
        @rtype: L{Element}
        """
        log.debug('reset type=:\n%s', type)
        self.nil_supported = False
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
        

       
class Literal(Basic):
    """
    A I{literal} marshaller.
    This marshaller is semi-typed as needed to support both
    document/literal and rpc/literal soap styles.
    """

    def __init__(self, schema, **kwargs):
        """
        @param schema: A schema object
        @type schema: L{schema.Schema}
        @param kwargs: keyword args
        @keyword nil_supported: The bindings will set the xsi:nil="true" on nodes
                that have a value=None when this flag is True (default:True).
                Otherwise, an empty node <x/> is sent.
        @type nil_supported: boolean
        """
        Basic.__init__(self, schema, **kwargs)
        self.resolver = GraphResolver(self.schema)
    
    def reset(self, type):
        """
        Reset the resolver.
        @param type: The I{parent} schema type used to prime
            the resolver.
        @type type: L{schema.SchemaProperty}
        """
        log.debug('reset type=:\n%s', type)
        resolved = type.resolve()
        self.resolver.reset((resolved,))
            
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
            content.type = \
                self.resolver.find(content.tag, content.value)
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
        current = self.resolver.top()
        if current == content.type:
            self.resolver.pop()
        else:
            raise Exception(
                'content (end) mismatch: top=(%s) cont=(%s)' % \
                (current, content))
    
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
        if type.must_qualify():
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
        if type.derived():
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
        return None



class Encoded(Literal):
    """
    A SOAP section (5) encoding marshaller.
    This marshaller supports rpc/encoded soap styles.
    """
    
    def __init__(self, schema, **kwargs):
        """
        @param schema: A schema object
        @type schema: L{schema.Schema}
        @param kwargs: keyword args
        @keyword nil_supported: The bindings will set the xsi:nil="true" on nodes
                that have a value=None when this flag is True (default:True).
                Otherwise, an empty node <x/> is sent.
        @type nil_supported: boolean
        """
        Literal.__init__(self, schema, **kwargs)
        
    def encode(self, node, type):
        """
        Add (soap) encoding information
        @param node: The node to update.
        @type node: L{Element}
        @param type: The schema type use for the encoding.
        @type type: L{schema.SchemaProperty}
        """
        name, ns = type.asref()
        node.set('xsi:type', name)
        log.debug('encoding name=(%s)', name)
        node.addPrefix(ns[0], ns[1])
        node.addPrefix(xsins[0], xsins[1])