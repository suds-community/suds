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
from suds.schema import qualified_reference

log = logger(__name__)

class RPC(Binding):
    
    """
    RPC/Literal binding style.
    """

    def __init__(self, wsdl, **kwargs):
        """
        @param wsdl: A WSDL object.
        @type wsdl: L{suds.wsdl.WSDL}
        @param kwargs: keyword arguments.
        @type kwargs: {}
        @keyword faults: Raise faults raised by server (default:True),
                else return tuple from service method invocation as (http code, object).
        @type faults: boolean
        @keyword nil_supported: The bindings will set the xsi:nil="true" on nodes
                that have a value=None when this flag is True (default:True).
                Otherwise, an empty node <x/> is sent.
        @type nil_supported: boolean
        """
        Binding.__init__(self, wsdl, **kwargs)

    def get_ptypes(self, method):
        """
        Get a list of I{parameter definitions} defined for the specified method.
        Each I{parameter definition} is a tuple: (I{name}, L{suds.schema.SchemaProperty})
        @param method: The I{name} of a method.
        @type method: str
        @return:  A list of parameter definitions
        @rtype: [I{definition},]
        """
        params = []
        operation = self.wsdl.get_operation(method)
        if operation is None:
            raise NoSuchMethod(method)
        input = operation.getChild('input')
        msg = self.wsdl.get_message(input.get('message'))
        for p in msg.getChildren('part'):
            ref = p.get('type')
            qref = qualified_reference(ref, p, self.wsdl.tns)
            type = self.schema.find(qref)
            if type is None:
                raise TypeNotFound(qref)
            params.append((p.get('name'), type))
        log.debug('parameters %s for method %s', tostr(params), method)
        return params

    def returns_collection(self, method):
        """
        Get whether the type defined for the method is a collection
        @param method: The I{name} of a method.
        @type method: str
        @rtype: boolean
        """
        operation = self.wsdl.get_operation(method)
        if operation is None:
            raise NoSuchMethod(method)
        output = operation.getChild('output')
        msg = self.wsdl.get_message(output.get('message'))
        result = False
        for p in msg.getChildren('part'):
            ref = p.get('type')
            qref = qualified_reference(ref, p, self.wsdl.tns)
            type = self.schema.find(qref)
            elements = type.get_children(empty=[])
            result = ( len(elements) > 0 and elements[0].unbounded() )
            break
        return result
    
    def returned_type(self, method):
        """
        Get the referenced type returned by the I{method}.
        @param method: The name of a method.
        @type method: str
        @return: The name of the type return by the method.
        @rtype: str
        """
        operation = self.wsdl.get_operation(method)
        if operation is None:
            raise NoSuchMethod(method)
        output = operation.getChild('output')
        msg = self.wsdl.get_message(output.get('message'))
        result = False
        for p in msg.getChildren('part'):
            ref = p.get('type')
            qref = qualified_reference(ref, p, self.wsdl.tns)
            result = self.schema.find(qref)
            result = result.ref()
            break
        return result