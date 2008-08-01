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

"""
The I{builder} module provides an wsdl/xsd defined types factory
"""

from suds import *
from suds.sudsobject import Factory
from suds.resolver import PathResolver

log = logger(__name__)


class Builder:
    """ Builder used to construct an object for types defined in the schema """
    
    def __init__(self, wsdl):
        """
        @param wsdl: A schema object.
        @type wsdl: L{wsdl.Definitions}
        """
        self.resolver = PathResolver(wsdl)
        
    def build(self, name):
        """ build a an object for the specified typename as defined in the schema """
        if isinstance(name, basestring):
            type = self.resolver.find(name)
            if type is None:
                raise TypeNotFound(name)
        else:
            type = name
        cls = type.name
        if len(type):
            data = Factory.object(cls)
        else:
            data = Factory.property(cls)
        md = data.__metadata__
        md.__type__ = type
        history = []
        self.add_attributes(data, type)
        for c in type.children:
            if c.any(): continue
            self.process(data, c, history)
        return data
            
    def process(self, data, type, history):
        """ process the specified type then process its children """
        if type in history:
            return
        history.append(type)
        resolved = type.resolve()
        self.add_attributes(data, type)
        value = None
        if type.unbounded():
            value = []
        else:
            children = resolved.children
            if len(children) > 0:
                value = Factory.object(type.name)
        setattr(data, type.name, value)
        if value is not None:
            data = value
        if not isinstance(data, list):
            for c in resolved.children:
                if c.any(): continue
                self.process(data, c, history)

    def add_attributes(self, data, type):
        """ add required attributes """
        for a in type.attributes:
            if a.required():
                name = '_%s' % a.name
                value = a.get_default()
                setattr(data, name, value)