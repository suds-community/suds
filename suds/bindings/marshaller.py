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
Provides classes for object->XML I{marshalling}.
"""

from logging import getLogger
from suds import *
from suds.sudsobject import Factory, Object, Property, items
from suds.resolver import GraphResolver
from suds.sax import splitPrefix, Namespace
from suds.sax.document import Document
from suds.sax.element import Element
from suds.sax.attribute import Attribute

log = getLogger(__name__)


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
        @type schema: L{xsd.schema.Schema}
        """
        self.basic = Basic()
        self.literal =  Literal(schema)
        self.encoded = Encoded(schema)


class Content(Object):
    """
    @ivar tag: The content tag.
    @type tag: str
    @ivar type: The (optional) content schema type.
    @type type: L{xsd.sxbase.SchemaObject}
    @ivar value: The content's value.
    @type value: I{any}
    """

    def __init__(self, tag, value, type=None):
        Object.__init__(self)
        self.tag = tag
        self.value = value
        self.type = type


class M:
    """
    Appender matcher.
    @ivar cls: A class object.
    @type cls: I{classobj}
    """

    def __init__(self, cls):
        """
        @param cls: A class object.
        @type cls: I{classobj}
        """
        self.cls = cls

    def __eq__(self, x):
        if self.cls is None:
            return ( x is None )
        else:
            return isinstance(x, self.cls)


class ContentAppender:
    """
    Appender used to add content to marshalled objects.
    @ivar default: The default appender.
    @type default: L{Appender}
    @ivar appenders: A I{table} of appenders mapped by class.
    @type appenders: I{table}
    """

    def __init__(self, marshaller):
        """
        @param marshaller: A marshaller.
        @type marshaller: L{MBase}
        """
        self.default = PrimativeAppender(marshaller)
        self.appenders = (
            (M(None), NoneAppender(marshaller)),
            (M(Property), PropertyAppender(marshaller)),
            (M(Object), ObjectAppender(marshaller)),
            (M(Element), ElementAppender(marshaller)),
            (M(list), ListAppender(marshaller)),
            (M(tuple), ListAppender(marshaller)),
        )
        
    def append(self, parent, content):
        """
        Select an appender and append the content to parent.
        @param parent: A parent node.
        @type parent: L{Element}
        @param content: The content to append.
        @type content: L{Content}
        """
        appender = self.default
        for a in self.appenders:
            if a[0] == content.value:
                appender = a[1]
                break
        appender.append(parent, content)


class Appender:
    """
    An appender used by the marshaller to append content.
    @ivar marshaller: A marshaller.
    @type marshaller: L{MBase}
    """
    
    def __init__(self, marshaller):
        """
        @param marshaller: A marshaller.
        @type marshaller: L{MBase}
        """
        self.marshaller  = marshaller
        
    def node(self, content):
        """
        Create and return an XML node that is qualified
        using the I{type}.  Also, make sure all referenced namespace
        prefixes are declared.
        @param content: The content for which proccessing has ended.
        @type content: L{Object}
        @return: A new node.
        @rtype: L{Element}
        """
        return self.marshaller.node(content)
    
    def setnil(self, node, content):
        """
        Set the value of the I{node} to nill.
        @param node: A I{nil} node.
        @type node: L{Element}
        @param content: The content for which proccessing has ended.
        @type content: L{Object}
        """
        self.marshaller.setnil(node, content)
        
    def suspend(self, content):
        """
        Notify I{marshaller} that appending this content has suspended.
        @param content: The content for which proccessing has been suspended.
        @type content: L{Object}
        """
        self.marshaller.suspend(content)
        
    def resume(self, content):
        """
        Notify I{marshaller} that appending this content has resumed.
        @param content: The content for which proccessing has been resumed.
        @type content: L{Object}
        """
        self.marshaller.resume(content)
    
    def append(self, parent, content):
        """
        Append the specified L{content} to the I{parent}.
        @param content: The content to append.
        @type content: L{Object}
        """
        self.marshaller.append(parent, content)

       
class PrimativeAppender(Appender):
    """
    An appender for python I{primative} types.
    """

    def __init__(self, marshaller):
        """
        @param marshaller: A marshaller.
        @type marshaller: L{MBase}
        """
        Appender.__init__(self, marshaller)
        
    def append(self, parent, content):
        """
        Append the specified L{content} to the I{parent}.
        @param content: The content to append.
        @type content: L{Object}
        """
        if content.tag.startswith('_'):
            attr = content.tag[1:]
            value = tostr(content.value)
            parent.set(attr, value)
        else:
            child = self.node(content)
            child.setText(tostr(content.value))
            parent.append(child)


class NoneAppender(Appender):
    """
    An appender for I{None} values.
    """

    def __init__(self, marshaller):
        """
        @param marshaller: A marshaller.
        @type marshaller: L{MBase}
        """
        Appender.__init__(self, marshaller)
        
    def append(self, parent, content):
        """
        Append the specified L{content} to the I{parent}.
        @param content: The content to append.
        @type content: L{Object}
        """
        child = self.node(content)
        self.setnil(child, content)
        parent.append(child)


