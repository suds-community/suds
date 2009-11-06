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
Provides literal I{marshaller} classes.
"""

from logging import getLogger
from suds import *
from suds.mx import *
from suds.mx.core import Core
from suds.mx.typer import Typer
from suds.resolver import GraphResolver, Frame
from suds.sax.element import Element

log = getLogger(__name__)


Content.extensions.append('type')


class Literal(Core):
    """
    A I{literal} marshaller.
    This marshaller is semi-typed as needed to support both
    document/literal and rpc/literal soap styles.
    @ivar schema: An xsd schema.
    @type schema: L{xsd.schema.Schema}
    @ivar resolver: A schema type resolver.
    @type resolver: L{GraphResolver}
    """

    def __init__(self, schema):
        """
        @param schema: A schema object
        @type schema: L{xsd.schema.Schema}
        """
        Core.__init__(self)
        self.schema = schema
        self.options = schema.options
        self.resolver = GraphResolver(self.schema)
    
    def reset(self):
        self.resolver.reset()
            
    def start(self, content):
        log.debug('starting content:\n%s', content)
        if content.type is None:
            name = content.tag
            if name.startswith('_'):
                name = '@'+name[1:]
            content.type = self.resolver.find(name, content.value)
            if content.type is None:
                raise TypeNotFound(content.tag)
        else:
            known = None
            if isinstance(content.value, Object):
                known = self.resolver.known(content.value)
                if known is None:
                    log.debug('object has no type information', content.value)
                    known = content.type
                self.sort(content.value, known)
            frame = Frame(content.type, resolved=known)
            self.resolver.push(frame)
        resolved = self.resolver.top().resolved
        content.value = self.translated(content.value, resolved)
        if self.skip(content):
            log.debug('skipping (optional) content:\n%s', content)
            self.resolver.pop()
            return False
        else:
            return True
        
    def suspend(self, content):
        content.suspended = True
        self.resolver.pop()
    
    def resume(self, content):
        frame = Frame(content.type)
        self.resolver.push(frame)
        
    def end(self, content):
        log.debug('ending content:\n%s', content)
        current = self.resolver.top().type
        if current == content.type:
            self.resolver.pop()
        else:
            raise Exception(
                'content (end) mismatch: top=(%s) cont=(%s)' % \
                (current, content))
    
    def node(self, content):
        ns = content.type.namespace()
        if content.type.form_qualified:
            node = Element(content.tag, ns=ns)
            node.addPrefix(ns[0], ns[1])
        else:
            node = Element(content.tag)
        self.encode(node, content)
        log.debug('created - node:\n%s', node)
        return node
    
    def setnil(self, node, content):
        if content.type.nillable:
            node.setnil()
            
    def setdefault(self, node, content):
        default = content.type.default
        if default is None:
            pass
        else:
            node.setText(default)
        return default
    
    def optional(self, content):
        if content.type.optional():
            return True
        resolver = self.resolver
        ancestry = resolver.top().ancestry
        for a in ancestry:
            if a.optional():
                return True
        return False
    
    def encode(self, node, content):
        # Add (soap) encoding information only if the resolved
        # type is derived by extension.  Further, the xsi:type values
        # is qualified by namespace only if the content (tag) and
        # referenced type are in different namespaces.
        if content.type.any():
            return
        resolved = self.resolver.top().resolved
        if resolved is None:
            resolved = content.type.resolve()
        if not resolved.extension():
            return
        ns = None
        name = resolved.name
        if self.options.xstq:
            ns = resolved.namespace('ns1')
        Typer.manual(node, name, ns)
    
    def skip(self, content):
        """ skip this content """
        if self.optional(content):
            v = content.value
            if v is None:
                return True
            if isinstance(v, (list,tuple)) and len(v) == 0:
                return True
        return False
    
    def optional(self, content):
        if content.type.optional():
            return True
        ancestry = self.resolver.top().ancestry
        for a in ancestry:
            if a.optional():
                return True
        return False
    
    def translated(self, value, resolved):
        """ translate using the schema type """
        if value is not None:
            return resolved.translate(value, False)
        else:
            return None
        
    def sort(self, sobject, resolved):
        """ sort attributes using the schema type """
        md = sobject.__metadata__
        md.ordering = self.ordering(resolved)

    def ordering(self, type):
        """ get the ordering """
        result = []
        for child, ancestry in type.resolve():
            name = child.name
            if child.name is None:
                continue
            if child.isattr():
                name = '_%s' % child.name
            result.append(name)
        return result

