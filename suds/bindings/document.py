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
import sys
if sys.version_info < (2,5):
    from lxml.etree import XML
else:
    from xml.etree.ElementTree import XML


docfmt = """
<SOAP-ENV:Envelope xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/"
  xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <SOAP-ENV:Header></SOAP-ENV:Header>
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
        self.schema = Schema(wsdl.definitions_schema())
        
    def get_ptypes(self, method):
        """get a list of parameter types defined for the specified method"""
        params = []
        operation = self.wsdl.get_operation(method)
        if operation is None:
            raise NoSuchMethod(method)
        msg = self.wsdl.get_message(operation.input._message)
        for p in msg.get(part=[]):
            type = self.schema.get_type(p._element)
            for e in type.get_children():
                params.append((e.get_name(), self.schema.stripns(e.get_type())))
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
            params += self.param(tag, a)
            p += 1
        msg = docfmt % (body[0], m[0], params, m[1], body[1])
        return msg
    
    def get_reply(self, method_name, msg):
        """extract the content from the specified soap reply message"""
        reply = XML(msg)[1][0]
        nodes = reply.getchildren()
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
        fault = XML(msg)[1][0]
        hint = Hint()
        p = self.translate_node(fault)
        if self.faults:
            raise WebFault(str(p.detail))
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
        if len(node) == 0:
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
                tags += '<%s>%s</%s>' % (name, item, name)
            return tags 
        if isinstance(object, Property):
            return self.writer.tostring(name, object.dict())
        return '<%s>%s</%s>' % (name, object, name)
        
    def body(self):
        """get the soap body fragment tag template"""
        return ('<SOAP-ENV:Body xmlns:ns1="%s">' % self.wsdl.get_tns(), '</SOAP-ENV:Body>')
    
    def method(self, name):
        """get method fragment"""
        return ('<ns1:%s xsi:type="ns1:%s">' % (name, name), '</ns1:%s>' % name)

    def returns_collection(self, method):
        """ get whether the  type defined for the specified method is a collection """
        operation = self.wsdl.get_operation(method)
        if operation is None:
            raise NoSuchMethod(method)
        msg = self.wsdl.get_message(operation.output._message)
        result = False
        for p in msg.get(part=[]):
            type = self.schema.get_type(p._element)
            elements = type.get_children(empty=[])
            result = ( len(elements) > 0 and elements[0].unbounded() )
            break
        return result
    
    def stripns(self, s):
        """strip the {} namespace prefix used by element tree"""
        return self.reader.stripns(s)



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
            self.reply = self.stripns(reply.tag)
            self.node = self.stripns(node.tag)
            rtype = self.schema().get_type('.'.join([self.reply, self.node]))
            self.rtype = rtype.__type__
        except Exception, e:
            self.log.debug("failed: reply=(%s), node=(%s)", self.reply, self.node)
        
    def stripns(self, s):
        """ strip the elementtree {} namespace prefix """
        return self.binding.reader.stripns(s)
        
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