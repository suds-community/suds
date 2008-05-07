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
from suds.sudsobject import Object
from suds.bindings.marshaller import Marshaller as Base
from suds.sax import Element

class Marshaller(Base):
    """ marshal a object."""

    def __init__(self, binding):
        """constructor """
        Base.__init__(self, binding)

    def process(self, pdef, data):
        """ get the xml fragment for the data and root name """
        node = Element(pdef[0])
        if isinstance(data, dict):
            data = Object.instance(dict=data)
        if isinstance(data, Object):
            for item in data.items():
                self.write_content(node, data, item[0], item[1])
        else:
            node.setText(tostr(data))
        return node
       
    def write_content(self, parent, data, tag, object):
        """ write the content of an object using the specified tag """
        if object is None:
            child = Element(tag)
            if self.binding.nil_supported:
                child.set('xsi:nil', 'true')
            parent.append(child)
            return
        if isinstance(object, dict):
            object = Object.instance(dict=object)
        if isinstance(object, Object):
            child = Element(tag)
            self.process_metadata(object, child)
            parent.append(child)
            for item in object.items():
                self.write_content(child, object, item[0], item[1])
            return
        if isinstance(object, (list,tuple)):
            for item in object:
                self.write_content(parent, data, tag, item)
            return
        try:
            md = data.__metadata__
            parent.setText(unicode(md.xml.text))
        except AttributeError:
            pass
        if isinstance(tag, basestring) and \
                tag.startswith('_'):
            parent.set(tag[1:], unicode(object))
        else:
            child = Element(tag)
            child.setText(unicode(object))
            parent.append(child)

    def process_metadata(self, data, node):
        """ process the (xsd) within the metadata """
        md = data.__metadata__
        try:
            xsd = md.xsd
            node.set('xsi:type', xsd.type)
        except AttributeError:
            pass