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

from urllib2 import Request, urlopen, urlparse, HTTPError
from suds import *
from suds.sudsobject import Object
from suds.builder import Builder
from suds.wsdl import WSDL


class ServiceProxy(object):
    
    """ 
    A lightweight soap based web service proxy.
    Flags:
       * faults = Raise faults raised by server (default:True), else return tuple from service method invocation
                        as (http code, object).
       * nil_supported = The bindings will set the xsi:nil="true" on nodes that have a value=None when this
                                      flag is True (default:True).  Otherwise, an empty node <x/> is sent.
       * proxy = An http proxy to be specified on requests (default:{}).
                       The proxy is defined as {protocol:proxy,}
    """

    def __init__(self, url, **kwargs):
        client = Client(url, **kwargs)
        self.__client__ = client
        self.__factory__ = Factory(client.schema)
    
    def get_instance(self, name):
        """get an instance of an meta-object by type."""
        return self.__factory__.get_instance(name)
    
    def get_enum(self, name):
        """ get an enumeration """
        return self.__factory__.get_enum(name)
 
    def __str__(self):
        return str(self.__client__)
        
    def __unicode__(self):
        return unicode(self.__client__)
    
    def __getattr__(self, name):
        builtin =  name.startswith('__') and name.endswith('__')
        if builtin:
            return self.__dict__[name]
        operation = self.__client__.wsdl.get_operation(name)
        if operation is None:
            raise MethodNotFound(name)
        method = Method(self.__client__, name)
        return method


class Method(object):
    
    """method wrapper""" 
    
    def __init__(self, client, name):
        self.client = client
        self.name = name
        self.log = client.log
        
    def __call__(self, *args):
        """call the method"""
        result = None
        try:
            result = self.client.send(self, *args)
        except WebFault, e:
            if self.client.faults:
                self.log.debug('raising (%s)', e)
                raise e
            else:
                self.log.debug('fault (%s)', e)
                result = (500, e)
        return result

    
class Factory:
    
    """ A factory for instantiating types defined in the wsdl """
    
    def __init__(self, schema):
        self.schema = schema
        self.builder = Builder(schema)
        
    def get_instance(self, name):
        """get an instance of an meta-object by type."""
        try:
            return self.builder.build(name)
        except TypeNotFound, e:
            raise e
        except:
            raise BuildError(name)
    
    def get_enum(self, name):
        """ get an enumeration """
        type = self.schema.find(name)
        if type is None:
            raise TypeNotFound(name)
        data = Object.instance(name)
        for e in type.get_children():
            enum = e.get_name()
            setattr(data, enum, enum)
        return data


class Client:
    
    """ a lightweight soap based web client"""

    def __init__(self, url, **kwargs):
        self.kwargs = kwargs
        self.faults = self.kwargs.get('faults', True)
        self.wsdl = WSDL(url)
        self.schema = self.wsdl.get_schema()
        self.builder = Builder(self.schema)
        self.log = logger('serviceproxy')
        
    def send(self, method, *args):
        """"send the required soap message to invoke the specified method"""
        result = None
        binding = self.wsdl.get_binding(method.name, **self.kwargs)
        headers = self.__headers(method.name)
        location = self.wsdl.get_location().encode('utf-8')
        msg = binding.get_message(method.name, *args)
        self.log.debug('sending to (%s)\nmessage:\n%s', location, msg)
        try:
            request = Request(location, msg, headers)
            self.__set_proxies(location, request)
            fp = urlopen(request)
            reply = fp.read()
            result = self.__succeeded(binding, method, reply)
        except HTTPError, e:
            result = self.__failed(binding, method, e)
        return result
    
    def __set_proxies(self, location, request):
        """ set the proxies for the request """
        proxies = self.kwargs.get('proxy', {})
        protocol = urlparse.urlparse(location).scheme       
        proxy = proxies.get(protocol, None)
        if proxy is not None:
            self.log.info('proxy %s used for %s', proxy, location)
            request.set_proxy(proxy, protocol)
    
    def __headers(self, method):
        """ get http headers """
        action = self.wsdl.get_soap_action(method)
        return \
            { 'SOAPAction': action, 
               'Content-Type' : 'text/xml' }
    
    def __succeeded(self, binding, method, reply):
        """ request succeeded, process reply """
        self.log.debug('http succeeded:\n%s', reply)
        if len(reply) > 0:
            p = binding.get_reply(method.name, reply)
            if self.faults:
                return p
            else:
                return (200, p)
        else:
            return (200, None)
        
    def __failed(self, binding, method, error):
        """ request failed, process reply based on reason """
        status, reason = (error.code, error.msg)
        reply = error.fp.read()
        self.log.debug('http failed:\n%s', reply)
        if status == 500:
            if len(reply) > 0:
                return (status, binding.get_fault(reply))
            else:
                return (status, None)
        if self.faults:
            raise Exception((status, reason))
        else:
            return (status, None)
        
    def __get_methods(self):
        """get a list of methods provided by this service"""
        list = []
        for op in self.wsdl.get_operations():
            method = op.attribute('name')
            binding = self.wsdl.get_binding(method, **self.kwargs)
            ptypes = binding.get_ptypes(method)
            params = ['%s{%s}' % (t[0], t[1].asref()[0]) for t in ptypes]
            m = '%s(%s)' % (method, ', '.join(params))
            list.append(m)
        return list
        
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
            for m in self.__get_methods():
                s += '\t\t%s\n' % m
            return unicode(s)
        except Exception, e:
            self.log.exception(e)
            return u'service not available'
