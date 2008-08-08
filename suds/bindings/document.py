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

from logging import getLogger
from suds import *
from suds.bindings.binding import Binding
from suds.sax import Element

log = getLogger(__name__)


class Document(Binding):
    """
    The document/literal style.  Literal is the only (@use) supported
    since document/encoded is pretty much dead.
    """

    def __init__(self, wsdl):
        """
        @param wsdl: A WSDL object.
        @type wsdl: L{suds.wsdl.Definitions}
        """
        Binding.__init__(self, wsdl)
        self.unwrapped = Unwrapped(wsdl)
        self.wrapped = Wrapped(wsdl)
        
    def method(self, name):
        """
        Get the document root.
        @param name: The method name.
        @type name: str
        @return: A root element.
        @rtype: L{Element}
        """
        return self.style(name).method(name)
        
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
    
    def style(self, method):
        """ 
        Get the sub-binding based on matching the operation name
        to the part type name.  In the wrapped style, the part type 
        will match the operation name.
        @param method: A method name.
        @type method: str
        @rtype: L{Document} 
        """
        pts = self.part_types(method)
        if pts[0][1].name == method:
            return self.wrapped
        else:
            return self.unwrapped

    
class Unwrapped(Binding):
    """
    The I{unwrapped} style.
    """

    def __init__(self, wsdl):
        """
        @param wsdl: A WSDL object.
        @type wsdl: L{suds.wsdl.Definitions}
        """
        Binding.__init__(self, wsdl)
        
    def method(self, name):
        """
        Get the document root.  For I{unwrapped}, this is
        the name of the operation qualified by the wsdl tns.
        @param name: The method name.
        @type name: str
        @return: A root element.
        @rtype: L{Element}
        """
        operation = self.wsdl.binding().type.operation(name)
        ns = operation.tns
        method = Element('%s:%s' % (ns[0], name))
        method.addPrefix(ns[0], ns[1])
        return method

      
class Wrapped(Binding):
    """
    The I{wrapped} style.
    """

    def __init__(self, wsdl):
        """
        @param wsdl: A WSDL object.
        @type wsdl: L{suds.wsdl.Definitions}
        """
        Binding.__init__(self, wsdl)
        
    def method(self, name):
        """
        Get the document root.  For I{wrapped}, this is the
        name of the wrapper element qualifed by the schema tns.
        @param name: The method name.
        @type name: str
        @return: A root element.
        @rtype: L{Element}
        """
        pts = self.part_types(name)
        wt = pts[0]
        tag = wt[1].name
        ns = wt[1].namespace()
        method = Element('%s:%s' % (ns[0], tag))
        method.addPrefix(ns[0], ns[1])
        return method
