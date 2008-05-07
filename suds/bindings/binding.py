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
from suds.sax import Parser, Element, xsins
from suds.sudsobject import Object
from suds.bindings.literal.marshaller import Marshaller as Literal
from suds.bindings.encoded.marshaller import Marshaller as Encoded
from unmarshaller import Unmarshaller

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

    def __init__(self, wsdl, **kwargs):
        self.wsdl = wsdl
        self.schema = wsdl.schema
        self.faults = kwargs.get('faults', True)
        self.log = logger('binding')
        self.parser = Parser()
        self.nil_supported = kwargs.get('nil_supported', True)
        self.marshaller = None
        self.unmarshaller = Unmarshaller(self)
        
    def use_literal(self):
        """ set the input message encoding to "literal" """
        self.marshaller = Literal(self)
    
    def use_encoded(self):
        """ set the input message encoding to "encoded" """
        self.marshaller = Encoded(self)

    def get_message(self, method_name, *args):
        """get the soap message for the specified method and args"""
        method = self.method(method_name)
        body = self.body(method)
        env = self.envelope(body)
        ptypes = self.get_ptypes(method_name)
        n = 0
        for arg in args:
            if n == len(ptypes): break
            pdef = ptypes[n]
            if arg is None:
                method.append(Element(pdef[0]).setnil())
            else:
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
                rt = self.returned_type(method)
                node.rename(rt)
            result = self.unmarshaller.process(node)
        else:
            result = node.text
        return result
    
    def param(self, method, pdef, object):
        """encode and return the specified object within the named root tag"""
        if isinstance(object, (Object, dict)):
            return self.marshaller.process(pdef, object)
        if isinstance(object, (list, tuple)):
            tags = []
            for item in object:
                tags.append(self.param(method, pdef, item))
            return tags
        return self.marshaller.process(pdef, object)
            
    def envelope(self, body=None):
        """ get soap envelope """
        env = Element('%s:Envelope' % envns[0], ns=envns)
        env.addPrefix(encns[0], encns[1])
        env.addPrefix(xsins[0], xsins[1])
        if body is not None:
            env.append(body)
        return env
    
    def body(self, method=None):
        """ get soap envelope body """
        ns = self.wsdl.tns
        body = Element('%s:Body' % envns[0])
        body.addPrefix(ns[0], ns[1])
        if method is not None:
            body.append(method)
        return body
    
    def method(self, name):
        """get method fragment"""
        prefix = self.wsdl.tns[0]
        method = Element('%s:%s' % (prefix, name))
        return method
