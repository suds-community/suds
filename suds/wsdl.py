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
"""

from suds import *
from suds.sax import Parser, Element, splitPrefix
from suds.bindings.document import Document
from suds.bindings.rpc import RPC
from suds.xsd.schema import Schema, SchemaCollection
from urlparse import urlparse

log = logger(__name__)

#
# soap namespaces
#
soapencns = (None, 'http://schemas.xmlsoap.org/soap/encoding/')
soapwsdlns = (None, 'http://schemas.xmlsoap.org/wsdl/')


class WSDL:
    """
    a web services definition language inspection object
    """
    
    def __init__(self, url):
        self.url = url
        try:
            log.debug('reading wsdl at: %s ...', url)
            self.root = Parser().parse(url=url).root()
            self.tns = self.__tns()
            self.schema = self.__get_schema()
            log.debug('parsed content:\n%s', unicode(self.root))
        except Exception, e:
            log.exception(e)
            raise e
        self.bindings =dict(
            document=Document(self),
            rpc=RPC(self))
           
    def __tns(self):
        """get the target namespace defined in the wsdl"""
        tns = self.root.get('targetNamespace')
        prefix = self.root.findPrefix(tns)
        ns = (prefix, tns)
        if ns[0] is None:
            log.warn('tns (%s), not mapped to a prefix', tns)
        return ns
    
    def __get_schema(self):
        """ get a collective schema of all <schema/> nodes """
        filter = \
            set([soapencns[1], soapwsdlns[1]])
        container = SchemaCollection(self, filter)
        for root in self.root.childrenAtPath('types/schema'):
            container.add(root)
        if not len(container): # empty
            root = Element.buildPath(self.root, 'types/schema')
            container.add(root)
        container.load()
        log.debug('schema (container):\n%s', container)
        return container
        
    def get_binding(self, method):
        """ get the binding object """
        binding = None
        style = self.get_binding_style(method)
        binding = self.bindings.get(style, None)
        if binding is None:
            raise Exception('style (%s), not-supported' % style)
        use = self.get_input_encoding(method)
        if use == 'literal':
            binding.use_literal()
        elif use == 'encoded':
            binding.use_encoded()
        else:
            raise Exception('%s: use(%s), not-supported' % (method, use))
        return binding 
        
    def get_binding_style(self, method):
        """ get the binding style """
        binding = self.root.childAtPath('binding/binding')
        style = binding.get('style', default='document')
        for operation in self.root.childrenAtPath('binding/operation'):
            if method == operation.get('name'):
                operation = operation.getChild('operation')
                style = operation.get('style', default=style)
                break
        return style
    
    def get_input_encoding(self, method):
        """ get an operation's encoding @use """
        for operation in self.root.childrenAtPath('binding/operation'):
            if method == operation.get('name'):
                body = operation.childAtPath('input/body')
                log.debug('input encoding for (%s) found as (%s)', method, body)
                return body.get('use')
        return None
    
    def get_soap_action(self, method):
        """ get an operation's soap action @soapAction """
        action = ''
        for operation in self.root.childrenAtPath('binding/operation'):
            if method == operation.get('name'):
                operation = operation.getChild('operation')
                action = operation.get('soapAction', default='')
        return '"%s"' % action

    def get_location(self):
        """get the location of the service defined in the wsdl"""
        port_address = self.root.childAtPath('service/port/address')
        return port_address.get('location')
    
    def get_servicename(self):
        """get the name of the serivce defined in the wsdl"""
        service = self.root.getChild('service')
        return service.get('name')
    
    def get_operation(self, name):
        """get an operation definition by name"""
        for op in self.root.childrenAtPath('portType/operation'):
            if name == op.get('name'):
                log.debug('operation by name (%s) found:\n%s', name, op)
                return op
        return None
    
    def get_operations(self):
        """get a list of operations provided by the service"""
        return self.root.childrenAtPath('portType/operation')

    def get_message(self, name):
        """get the definition of a specified message by name"""
        name = splitPrefix(name)[1]
        for m in self.root.getChildren('message'):
            if name == m.get('name'):
                log.debug('message by name (%s) found:\n%s', name, m)
                return m
        return None
    
    def get_parts(self, method, input=True):
        """ get message parts by name and input/output """
        result = []
        operation = self.get_operation(method)
        if operation is None:
            raise MethodNotFound(method)
        if input:
            iotag = 'input'
        else:
            iotag = 'output'
        mp = operation.getChild(iotag)
        if mp is not None:
            msg = self.get_message(mp.get('message'))
            result = msg.getChildren('part')
        return result
    
    def __str__(self):
        return unicode(self).encode('utf-8')
    
    def __unicode__(self):
        return unicode(self.root.str())
