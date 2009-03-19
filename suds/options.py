# This program is free software; you can redistribute it and/or modify
# it under the terms of the (LGPL) GNU Lesser General Public License as
# published by the Free Software Foundation; either version 3 of the 
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library Lesser General Public License for more details at
# ( http://www.gnu.org/licenses/lgpl.html ).
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
# written by: Jeff Ortel ( jortel@redhat.com )

"""
Options classes.
"""

from suds.transport import Transport, Cache, NoCache
from suds.wsse import Security

class Options(object):
    """
    Options:
        - B{faults} - Raise faults raised by server (default:True),
             else return tuple from service method invocation as (http code, object).
                - type: I{bool}
        - B{port} - The default service port.  (not tcp port).
                - type: I{str}
        - B{location} - This overrides the service port address I{URL} defined in the WSDL.
                - type: I{str}
        - B{proxy} - An http proxy to be specified on requests (default:None).
             The proxy is defined as {protocol:proxy,}
                - type: I{dict}
        - B{transport} - The message transport
                - type: L{Transport}
        - B{cache} - The http I{transport} cache.
                - type: L{Cache}
        - B{headers} - Extra HTTP headers
                - type: I{dict}
                    - I{str} B{http} - The I{http} protocol proxy URL.
                    - I{str} B{https} - The I{https} protocol proxy URL.
        - B{soapheaders} - The soap headers to be included in the soap message.
                - type: I{any}
        - B{username} - The username used for http authentication.
                - type: I{str}
        - B{password} - The password used for http authentication.
                - type: I{str}
        - B{wsse} - The web services I{security} provider object.
                - type: L{Security}
    """

    __options__ = \
    dict(
        faults=(bool, True),
        transport=(Transport, None),
        cache=(Cache, NoCache()),
        port=(basestring, None),
        location=(basestring, None),
        proxy=(dict, {}), 
        headers=(dict, {}),
        soapheaders=((), ()),
        username=(basestring, None),
        password=(basestring, None),
        wsse=(Security, None),
    )
    
    def __init__(self, **kwargs):
        constraint = Constraint()
        for p in self.__options__.items():
            n = p[0]
            classes = p[1][0]
            constraint.classes[n] = classes
            constraint.keys.append(n)
        self.__constraint__ = constraint
        self.prime()
        self.set(**kwargs)
        
    def __setattr__(self, name, value):
        builtin =  name.startswith('__') and name.endswith('__')
        if not builtin:
            self.__constraint__.validate(name, value)
        self.__dict__[name] = value
 
    def prime(self):
       for p in self.__options__.items():
            name = p[0]
            value = p[1][1]
            self.__dict__[name] = value
            
    def set(self, **kwargs):
        for p in kwargs.items():
            name = p[0]
            value = p[1]
            setattr(self, name, value)
            
    def get(self, name, *d):
        value = getattr(self, name)
        p = self.__options__.get(name)
        default = p[1]
        if value == default and len(d):
            value = d[0]
        return value


class Constraint:

    def __init__(self):
        self.keys = []
        self.classes = {}

    def validate(self, name, value):
        if len(self.keys):
            self.vkeys(name)
        if len(self.classes):
            self.vclasses(name, value)

    def vkeys(self, name):
        if name not in self.keys:
            msg = '"%s" not in: %s' % (name, self.keys)
            raise AttributeError(msg)

    def vclasses(self, name, value):
        if value is None:
            return
        classes = self.classes.get(name, [])
        if not isinstance(classes, (list,tuple)):
            classes = (classes,)
        if len(classes) and not isinstance(value, classes):
            msg = '"%s" must be: %s' % (name, classes)
            raise AttributeError(msg)
