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

from urllib2 import Request, urlopen, HTTPError
from suds import *
from wsdl import WSDL

class ServiceProxy(object):
    
    """ a lightweight soap based web service proxy"""

    def __init__(self, url, faults=True):
        self.faults = faults
        self.wsdl = WSDL(url)
        self.binding = self.wsdl.get_binding(faults)
        self.log = logger('serviceproxy')
        
    def get_methods(self):
        """get a list of methods provided by this service"""
        return self.binding.get_method_descriptions()
    
    def get_instance(self, type):
        """get an instance of the specified object type"""
        return self.binding.get_instance(type)
    
    def get_enum(self, type):
        """get an enumeration of the specified object type"""
        return self.binding.get_enum(type)
        
    def _send(self, method, *args):
        """"send the required soap message to invoke the specified method"""
        result = None
        headers = self.__headers()
        location = self.wsdl.get_location().encode('utf-8')
        msg = self.binding.get_message(method.name, *args)
        self.log.debug('sending to (%s)\nmessage:\n%s', location, msg)
        try:
            request = Request(location, msg, headers)
            fp = urlopen(request)
            reply = fp.read()
            result = self.__succeeded(method, reply)
        except HTTPError, e:
            result = self.__failed(method, e)
        return result
    
    def __headers(self):
        """ get http headers """
        return \
            { 'Content-Type' : 'text/xml' }
    
    def __succeeded(self, method, reply):
        """ request succeeded, process reply """
        self.log.debug('http succeeded:\n%s', reply)
        if len(reply) > 0:
            p = self.binding.get_reply(method.name, reply)
            if self.faults:
                return p
            else:
                return (200, p)
        else:
            return (200, None)
        
    def __failed(self, method, error):
        """ request failed, process reply based on reason """
        status, reason = (error.code, error.msg)
        reply = error.fp.read()
        if status == 500:
            if len(reply) > 0:
                return (status, self.binding.get_fault(reply))
            else:
                return (status, None)
        if self.faults:
            raise Exception((status, reason))
        else:
            return (status, None)
        
    def __str__(self):
        return unicode(self).encode('utf-8')
        
    def __unicode__(self):
        try:
            s = 'service (%s)' % self.wsdl.get_servicename()
            s += '\n\tprefixes:\n'
            prefixes = self.wsdl.mapped_prefixes()
            prefixes.sort()
            for p in prefixes:
                s += '\t\t%s = "%s"\n' % p
            s += '\n\tmethods:\n'
            for m in self.get_methods():
                s += '\t\t%s\n' % m
            return unicode(s)
        except Exception, e:
            self.log.exception(e)
            return u'service not available'
        
    def __repr__(self):
        return unicode(self).encode('utf-8')
    
    def __getattr__(self, name):
        try:
            return self.__getattribute__(name)
        except:
            pass
        if self.wsdl.get_operation(name) is None:
            raise MethodNotFound(name)
        return self.Method(self, name)

    class Method(object):
        """method wrapper""" 
        def __init__(self, proxy, name):
            self.proxy = proxy
            self.name = name
            
        def __call__(self, *args):
            """call the method"""
            result = None
            try:
                result = self.proxy._send(self, *args)
            except WebFault, e:
                if self.proxy.faults:
                    self.proxy.log.debug('raising (%s)', e)
                    raise e
                else:
                    self.proxy.log.debug('fault (%s)', e)
                    result = (500, e)
            return result
