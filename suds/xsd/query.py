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
from suds.sudsobject import Object
from suds.xsd import *
from suds.xsd.sxbuiltin import XBuiltin
from suds.xsd.sxbasic import Simple, Element, Complex

"""
The I{query} module defines a class for performing schema queries.
"""

log = logger(__name__)


class Query(Object):
    """
    A schema query class.
    @ivar id: The object id.
    @type id: str
    @ivar name: The schema type name being queried.
    @type name: (str|qref)
    @ivar qname: The qualified name being queried for.
    @type qname: I{qref}
    @ivar history: A list of items tracked during query processing.
        This list primarily contians items found by the query.  However, 
        it can hold and be preloaded as needed.
    @type history: []
    @ivar resolved: A flag indicating that the result should be
        fully resolved.
    @type resolved: boolean
    @ivar cidx: The class match list index.
    @type cidx: number
    @ivar clsfilter: A class filter list.  When empty, all
        classes match.
    @type clsfilter: [L{sxbase.SchemaObject},...]
    @ivar schema: The schema associated with the query.  The schema
        is used by the query to search for items.
    @type schema: L{schema.Schema}
    @ivar locked: A flag indicates that the query may not be incremented.
    @type locked: boolean
    @cvar clsorder: A list of classes, used to ensure that types
        are found in a particular order.
    @type clsorder: ()
    """
    
    clsorder = ((XBuiltin, Simple, Element),(Complex,))
    
    def __init__(self, name):
        """
        @param name: The schema type name being queried.
        @type name: (str|qref)
        """
        Object.__init__(self)
        self.id = objid(self)
        self.name = name
        if isqref(name):
            self.name = name[0]
            self.qname = name
        else:
            self.name = name  
            self.qname = None
        self.history = []
        self.resolved = False
        self.cidx = 0
        self.clsfilter = []
        self.schema = None
        
    def filter(self, result):
        """
        Filter the specified result based on query criteria.
        @param result: A potential result.
        @type result: L{sxbase.SchemaObject}
        @return: True if result should be excluded.
        @rtype: boolean
        """
        if result is None:
            return True
        cls = result.__class__
        classes = Query.clsorder[self.cidx]
        reject = \
            ( cls not in classes or \
              ( len(self.clsfilter) and cls not in self.clsfilter ) or \
              result in self.history )
        if reject:
            log.debug('result %s, rejected by\n%s', repr(result), tostr(self))
        return reject
    
    def qualify(self, resolvers, defns):
        """
        Qualify the I{name}.  Convert the name a qualified reference
        @param resolvers: A list of namespace prefix resolvers.
        @type resolvers: (tuple|list)
        @param defns: The default namespace when name has no prefix.
        @type defns: I{namesapce}
        """
        if self.qname is None:
            if isinstance(self.name, basestring):
                self.qname = qualified_reference(self.name, resolvers, defns)
            elif isqref(self.name):
                self.qname = name
                self.name = self.qname[0]
            else:
                raise Exception('name must be (str|qref)')
            
    def inprogress(self):
        """
        Get whether the query is I{in-use} or I{in-progress}.
        @return: True when in progress.
        @rtype: boolean
        """
        return ( self.schema is not None )
    
    def signature(self):
        """
        Get the query's search signature.
        @return: A string representation of the search criteria.
        @rtype: str
        """
        return \
            str(self.resolved) \
            + tostr(self.qname) \
            + tostr(self.clsfilter) \
            + tostr(Query.clsorder[self.cidx])
            
    def execute(self, schema):
        """
        Execute this query using the specified schema.
        @param schema: The schema associated with the query.  The schema
            is used by the query to search for items.
        @type schema: L{schema.Schema}
        @return: The item matching the search criteria.
        @rtype: L{sxbase.SchemaObject}
        """
        if self.inprogress():
            raise Exception('%s, already in progress' % self.id)
        self.schema = schema
        self.qualify(schema.root, schema.tns)
        result = None
        while result is None:
            result = schema.find(self)
            if result is None and self.__increment():
                continue
            else:
                break
        if result is not None:
            self.history.append(result)
        return result
    
    def __increment(self):
        """ Increment the class ordering """
        result = False
        max = len(self.clsorder)-1
        if self.cidx < max:
            self.cidx += 1
            classes = Query.clsorder[self.cidx]
            log.debug('%s, targeting %s', self.id, classes)
            result = True
        return result
