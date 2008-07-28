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

"""
The I{wsdl} module provides an objectification of the WSDL.
The primary class is I{Definitions} as it represends the root element
found in the document.
"""

from suds import *
from suds.sax import Parser, Element, splitPrefix
from suds.bindings.document import Document
from suds.bindings.rpc import RPC
from suds.xsd import qualified_reference
from suds.xsd.schema import SchemaCollection
from suds.sudsobject import Object
from suds.sudsobject import Factory as SOFactory
from urlparse import urljoin

log = logger(__name__)

wsdlns = (None, "http://schemas.xmlsoap.org/wsdl/")

class Factory:
    """
    Simple WSDL object factory.
    @cvar tags: Dictionary of tag->constructor mappings.
    @type tags: dict
    """

    tags =\
    {
        'import' : lambda x,y: Import(x,y), 
        'schema' : lambda x,y: Schema(x,y), 
        'message' : lambda x,y: Message(x,y), 
        'portType' : lambda x,y: PortType(x,y),
        'binding' : lambda x,y: Binding(x,y),
        'service' : lambda x,y: Service(x,y),
    }
    
    @classmethod
    def create(cls, root, definitions):
        """
        Create an object based on the root tag name.
        @param root: An XML root element.
        @type root: L{Element}
        @param definitions: A definitions object.
        @type definitions: L{Definitions}
        @return: The created object.
        @rtype: L{WObject} 
        """
        fn = cls.tags.get(root.name)
        if fn is not None:
            return fn(root, definitions)
        else:
            return None


class WObject(Object):
    """
    Base object for wsdl types.
    @ivar root: The XML I{root} element.
    @type root: L{Element}
    """
    
    @classmethod
    def asqname(cls, qref):
        """
        Convert I{qref} to a I{qname} where a I{qref} is a tuple of:
        (name, I{namespace}) as returned by L{suds.xsd.qualified_reference} and
        a I{qname} is a tuple of (name, I{namespace-uri}).
        @param qref: A qualified reference.
        @type qref: (name, I{namespace})
        @return: A qualified name.
        @rtype: (name, I{namespace-uri}).
        """
        n,ns = qref
        return (n, ns[1])
    
    def __init__(self, root, definitions=None):
        """
        @param root: An XML root element.
        @type root: L{Element}
        @param definitions: A definitions object.
        @type definitions: L{Definitions}
        """
        Object.__init__(self)
        self.root = root
        pmd = SOFactory.metadata()
        pmd.excludes = ['root']
        pmd.wrappers = dict(qname=lambda x: repr(x))
        self.__metadata__.__print__ = pmd
        
    def resolve(self, definitions):
        """
        Resolve named references to other WSDL objects.
        @param definitions: A definitions object.
        @type definitions: L{Definitions}
        """
        pass

        
class NamedObject(WObject):
    """
    A B{named} WSDL object.
    @ivar name: The name of the object.
    @type name: str
    @ivar qname: The I{qualified} name of the object.
    @type qname: (name, I{namespace-uri}).
    """

    def __init__(self, root, definitions):
        """
        @param root: An XML root element.
        @type root: L{Element}
        @param definitions: A definitions object.
        @type definitions: L{Definitions}
        """
        WObject.__init__(self, root, definitions)
        self.name = root.get('name')
        self.qname = (self.name, definitions.tns[1])
        pmd = self.__metadata__.__print__
        pmd.wrappers['qname'] = lambda x: repr(x)


