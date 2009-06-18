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
Contains XML text classes.
"""

class Text(unicode):
    """
    An XML text object used to represent text content.
    @ivar lang: The (optional) language flag.
    @type lang: bool
    @ivar encoded: The (optional) XML encoded flag.
    @type encoded: bool
    """
    __slots__ = ('lang', 'encoded',)
    
    @classmethod
    def __valid(cls, *args):
        return ( len(args) and args[0] is not None )
    
    def __new__(cls, *args, **kwargs):
        if cls.__valid(*args):
            lang = kwargs.pop('lang', None)
            encoded = kwargs.pop('encoded', False)
            result = super(Text, cls).__new__(cls, *args, **kwargs)
            result.lang = lang
            result.encoded = encoded
        else:
            result = None
        return result
    
    def __add__(self, other):
        joined = u''.join((self, other))
        result = Text(joined, lang=self.lang, encoded=self.encoded)
        if isinstance(other, Text):
            result.encoded = ( self.encoded or other.encoded )
        return result
    
    def __repr__(self):
        s = [self]
        if self.lang is not None:
            s.append(' [%s]' % self.lang)
        if self.encoded:
            s.append(' <encoded>')
        return ''.join(s)
    
    def trim(self):
        return Text(self.strip(), encoded=self.encoded)