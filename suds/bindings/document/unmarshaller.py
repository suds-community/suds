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


class Unmarshaller:
    """ property unmarshaller """
    
    reserved = { 'class':'cls', 'def':'dfn', }
    
    booleans = { 'true':True, 'false':False }
    
    def __init__(self, schema):
        self.schema = schema
        self.path = []
            
    def process(self, node):
        """
        process the specified node and convert the XML document into
        a property object.
        """
        data = Property()
        self.path.append(node.name)
        self.import_attrs(data, node)
        self.import_children(data, node)
        self.import_text(data, node)
        self.path.pop()
        return self.result(data, node)
    
    def import_attrs(self, data, node):
        """import attribute nodes into the data structure"""
        for attr in node.attributes:
            if self.xstype(attr):
                md = data.get_metadata()
                md.xsd = Property()
                md.xsd.type = attr.value
                continue
            key = attr.name
            key = '_%s' % self.reserved.get(key, key)
            value = attr.getValue()
            value = self.booleans.get(value.lower(), value)
            data[key] = value

    def import_children(self, data, node):
        """import child nodes into the data structure"""
        for child in node.children:
            cdata = self.process(child)
            key = self.reserved.get(child.name, child.name)
            if key in data:
                v = data[key]
                if isinstance(v, list):
                    data[key].append(cdata)
                else:
                    data[key] = [v, cdata]
                continue
            if self.unbounded(key):
                if cdata is None:
                    data[key] = []
                else:
                    data[key] = [cdata,]
            else:
                data[key] = cdata
    
    def import_text(self, data, node):
        """import text nodes into the data structure"""
        if node.text is None: return
        if len(node.text):
            value = node.getText()
            value = self.booleans.get(value.lower(), value)
            data['text'] = value
            
    def result(self, data, node):
        """
        perform final processing of the resulting data structure as follows:
        simple elements (not attrs or children) with text nodes will have a string 
        result equal to the value of the text node.
        """
        try:
            if len(data) == 0:
                return None
            if len(data) == 1 and self.bounded(node.name):
                return data['text']
        except:
            pass
        return data
    
    def unbounded(self, nodename):
        """ determine if the named node is unbounded (max > 1) """
        try:
            path = list(self.path)
            path.append(nodename)
            path = '.'.join(path)
            type = self.schema.get_type(path)
            return type.unbounded()
        except:
            return False
    
    def bounded(self, nodename):
        """ determine if the named node is bounded (max=1) """
        return (not unbounded(nodename))

    def xstype(self, a):
        """ determine if the attr is a xsi:type """
        return ( a.prefix == 'xsi' and a.name == 'type' )