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
from suds.bindings.stack import Stack
from suds.bindings.marshaller import Marshaller as Base
from suds.sax import Element, splitPrefix

log = logger(__name__)


class Marshaller(Base):

    """ marshal a data object."""

    def __init__(self, binding):
        """constructor """
        Base.__init__(self, binding)
        self.path = Stack(log)

    def process(self, pdef, data):
        """ get the xml fragment for the data and root name """
        type = pdef[1]
        self.path.clear()
        self.path.push(type.get_name())
        root = self.__root(pdef)
        if isinstance(data, dict):
            data = Object.instance(dict=data)
        if isinstance(data, Object):
            for item in data.items():
                self.write(root, data, item[0], item[1])
        else:
            root.setText(tostr(data))
        return root
    
    def __root(self, pdef):
        """ create the root node """
        type = pdef[1]
        ns = type.namespace()
        if len(type):
            tag = ':'.join((ns[0], pdef[0]))
        else:
            tag = pdef[0]
        node = Element(tag)
        node.addPrefix(ns[0], ns[1])
        self.set_type(node, type)
        return node
    
    def write(self, parent, data, tag, object):
        """ write the content of the data object using the specified tag """
        self.path.push(tag)
        path = '.'.join(self.path)
        type = self.schema.find(path)
        if type is None:
            raise TypeNotFound(path)
        self.write_content(parent, data, tag, object, type)
        self.path.pop()         
       
    def write_content(self, parent, data, tag, object, type):
        """ write the content of the data object using the specified tag """
        if object is None:
            child = Element(tag)
            self.set_type(child, type)
            if self.binding.nil_supported:
                child.setnil()
            parent.append(child)
            return
        if isinstance(object, dict):
            object = Object.instance(dict=object)
        if isinstance(object, Object):
            child = Element(tag)
            self.set_type(child, type)
            self.process_metadata(object, child)
            parent.append(child)
            for item in object.items():
                self.write(child, object, item[0], item[1])
            return
        if isinstance(object, (list,tuple)):
            for item in object:
                self.path.pop()
                self.write(parent, data, tag, item)
            return
        if tag == '__text__':
            parent.setText(unicode(object))
        elif tag.startswith('_'):
            parent.set(tag[1:], unicode(object))
        else:
            child = Element(tag)
            self.set_type(child, type)
            child.setText(unicode(object))
            parent.append(child)
    
    def set_type(self, node, type):
        """ set the node's soap type """
        name, ns = type.asref()
        node.set('xsi:type', name)
        node.addPrefix(ns[0], ns[1])       

    def process_metadata(self, data, node):
        """ process the (xsd) within the metadata """
        md = data.__metadata__
        try:
            xsd = md.xsd
            self.set_type(node, (xsd.type, xsd.ns))
        except AttributeError:
            pass