class Definitions(WObject):
    """
    Represents the I{root} container of the WSDL objects as defined
    by <wsdl:definitions/>
    @ivar id: The object id.
    @type id: str
    @ivar url: The URL used to load the object.
    @type url: str
    @ivar tns: The target namespace for the WSDL.
    @type tns: str
    @ivar schema: The collective WSDL schema object.
    @type schema: L{SchemaCollection}
    @ivar children: The raw list of child objects.
    @type children: [L{WObject},...]
    @ivar imports: The list of L{Import} children.
    @type imports: [L{Import},...]
    @ivar messages: The dictionary of L{Message} children key'd by I{qname}
    @type messages: [L{Message},...]
    @ivar port_types: The dictionary of L{PortType} children key'd by I{qname}
    @type port_types: [L{PortType},...]
    @ivar bindings: The dictionary of L{Binding} children key'd by I{qname}
    @type bindings: [L{Binding},...]
    @ivar service: The service object.
    @type service: L{Service}
    """

    def __init__(self, url, opener=None):
        """
        @param url: A URL to the WSDL.
        @type url: str
        @param opener: A urllib2 opener (may be None).
        @type opener: urllib2.Opener
        """
        log.debug('reading wsdl at: %s ...', url)
        p = Parser(opener)
        root = p.parse(url=url).root()
        WObject.__init__(self, root)
        self.id = objid(self)
        self.url = url
        self.tns = self.mktns(root)
        self.schema = None
        self.children = []
        self.imports = []
        self.schemas = []
        self.messages = {}
        self.port_types = {}
        self.bindings = {}
        self.service = None
        self.add_children(self.root)
        self.children.sort()
        pmd = self.__metadata__.__print__
        pmd.excludes.append('children')
        pmd.excludes.append('wsdl')
        pmd.wrappers['schema'] = lambda x: repr(x)
        self.open_imports(opener)
        self.resolve()
        self.build_schema()
        self.assign_bindings()
        log.debug("wsdl at '%s' loaded:\n%s", url, self)
        
    def mktns(self, root):
        """ Get/create the target namespace """
        tns = root.get('targetNamespace')
        prefix = root.findPrefix(tns)
        ns = (prefix, tns)
        if ns[0] is None:
            log.debug('warning: tns (%s), not mapped to a prefix', tns)
        return ns
        
    def add_children(self, root):
        """ Add child objects using the factory """
        paths = \
            ('import', 'types/schema', 'message', 'portType', 'binding', 'service')
        for path in paths:
            for c in root.childrenAtPath(path):
                child = Factory.create(c, self)
                if child is None: continue
                self.children.append(child)
                if isinstance(child, Import):
                    self.imports.append(child)
                    continue
                if isinstance(child, Schema):
                    self.schemas.append(child)
                    continue
                if isinstance(child, Message):
                    self.messages[child.qname] = child
                    continue
                if isinstance(child, PortType):
                    self.port_types[child.qname] = child
                    continue
                if isinstance(child, Binding):
                    self.bindings[child.qname] = child
                    continue
                if isinstance(child, Service):
                    self.service = child
                    continue
                
    def open_imports(self, opener):
        """ Import the I{imported} WSDLs. """
        for imp in self.imports:
            base = self.url
            imp.load(self, opener)
                
    def resolve(self):
        """ Tell all children to resolve themselves """
        for c in self.children:
            c.resolve(self)
                
    def build_schema(self):
        """ Process schema objects and create the schema collection """
        container = SchemaCollection(self)
        for s in self.schemas:
            entry = (s.root, s.definitions)
            container.add(entry)
        if not len(container): # empty
            root = Element.buildPath(self.root, 'types/schema')
            entry = (root, self)
            container.add(entry)
        container.load()
        self.schema = container
        
    def assign_bindings(self):
        """ Create suds binding objects based on sytle/use """
        bindings = {
            'document/literal' : Document(self),
            'rpc/literal' : RPC(self),
            'rpc/encoded' : RPC(self).use_encoded()
        }
        for b in self.bindings.values():
            for op in b.operations.values():
                soap = op.soap
                key = '/'.join((soap.style, soap.input.body.use))
                binding = bindings.get(key)
                if binding is None:
                    raise Exception("binding: '%s/%s', not-supported" % key)
                op.binding = SOFactory.object('Suds-Binding')
                op.binding.input = binding
                key = '/'.join((soap.style, soap.output.body.use))
                binding = bindings.get(key)
                if binding is None:
                    raise Exception("binding: '%s/%s', not-supported" % key)
                op.binding.output = binding
            
    def binding(self):
        """
        Get the binding object associated with the service's port.
        @return: The binding object.
        @rtype: L{Binding}
        """
        return self.service.port.binding


