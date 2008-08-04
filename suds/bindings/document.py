# This program is free software; you can redistribute it and/or modify
# it under the terms of the (LGPL) GNU Lesser General Public License as
# published by the Free Software Foundation; either version 3 of the 
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library Lesser General Public License for more details at
# ( http://www.gnu.org/licenses/lgpl.html ).
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
# written by: Jeff Ortel ( jortel@redhat.com )

from suds import *
from suds.bindings.binding import Binding

log = logger(__name__)

class Document(Binding):
    """
    The I{wrapped} document/literal binding style.
    """

    def __init__(self, wsdl):
        """
        @param wsdl: A WSDL object.
        @type wsdl: L{suds.wsdl.Definitions}
        """
        Binding.__init__(self, wsdl)
    
    def param_defs(self, method):
        """
        Get parameter definitions.
        @param method: A method name.
        @type method: basestring
        @return: A collection of parameter definitions
        @rtype: [(str, L{xsd.sxbase.SchemaObject}),..]
        """
        result = []
        for p in self.part_types(method):
            resolved = p[1].resolve()
            for c in resolved.children:
                result.append((c.name, c))
        return result
    
    def returned_types(self, method):
        """
        Get the referenced type returned by the I{method}.
        @param method: The name of a method.
        @type method: str
        @return: The name of the type return by the method.
        @rtype: [L{xsd.sxbase.SchemaObject}]
        """
        result = []
        for pt in self.part_types(method, False):
            pt = pt.resolve(nobuiltin=True)
            for rt in pt.children:
                result.append(rt)
            break
        return result
