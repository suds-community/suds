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

import sys
if sys.version_info < (2,5):
    from lxml.etree import Element, tostring
else:
    from xml.etree.ElementTree import Element, tostring

class DocumentWriter:

    def __init__(self, atpfx='_'):
        """
        initialize the writer, specify the prefix for properties to be written as attributes
        using the atpfx (attribute prefix) param.
        """
        self.atpfx = atpfx

    def tostring(self, root, object):
        """ get the xml string value of the dictionary and root name """
        dict = self.translate(object)
        parent = Element(root)
        for item in dict.items():
            self.writecontent(parent, item[0], item[1])
        return tostring(parent)
       
    def writecontent(self, parent, tag, object):
        """ write the content of the property object using the specified tag """
        if object is None:
            return
        object = self.translate(object)
        if isinstance(object, dict):
            child = Element(tag)
            parent.append(child)
            for item in object.items():
                self.writecontent(child, item[0], item[1])
            return
        if isinstance(object, list) or isinstance(object, tuple):
            for item in object:
                self.writecontent(parent, tag, item)
            return
        if self.atpfx and tag.startswith(self.atpfx):
            parent.attrib[tag[len(self.atpfx):]] = str(object)
        else:
            child = Element(tag)
            child.text = str(object)
            parent.append(child)
            
    def translate(self, object):
        """ attempt to translate the object into a dictionary """
        result = object
        try:
            result = object.dict()
        except:
            pass
        return result
