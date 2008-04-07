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
from suds.bindings.binding import Binding
from suds.bindings.literal.base import Literal


class Document(Literal):
    
    """
    Document/Literal binding style.
    """

    def __init__(self, wsdl, faults=True):
        """constructor """
        Literal.__init__(self, wsdl, faults)
        
    def get_ptypes(self, method):
        """get a list of parameter types defined for the specified method"""
        params = []
        operation = self.wsdl.get_operation(method)
        if operation is None:
            raise NoSuchMethod(method)
        input = operation.getChild('input')
        msg = self.wsdl.get_message(input.attribute('message'))
        for p in msg.getChildren('part'):
            ref = p.attribute('element')
            type = self.schema.get_type(ref)
            if type is None:
                raise TypeNotFound(ref)
            for e in type.get_children():
                params.append((e.get_name(), e.get_type()))
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
            ref = p.attribute('element')
            type = self.schema.get_type(ref)
            elements = type.get_children(empty=[])
            result = ( len(elements) > 0 and elements[0].unbounded() )
            break
        return result