class PropertyAppender(Appender):
    """
    A L{Property} appender.
    """

    def __init__(self, marshaller):
        """
        @param marshaller: A marshaller.
        @type marshaller: L{MBase}
        """
        Appender.__init__(self, marshaller)
        
    def append(self, parent, content):
        """
        Append the specified L{content} to the I{parent}.
        @param content: The content to append.
        @type content: L{Object}
        """
        p = content.value
        child = self.node(content)
        child.setText(p.get())
        parent.append(child)
        for item in p.items():
            cont = Content(item[0], item[1])
            Appender.append(self, child, cont)

            
class ObjectAppender(Appender):
    """
    An L{Object} appender.
    """

    def __init__(self, marshaller):
        """
        @param marshaller: A marshaller.
        @type marshaller: L{MBase}
        """
        Appender.__init__(self, marshaller)
        
    def append(self, parent, content):
        """
        Append the specified L{content} to the I{parent}.
        @param content: The content to append.
        @type content: L{Object}
        """
        object = content.value
        child = self.node(content)
        parent.append(child)
        for item in items(object):
            cont = Content(item[0], item[1])
            Appender.append(self, child, cont)


class ElementAppender(Appender):
    """
    An appender for I{Element} types.
    """

    def __init__(self, marshaller):
        """
        @param marshaller: A marshaller.
        @type marshaller: L{MBase}
        """
        Appender.__init__(self, marshaller)
        
    def append(self, parent, content):
        """
        Append the specified L{content} to the I{parent}.
        @param content: The content to append.
        @type content: L{Object}
        """
        if content.tag.startswith('_'):
            raise Exception('raw XML not valid as attribute value')
        child = content.value.detach()
        parent.append(child)


class ListAppender(Appender):
    """
    A list/tuple appender.
    """
    
    def __init__(self, marshaller):
        """
        @param marshaller: A marshaller.
        @type marshaller: L{MBase}
        """
        Appender.__init__(self, marshaller)
        
    def append(self, parent, content):
        """
        Append the specified L{content} to the I{parent}.
        @param content: The content to append.
        @type content: L{Object}
        """
        collection = content.value
        if len(collection):
            self.suspend(content)
            for item in collection:
                cont = Content(content.tag, item)
                Appender.append(self, parent, cont)
            self.resume(content)


class MBase:
    """
    An I{abstract} marshaller.  This class implement the core
    functionality of the marshaller.
    @ivar appender: A content appender.
    @type appender: L{ContentAppender}
    """

    def __init__(self):
        """
        """
        self.appender = ContentAppender(self)

    def process(self, content):
        """
        Process (marshal) the tag with the specified value using the
        optional type information.
        @param content: The content to process.
        @type content: L{Object}
        """
        log.debug('processing:\n%s', content)
        self.reset()
        document = Document()
        if isinstance(content.value, Property):
            root = self.node(content)
            self.append(document, content)
        elif content.value is None or \
            isinstance(content.value, Object):
                self.append(document, content)
        else:
            root = self.node(content)
            document.append(root)
            root.setText(tostr(content.value))
        return document.root()
    
    def append(self, parent, content):
        """
        Append the specified L{content} to the I{parent}.
        @param content: The content to append.
        @type content: L{Object}
        """
        log.debug('appending parent:\n%s\ncontent:\n%s', parent, content)
        if self.start(content):
            self.appender.append(parent, content)
            self.end(content)

    def reset(self):
        """
        Reset the marshaller.
        """
        pass

    def node(self, content):
        """
        Create and return an XML node.
        @param content: The content for which proccessing has been suspended.
        @type content: L{Object}
        @return: An element.
        @rtype: L{Element}
        """
        return Element(content.tag)
    
    def start(self, content):
        """
        Appending this content has started.
        @param content: The content for which proccessing has started.
        @type content: L{Object}
        @return: True to continue appending
        @rtype: boolean
        """
        return True
    
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
    
    def setnil(self, node, content):
        """
        Set the value of the I{node} to nill.
        @param node: A I{nil} node.
        @type node: L{Element}
        @param content: The content for which proccessing has ended.
        @type content: L{Object}
        """
        pass


class Basic(MBase):
    """
    A I{basic} (untyped) marshaller.
    """

    def __init__(self):
        """
        """
        MBase.__init__(self)
    
    def process(self, value, tag=None):
        """
        Process (marshal) the tag with the specified value using the
        optional type information.
        @param value: The value (content) of the XML node.
        @type value: (L{Object}|any)
        @param tag: The (optional) tag name for the value.  The default is
            value.__class__.__name__
        @type tag: str
        @return: An xml node.
        @rtype: L{Element}
        """
        if tag is None:
            tag = value.__class__.__name__
        content = Content(tag, value)
        result = \
            MBase.process(self, content)
        return result

       
