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

import httplib
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
        location = self.wsdl.get_location()
        msg = self.binding.get_message(method.name, *args)
        http = httplib.HTTP(location[0], int(location[1]))
        http.putrequest("POST", location[2])
        http.putheader("Host", location[0])
        http.putheader("user-agent", "Python post")
        http.putheader("Content-type", "text/xml; charset=\"UTF-8\"")
        http.putheader("Content-length", "%d" % len(msg))
        http.putheader("SOAPAction", "\"\"")
        http.endheaders()
        self.log.debug('sending\ndestination:\n  (%s)\nmessage:%s', location, msg)
        try:
            http.send(msg)
            result = self.__receive(http, method)
        finally:
            http.close()
        return result 
        
    def __receive(self, http, method):
        """receive the http reply for a sent message"""
        status, message, header = http.getreply()
        self.log.debug('received response (%s, %s)', status, message)
        reply = http.getfile().read()
        self.log.debug('reply (%s)', reply)
        if status == 500:
            if len(reply) > 0:
                return (status, self.binding.get_fault(reply))
            else:
                return (status, None)
        if status == 200:
            if len(reply) > 0:
                p = self.binding.get_reply(method.name, reply)
                if self.faults:
                    return p
                else:
                    return (status, p)
        if self.faults:
            raise Exception('failed, http status (%s)', status)
        else:
            return (status, None)
        
    def __str__(self):
        return unicode(self).encode('utf-8')
        
    def __unicode__(self):
        try:
            s = 'service (%s)' % self.wsdl.get_servicename()
            s += '\n\tprefixes:\n'
            for p in self.wsdl.mapped_prefixes():
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
                    
        


