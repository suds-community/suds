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
Provides encoded I{marshaller} classes.
"""

from logging import getLogger
from suds import *
from suds.mx import *
from suds.mx.literal import Literal
from suds.mx.typer import Typer
from suds.sudsobject import Factory

log = getLogger(__name__)


Content.extensions.append('aty')


class Encoded(Literal):
    """
    A SOAP section (5) encoding marshaller.
    This marshaller supports rpc/encoded soap styles.
    """
    
    def start(self, content):
        start = Literal.start(self, content)
        if start and isinstance(content.value, (list,tuple)):
            resolved = content.type.resolve()
            for c in resolved:
                if hasattr(c[0], 'aty'):
                    content.aty = (content.tag, c[0].aty)
                    array = Factory.object(resolved.name)
                    array.item = content.value
                    content.value = array
                    break
        return start
    
    def end(self, parent, content):
        Literal.end(self, parent, content)
        if content.aty is None:
            return
        tag, aty = content.aty
        ns0 = ('at0', aty[1])
        ns1 = ('at1', 'http://schemas.xmlsoap.org/soap/encoding/')
        array = content.value.item
        child = parent.getChild(tag)
        child.addPrefix(ns0[0], ns0[1])
        child.addPrefix(ns1[0], ns1[1])
        name = '%s:arrayType' % ns1[0]
        value = '%s:%s[%d]' % (ns0[0], aty[0], len(array)) 
        child.set(name, value)
        
    def encode(self, node, content):
        if content.type.any():
            Typer.auto(node, content.value)
            return
        resolved = self.resolver.top().resolved
        if resolved is None:
            resolved = content.type.resolve()
        if resolved.any():
            Typer.auto(node, content.value)
            return
        ns = None
        name = resolved.name
        if self.options.xstq:
            ns = resolved.namespace()
        Typer.manual(node, name, ns)