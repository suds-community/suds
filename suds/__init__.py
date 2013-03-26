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
Suds is a lightweight SOAP Python client that provides a
service proxy for Web Services.
"""

import sys

#
# Project properties
#

from version import __build__, __version__

#
# Exceptions
#

class MethodNotFound(Exception):
    def __init__(self, name):
        Exception.__init__(self, "Method not found: '%s'" % name)

class PortNotFound(Exception):
    def __init__(self, name):
        Exception.__init__(self, "Port not found: '%s'" % name)

class ServiceNotFound(Exception):
    def __init__(self, name):
        Exception.__init__(self, "Service not found: '%s'" % name)

class TypeNotFound(Exception):
    def __init__(self, name):
        Exception.__init__(self, "Type not found: '%s'" % tostr(name))

class BuildError(Exception):
    msg = """
        An error occured while building an instance of (%s).  As a result
        the object you requested could not be constructed.  It is recommended
        that you construct the type manually using a Suds object.
        Please open a ticket with a description of this error.
        Reason: %s
        """
    def __init__(self, name, exception):
        Exception.__init__(self, BuildError.msg % (name, exception))

class SoapHeadersNotPermitted(Exception):
    msg = """
        Method (%s) was invoked with SOAP headers.  The WSDL does not
        define SOAP headers for this method.  Retry without the soapheaders
        keyword argument.
        """
    def __init__(self, name):
        Exception.__init__(self, self.msg % name)

class WebFault(Exception):
    def __init__(self, fault, document):
        if hasattr(fault, 'faultstring'):
            Exception.__init__(self, smart_str("Server raised fault: '%s'" %
                fault.faultstring))
        self.fault = fault
        self.document = document

#
# Logging
#

class Repr:
    def __init__(self, x):
        self.x = x
    def __str__(self):
        return repr(self.x)

#
# Utility
#

def smart_str(s, encoding='utf-8', errors='strict'):
    """
    Returns a bytestring version of 's', encoded as specified in 'encoding'.

    Taken from django.
    """
    if not isinstance(s, basestring):
        try:
            return str(s)
        except UnicodeEncodeError:
            if isinstance(s, Exception):
                # An Exception subclass containing non-ASCII data that does not
                # know how to print itself properly. We should not raise a
                # further exception.
                return ' '.join([smart_str(arg, encoding, errors) for arg in s]
                    )
            return unicode(s).encode(encoding, errors)
    if isinstance(s, unicode):
        return s.encode(encoding, errors)
    if s and encoding != 'utf-8':
        return s.decode('utf-8', errors).encode(encoding, errors)
    return s

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

class null:
    """
    The I{null} object.
    Used to pass NULL for optional XML nodes.
    """
    pass

def objid(obj):
    return obj.__class__.__name__\
        +':'+hex(id(obj))

#
# Python 3 compatibility
#

# Idea from 'http://lucumr.pocoo.org/2011/1/22/forwards-compatible-python'.
class UnicodeMixin(object):
    if sys.version_info >= (3, 0):
        # For Python 3, __str__() and __unicode__() should be identical.
        __str__ = lambda x: x.__unicode__()
    else:
        __str__ = lambda x: unicode(x).encode('utf-8')

# Compatibility wrappers to convert between bytes and strings.
if sys.version_info >= (3, 0):
    def str2bytes(s):
        if isinstance(s, bytes):
            return s
        return s.encode('latin1')
    def bytes2str(s):
        if isinstance(s, str):
            return s
        return s.decode('latin1')
else:
    # For Python 2 bytes and string types are the same.
    str2bytes = lambda s: s
    bytes2str = lambda s: s

#   Quick-fix helper function for making some __str__ & __repr__ function
# implementations originally returning UTF-8 encoded strings portable to Python
# 3. The original implementation worked in Python 2 but in Python 3 this would
# return a bytes object which is not an allowed return type for those calls. In
# Python 3 on the other hand directly returning a unicode string from them is
# perfectly valid and there is no need for converting those strings to utf-8
# encoded strings in the first place.
#   The original implementation classes should most likely be refactored to use
# unicode for internal representation and convert to encoded bytes only at the
# last possible moment, e.g. on an explicit __str__/__repr__ call.
if sys.version_info >= (3, 0):
    str_to_utf8_in_py2 = lambda str: str
else:
    str_to_utf8_in_py2 = lambda str: str.encode('utf-8')


import client
