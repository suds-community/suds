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


class Builder:
    """ Builder used to construct property object for types defined in the schema """
    
    def __init__(self, schema):
        """ initialize with a schema object """
        self.schema = schema
        
    def build(self, typename):
        """ build a property object for the specified typename as defined in the schema """
        type = self.schema.get_type(typename)
        if type is None:
            raise TypeNotFound(typename)
        p = Property()
        p.__type__ = type.get_name()
        md = p.get_metadata()
        md.xsd = Property()
        md.xsd.type = type.get_name()
        for c in type.get_children():
            self.process(p, c)
        return p
            
    def process(self, p, type):
        """ process the specified type then process its children """
        history = [type]
        resolved = type.resolve(history)
        value = None
        if type.unbounded():
            value = []
        else:
            children = resolved.get_children()
            if len(children) > 0:
                value = Property()
        p.set(type.get_name(), value)
        if value is not None:
            p = value
        if not isinstance(p, list):
            for c in resolved.get_children():
                self.process(p, c)
