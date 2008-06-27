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

log = logger(__name__)

class Document(Binding):
    """
    The document/literal binding style.
    """

    def __init__(self, wsdl):
        """
        @param wsdl: A WSDL object.
        @type wsdl: L{suds.wsdl.WSDL}
        """
        Binding.__init__(self, wsdl)
        
    def part_refattr(self):
        """
        Get the part attribute that defines the part's I{type}.
        @return: An attribute name.
        @rtype: basestring 
        """
        return "element"
    
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
            for c in resolved.get_children():
                name = c.get_name()
                result.append((name, c))
        return result
    
    def returned_type(self, method):
        """
        Get the referenced type returned by the I{method}.
        @param method: The name of a method.
        @type method: str
        @return: The name of the type return by the method.
        @rtype: str
        """
        result = None
        for rt in self.part_types(method, False):
            rt = rt.resolve(nobuiltin=True)
            if len(rt):
                rt = rt[0]
                result = rt.resolve(nobuiltin=True)
            break
        return result
