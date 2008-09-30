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

"""
Provides classes for the (WS) SOAP I{rpc/literal} and I{rpc/encoded} bindings.
"""

from logging import getLogger
from suds import *
from suds.bindings.binding import Binding
from suds.sax.element import Element


log = getLogger(__name__)

class RPC(Binding):
    """
    RPC/Literal binding style.
    """

    def __init__(self, wsdl):
        """
        @param wsdl: A WSDL object.
        @type wsdl: L{suds.wsdl.Definitions}
        """
        Binding.__init__(self, wsdl)
        
    def bodycontent(self, method, args):
        """
        Get the content for the soap I{body}.
        @param method: A service method.
        @type method: I{service.Method}
        @param args: method parameter values
        @type args: list
        @return: The xml content for the <body/>
        @rtype: L{Element}
        """
        n = 0
        root = self.method(method)
        pdefs = self.param_defs(method)
        for arg in args:
            if len(pdefs) == n: break
            p = self.param(method, pdefs[n], arg)
            if p is not None:
                root.append(p)
            n += 1
        return root
        
    def method(self, method):
        """
        Get the document root.  For I{rpc/(literal|encoded)}, this is the
        name of the method qualifed by the schema tns.
        @param method: A service method.
        @type method: I{service.Method}
        @return: A root element.
        @rtype: L{Element}
        """
        ns = method.soap.input.body.namespace
        method = Element(method.name, ns=ns)
        return method

    def param_defs(self, method):
        """
        Get parameter definitions.  
        Each I{pdef} is a tuple (I{name}, L{xsd.sxbase.SchemaObject})
        @param method: A servic emethod.
        @type method: I{service.Method}
        @return: A collection of parameter definitions
        @rtype: [I{pdef},..]
        """
        return self.part_types(method)