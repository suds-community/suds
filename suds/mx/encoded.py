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

log = getLogger(__name__)


class Encoded(Literal):
    """
    A SOAP section (5) encoding marshaller.
    This marshaller supports rpc/encoded soap styles.
    """
        
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