class Import(WObject):
    """
    Represents the <wsdl:import/>.
    @ivar location: The value of the I{location} attribute.
    @type location: str
    @ivar ns: The value of the I{namespace} attribute.
    @type ns: str
    @ivar imported: The imported object.
    @type: L{Definitions}
    """
    
    def __init__(self, root, definitions):
        """
        @param root: An XML root element.
        @type root: L{Element}
        @param definitions: A definitions object.
        @type definitions: L{Definitions}
        """
        WObject.__init__(self, root, definitions)
        self.location = root.get('location')
        self.ns = root.get('namespace')
        self.imported = None
        pmd = self.__metadata__.__print__
        pmd.wrappers['imported'] = ( lambda x: x.id )
        
    def load(self, definitions, opener):
        """ Load the object by opening the URL """
        url = self.location
        log.debug('importing (%s)', url)
        if '://' not in url:
            url = urljoin(definitions.url, url)
        d = Definitions(url, opener)
        definitions.schemas += d.schemas
        definitions.messages.update(d.messages)
        definitions.port_types.update(d.port_types)
        definitions.bindings.update(d.bindings)
        self.imported = d
        
    def __gt__(self, other):
        return False
        

class Schema(WObject):
    """
    Represents <types><schema/></types>.
    """

    def __init__(self, root, definitions):
        """
        @param root: An XML root element.
        @type root: L{Element}
        @param definitions: A definitions object.
        @type definitions: L{Definitions}
        """
        WObject.__init__(self, root, definitions)
        self.definitions = definitions
        
    def __gt__(self, other):
        return isinstance(other, Import)
    

class Part(NamedObject):
    """
    Represents <message><part/></message>.
    @ivar element: The value of the {element} attribute.
        Stored as a I{qref} as converted by L{suds.xsd.qualified_reference}.
    @type element: str
    @ivar type: The value of the {type} attribute.
        Stored as a I{qref} as converted by L{suds.xsd.qualified_reference}.
    @type type: str
    """

    def __init__(self, root, definitions):
        """
        @param root: An XML root element.
        @type root: L{Element}
        @param definitions: A definitions object.
        @type definitions: L{Definitions}
        """
        NamedObject.__init__(self, root, definitions)
        pmd = SOFactory.metadata()
        pmd.wrappers = \
            dict(element=lambda x: repr(x), type=lambda x: repr(x))
        self.__metadata__.__print__ = pmd
        tns = definitions.tns
        self.element = self.__getref('element', tns)
        self.type = self.__getref('type', tns)
        
    def xsref(self):
        """
        Get the value of whichever is defined ( I{element} | I{type} ).
        @return: The value of whichever is defined ( I{element} | I{type} ).
        @rtype: (name, I{namespace}).
        """
        if self.element is None:
            return self.type
        else:
            return self.element
        
    def __getref(self, a, tns):
        """ Get the qualified value of attribute named 'a'."""
        s = self.root.get(a)
        if s is None:
            return s
        else:
            return qualified_reference(s, self.root, tns)  


class Message(NamedObject):
    """
    Represents <message/>.
    @ivar parts: A list of message parts.
    @type parts: [I{Part},...]
    """

    def __init__(self, root, definitions):
        """
        @param root: An XML root element.
        @type root: L{Element}
        @param definitions: A definitions object.
        @type definitions: L{Definitions}
        """
        NamedObject.__init__(self, root, definitions)
        self.parts = []
        for p in root.getChildren('part'):
            part = Part(p, definitions)
            self.parts.append(part)
            
    def __gt__(self, other):
        return isinstance(other, (Import, Schema))


class PortType(NamedObject):
    """
    Represents <portType/>.
    @ivar operations: A list of contained operations.
    @type operations: list
    """

    def __init__(self, root, definitions):
        """
        @param root: An XML root element.
        @type root: L{Element}
        @param definitions: A definitions object.
        @type definitions: L{Definitions}
        """
        NamedObject.__init__(self, root, definitions)
        self.operations = {}
        for c in root.getChildren('operation'):
            op = SOFactory.object('Operation')
            op.name = c.get('name')
            input = c.getChild('input')
            op.input = input.get('message')
            output = c.getChild('output')
            op.output = output.get('message')
            self.operations[op.name] = op
            
    def resolve(self, definitions):
        """
        Resolve named references to other WSDL objects.
        @param definitions: A definitions object.
        @type definitions: L{Definitions}
        """
        for op in self.operations.values():
            qref = qualified_reference(op.input, self.root, wsdlns)
            msg = definitions.messages.get(self.asqname(qref))
            if msg is None:
                raise Exception("msg '%s', not-found" % op.input)
            else:
                op.input = msg
            qref = qualified_reference(op.output, self.root, wsdlns)
            msg = definitions.messages.get(self.asqname(qref))
            if msg is None:
                raise Exception("msg '%s', not-found" % op.input)
            else:
                op.output = msg
                
    def operation(self, name):
        """
        Shortcut used to get a contained operation by name.
        @param name: An operation name.
        @type name: str
        @return: The named operation.
        @rtype: Operation
        @raise L{MethodNotFound}: When not found.
        """
        try:
            return self.operations[name]
        except Exception, e:
            raise MethodNotFound(name)
                
    def __gt__(self, other):
        return isinstance(other, (Import, Schema, Message))


