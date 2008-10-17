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
Provides classes for (WS) SOAP bindings.
"""

from logging import getLogger
from suds import *
from suds.sax import Namespace
from suds.sax.parser import Parser
from suds.sax.element import Element
from suds.sudsobject import Factory, Object
from suds.bindings.marshaller import Marshaller
from suds.bindings.unmarshaller import Unmarshaller
from suds.xsd.query import TypeQuery, ElementQuery
from suds.bindings.multiref import MultiRef

log = getLogger(__name__)

encns = ('SOAP-ENC', 'http://schemas.xmlsoap.org/soap/encoding/')
envns = ('SOAP-ENV', 'http://schemas.xmlsoap.org/soap/envelope/')


class Binding:
    """
    The soap binding class used to process outgoing and imcoming
    soap messages per the WSDL port binding.
    @cvar replyfilter: The reply filter function.
    @type replyfilter: (lambda s,r: r)
    @ivar wsdl: The wsdl.
    @type wsdl: L{suds.wsdl.Definitions}
    @ivar schema: The collective schema contained within the wsdl.
    @type schema: L{xsd.schema.Schema}
    @ivar faults: The faults flag used to indicate whether a web fault should raise
        an exception or that all results are returned in a tuple (http-code, result).
    @type faults: boolean
    @ivar parser: A sax parser.
    @type parser: L{suds.sax.parser.Parser}
    @ivar unmarshaller: An unmarshaller used to generate an L{Object}
        representation of received soap messages.
    @type unmarshaller: L{Unmarshaller}
    @ivar marshaller: A marshaller used to generate soap messages from
        python L{Object}s.
    @type marshaller: L{Marshaller}
    @ivar encoded: The I{usr=literal} vs I{use=encoded} flag defines with version
        of the I{marshaller} and I{unmarshaller} should be used to encode/decode
        soap messages.
    @type encoded: boolean
    """
    
    replyfilter = (lambda s,r: r)

    def __init__(self, wsdl):
        self.wsdl = wsdl
        self.schema = wsdl.schema
        self.faults = True
        self.parser = Parser()
        self.unmarshaller = Unmarshaller(self.schema)
        self.marshaller = Marshaller(self.schema)
        self.multiref = MultiRef()
        self.encoded = False
        
    def use_literal(self):
        """
        Set the input message encoding to I{literal} by setting the
        L{self.encoded} flag = True.
        @return: self
        @rtype: L{Binding}
        """
        self.encoded = False
        return self
    
    def use_encoded(self):
        """
        Set the input message encoding to I{encoded} by setting the 
        L{self.encoded} flag = False.
        @return: self
        @rtype: L{Binding}
        """
        self.encoded = True
        return self

    def get_message(self, method, args, soapheaders):
        """
        Get the soap message for the specified method, args and soapheaders.
        This is the entry point for creating the outbound soap message.
        @param method: The method being invoked.
        @type method: I{service.Method}
        @param args: A I{list} of method arguments (parameters).
        @type args: list
        @param soapheaders: A list of objects to be encoded as soap-headers.
        @type soapheaders: list
        @return: The soap message.
        @rtype: str
        """
        content = self.headercontent(method, soapheaders)
        header = self.header(content)
        content = self.bodycontent(method, args)
        body = self.body(content)
        env = self.envelope(header, body)
        env.promotePrefixes()
        return env
    
    def get_reply(self, method, reply):
        """
        Process the I{reply} for the specified I{method} by sax parsing the I{reply}
        and then unmarshalling into python object(s).
        @param method: The name of the invoked method.
        @type method: str
        @param reply: The reply XML received after invoking the specified method.
        @type reply: str
        @return: The unmarshalled reply.  The returned value is an L{Object} for a
            I{list} depending on whether the service returns a single object or a 
            collection.
        @rtype: tuple ( L{Element}, L{Object} )
        """
        reply = self.replyfilter(reply)
        replyroot = self.parser.parse(string=reply)
        soapenv = replyroot.getChild('Envelope')
        soapenv.promotePrefixes()
        soapbody = soapenv.getChild('Body')
        soapbody = self.multiref.process(soapbody)
        nodes = soapbody[0].children
        rtypes = self.returned_types(method)
        if len(rtypes) == 1 and rtypes[0].unbounded():
            result = self.reply_list(rtypes[0], nodes)
            return (replyroot, result)
        if len(nodes) > 1:
            result = self.reply_composite(rtypes, nodes)
            return (replyroot, result)
        if len(nodes) == 1:
            unmarshaller = self.unmarshaller.typed
            resolved = rtypes[0].resolve(nobuiltin=True)
            result = unmarshaller.process(nodes[0], resolved)
            return (replyroot, result)
        return (replyroot, None)
    
    def reply_list(self, rt, nodes):
        """
        Construct a I{list} reply.  This mehod is called when it has been detected
        that the reply is a list.
        @param rt: The return I{type}.
        @type rt: L{suds.xsd.sxbase.SchemaObject}
        @param nodes: A collection of XML nodes.
        @type nodes: [L{Element},...]
        @return: A list of I{unmarshalled} objects.
        @rtype: [L{Object},...]
        """
        result = []
        resolved = rt.resolve(nobuiltin=True)
        unmarshaller = self.unmarshaller.typed
        for node in nodes:
            sobject = unmarshaller.process(node, resolved)
            result.append(sobject)
        return result
    
    def reply_composite(self, rtypes, nodes):
        """
        Construct a I{composite} reply.  This method is called when it has been
        detected that the reply is a composite (object).
        @param rtypes: A list of legal return I{types}.
        @type rtypes: [L{suds.xsd.sxbase.SchemaObject},...]
        @param nodes: A collection of XML nodes.
        @type nodes: [L{Element},...]
        @return: The I{unmarshalled} composite object.
        @rtype: L{Object},...
        """
        dictionary = {}
        for rt in rtypes:
            dictionary[rt.name] = rt
        unmarshaller = self.unmarshaller.typed
        composite = Factory.object()
        for node in nodes:
            tag = node.name
            rt = dictionary.get(tag, None)
            if rt is None:
                raise Exception('tag (%s), not-found' % tag)
            resolved = rt.resolve(nobuiltin=True)
            sobject = unmarshaller.process(node, resolved)
            if rt.unbounded():
                value = getattr(composite, tag, None)
                if value is None:
                    value = []
                    setattr(composite, tag, value)
                value.append(sobject)
            else:
                setattr(composite, tag, sobject)
        return composite
    
    def get_fault(self, reply):
        """
        Extract the fault from the specified soap reply.  If L{self.faults} is True, an
        exception is raised.  Otherwise, the I{unmarshalled} fault L{Object} is
        returned.  This method is called when the server raises a I{web fault}.
        @param reply: A soap reply message.
        @type reply: str
        @return: A fault object.
        @rtype: tuple ( L{Element}, L{Object} )
        """
        reply = self.replyfilter(reply)
        faultroot = self.parser.parse(string=reply)
        soapenv = faultroot.getChild('Envelope')
        soapbody = soapenv.getChild('Body')
        fault = soapbody.getChild('Fault')
        unmarshaller = self.unmarshaller.basic
        p = unmarshaller.process(fault)
        if self.faults:
            raise WebFault(p, faultroot)
        return (faultroot, p.detail)
    
    def param(self, method, pdef, object):
        """
        Builds a parameter for the specified I{method} using the parameter
        definition (pdef) and the specified value (object).
        @param method: A method name.
        @type method: str
        @param pdef: A parameter definition.
        @type pdef: tuple: (I{name}, L{xsd.sxbase.SchemaObject})
        @param object: The parameter value.
        @type object: any
        @return: The parameter fragment.
        @rtype: L{Element}
        """
        if self.encoded:
            marshaller = self.marshaller.encoded
        else:
            marshaller = self.marshaller.literal
        if isinstance(object, (Object, dict)):
            return marshaller.process(object, pdef[1], pdef[0])
        if isinstance(object, (list, tuple)):
            tags = []
            for item in object:
                tags.append(self.param(method, pdef, item))
            return tags
        return marshaller.process(object, pdef[1], pdef[0])
            
    def envelope(self, header, body):
        """
        Build the B{<Envelope/>} for an soap outbound message.
        @param header: The soap message B{header}.
        @type header: L{Element}
        @param body: The soap message B{body}.
        @type body: L{Element}
        @return: The soap envelope containing the body and header.
        @rtype: L{Element}
        """
        env = Element('Envelope', ns=envns)
        env.addPrefix(encns[0], encns[1])
        env.addPrefix(Namespace.xsins[0], Namespace.xsins[1])
        env.append(header)
        env.append(body)
        return env
    
    def header(self, content):
        """
        Build the B{<Body/>} for an soap outbound message.
        @param method: The name of the method.
        @return: the soap body fragment.
        @rtype: L{Element}
        """
        header = Element('Header', ns=envns)
        header.append(content)
        return header
    
    def headercontent(self, method, headers):
        """
        Get the content for the soap I{Header} node.
        @param method: A service method.
        @type method: I{service.Method}
        @param headers: method parameter values
        @type headers: list
        @return: The xml content for the <body/>
        @rtype: [L{Element},..]
        """
        n = 0
        content = []
        if len(headers):
            pts = self.part_types(method, header=True)
            for header in headers:
                if len(pts) == n: break
                p = self.param(method, pts[n], header)
                if p is not None:
                    content.append(p)
                n += 1
        return content
    
    def body(self, content):
        """
        Build the B{<Body/>} for an soap outbound message.
        @param method: The name of the method.
        @return: the soap body fragment.
        @rtype: L{Element}
        """
        body = Element('Body', ns=envns)
        body.append(content)
        return body
    
    def part_types(self, method, input=True, header=False):
        """
        Get a list of I{parameter definitions} (pdef) defined for the specified method.
        Each I{pdef} is a tuple (I{name}, L{xsd.sxbase.SchemaObject})
        @param method: A service method.
        @type method: I{service.Method}
        @param input: Defines input/output message.
        @type input: boolean
        @param header: Defines if parts are for soapheader.
        @type header: boolean
        @return:  A list of parameter definitions
        @rtype: [I{pdef},]
        """
        result = []
        if input:
            if header:
                parts = method.soap.input.header.message.parts
            else:
                parts = method.message.input.parts
        else:
            if header:
                parts = method.soap.output.header.message.parts
            else:
                parts = method.message.output.parts
        for p in parts:
            if p.element is not None:
                query = ElementQuery(p.element)
            else:
                query = TypeQuery(p.type)
            pt = query.execute(self.schema)
            if pt is None:
                raise TypeNotFound(qref)
            if input:
                result.append((p.name, pt))
            else:
                result.append(pt)
        return result
    
    def returned_types(self, method):
        """
        Get the L{xsd.sxbase.SchemaObject} returned by the I{method}.
        @param method: A service method.
        @type method: I{service.Method}
        @return: The name of the type return by the method.
        @rtype: [I{rtype},..]
        """
        result = []
        for rt in self.part_types(method, input=False):
            result.append(rt)
        return result
