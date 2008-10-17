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
Provides classes for the (WS) SOAP I{document/literal}.
"""

from logging import getLogger
from suds import *
from suds.bindings.binding import Binding
from suds.sax.element import Element

log = getLogger(__name__)


class Document(Binding):
    """
    The document/literal style.  Literal is the only (@use) supported
    since document/encoded is pretty much dead.
    Although the soap specification supports multiple documents within the soap
    <body/>, it is very uncommon.  As such, suds presents an I{RPC} view of
    service methods defined with a single document parameter.  This is done so 
    that the user can pass individual parameters instead of one, single document.
    To support the complete specification, service methods defined with multiple documents
    (multiple message parts), must present a I{document} view for that method.
    """

    def __init__(self, wsdl):
        """
        @param wsdl: A WSDL object.
        @type wsdl: L{suds.wsdl.Definitions}
        """
        Binding.__init__(self, wsdl)
        
    def bodycontent(self, method, args):
        """
        Get the content for the soap I{body} node.
        @param method: A service method.
        @type method: I{service.Method}
        @param args: method parameter values
        @type args: list
        @return: The xml content for the <body/>
        @rtype: [L{Element},..]
        """
        n = 0
        pts = self.part_types(method)
        root = self.document(pts)
        pdefs = self.param_defs(method)
        for arg in args:
            if len(pdefs) == n: break
            p = self.param(method, pdefs[n], arg)
            if p is not None:
                root.append(p)
            n += 1
        if len(pts) > 1:
            return root.children
        else:
            return root
        
    def document(self, pts):
        """
        Get the document root.  For I{document/literal}, this is the
        name of the wrapper element qualifed by the schema tns.
        @param pts: The method name.
        @type pts: str
        @return: A root element.
        @rtype: L{Element}
        """
        tag = pts[0][1].name
        ns = pts[0][1].namespace()
        d = Element(tag, ns=ns)
        return d
        
    def param_defs(self, method):
        """
        Get parameter definitions.
        @param method: A method name.
        @type method: basestring
        @return: A collection of parameter definitions
        @rtype: [(str, L{xsd.sxbase.SchemaObject}),..]
        """
        pts = self.part_types(method)
        if len(pts) > 1:
            return pts
        result = []
        for p in pts:
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
        for pt in self.part_types(method, input=False):
            pt = pt.resolve(nobuiltin=True)
            for rt in pt.children:
                result.append(rt)
            break
        return result