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
from urlparse import urlparse
from propertyreader import DocumentReader, Hint
from bindings.document import DocumentBinding
from bindings.rpc import RPCBinding
from schema import Schema

class WSDL:
    """
    a web services definition language inspection object
    """

    hint = Hint()
    hint.sequences = [
      '/definitions/message', 
      '/definitions/message/part',
      '/definitions/portType/operation',
      '/definitions/types/schema',]
    
    hint.sequences += Schema.hint.sequences
    
    def __init__(self, url):
        self.log = logger('wsdl')
        self.url = url
        try:
            self.log.debug('opening %s', url)
            self.properties = DocumentReader(hint=WSDL.hint).read(url=url)
            self.log.debug(str(self.properties))
        except Exception, e:
            self.log.exception(e)
            raise e
        
    def get_binding(self, faults):
        style = self.get_binding_style()
        if style == 'document':
            self.log.debug('document binding detected')
            return DocumentBinding(self, faults)
        elif style == 'rpc':
            self.log.info('document binding detected')
            return RPCBinding(self, faults)
        self.log.debug('document binding (%s), not-supported', style)
        return None 
        
    def get_binding_style(self):
        return self.properties.binding.binding._style

    def get_location(self):
        """get the location of the service defined in the wsdl"""
        result = []
        url = self.properties.service.port.address._location
        parts = urlparse(url)
        result.append(parts[1].split(':')[0])
        result.append(parts[1].split(':')[1])
        result.append(parts[2])
        return result
    
    def get_tns(self):
        """get the target namespace defined in the wsdl"""
        return self.properties._targetNamespace
    
    def definitions_schema(self):
        tns = self.get_tns()
        for schema in self.properties.types.schema:
            if schema._targetNamespace == tns:
                return schema
        return Property()
    
    def get_servicename(self):
        """get the name of the serivce defined in the wsdl"""
        return self.properties.service._name
    
    def get_operation(self, name):
        """get an operation definition by name"""
        for o in self.properties.portType.operation:
            if o._name == self.stripns(name):
                self.log.debug('operation by name (%s) found:\n%s', name, o)
                return o
        return None
    
    def get_operations(self):
        """get a list of operations provided by the service"""
        return self.properties.portType.operation

    def get_message(self, name):
        """get the definition of a specified message by name"""
        for m in self.properties.message:
            if m._name == self.stripns(name):
                self.log.debug('message by name (%s) found:\n%s', name, m)
                return m
        return None
    
    def stripns(self, name):
        """strip the namespace {} prefix from the specified tag name"""
        if name is not None:
            parts = name.split(':')
            if len(parts) > 1:
                return parts[1]
        return name
    
    def __str__(self):
        return str(self.properties)
