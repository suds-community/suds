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
from suds.sudsobject import Object
from suds.builder import Builder
from suds.wsdl import WSDL


class ServiceProxy(object):
    
    """ a lightweight soap based web service proxy"""

    def __init__(self, url, **kwargs):
        self.__kwargs = kwargs
        self.__wsdl = WSDL(url)
        self.__schema = self.__wsdl.get_schema()
        self.__builder = Builder(self.__schema)
        self._log = logger('serviceproxy')
        
    def _get_methods(self):
        """get a list of methods provided by this service"""
        list = []
        for op in self.__wsdl.get_operations():
            method = op.attribute('name')
            binding = self.__wsdl.get_binding(method, **self.__kwargs)
            ptypes = binding.get_ptypes(method)
            params = ['%s{%s}' % (t[0], t[1].asref()[0]) for t in ptypes]
            m = '%s(%s)' % (method, ', '.join(params))
            list.append(m)
        return list
    
    def get_instance(self, name):
        """get an instance of an meta-object by type."""
        try:
            return self.__builder.build(name)
        except TypeNotFound, e:
            raise e
        except:
            raise BuildError(name)
    
    def get_enum(self, name):
        """ get an enumeration """
        type = self.__schema.find(name)
        if type is None:
            raise TypeNotFound(name)
        data = Object.instance(name)
        for e in type.get_children():
            enum = e.get_name()
            setattr(data, enum, enum)
        return data
        
    def _send(self, method, *args):
        """"send the required soap message to invoke the specified method"""
        result = None
        binding = self.__wsdl.get_binding(method.name, **self.__kwargs)
        headers = self.__headers(method.name)
        location = self.__wsdl.get_location().encode('utf-8')
        proxy = self.__kwargs.get('http_proxy', None)
        msg = binding.get_message(method.name, *args)
        self._log.debug('sending to (%s)\nmessage:\n%s', location, msg)
        try:
            request = Request(location, msg, headers)
            if proxy is not None:
                request.set_proxy(proxy)
            fp = urlopen(request)
            reply = fp.read()
            result = self.__succeeded(binding, method, reply)
        except HTTPError, e:
            result = self.__failed(binding, method, e)
        return result
    
    def _faults(self):
        """ get whether the proxy should raise web faults on error """
        return self.__kwargs.get('faults', True)
    
    def __headers(self, method):
        """ get http headers """
        action = self.__wsdl.get_soap_action(method)
        return \
            { 'SOAPAction': action, 
               'Content-Type' : 'text/xml' }
    
    def __succeeded(self, binding, method, reply):
        """ request succeeded, process reply """
        self._log.debug('http succeeded:\n%s', reply)
        if len(reply) > 0:
            p = binding.get_reply(method.name, reply)
            if self._faults():
                return p
            else:
                return (200, p)
        else:
            return (200, None)
        
    def __failed(self, binding, method, error):
        """ request failed, process reply based on reason """
        status, reason = (error.code, error.msg)
        reply = error.fp.read()
        self._log.debug('http failed:\n%s', reply)
        if status == 500:
            if len(reply) > 0:
                return (status, binding.get_fault(reply))
            else:
                return (status, None)
        if self._faults():
            raise Exception((status, reason))
        else:
            return (status, None)
        
    def __str__(self):
        return unicode(self).encode('utf-8')
        
    def __unicode__(self):
        try:
            s = 'service (%s)' % self.__wsdl.get_servicename()
            s += '\n\tprefixes:\n'
            prefixes = self.__wsdl.mapped_prefixes()
            prefixes.sort()
            for p in prefixes:
                s += '\t\t%s = "%s"\n' % p
            s += '\n\tmethods:\n'
            for m in self._get_methods():
                s += '\t\t%s\n' % m
            return unicode(s)
        except Exception, e:
            self._log.exception(e)
            return u'service not available'
        
    def __repr__(self):
        return unicode(self).encode('utf-8')
    
    def __getattr__(self, name):
        try:
            return self.__getattribute__(name)
        except:
            pass
        if self.__wsdl.get_operation(name) is None:
            raise MethodNotFound(name)
        return self.Method(self, name)

    class Method(object):
        """method wrapper""" 
        def __init__(self, proxy, name):
            self.proxy = proxy
            self.name = name
            self.log = proxy._log
            
        def __call__(self, *args):
            """call the method"""
            result = None
            try:
                result = self.proxy._send(self, *args)
            except WebFault, e:
                if self.proxy._faults():
                    self.log.debug('raising (%s)', e)
                    raise e
                else:
                    self.log.debug('fault (%s)', e)
                    result = (500, e)
            return result
