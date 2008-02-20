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
from binding import Binding
from suds.schema import Schema, Element
from suds.property import Property
from suds.propertyreader import DocumentReader, Hint
from suds.propertywriter import DocumentWriter
import re


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

class DocumentBinding(Binding):
    
    """
    a document literal binding style.
    """

    def __init__(self, wsdl, faults=True):
        Binding.__init__(self, wsdl, faults)
        self.schema = Schema(wsdl.get_schema())
        
    def get_ptypes(self, method):
        """get a list of parameter types defined for the specified method"""
        params = []
        operation = self.wsdl.get_operation(method)
        if operation is None:
            raise NoSuchMethod(method)
        input = operation.getChild('input')
        msg = self.wsdl.get_message(input.attribute('message'))
        for p in msg.getChildren('part'):
            type = self.schema.get_type(p.attribute('element'))
            if type is None:
                raise TypeNotFound(p.attribute('element'))
            for e in type.get_children():
                params.append((e.get_name(), e.get_type()))
        self.log.debug('parameters %s for method %s', str(params), method)
        return params
        
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
                params += self.param(tag, a)
            p += 1
        msg = docfmt % (body[0], m[0], params, m[1], body[1])
        return msg
    
    def get_reply(self, method_name, msg):
        """extract the content from the specified soap reply message"""
        replyroot = self.parser.parse(string=msg)
        reply = replyroot[0][1][0]
        nodes = reply.children
        if self.returns_collection(method_name):
            list = []
            for node in nodes:
                hint = ReplyHint(self, reply, node)
                list.append(self.translate_node(node, hint))
            return list
        if len(nodes) > 0:
            hint = ReplyHint(self, reply, nodes[0])
            return self.translate_node(nodes[0], hint)
        return None
    
    def get_fault(self, msg):
        """extract the fault from the specified soap reply message"""
        faultroot = self.parser.parse(string=msg)
        soapenv = faultroot.getChild('Envelope')
        soapbody = soapenv.getChild('Body')
        fault = soapbody.getChild('Fault')
        hint = Hint()
        p = self.translate_node(fault)
        if self.faults:
            raise WebFault(str(p))
        else:
            return p.detail
        
    def get_instance(self, typename, *args):
        """get an instance of an meta-object by type."""
        try:
            return self.schema.build(typename)
        except TypeNotFound, e:
            raise e
        except:
            raise BuildError(typename)
    
    def get_enum(self, name):
        result = None
        type = self.schema.get_type(name)
        if type is not None:
            result = Property()
            for e in type.get_children():
                result.dict()[e.get_name()] = e.get_name()
        return result
                    
    def translate_node(self, node, hint=Hint()):
        """translate the specified node into a property object"""
        result = None
        if len(node.children) == 0:
            result = node.text
        else:
            self.reader.set_hint(hint)
            result = self.reader.process(node)
        return result
    
    def param(self, name, object):
        """encode and return the specified property within the named root tag"""
        if isinstance(object, dict):
            return self.writer.tostring(name, object)
        if isinstance(object, list) or isinstance(object, tuple):
            tags = ''
            for item in object:
                tags += self.param(name, item)
            return tags 
        if isinstance(object, Property):
            return self.writer.tostring(name, object)
        return '<%s>%s</%s>' % (name, object, name)
        
    def body(self):
        """get the soap body fragment tag template"""
        return ('<SOAP-ENV:Body xmlns:tns="%s">' % self.wsdl.get_tns(), '</SOAP-ENV:Body>')
    
    def method(self, name):
        """get method fragment"""
        return ('<tns:%s xsi:type="tns:%s">' % (name, name), '</tns:%s>' % name)

    def returns_collection(self, method):
        """ get whether the  type defined for the specified method is a collection """
        operation = self.wsdl.get_operation(method)
        if operation is None:
            raise NoSuchMethod(method)
        msg = self.wsdl.get_message(operation.getChild('output').attribute('message'))
        result = False
        for p in msg.getChildren('part'):
            type = self.schema.get_type(p.attribute('element'))
            elements = type.get_children(empty=[])
            result = ( len(elements) > 0 and elements[0].unbounded() )
            break
        return result
    

class ReplyHint(Hint):
    """
    A dynamic hint used to process reply content.
    Performs a lookup to determine if the specified path references a collection.
    """
    
    def __init__(self, binding, reply, node):
        Hint.__init__(self)
        self.binding = binding
        self.log = binding.log
        self.reply = ''
        self.node = ''
        self.rtype = ''
        try:
            self.reply = reply.name
            self.node = node.name
            rtype = self.schema().get_type('.'.join([self.reply, self.node]))
            self.rtype = rtype.name
        except Exception, e:
            self.log.debug("failed: reply=(%s), node=(%s)", self.reply, self.node)
        
    def schema(self):
        """ get the binding's schema """
        return self.binding.schema

    def match_sequence(self, path):
        """ override the match_sequence method and lookup if the specified path is a sequence """
        result = False
        if not path.startswith('/'):
            return result
        try:
            parts = path[1:].split('/')
            if parts[0] == self.node:
                parts[0] = self.rtype
            path = '.'.join(parts)
            type = self.schema().get_type(path)
            result = type.unbounded()
        except:
            self.log.debug("match failed: reply=(%s)", path) 
        return result