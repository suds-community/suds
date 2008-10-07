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
Provides classes for handling soap multirefs.
"""

from logging import getLogger
from suds import *
from suds.sax.element import Element

log = getLogger(__name__)

class MultiRef:
    """
    Resolves and replaces multirefs.
    @ivar nodes: A list of non-multiref nodes.
    @type nodes: list
    @ivar catalog: A dictionary of multiref nodes by id.
    @type catalog: dict 
    """
    
    def __init__(self):
        self.nodes = []
        self.catalog = {}
    
    def process(self, body):
        """
        Process the specified soap envelope body and replace I{multiref} node
        references with the contents of the referenced node.
        @param body: A soap envelope body node.
        @type body: L{Element}
        @return: The processed I{body}
        @rtype: L{Element}
        """
        self.nodes = []
        self.catalog = {}
        self.build_catalog(body)
        self.update(body)
        body.children = self.nodes
        return body
    
    def update(self, node):
        """
        Update the specified I{node} by replacing the I{multiref} references with
        the contents of the referenced nodes and remove the I{href} attribute.
        @param node: A node to update.
        @type node: L{Element}
        """
        self.replace_references(node)
        for c in node.children:
            self.update(c)
            
    def replace_references(self, node):
        """
        Replacing the I{multiref} references with the contents of the 
        referenced nodes and remove the I{href} attribute.
        @param node: A node to update.
        @type node: L{Element}
        """
        href = node.attrib('href')
        if href is None:
            return
        id = href.getValue()
        ref = self.catalog.get(id)
        if ref is None:
            log.error('multiRef: %s, not-resolved', id)
            return
        node.append(ref.children)
        node.remove(href)
            
    def build_catalog(self, body):
        """
        Create the I{catalog} of multiref nodes by id and the list of
        non-multiref nodes.
        @param body: A soap envelope body node.
        @type body: L{Element}
        """
        for c in body.children:
            if c.name == 'multiRef':
                key = '#'+c.get('id')
                self.catalog[key] = c
            else:
                self.nodes.append(c)

