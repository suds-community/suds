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
The I{depsolve} module defines a class for performing dependancy solving.
"""

from logging import getLogger
from suds import *

log = getLogger(__name__)


class DepList:
    """
    Dependancy solving list.
    Items are tuples: (object, (deps,))
    @ivar raw: The raw (unsorted) items.
    @type raw: list
    @ivar index: The index of (unsorted) items.
    @type index: list
    @ivar stack: The sorting stack.
    @type stack: list
    @ivar pushed: A set of items pushed.  This is an effecient way to keep
        track of the items we've pushed.
    @type stack: list
    @ivar sorted The sorted list of items.
    @type sorted: list
    """

    def __init__(self):
        """ """
        self.raw = []
        self.index = {}
        self.stack = []
        self.pushed = None
        self.sorted = None
        
    def add(self, *items):
        """
        Add items to be sorted.
        @param items: One or more items to be added.
        @type items: I{item}
        @return: self
        @rtype: L{DepList}
        """
        for item in items:
            self.raw.append(item)
            self.index[item[0]] = item
        return self
        
    def sort(self):
        """
        Sort the list based on dependancies.
        @return: The sorted items.
        @rtype: list
        """
        self.sorted = list()
        self.pushed = set()  
        for item in self.raw:
            self.push(item)
            while len(self.stack):
                self.pop()
        self.raw = self.sorted
        return self.sorted
    
    def push(self, item):
        """
        Push and item onto the sorting stack.
        @param item: An item to push.
        @type item: I{item}
        @return: The number of items pushed.
        @rtype: int
        """
        if item in self.pushed:
            return 0
        self.pushed.add(item)
        self.stack.append(item)
        n = 1
        for d in item[1]:
            n += 1
            dx = self.index.get(d)
            if dx is None:
                log.debug('dependency: %s not-found, skipped', Repr(d))
                continue
            if self.push(dx) == 1:
                self.pop()
                n -= 1
        return n
    
    def pop(self):
        """
        Pop the top item off the stack and append
        it to the sorted list.
        @return: self
        @rtype: L{DepList}
        """
        p = self.stack.pop()
        self.sorted.append(p)
        return self



if __name__ == '__main__':
    a = ('a', ())
    b = ('b', ('a',))
    c = ('c', ('a','b'))
    d = ('d', ('c',))
    e = ('e', ('d','a'))
    f = ('f', ('e','c','d','a'))
    L = DepList()
    L.add(c, e, d, b, f, a)
    print [x[0] for x in L.sort()]