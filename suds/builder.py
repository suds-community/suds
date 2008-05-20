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
from suds.resolver import PathResolver

log = logger(__name__)


class Builder:
    """ Builder used to construct an object for types defined in the schema """
    
    def __init__(self, schema):
        """
        @param schema: A schema object.
        @type schema: L{schema.Schema}
        """
        self.resolver = PathResolver(schema)
        
    def build(self, typename):
        """ build a an object for the specified typename as defined in the schema """
        type = self.resolver.find(typename)
        if type is None:
            raise TypeNotFound(typename)
        data = Object.__factory__.instance(type.get_name())
        md = data.__metadata__
        md.__type__ = type
        md.xsd = Object.__factory__.metadata()
        self.add_attributes(data, type)
        for c in type.get_children():
            self.process(data, c)
        return data
            
    def process(self, data, type):
        """ process the specified type then process its children """
        resolved = type.resolve()
        self.add_attributes(data, type)
        value = None
        if type.unbounded():
            value = []
        else:
            children = resolved.get_children()
            if len(children) > 0:
                value = Object.__factory__.instance(type.get_name())
        setattr(data, type.get_name(), value)
        if value is not None:
            data = value
        if not isinstance(data, list):
            for c in resolved.get_children():
                self.process(data, c)

    def add_attributes(self, data, type):
        """ add required attributes """
        for a in type.get_attributes():
            if a.required():
                name = '_%s' % a.get_name()
                value = a.get_default()
                setattr(data, name, value)