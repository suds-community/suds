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
from suds.property import Property
from suds.sax import Element

class Marshaller:
    """ marshal a property object."""

    def __init__(self, schema):
        """constructor """
        self.schema = schema

    def process(self, root, property):
        """ get the xml string value of the property and root name """
        parent = Element(root)
        if isinstance(property, dict):
            property = Property(property)
        for item in property.get_items():
            self.write_content(parent, property, item[0], item[1])
        return str(parent)
       
    def write_content(self, parent, property, tag, object):
        """ write the content of the property object using the specified tag """
        if object is None:
            return
        if isinstance(object, dict):
            object = Property(object)
        if isinstance(object, Property):
            child = Element(tag)
            self.process_metadata(object, child)
            parent.append(child)
            for item in object.get_items():
                self.write_content(child, object, item[0], item[1])
            return
        if isinstance(object, (list,tuple)):
            for item in object:
                self.write_content(parent, property, tag, item)
            return
        if tag.startswith('_'):
            parent.attribute(tag[1:], str(object))
        elif tag == 'text':
            parent.setText(str(object))
        else:
            child = Element(tag)
            child.setText(str(object))
            parent.append(child)

    def process_metadata(self, p, node):
        """ process the (xsd) within the metadata """
        md = p.get_metadata()
        md = md.xsd
        if md is None: return
        md = md.type
        if md is None: return
        node.attribute('xsi:type', md)