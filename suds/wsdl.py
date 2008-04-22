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
from suds.sax import Parser, Element, splitPrefix
from bindings.document import Document
from bindings.rpc import RPC
from schema import Schema, SchemaCollection
from urlparse import urlparse

class WSDL:
    """
    a web services definition language inspection object
    """
    
    def __init__(self, url):
        self.log = logger('wsdl')
        self.url = url
        try:
            self.log.debug('reading wsdl at: %s ...', url)
            self.root = Parser().parse(url=url).root()
            self.tns = self.__tns()
            self.log.debug('parsed content:\n%s', unicode(self.root))
        except Exception, e:
            self.log.exception(e)
            raise e
           
    def __tns(self):
        """get the target namespace defined in the wsdl"""
        uri = self.root.attribute('targetNamespace')
        prefix = self.root.findPrefix(uri)
        ns = (prefix, uri)
        if ns[0] is None:
            self.warn('tns (%s), not mapped to a prefix', uri)
        return ns
        
    def get_binding(self, method, faults):
        """ get the binding object """
        binding = None
        style = self.get_binding_style(method)
        if style == 'document':
            binding = Document(self, faults)
        elif style == 'rpc':
            binding = RPC(self, faults)
        else:
            raise Exception('binding (%s), not-supported' % style)
        use = self.get_input_encoding(method)
        if use == 'literal':
            binding.use_literal()
        elif use == 'encoded':
            binding.use_encoded()
        else:
            raise Exception('soap:body (%s), not-supported' % style)
        return binding 
        
    def get_binding_style(self, method):
        """ get the binding style """
        binding = self.root.childAtPath('binding/binding')
        style = binding.attribute('style', default='document')
        for operation in self.root.childrenAtPath('binding/operation'):
            if method == operation.attribute('name'):
                operation = operation.getChild('operation')
                style = operation.attribute('style', default=style)
                break
        return style
    
    def get_input_encoding(self, method):
        """ get an operation's encoding @use """
        for operation in self.root.childrenAtPath('binding/operation'):
            if method == operation.attribute('name'):
                body = operation.childAtPath('input/body')
                self.log.debug('input encoding for (%s) found as (%s)', method, body)
                return body.attribute('use')
        return None
    
    def get_soap_action(self, method):
        """ get an operation's soap action @soapAction """
        for operation in self.root.childrenAtPath('binding/operation'):
            if method == operation.attribute('name'):
                operation = operation.getChild('operation')
                return operation.attribute('soapAction')
        return 'none'

    def get_location(self):
        """get the location of the service defined in the wsdl"""
        port_address = self.root.childAtPath('service/port/address')
        return port_address.attribute('location')
    
    def get_schema(self):
        """ get a collective schema of all <schema/> nodes """
        container = SchemaCollection(self)
        for sr in self.root.childrenAtPath('types/schema'):
            schema = Schema(sr, self.url, container)
            container.append(schema)
        self.log.debug('schema (container):\n', container)
        return container
    
    def get_servicename(self):
        """get the name of the serivce defined in the wsdl"""
        service = self.root.getChild('service')
        return service.attribute('name')
    
    def get_operation(self, name):
        """get an operation definition by name"""
        for op in self.root.childrenAtPath('portType/operation'):
            if name == op.attribute('name'):
                self.log.debug('operation by name (%s) found:\n%s', name, op)
                return op
        return None
    
    def get_operations(self):
        """get a list of operations provided by the service"""
        return self.root.childrenAtPath('portType/operation')

    def get_message(self, name):
        """get the definition of a specified message by name"""
        name = splitPrefix(name)[1]
        for m in self.root.getChildren('message'):
            if name == m.attribute('name'):
                self.log.debug('message by name (%s) found:\n%s', name, m)
                return m
        return None
            
    def mapped_prefixes(self):
        """ get a list of mapped prefixes """
        return self.root.flattened_nsprefixes()
    
    def __str__(self):
        return unicode(self).encode('utf-8')
    
    def __unicode__(self):
        return unicode(self.root.str())
