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

class Marshaller:
    
    def __init__(self, binding):
        self.binding = binding
        self.schema = binding.schema

    
class SoapObject:
    
    def __init__(self, master, name, content, tns=None, xs=None):
        self.master = master
        self.content = content
        self.xs = xs
        self.prefix, self.name = splitPrefix(name)
        if self.prefix is not None:
            self.ns = master.resolvePrefix(self.prefix)
        else:
            self.ns = tns
        if ns is not None:
            self.prefix = ns[0]

    def qname(self):
        if prefix is not None:
            return ':'.join(self.prefix, self.name)
        else:    
            return self.name