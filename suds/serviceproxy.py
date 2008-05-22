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
The service proxy provides access to web services.
"""

from cookielib import CookieJar
from urllib2 import Request, urlopen, urlparse, HTTPError
from suds import *
from suds.sudsobject import Object
from suds.schema import Enumeration
from suds.resolver import PathResolver
from suds.builder import Builder
from suds.wsdl import WSDL

log = logger(__name__)


def get_factory(p):
    """
    Get an object factory that is associated with the specified service proxy.
    The factory is used to create instances of object defined in the wsdl.
    @param p: A service proxy.
    @type p: L{ServiceProxy}
    @return: A factory that is associated with I{p}.
    @rtype: L{Factory}
    """
    return p.__factory__
    

class ServiceProxy(object):
    
    """ 
    A lightweight soap based web service proxy.
    @ivar __client__: The embedded soap client.
    @ivar __factory__: The embedded type factory.
    """

    def __init__(self, url, **kwargs):
        """
        @param url: The URL for the WSDL.
        @type url: str
        @param kwargs: keyword arguments.
        @keyword faults: Raise faults raised by server (default:True),
                else return tuple from service method invocation as (http code, object).
        @type faults: boolean
        @keyword nil_supported: The bindings will set the xsi:nil="true" on nodes
                that have a value=None when this flag is True (default:True).
                Otherwise, an empty node <x/> is sent.
        @type nil_supported: boolean
        @keyword proxy: An http proxy to be specified on requests (default:{}).
                           The proxy is defined as {protocol:proxy,}
        @type proxy: dict
        """
        client = Client(url, **kwargs)
        self.__client__ = client
        self.__factory__ = Factory(client.schema)
    
    def get_instance(self, name):
        """
        Get an instance of a WSDL type by name
        @param name: The name of a type defined in the WSDL.
        @type name: str
        @return: An instance on success, else None
        @rtype: I{subclass of} L{Object}
        """
        return self.__factory__.create(name)
    
    def get_enum(self, name):
        """
        Get an instance of an enumeration defined in the WSDL by name.
        @param name: The name of a enumeration defined in the WSDL.
        @type name: str
        @return: An instance on success, else None
        @rtype: I{subclass of} L{Object}
        """
        return self.__factory__.create(name)
 
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
    
    """Method invocation wrapper""" 
    
    def __init__(self, client, name):
        """
        @param client: A client object.
        @type client: L{Client}
        @param name: The method's name.
        @type name: str
        """
        self.client = client
        self.name = name
        
    def __call__(self, *args):
        """call the method"""
        result = None
        try:
            result = self.client.send(self, *args)
        except WebFault, e:
            if self.client.faults:
                log.debug('raising (%s)', e)
                raise e
            else:
                log.debug('fault (%s)', e)
                result = (500, e)
        return result

    
class Factory:
    
    """ A factory for instantiating types defined in the wsdl """
    
    def __init__(self, schema):
        """
        @param schema: A schema object.
        @type schema: L{schema.Schema}
        """
        self.schema = schema
        self.resolver = PathResolver(schema)
        self.builder = Builder(schema)
    
    def create(self, name):
        """
        create a WSDL type by name
        @param name: The name of a type defined in the WSDL.
        @type name: str
        @return: The requested object.
        @rtype: L{Object}
        """
        type = self.resolver.find(name)
        if type is None:
            raise TypeNotFound(name)
        if isinstance(type, Enumeration):
            result = Object.__factory__.instance(name)
            for e in type.get_children():
                enum = e.get_name()
                setattr(result, enum, enum)
        else:
            try:
                result = self.builder.build(type=type)
            except Exception, e:
                msg = repr(type)
                log.exception(msg)
                raise BuildError(msg)
        return result



class Client:
    
    """
    A lightweight soap based web client B{**not intended for external use}
    @ivar faults: Indicates how I{web faults} are to be handled.
    @type faults: boolean
    @ivar wsdl: A WSDL object.
    @type wsdl: L{WSDL}
    @ivar schema: A schema object.
    @type schema: L{schema.Schema}
    @ivar builder: A builder object used to build schema types.
    @type builder: L{Builder}
    @ivar cookiejar: A cookie jar.
    @type cookiejar: libcookie.CookieJar
    """

    def __init__(self, url, **kwargs):
        """
        @param url: The URL for a WSDL.
        @type url: str
        @param kwargs: Keyword Arguments.
        @keyword faults: Raise faults raised by server (default:True),
                else return tuple from service method invocation as (http code, object).
        @type faults: boolean
        @keyword nil_supported: The bindings will set the xsi:nil="true" on nodes
                that have a value=None when this flag is True (default:True).
                Otherwise, an empty node <x/> is sent.
        @type nil_supported: boolean
        @keyword proxy: An http proxy to be specified on requests (default:{}).
                           The proxy is defined as {protocol:proxy,}
        @type proxy: dict
        """
        self.kwargs = kwargs
        self.faults = self.kwargs.get('faults', True)
        self.wsdl = WSDL(url)
        self.schema = self.wsdl.schema
        self.builder = Builder(self.schema)
        self.cookiejar = CookieJar()
        
    def send(self, method, *args):
        """
        Send the required soap message to invoke the specified method
        @param method: A method object to be invoked.
        @type method: L{Method}
        @return: The result of the method invocation.
        @rtype: I{builtin} or I{subclass of} L{Object}
        """
        result = None
        binding = self.wsdl.get_binding(method.name, **self.kwargs)
        headers = self.headers(method.name)
        location = self.wsdl.get_location().encode('utf-8')
        msg = binding.get_message(method.name, *args)
        log.debug('sending to (%s)\nmessage:\n%s', location, msg)
        try:
            request = Request(location, msg, headers)
            self.cookiejar.add_cookie_header(request) 
            self.set_proxies(location, request)
            fp = urlopen(request)
            self.cookiejar.extract_cookies(fp, request)
            reply = fp.read()
            result = self.succeeded(binding, method, reply)
        except HTTPError, e:
            result = self.failed(binding, method, e)
        return result
    
    def set_proxies(self, location, request):
        """
        Set the proxies for the request.
        @param location: A URL location of the service method
        @type location: str
        @param request: A soap request object to be sent.
        @type request: urllib2.Request
        """
        proxies = self.kwargs.get('proxy', {})
        protocol = urlparse.urlparse(location)[0]
        proxy = proxies.get(protocol, None)
        if proxy is not None:
            log.debug('proxy %s used for %s', proxy, location)
            request.set_proxy(proxy, protocol)
    
    def headers(self, method):
        """
        Get http headers or the http/https request.
        @param method: The B{name} of method being invoked.
        @type method: str
        @return: A dictionary of header/values.
        @rtype: dict
        """
        action = self.wsdl.get_soap_action(method)
        result = \
            { 'SOAPAction': action, 
               'Content-Type' : 'text/xml' }
        log.debug('headers = %s', result)
        return result
    
    def succeeded(self, binding, method, reply):
        """
        Request succeeded, process the reply
        @param binding: The binding to be used to process the reply.
        @type binding: L{bindings.binding.Binding}
        @param method: The service method that was invoked.
        @type method: L{Method}
        @return: The method result.
        @rtype: I{builtin}, L{Object}
        @raise WebFault: On server.
        """
        log.debug('http succeeded:\n%s', reply)
        if len(reply) > 0:
            p = binding.get_reply(method.name, reply)
            if self.faults:
                return p
            else:
                return (200, p)
        else:
            return (200, None)
        
    def failed(self, binding, method, error):
        """
        Request failed, process reply based on reason
        @param binding: The binding to be used to process the reply.
        @type binding: L{suds.bindings.binding.Binding}
        @param method: The service method that was invoked.
        @type method: L{Method}
        @param error: The http error message
        @type error: urllib2.HTTPException
        """
        status, reason = (error.code, error.msg)
        reply = error.fp.read()
        log.debug('http failed:\n%s', reply)
        if status == 500:
            if len(reply) > 0:
                return (status, binding.get_fault(reply))
            else:
                return (status, None)
        if self.faults:
            raise Exception((status, reason))
        else:
            return (status, None)
        
    def get_methods(self):
        """
        Get a list of methods provided by this service
        @return: A list of method descriptions.
        @rtype: [str,]
        """
        list = []
        for op in self.wsdl.get_operations():
            method = op.get('name')
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
            for m in self.get_methods():
                s += '\t\t%s\n' % m
            return unicode(s)
        except Exception, e:
            log.exception(e)
            return u'service not available'