class Binding(NamedObject):
    """
    Represents <binding/>
    @ivar operations: A list of contained operations.
    @type operations: list
    """

    def __init__(self, root, definitions):
        """
        @param root: An XML root element.
        @type root: L{Element}
        @param definitions: A definitions object.
        @type definitions: L{Definitions}
        """
        NamedObject.__init__(self, root, definitions)
        self.operations = {}
        self.type = root.get('type')
        sr = root.getChild('binding')
        soap = SOFactory.object('SOAP')
        self.soap = soap
        self.soap.style = sr.get('style', default='document')
        self.add_operations(self.root)
        
    def add_operations(self, root):
        """ Add <operation/> children """
        for c in root.getChildren('operation'):
            op = SOFactory.object('Operation')
            op.name = c.get('name')
            sr = c.getChild('operation')
            soap = SOFactory.object('SOAP')
            soap.action = '"%s"' % sr.get('soapAction', default='')
            soap.style = sr.get('style', default=self.soap.style)
            soap.input = SOFactory.object('Input')
            soap.input.body = SOFactory.object('Body')
            soap.output = SOFactory.object('Output')
            soap.output.body = SOFactory.object('Body')
            op.soap = soap
            input = c.getChild('input')
            soapbody = input.getChild('body')
            if soapbody is None:
                soap.input.body.use = 'literal'
            else:
                soap.input.body.use = soapbody.get('use', default='literal')
            output = c.getChild('output')
            soapbody = output.getChild('body')
            if soapbody is None:
                soap.output.body.use = 'literal'
            else:
                soap.output.body.use = soapbody.get('use', default='literal')
            self.operations[op.name] = op
            
    def resolve(self, definitions):
        """
        Resolve named references to other WSDL objects.
        @param definitions: A definitions object.
        @type definitions: L{Definitions}
        """
        ref = qualified_reference(self.type, self.root, wsdlns)
        port_type = definitions.port_types.get(self.asqname(ref))
        if port_type is None:
            raise Exception("portType '%s', not-found" % self.type)
        else:
            self.type = port_type
            
    def operation(self, name):
        """
        Shortcut used to get a contained operation by name.
        @param name: An operation name.
        @type name: str
        @return: The named operation.
        @rtype: Operation
        @raise L{MethodNotFound}: When not found.
        """
        try:
            return self.operations[name]
        except:
            raise MethodNotFound(name)
            
    def __gt__(self, other):
        return ( not isinstance(other, Service) )


class Service(NamedObject):
    """
    Represents <service/>.
    @ivar port: The contained port.
    @type port: Port
    """
    
    def __init__(self, root, definitions):
        """
        @param root: An XML root element.
        @type root: L{Element}
        @param definitions: A definitions object.
        @type definitions: L{Definitions}
        """
        NamedObject.__init__(self, root, definitions)
        self.port = SOFactory.object('Port')
        port = root.getChild('port')
        self.port.name = port.get('name')
        self.port.binding = port.get('binding')
        address = port.getChild('address')
        self.port.location = address.get('location').encode('utf-8')
        
    def resolve(self, definitions):
        """
        Resolve named references to other WSDL objects.
        @param definitions: A definitions object.
        @type definitions: L{Definitions}
        """
        ref = qualified_reference(self.port.binding, self.root, wsdlns)
        binding = definitions.bindings.get(self.asqname(ref))
        if binding is None:
            raise Exception("binding '%s', not-found" % self.port.binding)
        else:
            self.port.binding = binding
        
    def __gt__(self, other):
        return True

