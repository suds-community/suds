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
Provides typed unmarshaller classes.
"""

from logging import getLogger
from suds import *
from suds.umx import *
from suds.umx.core import Core
from suds.resolver import NodeResolver, Frame
from suds.sudsobject import Factory

log = getLogger(__name__)


Content.extensions.append('type')


class Typed(Core):
    """
    A I{typed} XML unmarshaller
    @ivar resolver: A schema type resolver.
    @type resolver: L{NodeResolver}
    """
    
    def __init__(self, schema):
        """
        @param schema: A schema object.
        @type schema: L{xsd.schema.Schema}
        """
        self.resolver = NodeResolver(schema)
        
    def process(self, node, type):
        """
        Process an object graph representation of the xml L{node}.
        @param node: An XML tree.
        @type node: L{sax.element.Element}
        @param type: The I{optional} schema type.
        @type type: L{xsd.sxbase.SchemaObject}
        @return: A suds object.
        @rtype: L{Object}
        """
        content = Content(node)
        content.type = type
        return Core.process(self, content)

    def reset(self):
        log.debug('reset')
        self.resolver.reset()
    
    def start(self, content):
        #
        # Resolve to the schema type; build an object and setup metadata.
        #
        if content.type is None:
            found = self.resolver.find(content.node)
            if found is None:
                log.error(self.resolver.schema)
                raise TypeNotFound(content.node.qname())
            content.type = found
        else:
            known = self.resolver.known(content.node)
            frame = Frame(content.type, resolved=known)
            self.resolver.push(frame)
        resolved = self.resolver.top().resolved
        cls_name = resolved.name
        if cls_name is None:
            cls_name = content.node.name
        content.data = Factory.object(cls_name)
        md = content.data.__metadata__
        md.sxtype = content.type
        
    def end(self, content):
        self.resolver.pop()
        
    def unbounded(self, data):
        try:
            if isinstance(data, Object):
                md = data.__metadata__
                type = md.sxtype
                return type.unbounded()
        except:
            log.error('metadata error:\n%s', data, exc_info=True)
        return False
    
    def nillable(self, data):
        try:
            if isinstance(data, Object):
                md = data.__metadata__
                type = md.sxtype
                resolved = type.resolve()
                return ( type.nillable or (resolved.builtin() and resolved.nillable ) )
        except:
            log.error('metadata error:\n%s', data, exc_info=True)
        return False
    
    def append_attribute(self, name, value, content):
        """
        Append an attribute name/value into L{Content.data}.
        @param name: The attribute name
        @type name: basestring
        @param value: The attribute's value
        @type value: basestring
        @param content: The current content being unmarshalled.
        @type content: L{Content}
        """
        type = self.resolver.findattr(name)
        if type is None:
            log.warn('attribute (%s) type, not-found', name)
        else:
            value = self.translated(value, type)
        Core.append_attribute(self, name, value, content)
    
    def append_text(self, content):
        """
        Append text nodes into L{Content.data}
        @param content: The current content being unmarshalled.
        @type content: L{Content}
        """
        Core.append_text(self, content)
        resolved = content.type.resolve()
        content.text = self.translated(content.text, content.type)
            
    def translated(self, value, type):
        """ translate using the schema type """
        if value is not None:
            resolved = type.resolve()
            return resolved.translate(value)
        else:
            return value