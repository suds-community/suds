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
from suds.sax import Parser, Element
from bindings.document import DocumentBinding
from bindings.rpc import RPCBinding
from schema import Schema
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
            self.purgePrefixes()
            self.log.debug('parsed content:\n%s', str(self.root))
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
        return self.root.childAtPath('binding/binding').attribute('style')

    def get_location(self):
        """get the location of the service defined in the wsdl"""
        result = []
        url = self.root.childAtPath('service/port/address').attribute('location')
        parts = urlparse(url)
        result.append(parts[1].split(':')[0])
        result.append(parts[1].split(':')[1])
        result.append(parts[2])
        return result
    
    def get_tns(self):
        """get the target namespace defined in the wsdl"""
        return self.root.attribute('targetNamespace')
    
    def get_schema(self):
        result = Element('schema')
        for schema in self.root.childrenAtPath('types/schema'):
            result.append(schema.detachChildren())
        self.log.info(result)
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
        for m in self.root.getChildren('message'):
            if name == m.attribute('name'):
                self.log.debug('message by name (%s) found:\n%s', name, m)
                return m
        return None
    
    def purgePrefixes(self, node=None):
        """ purge prefixes from attribute values """
        if node is None:
            node = self.root
        for a in node.attributes:
            if a.prefix != 'xmlns' and \
                    a.name in ['name', 'type', 'element', 'message']:
                a.value = node.splitPrefix(a.value)[1]
        for child in node.children:
            self.purgePrefixes(child)
    
    def __str__(self):
        return str(self.root)
