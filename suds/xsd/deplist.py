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
    """
    Dependency solving list.

    Items are tuples: (object, (deps,))

    """

    def __init__(self):
        self.__unsorted = []
        self.__index = {}
        self.__stack = []
        self.__pushed = set()

    def add(self, *items):
        """
        Add items to be sorted.

        @param items: One or more items to be added.
        @type items: I{item}

        """
        for item in items:
            self.__unsorted.append(item)
            key = item[0]
            self.__index[key] = item

    def sort(self):
        """
        Sort the list based on dependencies.

        @return: The sorted items.
        @rtype: list

        """
        sorted = []
        self.__pushed = set()
        for item in self.__unsorted:
            self.__push(item)
            while self.__stack:
                try:
                    top = self.__top()
                    ref = top[1].next()
                    refd = self.__index.get(ref)
                    if refd is None:
                        log.debug('"%s" not found, skipped', Repr(ref))
                        continue
                    self.__push(refd)
                except StopIteration:
                    sorted.append(self.__pop())
                    continue
        self.__unsorted = sorted
        return sorted

    def __pop(self):
        """
        Pop & return the top item off the sorting stack.

        @return: The popped item.
        @rtype: I{item}

        """
        return self.__stack.pop()[0]

    def __push(self, item):
        """
        Push an item onto the sorting stack.

        Each item is pushed as a stack frame 2-tuple containing:
          - the item itself,
          - an iterator over all of the item's dependencies

        @param item: An item to push.
        @type item: I{item}

        """
        if item in self.__pushed:
            return
        frame = (item, iter(item[1]))
        self.__stack.append(frame)
        self.__pushed.add(item)

    def __top(self):
        """
        Get the top sorting stack frame.

        @return: The top sorting stack frame.
        @rtype: (I{item}, iter)

        """
        return self.__stack[-1]
