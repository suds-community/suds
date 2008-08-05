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
The I{query} module defines a class for performing schema queries.
"""

from logging import getLogger
from suds import *
from suds.sudsobject import *
from suds.xsd import *

log = getLogger(__name__)


class Query(Object):
    """
    A schema query class.
    """
    
    def __init__(self, ref=None, type=None):
        """
        @param ref: The schema reference being queried.
        @type ref: qref
        @param type: The schema B{type} reference being queried.
        @type type: qref
        """
        Object.__init__(self)
        self.id = objid(self)
        self.ref = ref
        self.history = []
        self.resolved = False
        self.element_priority = False
        if type is None:
            self.element_priority = True
        else:
            self.ref = type
        if not isqref(self.ref):
            raise Exception('%s, must be qref' % self.ref)
        
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
        reject = ( result in self.history )
        if reject:
            log.debug('result %s, rejected by\n%s', Repr(result), self)
        return reject
            
    def execute(self, schema):
        """
        Execute this query using the specified schema.
        @param schema: The schema associated with the query.  The schema
            is used by the query to search for items.
        @type schema: L{schema.Schema}
        @return: The item matching the search criteria.
        @rtype: L{sxbase.SchemaObject}
        """
        return schema.execute(self)
    
    def result(self, result):
        """
        Notification of a query result.
        @param result: A query result.
        @type result: L{sxbase.SchemaObject}
        """
        if result is None:
            log.debug('%s, not-found', self.ref)
            return
        log.debug('%s, found as: %s', self.ref, Repr(result))
        self.history.append(result)
