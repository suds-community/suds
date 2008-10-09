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

#
# sax encoding/decoding test.
#

from suds.sax.element import Element
from suds.sax.parser import Parser

xml = "<a>Me &amp;&amp; &lt;b&gt;my&lt;/b&gt; shadow&apos;s &lt;i&gt;dog&lt;/i&gt; love to &apos;play&apos; and sing &quot;la,la,la&quot;;</a>"
p = Parser()
d = p.parse(string=xml)
a = d.root()
print 'A=\n%s' % a
assert str(a) == xml
b = Element('a')
b.setText('Me &&amp; &lt;b>my</b> shadow\'s <i>dog</i> love to \'play\' and sing "la,la,la";')
print 'B=\n%s' % b
assert str(b) == xml