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
from suds.sax import Parser
from suds.property import Property
from builder import Builder

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

class Binding:
    """ The soap binding base class """

    def __init__(self, wsdl, faults):
        self.wsdl = wsdl
        self.schema = wsdl.get_schema()
        self.builder = Builder(self.schema)
        self.faults = faults
        self.log = logger('binding')
        self.parser = Parser()
        self.nil_supported = True
        
    def get_method_descriptions(self):
        """get a list of methods provided by this service"""
        list = []
        ops = self.wsdl.get_operations()
        for op in self.wsdl.get_operations():
            ptypes = self.get_ptypes(op.attribute('name'))
            params = ['%s{%s}' % (t[0], t[1]) for t in ptypes]
            m = '%s(%s)' % (op.attribute('name'), ', '.join(params))
            list.append(m)
        return list

    def get_message(self, method_name, *args):
        """get the soap message for the specified method and args"""
        body = self.body()
        ptypes = self.get_ptypes(method_name)
        m = self.method(method_name)
        p = 0
        params = '';
        for a in args:
            if p == len(ptypes): break
            tag = ptypes[p][0]
            if a is None:
                params += '<%s xsi:nil="true"/>' % tag
            else:
                params += self.param(method_name, tag, a)
            p += 1
        msg = docfmt % (body[0], m[0], params, m[1], body[1])
        return msg.encode('utf-8')
    
    def get_reply(self, method_name, msg):
        """extract the content from the specified soap reply message"""
        replyroot = self.parser.parse(string=msg)
        soapenv = replyroot.getChild('Envelope')
        soapbody = soapenv.getChild('Body')
        nodes = soapbody[0].children
        if self.returns_collection(method_name):
            list = []
            for node in nodes:
                list.append(self.translate_node(node))
            return list
        if len(nodes) > 0:
            return self.translate_node(nodes[0])
        return None
    
    def get_fault(self, msg):
        """extract the fault from the specified soap reply message"""
        faultroot = self.parser.parse(string=msg)
        soapenv = faultroot.getChild('Envelope')
        soapbody = soapenv.getChild('Body')
        fault = soapbody.getChild('Fault')
        p = self.translate_node(fault)
        if self.faults:
            raise WebFault(unicode(p))
        else:
            return p.detail
        
    def get_instance(self, typename, *args):
        """get an instance of an meta-object by type."""
        try:
            return self.builder.build(typename)
        except TypeNotFound, e:
            raise e
        except:
            raise BuildError(typename)
    
    def get_enum(self, name):
        """ get an enumeration """
        result = None
        type = self.schema.get_type(name)
        if type is not None:
            result = Property()
            for e in type.get_children():
                result.dict()[e.get_name()] = e.get_name()
        return result
                    
    def translate_node(self, node):
        """translate the specified node into a property object"""
        result = None
        if len(node.children) == 0:
            result = node.text
        else:
            result = self.unmarshaller.process(node)
        return result
    
    def param(self, method, name, object):
        """encode and return the specified property within the named root tag"""
        if isinstance(object, dict):
            return self.marshaller.process(name, object)
        if isinstance(object, (list,tuple)):
            tags = ''
            for item in object:
                tags += self.param(method, name, item)
            return tags 
        if isinstance(object, Property):
            return self.marshaller.process(name, object)
        return '<%s>%s</%s>' % (name, tostr(object), name)
        
    def body(self):
        """get the soap body fragment tag template"""
        return ('<SOAP-ENV:Body xmlns:tns="%s">' % self.wsdl.tns[1], '</SOAP-ENV:Body>')
    
    def method(self, name):
        """get method fragment"""
        return ('<tns:%s xsi:type="tns:%s">' % (name, name), '</tns:%s>' % name)