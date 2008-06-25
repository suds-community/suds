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
from suds.sax import Parser, Element, Namespace
from suds.sudsobject import Object
from suds.bindings.marshaller import Marshaller
from suds.bindings.unmarshaller import Unmarshaller
from suds.schema import Query, qualified_reference

log = logger(__name__)

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
    
    def use_encoded(self):
        """ set the input message encoding to "encoded" """
        self.encoded = True

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
            method.append(self.param(method_name, pdef, arg))
            n += 1
        env.promotePrefixes()
        return str(env)
    
    def get_reply(self, method, msg):
        """extract the content from the specified soap reply message"""
        replyroot = self.parser.parse(string=msg)
        soapenv = replyroot.getChild('Envelope')
        soapbody = soapenv.getChild('Body')
        nodes = soapbody[0].children
        if self.returns_collection(method):
            list = []
            for node in nodes:
                list.append(self.unmarshal(node, method))
            return list
        if len(nodes) > 0:
            return self.unmarshal(nodes[0], method)
        return None
    
    def get_fault(self, msg):
        """extract the fault from the specified soap reply message"""
        faultroot = self.parser.parse(string=msg)
        soapenv = faultroot.getChild('Envelope')
        soapbody = soapenv.getChild('Body')
        fault = soapbody.getChild('Fault')
        p = self.unmarshal(fault)
        if self.faults:
            raise WebFault(unicode(p))
        else:
            return p.detail
                    
    def unmarshal(self, node, method=None):
        """unmarshal the specified node into a object"""
        result = None
        if len(node.children) > 0:
            if method is not None:
                type = self.returned_type(method)
                result = \
                    self.unmarshaller.typed.process(node, type)
            else:
                result = \
                    self.unmarshaller.basic.process(node)
        else:
            result = node.text
        return result
    
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
        env = Element('%s:Envelope' % envns[0], ns=envns)
        env.addPrefix(encns[0], encns[1])
        env.addPrefix(Namespace.xsins[0], Namespace.xsins[1])
        env.append(header)
        env.append(body)
        return env
    
    def header(self, headers):
        """ get soap header """
        hdr = Element('%s:Header' % envns[0], ns=envns)
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
        body = Element('%s:Body' % envns[0])
        body.addPrefix(ns[0], ns[1])
        body.append(method)
        return body
    
    def method(self, name):
        """get method fragment"""
        prefix = self.wsdl.tns[0]
        method = Element('%s:%s' % (prefix, name))
        return method
    
    def part_refattr(self):
        """
        Get the part attribute that defines the part's I{type}.
        @return: An attribute name.
        @rtype: basestring 
        """
        pass
    
    def part_types(self, method, input=True):
        """
        Get a list of I{parameter definitions} defined for the specified method.
        Each I{parameter definition} is a tuple: (I{name}, L{schema.SchemaProperty})
        @param method: The I{name} of a method.
        @type method: str
        @param input: Defines input/output message.
        @type input: boolean
        @return:  A list of parameter definitions
        @rtype: [I{definition},]
        """
        result = []
        for p in self.wsdl.get_parts(method, input):
            ref = p.get(self.part_refattr())
            qref = qualified_reference(ref, p, self.wsdl.tns)
            query = Query(qref)
            pt = self.schema.find(query)
            if pt is None:
                raise TypeNotFound(method)
            if input:
                result.append((p.get('name'), pt))
            else:
                result.append(pt)
        return result
    
    def param_defs(self, method):
        """
        Get parameter definitions.
        @param method: A method name.
        @type method: basestring
        @return: A collection of parameter definitions
        @rtype: [(str, L{schema.SchemaProperty}),..]
        """
        return self.part_types(method)
    
    def returns_collection(self, method):
        """
        Get whether the type defined for the method is a collection
        @param method: The I{name} of a method.
        @type method: str
        @rtype: boolean
        """
        result = False
        rt = self.returned_type(method)
        if rt is not None:
            result = rt.unbounded()
        return result
    
    def returned_type(self, method):
        """
        Get the referenced type returned by the I{method}.
        @param method: The name of a method.
        @type method: str
        @return: The name of the type return by the method.
        @rtype: str
        """
        result = None
        for rt in self.part_types(method, False):
            result = rt.resolve(nobuiltin=True)
            break
        return result
