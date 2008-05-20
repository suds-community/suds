# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
# written by: Jeff Ortel ( jortel@redhat.com )

from suds import *
from suds.sax import splitPrefix
from suds.sudsobject import Object
from suds.schema import *

log = logger(__name__)


class Resolver:
    """
    An I{abstract} schema-type resolver.
    @ivar schema: A schema object.
    @type schema: L{schema.Schema}
    """

    def __init__(self, schema):
        """
        @param schema: A schema object.
        @type schema: L{schema.Schema}
        """
        self.schema = schema



class PathResolver(Resolver):
    """
    Resolveds the definition object for the schema type located at the specified path.
    The path may contain (.) dot notation to specify nested types.
    """
    
    def __init__(self, schema):
        """
        @param schema: A schema object.
        @type schema: L{schema.Schema}
        """
        Resolver.__init__(self, schema)

    def find(self, path, resolved=True):
        """
        Get the definition object for the schema type located at the specified path.
        The path may contain (.) dot notation to specify nested types.
        @param path: A (.) separated path to a schema type.
        @type path: basestring
        @param resolved: A flag indicating that the fully resolved type
            should be returned.
        @type resolved: boolean
        @return: The found schema I{type}
        @rtype: L{SchemaProperty}
        """
        result = None
        parts = path.split('.')
        log.debug('searching schema for (%s)', parts[0])
        result = self.schema.find(parts[0], resolved=False)
        if result is None:
            log.error('(%s) not-found', parts[0])
            return result
        log.debug('found (%s) as (%s)', parts[0], repr(result))
        leaf = parts[-1]
        if resolved or \
            result != leaf:
                result = result.resolve()
        for part in parts[1:]:
            name = splitPrefix(part)[1]
            log.debug('searching parent (%s) for (%s)', repr(result), name)
            result = result.get_child(name)
            if result is None:
                log.error('(%s) not-found', name)
                break
            log.debug('found (%s) as (%s)', name, repr(result))
            if resolved or \
                result != leaf:
                    result = result.resolve()
        return result
    


class TreeResolver(Resolver):
    """
    The tree resolver is a I{stateful} tree resolver
    used to resolve each node in a tree.  As such, it mirrors
    the tree structure to ensure that nodes are resolved in
    context.
    @ivar stack: The context stack.
    @type stack: list
    """
    
    def __init__(self, schema):
        """
        @param schema: A schema object.
        @type schema: L{schema.Schema}
        """
        Resolver.__init__(self, schema)
        self.stack = []
        
    def reset(self, items=()):
        """
        Reset the resolver's state.
        @param items: Items used to initialize the stack.
        @type items: [L{SchemaProperty},...]
        """
        self.stack = []
        for item in items:
            self.push(item)
            
    def push(self, item):
        """
        Push a type onto the stack
        @param item: An item to push.
        @type item: L{SchemaProperty}
        @return: self
        @rtype: L{TreeResolver}
        """
        self.stack.append(item)
        log.debug('push: (%s) %s', repr(item), repr(self.stack))
        return self
    
    def top(self):
        """
        Get the item at the top of the stack.
        @return: The I{top} item, else None.
        @rtype: any
        """
        if len(self.stack):
            return self.stack[-1]
        else:
            return None
        
    def pop(self):
        if len(self.stack):      
            popped = self.stack.pop()
            log.debug('pop: (%s) %s', repr(popped), repr(self.stack))
            return popped
        else:
            log.debug('stack empty, not-popped')
        return None

    def __find(self, name, parent):
        """ find the type for name and optional parent """
        if parent is None:
            log.debug('searching schema for (%s)', name)
            result = self.schema.find(name, resolved=False)
        else:
            log.debug('searching parent (%s) for (%s)', repr(parent), name)
            result = parent.get_child(name)
        if result is None:
            log.error('(%s) not-found', name)
        else:
            log.debug('(%s) found as (%s)', name, repr(result))
        return result



class NodeResolver(TreeResolver):
    """
    The node resolver is a I{stateful} XML document resolver
    used to resolve each node in a tree.  As such, it mirrors
    the tree structure to ensure that nodes are resolved in
    context.
    """
    
    def __init__(self, schema):
        """
        @param schema: A schema object.
        @type schema: L{schema.Schema}
        """
        TreeResolver.__init__(self, schema)
        
    def find(self, node, resolved=False, push=True):
        """
        @param node: An xml node to be resolved.
        @type node: L{sax.Element}
        @param resolved: A flag indicating that the fully resolved type should be
            returned.
        @type resolved: boolean
        @param push: Indicates that the resolved type should be
            pushed onto the stack.
        @type push: boolean
        @return: The found schema I{type}
        @rtype: L{SchemaProperty}
        """
        name = node.get('type', xsins)
        if name is None:
            name = node.name
            parent = self.top()
        else:
            parent = None
        result = self._TreeResolver__find(name, parent)
        if result is None:
            return result
        resolved = result.resolve()
        if push:
            self.push(resolved)
        if resolved:
            result = result.resolve()
        return result


class GraphResolver(TreeResolver):
    """
    The graph resolver is a I{stateful} L{Object} graph resolver
    used to resolve each node in a tree.  As such, it mirrors
    the tree structure to ensure that nodes are resolved in
    context.
    """
    
    def __init__(self, schema):
        """
        @param schema: A schema object.
        @type schema: L{schema.Schema}
        """
        TreeResolver.__init__(self, schema)
        
    def find(self, name, object, resolved=False, push=True):
        """
        @param name: The name of the object to be resolved.
        @type name: basestring
        @param object: The name's value.
        @type object: (any|L{Object}) 
        @param resolved: A flag indicating that the fully resolved type
            should be returned.
        @type resolved: boolean
        @param push: Indicates that the resolved type should be
            pushed onto the stack.
        @type push: boolean
        @return: The found schema I{type}
        @rtype: L{SchemaProperty}
        """
        if isinstance(object, Object):
            result = self.__embedded(object)
            if result is not None:
                self.push(result.resolve())
                return result
            name = object.__class__.__name__
        parent = self.top()
        result = self._TreeResolver__find(name, parent)
        if result is None:
            return result
        resolved = result.resolve()
        if push:
            self.push(resolved)
        if resolved:
            result = result.resolve()
        return result
    
    def __embedded(self, object):
        try:
            md = object.__metadata__
            return md.__type__
        except:
            pass
