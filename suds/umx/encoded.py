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
Provides soap encoded unmarshaller classes.
"""

from logging import getLogger
from suds import *
from suds.umx import *
from suds.umx.typed import Typed
from suds.sax import splitPrefix
from suds.xsd.query import TypeQuery

log = getLogger(__name__)


Content.extensions.append('aty')


class Encoded(Typed):
    """
    A SOAP section (5) encoding unmarshaller.
    This marshaller supports rpc/encoded soap styles.
    """

    def start(self, content):
        #
        # Grab the array type and continue
        #
        start = Typed.start(self, content)
        self.setaty(content)
        return start
    
    def end(self, content):
        #
        # Squash soap encoded arrays into python lists.  This is
        # also where we insure that empty arrays are represented
        # as empty python lists.
        #
        aty = content.aty
        if aty is not None:
            pylist = []
            if len(content.data):
                items = content.data[0]
                for x in items:
                    pylist.append(aty.translate(x))
            content.data = pylist
        return Typed.end(self, content)
    
    def postprocess(self, content):
        #
        # Ensure proper rendering of empty arrays.
        #
        if content.aty is None:
            return Typed.postprocess(self, content)
        else:
            return content.data
    
    def setaty(self, content):
        """
        Grab the (aty) soap-enc:arrayType and attach it to the
        content for proper array processing later in end().
        @param content: The current content being unmarshalled.
        @type content: L{Content}
        @return: self
        @rtype: L{Encoded}
        """
        spns = (None, 'http://schemas.xmlsoap.org/soap/encoding/')
        aty = content.node.get('arrayType', spns)
        if aty is None:
            return
        aty = aty.split('[')[0]
        p,t = splitPrefix(aty)
        ns = content.node.resolvePrefix(p)
        qref = (t, ns[1])
        query = TypeQuery(qref)
        content.aty = query.execute(self.resolver.schema)
        return self