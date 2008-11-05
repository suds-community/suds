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
from suds.sax import Namespace as NS
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
    Marshaller Content.
    @ivar parent: The content parent.
    @type parent: (L{Element}|L{Content})
    @ivar tag: The content tag.
    @type tag: str
    @ivar value: The content's value.
    @type value: I{any}
    @ivar type: The (optional) content schema type.
    @type type: L{xsd.sxbase.SchemaObject}
    @ivar resolved: The content's I{resolved} type.
    @type resolved: L{xsd.sxbase.SchemaObject}
    """
    def __init__(self, parent=None, tag=None, value=None, type=None):
        """
        @param parent: The content parent.
        @type parent: (L{Element}|L{Content})
        @param tag: The content tag.
        @type tag: str
        @param value: The content's value.
        @type value: I{any}
        @param type: The (optional) content schema type.
        @type type: L{xsd.sxbase.SchemaObject}
        """
        Object.__init__(self)
        self.parent = parent
        self.tag = tag
        self.value = value
        self.type = type
        self.resolved = None

    def namespace(self):
        """
        Get the tag's namesapce by looking at the parent's resolved
        schema type.  If the parent is an L{Element}, its namespace is used.
        @return: The tag's namespace.
        @rtype: (prefix, uri)
        """
        p = self.parent
        if isinstance(p, Element):
            return p.namespace()
        if isinstance(p, Content):
            pr = self.parent.resolved
            if pr is not None:
                return pr.namespace()
            pt = self.parent.type
            if pt is not None:
                return pt.resolve().namespace()
        return NS.default


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
            if value is not None and len(value):
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
            cont = Content(
                parent=content,
                tag=item[0], 
                value=item[1])
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
            cont = Content(
                parent=content, 
                tag=item[0], 
                value=item[1])
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
                cont = Content(
                    parent=content, 
                    tag=content.tag, 
                    value=item)
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
        if content.tag is None:
            content.tag = content.value.__class__.__name__
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
        content = Content(tag=tag, value=value)
        result = MBase.process(self, content)
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
        if content.type is None:
            name = content.tag
            if name.startswith('_'):
                name = '@'+name[1:]
            content.type = self.resolver.find(name, content.value)
            if content.type is None:
                raise TypeNotFound(content.tag)
        else:
            if isinstance(content.value, Object):
                known = self.resolver.known(content.value)
                item = (content.type, known)
                self.resolver.push(item)
            else:
                self.resolver.push(content.type)
        content.resolved = self.resolver.top(1)
        content.value = content.resolved.translate(content.value, False)
        if self.__skip(content):
            log.debug('skipping (optional) content:\n%s', content)
            self.resolver.pop()
            return False
        else:
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
        current = self.resolver.top(0)
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
        ns = content.namespace()
        if content.type.form_qualified:
            node = Element(content.tag, ns=ns)
            node.addPrefix(ns[0], ns[1])
        else:
            node = Element(content.tag, ns=(None, ns[1]))
        self.encode(node, content)
        log.debug('created - node:\n%s', node)
        return node
    
    def setnil(self, node, content):
        """
        Set the value of the I{node} to nill when nillable by the type or the
        resolved type is a builtin B{and} it is nillable.
        @param node: A I{nil} node.
        @type node: L{Element}
        @param content: The content for which proccessing has ended.
        @type content: L{Object}
        """
        resolved = content.type.resolve()
        if ( content.type.nillable or ( resolved.builtin() and resolved.nillable ) ):
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
            resolved = content.type.resolve()
            name = resolved.name
            ns = resolved.namespace()
            Typer.manual(node, name)
    
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
        if content.type.any():
            Typer.auto(node, content.value)
            return
        resolved = self.resolver.top(1)
        if resolved is None:
            resolved = content.type.resolve()
        name = resolved.name
        ns = resolved.namespace()
        Typer.manual(node, name, ns)


class Typer:
    """
    Provides XML node typing as either automatic or manual.
    @cvar types:  A dict of class to xs type mapping.
    @type types: dict
    """

    types = {
        int : ('int', NS.xsdns),
        long : ('long', NS.xsdns),
        str : ('string', NS.xsdns),
        unicode : ('string', NS.xsdns),
        bool : ('boolean', NS.xsdns),
     }
                
    @classmethod
    def auto(cls, node, value=None):
        """
        Automatically set the node's xsi:type attribute based on either I{value}'s
        class or the class of the node's text.  When I{value} is an unmapped class,
        the default type (xs:any) is set.
        @param node: An XML node
        @type node: L{sax.element.Element}
        @param value: An object that is or would be the node's text.
        @type value: I{any}
        @return: The specified node.
        @rtype: L{sax.element.Element}
        """
        if value is None:
            value = node.getText()
        tm = cls.types.get(value.__class__, ('any', NS.xsdns))
        cls.manual(node, *tm)
        return node

    @classmethod
    def manual(cls, node, tval, ns=None):
        """
        Set the node's xsi:type attribute based on either I{value}'s
        class or the class of the node's text.  Then adds the referenced
        prefix(s) to the node's prefix mapping.
        @param node: An XML node
        @type node: L{sax.element.Element}
        @param tval: The name of the schema type.
        @type tval: str
        @param ns: The XML namespace of I{tval}.
        @type ns: (prefix, uri)
        @return: The specified node.
        @rtype: L{sax.element.Element}
        """
        a = cls.qname(NS.xsins, 'type')
        node.addPrefix(NS.xsins[0], NS.xsins[1])
        if ns is None:
            node.set(a, tval)
        else:
            node.set(a, cls.qname(ns, tval))
            node.addPrefix(ns[0], ns[1])
        return node
    
    @classmethod
    def qname(self, ns, tval):
        """
        Create a I{qname} for I{tval} and the specified namespace.
        @param ns: The namespace of I{tval}.
        @type ns: (prefix, uri)
        @param tval: The name of the schema type.
        @type tval: str
        @return: The prefix:tval.
        @rtype: str
        """
        try:
            return ':'.join((ns[0], tval))
        except:
            pass

