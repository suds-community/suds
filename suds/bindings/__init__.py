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
Provides modules containing classes to support Web Services (SOAP)
bindings.
"""

class xlstr(unicode):
    """
    Language aware string contains a I{lang} attribute.
    @ivar lang: The string language when set (may be None).
    @type lang: str
    """
    __slots__ = ('lang',)
    
    @classmethod
    def string(cls, s, lang=None):
        return xlstr(s, lang=lang)
    
    def __new__(cls, *args, **kwargs):
        lang = kwargs.pop('lang', None)
        res = super(xlstr, cls).__new__(cls, *args, **kwargs)
        res.lang = lang
        return res