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

from logging import getLogger
from suds.sax import splitPrefix, Namespace
from suds.sax.element import Element

log = getLogger(__name__)


class Doctor:
    """
    Schema Doctor.
    """
    def examine(self, root):
        """
        Examine and repair the schema (if necessary).
        @param root: A schema root element.
        @type root: L{Element}
        """
        pass


class Practice(Doctor):
    """
    A collection of doctors.
    @ivar doctors: A list of doctors.
    @type doctors: list
    """
    
    def __init__(self):
        self.doctors = []
        
    def add(self, doctor):
        """
        Add a doctor to the practice
        @param doctor: A doctor to add.
        @type doctor: L{Doctor}
        """
        self.doctors.append(doctor)

    def examine(self, root):
        for d in self.doctors:
            d.examine(root)
        return root


class ImportDoctor(Doctor):
    """
    Doctor used to fix missing imports.
    @ivar tns: A list of target namespaces.
    @type tns: list
    @ivar namespaces: A list of namespaces to add import for.
    @type namespaces: list of (ns, location)
    """

    def __init__(self, *tns):
        """
        @param tns: A list of target namespaces
        @type tns: str
        """
        self.tns = tns
        self.namespaces = []
        
    def add(self, ns, location=None):
        """
        Add a namesapce to be checked.
        @param ns: A namespace.
        @type ns: str
        @param location: A schema location.
        @type location: str
        """
        entry = (ns,location)
        self.namespaces.append(entry)
        
    def examine(self, root):
        found = []
        if not self.matchtarget(root):
            return
        for c in root.children:
            for entry in self.namespaces:
                if self.matchimport(c, entry):
                    found.append(entry[0])
        for entry in self.namespaces:
            if entry[0] not in found:
                self.addimport(root, entry)
            
    def addimport(self, root, entry):
        node = Element('import', ns=Namespace.xsdns)
        node.set('namespace', entry[0])
        if entry[1] is not None:
            node.set('schemaLocation', entry[1])
        log.debug('add: %s', node)
        root.insert(node)
            
    def matchtarget(self, root):
        tns = root.get('targetNamespace')
        return ( tns in self.tns )
    
    def matchimport(self, node, entry):
        if node.name == 'import':
            ns = node.get('namespace')
            if entry[0] == ns:
                return 1
        return 0
