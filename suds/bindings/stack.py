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
from logging import Logger

log = logger(__name__)

class Stack:
    
    def __init__(self, log=log):
        """
        @param log: An optional logger.
        @type log: L{Logger}
        """
        self.content = []
        self.log = log
        
    def clear(self):
        """
        Clear the stack.
        @return: self
        @rtype: L{Stack}
        """
        self.content = []
        return self
            
    def top(self):
        """
        Get the item at the top of the stack.
        @return: The I{top} item, else None.
        @rtype: any
        """
        if len(self):
            return self.content[-1]
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
        self.content.append(s)
        log.debug('push: (%s) %s', s, str(self))
        return self
        
    def pop(self):
        """
        Pop the top item off the stack.
        @return: The popped item, else None.
        @rtype: any
        """
        if len(self.content):
            s = self.content.pop()
            log.debug('pop: (%s) %s', s, str(self))
        else:
            log.debug('stack empty, not-popped')
        return s
    
    def __repr__(self):
        return repr(self.content)
    
    def __len__(self):
        return len(self.content)
    
    def __getitem__(self, index):
        return self.content[index]
    
    def __str__(self):
        return str(self.content)
    
    def __unicode__(self):
        return unicode(self.content)
    
    def __iter__(self):
        return iter(self.content)