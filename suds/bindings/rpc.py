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
from suds.schema import XBuiltin
from suds.bindings.binding import Binding


class RPC(Binding):
    
    """
    RPC/Literal binding style.
    """

    def __init__(self, wsdl, faults=True):
        """constructor """
        Binding.__init__(self, wsdl, faults)
        
    def get_ptypes(self, method):
        """get a list of parameter types defined for the specified method"""
        params = []
        operation = self.wsdl.get_operation(method)
        if operation is None:
            raise NoSuchMethod(method)
        input = operation.getChild('input')
        msg = self.wsdl.get_message(input.attribute('message'))
        for p in msg.getChildren('part'):
            ref = p.attribute('type')
            if self.schema.builtin(ref):
                xsb = XBuiltin(self.schema, ref)
                params.append((p.attribute('name'), xsb))
                continue
            type = self.schema.find(ref)
            if type is None:
                raise TypeNotFound(ref)
            params.append((p.attribute('name'), type))
        self.log.debug('parameters %s for method %s', tostr(params), method)
        return params

    def returns_collection(self, method):
        """ get whether the type defined for the specified method is a collection """
        operation = self.wsdl.get_operation(method)
        if operation is None:
            raise NoSuchMethod(method)
        msg = self.wsdl.get_message(operation.getChild('output').attribute('message'))
        result = False
        for p in msg.getChildren('part'):
            ref = p.attribute('type')
            if self.schema.custom(ref):
                type = self.schema.find(ref)
                elements = type.get_children(empty=[])
                result = ( len(elements) > 0 and elements[0].unbounded() )
            break
        return result