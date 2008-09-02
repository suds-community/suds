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
from suds.xsd.query import Query

log = getLogger(__name__)

docfmt = """
<SOAP-ENV:Envelope xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/"
      xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"
      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <SOAP-ENV:Header/>
    %s
    %s
    %s
    %s
    %s
</SOAP-ENV:Envelope>
"""

encns = ('SOAP-ENC', 'http://schemas.xmlsoap.org/soap/encoding/')
envns = ('SOAP-ENV', 'http://schemas.xmlsoap.org/soap/envelope/')


class Binding:
    """ The soap binding base class """

    def __init__(self, wsdl):
        self.wsdl = wsdl
        self.schema = wsdl.schema
        self.faults = True
        self.parser = Parser()
        self.unmarshaller = Unmarshaller(self.schema)
        self.marshaller = Marshaller(self.schema)
        self.encoded = False
        
    def use_literal(self):
        """ set the input message encoding to "literal" """
        self.encoded = False
        return self
    
    def use_encoded(self):
        """ set the input message encoding to "encoded" """
        self.encoded = True
        return self

    def get_message(self, method_name, args, soapheaders):
        """get the soap message for the specified method and args"""
        method = self.method(method_name)
        body = self.body(method)
        header = self.header(soapheaders)
        env = self.envelope(body, header)
        ptypes = self.param_defs(method_name)
        n = 0
        for arg in args:
            if n == len(ptypes): break
            pdef = ptypes[n]
            p = self.param(method_name, pdef, arg)
            if p is not None:
                method.append(p)
            n += 1
        env.promotePrefixes()
        return str(env)
    
    def get_reply(self, method, msg):
        """extract the content from the specified soap reply message"""
        replyroot = self.parser.parse(string=msg)
        soapenv = replyroot.getChild('Envelope')
        soapbody = soapenv.getChild('Body')
        nodes = soapbody[0].children
        rtypes = self.returned_types(method)
        if len(rtypes) == 1 and rtypes[0].unbounded():
            return self.reply_list(rtypes[0], nodes)
        if len(nodes) > 1:
            return self.reply_composite(rtypes, nodes)
        if len(nodes) == 1:
            unmarshaller = self.unmarshaller.typed
            resolved = rtypes[0].resolve(nobuiltin=True)
            return unmarshaller.process(nodes[0], resolved)
        return None
    
    def reply_list(self, rt, nodes):
        """ construct a 'list' reply """
        result = []
        resolved = rt.resolve(nobuiltin=True)
        unmarshaller = self.unmarshaller.typed
        for node in nodes:
            sobject = unmarshaller.process(node, resolved)
            result.append(sobject)
        return result
    
    def reply_composite(self, rtypes, nodes):
        """ construct a 'composite' reply """
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
    
    def get_fault(self, msg):
        """extract the fault from the specified soap reply message"""
        faultroot = self.parser.parse(string=msg)
        soapenv = faultroot.getChild('Envelope')
        soapbody = soapenv.getChild('Body')
        fault = soapbody.getChild('Fault')
        unmarshaller = self.unmarshaller.basic
        p = unmarshaller.process(fault)
        if self.faults:
            raise WebFault(p)
        else:
            return p.detail
    
    def param(self, method, pdef, object):
        """encode and return the specified object within the named root tag"""
        if self.encoded:
            marshaller = self.marshaller.encoded
        else:
            marshaller = self.marshaller.literal
        if isinstance(object, (Object, dict)):
            return marshaller.process(pdef[0], object, pdef[1])
        if isinstance(object, (list, tuple)):
            tags = []
            for item in object:
                tags.append(self.param(method, pdef, item))
            return tags
        return marshaller.process(pdef[0], object, pdef[1])
            
    def envelope(self, body, header):
        """ get soap envelope """
        env = Element('Envelope', ns=envns)
        env.addPrefix(encns[0], encns[1])
        env.addPrefix(Namespace.xsins[0], Namespace.xsins[1])
        env.append(header)
        env.append(body)
        return env
    
    def header(self, headers):
        """ get soap header """
        hdr = Element('Header', ns=envns)
        if not isinstance(headers, (list,tuple)):
            headers = (headers,)
        if self.encoded:
            marshaller = self.marshaller.encoded
        else:
            marshaller = self.marshaller.literal
        for h in headers:
            tag = h.__class__.__name__
            if isinstance(h, Object):
                value = h
                type = h.__metadata__.__type__
                node = marshaller.process(tag, value, type)
                hdr.append(node)
            else:
                log.error('soapheader (%s) must be Object', tag)
        return hdr
    
    def body(self, method):
        """ get soap envelope body """
        ns = self.wsdl.tns
        body = Element('Body', ns=envns)
        body.append(method)
        return body
    
    def part_types(self, method, input=True):
        """
        Get a list of I{parameter definitions} defined for the specified method.
        Each I{parameter definition} is a tuple: (I{name}, L{xsd.sxbase.SchemaObject})
        @param method: The I{name} of a method.
        @type method: str
        @param input: Defines input/output message.
        @type input: boolean
        @return:  A list of parameter definitions
        @rtype: [I{definition},]
        """
        result = []
        method = self.wsdl.method(method)
        if input:
            parts = method.message.input.parts
        else:
            parts = method.message.output.parts
        for p in parts:
            qref = p.xsref()
            query = Query(qref)
            pt = query.execute(self.schema)
            if pt is None:
                raise TypeNotFound(qref)
            if input:
                result.append((p.name, pt))
            else:
                result.append(pt)
        return result
    
    def param_defs(self, method):
        """
        Get parameter definitions.
        @param method: A method name.
        @type method: basestring
        @return: A collection of parameter definitions
        @rtype: [(str, L{xsd.sxbase.SchemaObject}),..]
        """
        return self.part_types(method)
    
    def returned_types(self, method):
        """
        Get the referenced type returned by the I{method}.
        @param method: The name of a method.
        @type method: str
        @return: The name of the type return by the method.
        @rtype: [L{xsd.sxbase.SchemaObject}]
        """
        result = []
        for rt in self.part_types(method, False):
            result.append(rt)
        return result
