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


from suds.sax import splitPrefix, Namespace
from suds.sax.element import Element


class Doctor:
    
    def examine(self, root):
        pass


class Practice(Doctor):
    
    def __init__(self):
        self.doctors = []
        
    def add(self, doctor):
        self.doctors.append(doctor)

    def examine(self, root):
        for d in self.doctors:
            d.examine(root)
        return root


class ImportDoctor(Doctor):
    
    class Case:
        def __init__(self, ns):
            self.imports = 0
            self.refs = 0
            self.ns = ns
            self.names = []
            self.values = []

        def clear(self):
            self.imports = 0
            self.refs = 0

        def sick(self):
            return ( self.refs and not self.imports )

        def cure(self, root):
            imp = Element('import', ns=Namespace.xsdns)
            imp.set('namespace', self.ns)
            root.insert(imp)
            return root
        
        def examine(self, node):
            if self.findimport(node):
                return
            self.findrefs(node)
            return self

        def findimport(self, node):
            if node.name == 'import':
                ns = node.get('namespace')
                if self.ns == ns:
                    self.imports += 1
                return 1
            return 0
            
        def findrefs(self, node):
            for a in node.attributes:
                p, n = splitPrefix(a.name)
                if n not in ('ref', 'type'):
                    continue
                p, v = splitPrefix(a.value)
                if len(self.values):
                    if v not in self.values:
                        continue
                ns = node.resolvePrefix(p)
                if self.ns == ns[1]:
                    self.refs += 1
            return self

    def __init__(self):
        self.cases = []
        
    def add(self, c):
        self.cases.append(c)
        
    def clear(self):
        for c in self.cases:
            c.clear()
        
    def examine(self, root):
        self.clear()
        root.walk(self.check)
        for c in self.cases:
            if c.sick():
                c.cure(root)
        return self

    def check(self, node):
        for c in self.cases:
            c.examine(node)

