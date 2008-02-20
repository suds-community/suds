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
   
from suds.property import Property
from suds.sax import Element, Attribute

class DocumentWriter:

    def __init__(self, atpfx='_'):
        """
        initialize the writer, specify the prefix for properties to be written as attributes
        using the atpfx (attribute prefix) param.
        """
        self.atpfx = atpfx

    def tostring(self, root, property):
        """ get the xml string value of the property and root name """
        parent = Element(root)
        for a in self.xmlnsattrs(property):
            parent.append(a)
        if isinstance(property, dict):
            property = Property(property)
        for item in property.get_items():
            self.writecontent(parent, property, item[0], item[1])
        return str(parent)
       
    def writecontent(self, parent, property, tag, object):
        """ write the content of the property object using the specified tag """
        if object is None:
            return
        if isinstance(object, dict):
            object = Property(object)
        if isinstance(object, Property):
            child = Element(self.tag(property, tag))
            for a in self.xmlnsattrs(property, tag):
                child.append(a)
            parent.append(child)
            for item in object.get_items():
                self.writecontent(child, object, item[0], item[1])
            return
        if isinstance(object, list) or isinstance(object, tuple):
            for item in object:
                self.writecontent(parent, property, tag, item)
            return
        if tag.startswith(self.atpfx):
            parent.attribute(self.tag(property, tag), str(object))
        elif tag == 'text':
            parent.setText(str(object))
        else:
            child = Element(self.tag(property, tag))
            child.setText(str(object))
            parent.append(child)
    
    def tag(self, property, tag):
        """
        format the tag based on the attribute prefix detection
        and the prefix found in the metadata.
        """
        md = property.get_metadata(tag)
        tag = self.stripatpfx(tag)
        if md is not None and md.prefix is not None:
            return '%s:%s' % (md.prefix, tag)
        else:
            return tag
        
    def stripatpfx(self, tag):
        """ strip the leading attribute prefix """
        if tag.startswith(self.atpfx):
            return tag[len(self.atpfx):]
        else:
            return tag
        
    def xmlnsattrs(self, property, tag=Property.__self__):
        """ get the list of xmlns declarations """
        attrs = []
        md = property.get_metadata(tag)
        if md is not None:
            if md.expns is not None:
                attrs.append(Attribute('xmlns', md.expns))
            if md.nsprefixes is not None:
                for p in md.nsprefixes:
                    a = Attribute('xmlns:%s'%p[0], p[1])
                    attrs.append(a)
        return attrs
            

