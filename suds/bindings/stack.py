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

log = logger(__name__)


class Stack(list):
    
    def __init__(self, s=None):
        """
        @param s: Initial content for the stack.
        @type s: any
        """
        if s is None:
            list.__init__(self)
            return
        if isinstance(s,(list,tuple)):
            list.__init__(self, s)
        else:
            list.__init__(self, (s,))
            
    def top(self):
        """
        Get the item at the top of the stack.
        @return: The I{top} item, else None.
        @rtype: any
        """
        if len(self):
            return self[-1]
        else:
            return None
    
    def push(self, s):
        """
        Push an item onto the stack.
        @param s: An item to push
        @type s: any
        @return: self
        @rtype: L{Stack}
        """
        self.append(s)
        log.debug('push: (%s) %s', s, str(self))
        return self
        
    def pop(self):
        """
        Pop the top item off the stack.
        @return: The popped item, else None.
        @rtype: any
        """
        if len(self):
            s = list.pop(self)
            log.debug('pop: (%s) %s', s, str(self))
        else:
            log.debug('stack empty, not-popped')
        return s