class Literal(MBase):
    """
    A I{literal} marshaller.
    This marshaller is semi-typed as needed to support both
    document/literal and rpc/literal soap styles.
    @ivar schema: An xsd schema.
    @type schema: L{xsd.schema.Schema}
    @ivar resolver: A schema type resolver.
    @type resolver: L{GraphResolver}
    """

    def __init__(self, schema):
        """
        @param schema: A schema object
        @type schema: L{xsd.schema.Schema}
        """
        MBase.__init__(self)
        self.schema = schema
        self.resolver = GraphResolver(self.schema)
        
    def process(self, value, type, tag=None):
        """
        Process (marshal) the tag with the specified value using the
        optional type information.
        @param value: The value (content) of the XML node.
        @type value: (L{Object}|any)
        @param type: The value's schema type.
        @type type: L{xsd.sxbase.SchemaObject}
        @param tag: The (optional) tag name for the value.  The default is
            value.__class__.__name__
        @type tag: str
        @return: An xml node.
        @rtype: L{Element}
        """
        if tag is None:
            tag = value.__class__.__name__
        content = Content(tag, value, type)
        result = MBase.process(self, content)
        return result
    
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
        @return: True to continue appending
        @rtype: boolean
        @note: This will I{push} the type in the resolver.
        """
        log.debug('starting content:\n%s', content)
        if isinstance(content.value, Object):
            content.type = self.__metatype(content)
        if content.type is None:
            name = content.tag
            if name.startswith('_'):
                name = '@'+name[1:]
            content.type = self.resolver.find(name, content.value)
        else:
            self.resolver.push(content.type)
        if content.type is None:
            raise TypeNotFound(content.tag)
        resolved = content.type.resolve()
        content.value = resolved.translate(content.value, False)
        if self.__skip(content):
            log.debug('skipping (optional) content:\n%s', content)
            self.resolver.pop()
            return False
        return True
        
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
    
    def node(self, content):
        """
        Create and return an XML node that is qualified
        using the I{type}.  Also, make sure all referenced namespace
        prefixes are declared.
        @param content: The content for which proccessing has ended.
        @type content: L{Object}
        @return: A new node.
        @rtype: L{Element}
        """
        ns = content.type.namespace()
        if content.type.form_qualified:
            node = Element(content.tag, ns=ns)
            node.addPrefix(ns[0], ns[1])
        else:
            node = Element(content.tag)
        self.encode(node, content)
        log.debug('created - node:\n%s', node)
        return node
    
    def setnil(self, node, content):
        """
        Set the value of the I{node} to nill.
        @param node: A I{nil} node.
        @type node: L{Element}
        @param content: The content for which proccessing has ended.
        @type content: L{Object}
        """
        if content.type.nillable:
            node.setnil()
    
    def encode(self, node, content):
        """
        Add (soap) encoding information
        @param node: The node to update.
        @type node: L{Element}
        @param content: The content for which proccessing has ended.
        @type content: L{Object}
        """
        if not content.type.any() and  content.type.derived():
            name = content.type.name
            ns = content.type.namespace()
            ref = ':'.join((ns[0], name))
            node.set('xsi:type', ref)
            log.debug('encoding name=(%s)', name)
            node.addPrefix(ns[0], ns[1])
            node.addPrefix(Namespace.xsins[0], Namespace.xsins[1])
    
    def __metatype(self, content):
        """
        Get the I{type} embedded in the content.I{value}.
        This makes the assumption that content.I{value} is an
        L{Object} and has I{type} metadata.
        @param content: The content for which proccessing has ended.
        @type content: L{Object}
        @return: The type found in the metadata.
        @rtype: L{xsd.sxbase.SchemaObject}
        """
        result = None
        try:
            md = content.value.__metadata__
            result = md.__type__
            log.debug('type (%s) found in metadata', result.name)
        except AttributeError:
            pass
        return result
    
    def __skip(self, content):
        if content.type.optional():
            v = content.value
            if v is None:
                return True
            if isinstance(v, (list,tuple)) and len(v) == 0:
                return True
        return False


class Encoded(Literal):
    """
    A SOAP section (5) encoding marshaller.
    This marshaller supports rpc/encoded soap styles.
    """
    
    def __init__(self, schema):
        """
        @param schema: A schema object
        @type schema: L{xsd.schema.Schema}
        """
        Literal.__init__(self, schema)
        
    def encode(self, node, content):
        """
        Add (soap) encoding information
        @param node: The node to update.
        @type node: L{Element}
        @param content: The content for which proccessing has ended.
        @type content: L{Object}
        """
        if not content.type.any():
            name = content.type.name
            ns = content.type.namespace()
            ref = ':'.join((ns[0], name))
            node.set('xsi:type', ref)
            log.debug('encoding name=(%s)', name)
            node.addPrefix(ns[0], ns[1])
            node.addPrefix(Namespace.xsins[0], Namespace.xsins[1])
