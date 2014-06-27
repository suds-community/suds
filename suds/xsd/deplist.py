# This program is free software; you can redistribute it and/or modify it under
# the terms of the (LGPL) GNU Lesser General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Library Lesser General Public License
# for more details at ( http://www.gnu.org/licenses/lgpl.html ).
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
# written by: Jeff Ortel ( jortel@redhat.com )

"""
The I{deplist} module defines a class for performing topological dependency
sorting - dependency entries before those that depend on them.

"""

from suds import *

from logging import getLogger
log = getLogger(__name__)


class DepList:
    """Dependency solving list."""

    def __init__(self):
        self.__index = {}

    def add(self, *items):
        """
        Add items to be sorted.

        Items are tuples: (object, (deps,))

        @param items: One or more items to be added.
        @type items: I{item}

        """
        self.__index.update(items)

    def sort(self):
        """
        Sort the list based on dependencies.

        If B is directly or indirectly dependent on A and they are not both a
        part of the same dependency cycle (i.e. then A is neither directly nor
        indirectly dependent on B) then A needs to come before B.

        If A and B are a part of the same dependency cycle, i.e. if they are
        both directly or indirectly dependent on each other, then it does not
        matter which comes first.

        Result contains the same data objects (object + dependency collection)
        as given on input, but packaged in different items/tuples, i.e. the
        returned items will 'equal' but not 'the same'.

        @return: The sorted items.
        @rtype: list

        """
        sorted = []
        processed = set()
        for key, deps in self.__index.iteritems():
            self.__sort_r(sorted, processed, key, deps)
        return sorted

    def __sort_r(self, sorted, processed, key, deps):
        """Recursive topological sort implementation."""
        if key in processed:
            return
        processed.add(key)
        for dep_key in deps:
            dep_deps = self.__index.get(dep_key)
            if dep_deps is None:
                log.debug('"%s" not found, skipped', Repr(dep_key))
                continue
            self.__sort_r(sorted, processed, dep_key, dep_deps)
        sorted.append((key, deps))
