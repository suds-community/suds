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
from bindings.literal.document import Document
from bindings.literal.rpc import RPC
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
        
    def get_binding(self, faults):
        """ get the binding object """
        style = self.get_binding_style()
        if style == 'document':
            self.log.debug('document/literal binding detected')
            return Document(self, faults)
        elif style == 'rpc':
            self.log.debug('rpc/literal binding detected')
            return RPC(self, faults)
        self.log.debug('document binding (%s), not-supported', style)
        return None 
        
    def get_binding_style(self):
        """ get the binding style """
        return self.root.childAtPath('binding/binding').attribute('style')

    def get_location(self):
        """get the location of the service defined in the wsdl"""
        return self.root.childAtPath('service/port/address').attribute('location')
    
    def get_schema(self):
        """ get a collective schema of all <schema/> nodes """
        result = SchemaCollection()
        for sr in self.root.childrenAtPath('types/schema'):
            schema = Schema(sr, self.url)
            result.append(schema)
        self.log.debug('aggregated schema:\n', result)
        return result
    
    def get_servicename(self):
        """get the name of the serivce defined in the wsdl"""
        return self.root.getChild('service').attribute('name')
    
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
