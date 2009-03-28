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
from suds.bindings.binding import Binding, envns
from suds.sax.element import Element

log = getLogger(__name__)


encns = ('SOAP-ENC', 'http://schemas.xmlsoap.org/soap/encoding/')

class RPC(Binding):
    """
    RPC/Literal binding style.
    """
        
    def envelope(self, header, body):
        """
        Build the B{<Envelope/>} for an soap outbound message.
        @param header: The soap message B{header}.
        @type header: L{Element}
        @param body: The soap message B{body}.
        @type body: L{Element}
        @return: The soap envelope containing the body and header.
        @rtype: L{Element}
        """
        env = Binding.envelope(self, header, body)
        env.addPrefix(encns[0], encns[1])
        env.set('%s:encodingStyle' % envns[0], 
                'http://schemas.xmlsoap.org/soap/encoding/')
        return env
        
    def bodycontent(self, method, args, kwargs):
        """
        Get the content for the soap I{body}.
        @param method: A service method.
        @type method: I{service.Method}
        @param args: method parameter values
        @type args: list
        @param kwargs: Named (keyword) args for the method invoked.
        @type kwargs: dict
        @return: The xml content for the <body/>
        @rtype: L{Element}
        """
        n = 0
        root = self.method(method)
        for pd in self.param_defs(method):
            if n < len(args):
                value = args[n]
            else:
                value = kwargs.get(pd[0])
            p = self.mkparam(method, pd, value)
            if p is not None:
                root.append(p)
            n += 1
        return root
    
    def replycontent(self, method, body):
        """
        Get the reply body content.
        @param method: A service method.
        @type method: I{service.Method}
        @param body: The soap body
        @type body: L{Element}
        @return: the body content
        @rtype: [L{Element},...]
        """
        return body[0].children
        
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
        if ns[0] is None:
            ns = ('ns0', ns[1])
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
        return self.bodypart_types(method)
    

class Encoded(RPC):
    """
    RPC/Encoded (section 5)  binding style.
    """

    def marshaller(self):
        """
        Get the appropriate marshaller.
        @return: Either the I{encoded} marshaller.
        @rtype: L{Marshaller}
        """
        output = self.xcodecs[1]
        return output.encoded