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

import logging
import socket

VERSION = "0.2.3"

#
# socket timeout - 10 seconds
#

socket.setdefaulttimeout(10)

#
# Exceptions
#

class MethodNotFound(Exception):
    def __init__(self, name):
        Exception.__init__(self, "Method not found: '%s'" % name)
    
class TypeNotFound(Exception):
    def __init__(self, name):
        Exception.__init__(self, "Type not found: '%s'" % tostr(name))
    
class BuildError(Exception):
    msg = \
        """
        An error occured while building a instance of (%s).  As a result
        the object you requested could not be constructed.  It is recommended
        that you construct the type manually uisng a Suds object.
        Please notify the project mantainer of this error.
        """
    def __init__(self, name):
        Exception.__init__(self, BuildError.msg % name)
    
class WebFault(Exception):
    def __init__(self, fault):
        if hasattr(fault, 'faultstring'):
            Exception.__init__(self, "Server raised fault: '%s'" % fault.faultstring)
        self.fault = fault

#
# Logging
#

def logger(name=None):
    if name is None:
        return logging.getLogger()
    fmt =\
        '%(asctime)s [%(levelname)s] %(funcName)s() @%(filename)s:%(lineno)d\n%(message)s\n'
    logger = logging.getLogger(name)
    root = logging.getLogger()
    if not root.handlers:
        root.setLevel(logging.INFO)
        __handler = logging.StreamHandler()
        __handler.setFormatter(logging.Formatter(fmt))
        root.addHandler(__handler)
    return logger

class Repr:
    def __init__(self, x):
        self.x = x
    def __str__(self):
        return repr(self.x)  

#
# Utility
#

def tostr(object, encoding=None):
    """ get a unicode safe string representation of an object """
    if isinstance(object, basestring):
        if encoding is None:
            return object
        else:
            return object.encode(encoding)
    if isinstance(object, tuple):
        s = ['(']
        for item in object:
            if isinstance(item, basestring):
                s.append(item)
            else:
                s.append(tostr(item))
            s.append(', ')
        s.append(')')
        return ''.join(s)
    if isinstance(object, list):
        s = ['[']
        for item in object:
            if isinstance(item, basestring):
                s.append(item)
            else:
                s.append(tostr(item))
            s.append(', ')
        s.append(']')
        return ''.join(s)
    if isinstance(object, dict):
        s = ['{']
        for item in object.items():
            if isinstance(item[0], basestring):
                s.append(item[0])
            else:
                s.append(tostr(item[0]))
            s.append(' = ')
            if isinstance(item[1], basestring):
                s.append(item[1])
            else:
                s.append(tostr(item[1]))
            s.append(', ')
        s.append('}')
        return ''.join(s)
    try:
        return unicode(object)
    except:
        return str(object)
    
def objid(obj):
    return obj.__class__.__name__\
        +':'+hex(id(obj))
