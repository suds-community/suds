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
from suds.bindings.marshaller import Marshaller as Base
from suds.sax import Element, splitPrefix


class Marshaller(Base):

    """ marshal a property object."""

    def __init__(self, binding):
        """constructor """
        Base.__init__(self, binding)
        self.path = []

    def process(self, pdef, property):
        """ get the xml fragment for the property and root name """
        type = pdef[1]
        self.path = [type.get_name()]
        root = self.__root(pdef)
        if isinstance(property, dict):
            property = Property(property)
        if isinstance(property, Property):
            for item in property.get_items():
                self.write(root, property, item[0], item[1])
        else:
            root.setText(tostr(property))
        return root
    
    def __root(self, pdef):
        """ create the root node """
        type = pdef[1]
        ns = type.namespace()
        tag = ':'.join((ns[0], pdef[0]))
        node = Element(tag)
        node.addPrefix(ns[0], ns[1])
        ref,refns = type.asref()
        node.attribute('xsi:type', ref)
        node.addPrefix(refns[0], refns[1])
        return node
    
    def write(self, parent, property, tag, object):
        """ write the content of the property object using the specified tag """
        self.path.append(tag)
        st = self.soaptype(tag)
        self.write_content(parent, property, tag, object, st)
        self.path.pop()         
       
    def write_content(self, parent, property, tag, object, st):
        """ write the content of the property object using the specified tag """
        if object is None:
            child = Element(tag)
            self.set_type(child, st)
            if self.binding.nil_supported:
                child.setnil()
            parent.append(child)
            return
        if isinstance(object, dict):
            object = Property(object)
        if isinstance(object, Property):
            child = Element(tag)
            self.set_type(child, st)
            self.process_metadata(object, child)
            parent.append(child)
            for item in object.get_items():
                self.write(child, object, item[0], item[1])
            return
        if isinstance(object, (list,tuple)):
            for item in object:
                self.path.pop()
                self.write(parent, property, tag, item)
            return
        if tag == '__text__':
            parent.setText(unicode(object))
        elif tag.startswith('_'):
            parent.attribute(tag[1:], unicode(object))
        else:
            child = Element(tag)
            self.set_type(child, st)
            child.setText(unicode(object))
            parent.append(child)
            
    def soaptype(self, tag):
        """ get the soap type for the specified type """
        path = '.'.join(self.path)
        type = self.schema.find(path)
        if type is None:
            raise TypeNotFound(path)
        ref = type.ref()
        if ref is None:
            ref = tag
        p,v = splitPrefix(ref)
        if p is None:
            ns = type.namespace()
        else:
            ref = v
            ns = type.root.resolvePrefix(p)
        return (ref, ns)
    
    def set_type(self, node, st):
        """ set the node's soap type """
        name, ns = st
        node.attribute('xsi:type', ':'.join((ns[0], name)))
        node.addPrefix(ns[0], ns[1])       

    def process_metadata(self, p, node):
        """ process the (xsd) within the metadata """
        md = p.get_metadata()
        md = md.xsd
        if md is not None:
            self.set_type(node, (md.type, md.ns))