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
from suds.bindings.marshaller import Marshaller, Content
from suds.bindings.unmarshaller import Unmarshaller
from suds.bindings.multiref import MultiRef
from suds.xsd.query import TypeQuery, ElementQuery
from suds.xsd.sxbasic import Element as SchemaElement
from suds.options import Options

log = getLogger(__name__)

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
    @ivar options: A dictionary options.
    @type options: L{Options}
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
        """
        @param wsdl: A wsdl.
        @type wsdl: L{wsdl.Definitions}
        """
        self.wsdl = wsdl
        self.schema = wsdl.schema
        self.options = Options()
        self.parser = Parser()
        self.unmarshaller = Unmarshaller(self.schema)
        self.marshaller = Marshaller(self.schema)
        self.multiref = MultiRef()
        self.encoded = False

    def get_message(self, method, args, kwargs):
        """
        Get the soap message for the specified method, args and soapheaders.
        This is the entry point for creating the outbound soap message.
        @param method: The method being invoked.
        @type method: I{service.Method}
        @param args: A list of args for the method invoked.
        @type args: list
        @param kwargs: Named (keyword) args for the method invoked.
        @type kwargs: dict
        @return: The soap message.
        @rtype: str
        """

        content = self.headercontent(method)
        header = self.header(content)
        content = self.bodycontent(method, args, kwargs)
        body = self.body(content)
        env = self.envelope(header, body)
        body.normalizePrefixes()
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
        nodes = self.replycontent(method, soapbody)
        rtypes = self.returned_types(method)
        if len(rtypes) > 1:
            result = self.replycomposite(rtypes, nodes)
            return (replyroot, result)
        if len(rtypes) == 1:
            if rtypes[0].unbounded():
                result = self.replylist(rtypes[0], nodes)
                return (replyroot, result)
            if len(nodes):
                unmarshaller = self.unmarshaller.typed
                resolved = rtypes[0].resolve(nobuiltin=True)
                result = unmarshaller.process(nodes[0], resolved)
                return (replyroot, result)
        return (replyroot, None)
    
    def replylist(self, rt, nodes):
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
    
    def replycomposite(self, rtypes, nodes):
        """
        Construct a I{composite} reply.  This method is called when it has been
        detected that the reply has multiple root nodes.
        @param rtypes: A list of known return I{types}.
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
        composite = Factory.object('reply')
        for node in nodes:
            tag = node.name
            rt = dictionary.get(tag, None)
            if rt is None:
                if node.get('id') is None:
                    raise Exception('<%s/> not mapped to message part', tag)
                else:
                    continue
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
        Extract the fault from the specified soap reply.  If I{faults} is True, an
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
        if self.options.faults:
            raise WebFault(p, faultroot)
        return (faultroot, p.detail)
    
    def mkparam(self, method, pdef, object):
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
        if isinstance(object, (list, tuple)):
            tags = []
            for item in object:
                tags.append(self.mkparam(method, pdef, item))
            return tags
        content = Content(tag=pdef[0], value=object, type=pdef[1])
        return marshaller.process(content)
    
    def mkheader(self, method, hdef, object):
        """
        Builds a soapheader for the specified I{method} using the header
        definition (hdef) and the specified value (object).
        @param method: A method name.
        @type method: str
        @param hdef: A header definition.
        @type hdef: tuple: (I{name}, L{xsd.sxbase.SchemaObject})
        @param object: The header value.
        @type object: any
        @return: The parameter fragment.
        @rtype: L{Element}
        """
        if self.encoded:
            marshaller = self.marshaller.encoded
        else:
            marshaller = self.marshaller.literal
        if isinstance(object, (list, tuple)):
            tags = []
            for item in object:
                tags.append(self.mkheader(method, hdef, item))
            return tags
        content = Content(tag=hdef[0], value=object, type=hdef[1])
        return marshaller.process(content)
            
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
        env.addPrefix(Namespace.xsins[0], Namespace.xsins[1])
        env.append(header)
        env.append(body)
        return env
    
    def header(self, content):
        """
        Build the B{<Body/>} for an soap outbound message.
        @param content: The header content.
        @type content: L{Element}
        @return: the soap body fragment.
        @rtype: L{Element}
        """
        header = Element('Header', ns=envns)
        header.append(content)
        return header
    
    def headercontent(self, method):
        """
        Get the content for the soap I{Header} node.
        @param method: A service method.
        @type method: I{service.Method}
        @return: The xml content for the <body/>
        @rtype: [L{Element},..]
        """
        n = 0
        content = []
        wsse = self.options.wsse
        if wsse is not None:
            content.append(wsse.xml())
        headers = self.options.soapheaders
        if len(headers) == 0:
            return content
        if not isinstance(headers, (tuple,list,dict)):
            headers = (headers,)
        pts = self.headpart_types(method)
        if isinstance(headers, (tuple,list)):
            for header in headers:
                if isinstance(header, Element):
                    content.append(header)
                    continue
                if len(pts) == n: break
                h = self.mkheader(method, pts[n], header)
                ns = pts[n][1].namespace('ns0')
                h.setPrefix(ns[0], ns[1])
                content.append(h)
                n += 1
        else:
            for pt in pts:
                header = headers.get(pt[0])
                if header is None:
                    continue
                h = self.mkheader(method, pt, header)
                ns = pt[1].namespace('ns0')
                h.setPrefix(ns[0], ns[1])
                content.append(h)
        return content
    
    def body(self, content):
        """
        Build the B{<Body/>} for an soap outbound message.
        @param content: The body content.
        @type content: L{Element}
        @return: the soap body fragment.
        @rtype: L{Element}
        """
        body = Element('Body', ns=envns)
        body.append(content)
        return body
    
    def bodypart_types(self, method, input=True):
        """
        Get a list of I{parameter definitions} (pdef) defined for the specified method.
        Each I{pdef} is a tuple (I{name}, L{xsd.sxbase.SchemaObject})
        @param method: A service method.
        @type method: I{service.Method}
        @param input: Defines input/output message.
        @type input: boolean
        @return:  A list of parameter definitions
        @rtype: [I{pdef},]
        """
        result = []
        if input:
            parts = method.message.input.parts
        else:
            parts = method.message.output.parts
        for p in parts:
            if p.element is not None:
                query = ElementQuery(p.element)
            else:
                query = TypeQuery(p.type)
            pt = query.execute(self.schema)
            if pt is None:
                raise TypeNotFound(query.ref)
            if p.type is not None:
                pt = PartElement(p.name, pt)
            if input:
                if pt.name is None:
                    result.append((p.name, pt))
                else:
                    result.append((pt.name, pt))
            else:
                result.append(pt)
        return result
    
    def headpart_types(self, method, input=True):
        """
        Get a list of I{parameter definitions} (pdef) defined for the specified method.
        Each I{pdef} is a tuple (I{name}, L{xsd.sxbase.SchemaObject})
        @param method: A service method.
        @type method: I{service.Method}
        @param input: Defines input/output message.
        @type input: boolean
        @return:  A list of parameter definitions
        @rtype: [I{pdef},]
        """
        result = []
        if input:
            headers = method.soap.input.headers
        else:
            headers = method.soap.output.headers
        for header in headers:
            for p in header.message.parts:
                if p.element is not None:
                    query = ElementQuery(p.element)
                else:
                    query = TypeQuery(p.type)
                pt = query.execute(self.schema)
                if pt is None:
                    raise TypeNotFound(query.ref)
                if p.type is not None:
                    pt = PartElement(p.name, pt)
                if input:
                    if pt.name is None:
                        result.append((p.name, pt))
                    else:
                        result.append((pt.name, pt))
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
        for rt in self.bodypart_types(method, input=False):
            result.append(rt)
        return result


class PartElement(SchemaElement):
    """
    A part used to represent a message part when the part
    references a schema type and thus assumes to be an element.
    @ivar resolved: The part type.
    @type resolved: L{suds.xsd.sxbase.SchemaObject}
    """
    
    def __init__(self, name, resolved):
        """
        @param name: The part name.
        @type name: str
        @param resolved: The part type.
        @type resolved: L{suds.xsd.sxbase.SchemaObject}
        """
        root = Element('element', ns=Namespace.xsdns)
        SchemaElement.__init__(self, resolved.schema, root)
        self.__resolved = resolved
        self.name = name
        self.form_qualified = False
        
    def namespace(self, prefix=None):
        return Namespace.default
        
    def resolve(self, nobuiltin=False):
        if nobuiltin and self.__resolved.builtin():
            return self
        else:
            return self.__resolved
    