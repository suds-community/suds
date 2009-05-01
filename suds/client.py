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
The I{2nd generation} service proxy provides access to web services.
See I{README.txt}
"""

from logging import getLogger
import suds.metrics as metrics
from cookielib import CookieJar
from suds import *
from suds.transport import TransportError, Request
from suds.transport.https import HttpAuthenticated
from suds.transport.cache import FileCache
from suds.servicedefinition import ServiceDefinition
from suds import sudsobject
from sudsobject import Factory as InstFactory
from sudsobject import Object
from suds.resolver import PathResolver
from suds.builder import Builder
from suds.wsdl import Definitions
from suds.sax.document import Document
from suds.sax.parser import Parser
from suds.options import Options
from urlparse import urlparse

log = getLogger(__name__)


class Client(object):
    """ 
    A lightweight web services client.
    I{(2nd generation)} API.
    @ivar wsdl: The WSDL object.
    @type wsdl:L{Definitions}
    @ivar service: The service proxy used to invoke operations.
    @type service: L{Service}
    @ivar factory: The factory used to create objects.
    @type factory: L{Factory}
    @ivar sd: The service definition
    @type sd: L{ServiceDefinition}
    @ivar messages: The last sent/received messages.
    @type messages: str[2]
    """
    @classmethod
    def items(cls, sobject):
        """
        Extract the I{items} from a suds object much like the
        items() method works on I{dict}.
        @param sobject: A suds object
        @type sobject: L{Object}
        @return: A list of items contained in I{sobject}.
        @rtype: [(key, value),...]
        """
        return sudsobject.items(sobject)
    
    @classmethod
    def dict(cls, sobject):
        """
        Convert a sudsobject into a dictionary.
        @param sobject: A suds object
        @type sobject: L{Object}
        @return: A python dictionary containing the
            items contained in I{sobject}.
        @rtype: dict
        """
        return sudsobject.asdict(sobject)
    
    @classmethod
    def metadata(cls, sobject):
        """
        Extract the metadata from a suds object.
        @param sobject: A suds object
        @type sobject: L{Object}
        @return: The object's metadata
        @rtype: L{sudsobject.Metadata}
        """
        return sobject.__metadata__

    def __init__(self, url, **kwargs):
        """
        @param url: The URL for the WSDL.
        @type url: str
        @param kwargs: keyword arguments.
        @see: L{Options}
        """
        options = Options()
        options.cache = FileCache(days=1)
        options.transport = HttpAuthenticated()
        options.set(**kwargs)
        self.options = options
        self.wsdl = Definitions(url, options)
        self.service = Wrapper(Service(self))
        self.factory = Factory(self.wsdl)
        self.sd = ServiceDefinition(self.wsdl)
        self.messages = dict(tx=None, rx=None)
        
    def set_options(self, **kwargs):
        """
        Set options.
        @param kwargs: keyword arguments.
        @see: L{Options}
        """
        self.options.set(**kwargs)
        
    def add_prefix(self, prefix, uri):
        """
        Add I{static} mapping of an XML namespace prefix to a namespace.
        This is useful for cases when a wsdl and referenced schemas make heavy
        use of namespaces and those namespaces are subject to changed.
        @param prefix: An XML namespace prefix.
        @type prefix: str
        @param uri: An XML namespace URI.
        @type uri: str
        @raise Exception: when prefix is already mapped.
        """
        root = self.wsdl.root
        mapped = root.resolvePrefix(prefix, None)
        if mapped is None:
            root.addPrefix(prefix, uri)
            return
        if mapped[1] != uri:
            raise Exception('"%s" already mapped as "%s"' % (prefix, mapped))
        
    def last_sent(self):
        """
        Get last sent I{soap} message.
        @return: The last sent I{soap} message.
        @rtype: L{Document}
        """
        return self.messages.get('tx')
    
    def last_received(self):
        """
        Get last received I{soap} message.
        @return: The last received I{soap} message.
        @rtype: L{Document}
        """
        return self.messages.get('rx')
 
    def __str__(self):
        return unicode(self)
        
    def __unicode__(self):
        s = ['\n']
        version = properties.get('version')
        build = properties.get('build').split()
        s.append('Suds ( https://fedorahosted.org/suds/ )')
        s.append('  version: %s' % version)
        s.append(' %s  build: %s' % (build[0], build[1]))
        s.append('\n\n%s' % unicode(self.sd))
        return ''.join(s)


class Factory:
    """
    A factory for instantiating types defined in the wsdl
    @ivar resolver: A schema type resolver.
    @type resolver: L{PathResolver}
    @ivar builder: A schema object builder.
    @type builder: L{Builder}
    """
    
    def __init__(self, wsdl):
        """
        @param wsdl: A schema object.
        @type wsdl: L{wsdl.Definitions}
        """
        self.wsdl = wsdl
        self.resolver = PathResolver(wsdl)
        self.builder = Builder(self.resolver)
    
    def create(self, name):
        """
        create a WSDL type by name
        @param name: The name of a type defined in the WSDL.
        @type name: str
        @return: The requested object.
        @rtype: L{Object}
        """
        timer = metrics.Timer()
        timer.start()
        type = self.resolver.find(name)
        if type is None:
            raise TypeNotFound(name)
        if type.enum():
            result = InstFactory.object(name)
            for e, a in type.children():
                setattr(result, e.name, e.name)
        else:
            try:
                result = self.builder.build(type)
            except Exception, e:
                log.error("create '%s' failed", name, exc_info=True)
                raise BuildError(name, e)
        timer.stop()
        metrics.log.debug('%s created: %s', name, timer)
        return result
    
    def separator(self, ps):
        """
        Set the path separator.
        @param ps: The new path separator.
        @type ps: char
        """
        self.resolver = PathResolver(self.wsdl, ps)

   
class Wrapper:
    """
    Wrapper, translates to resolve() and call().
    """
    
    def __init__(self, wrapped):
        self.__wrapped__ = wrapped

    def __getattr__(self, name):
        builtin =  name.startswith('__') and name.endswith('__')
        if builtin:
            return self.__dict__[name]
        else:
            return self.__wrapped__.resolve(name)
        
    def __call__(self, *args, **kwargs):
        target = self.__wrapped__
        return target.call(*args, **kwargs)
    
    def __str__(self):
        return str(self.__wrapped__)
    
    def __unicode__(self):
        return unicode(self.__wrapped__) 
        

class Service:
    """
    The I{service} (namespace) object.
    @ivar client: A client object.
    @type client: L{Client}
    """
    
    def __init__(self, client):
        """
        @param client: A client object.
        @type client: L{Client}
        """
        self.client = client
        
    def resolve(self, name):
        """
        Resolve I{name} to a service port.
        @param name: A port/method name.
        @type name: str
        @return: The I{wrapped} L{Port}
        """
        service = self.client.wsdl.service
        port = self.dport(service)
        if port is None:
            port = service.port(name)
        return Wrapper(Port(self.client, (name, port)))
    
    def dport(self, service):
        """
        The I{default} port as defined by L{Options}.
        @param service: A wsdl service object.
        @type service : L{wsdl.Service}
        @return: The I{raw} L{wsdl.Port}
        """
        name = self.client.options.port
        if name is not None:
            port = service.port(name)
            if port is None:
                raise PortNotFound(name)
        else:
            port = None
        return port
    
    def __str__(self):
        return unicode(self)
    
    def __unicode__(self):
        return unicode(self.client.sd) 

        
class Port:
    """
    The I{port} (namespace) object.
    @ivar client: A client object.
    @type client: L{Client}
    @ivar port: A port tuple (name, L{wsdl.Port})
    @type port: tuple
    """
    
    def __init__(self, client, port):
        """
        @param client: A client object.
        @type client: L{Client}
        @param port: A port tuple (name, L{wsdl.Port})
        @type port: tuple
        """
        self.client = client
        self.port = port
        
    def resolve(self, name, strict=True):
        """
        Resolve I{name} to a service method.
        @param name: A method name.
        @type name: str
        @param strict: Make sure this is a real port.
        @type strict: bool
        @return: The I{wrapped} L{Method}
        """
        if strict and self.anyport():
            raise PortNotFound(self.name())
        finder = self.finder()
        method = finder.method(name)
        if method is None:
            raise MethodNotFound(name)
        return Wrapper(Method(self.client, method))
    
    def name(self):
        """
        The port name.
        @return: The port name.
        @rtype: str
        """
        return self.port[0]
    
    def realport(self):
        """
        The I{real} port.
        @return: The contained port object.
        @rtype: L{wsdl.Port}
        """
        return self.port[1]
    
    def anyport(self):
        """
        Get whether this port references a real port or just a
        placeholder for I{any} port.
        @return: True if real port reference is None.
        @rtype: bool
        """
        return ( self.realport() is None )
    
    def finder(self):
        """
        The method name I{finder}.
        @return: A method name resolver.
        @rtype: (L{wsdl.Port}|L{wsdl.Service})
        """
        if self.anyport():
            return self.client.wsdl.service
        else:
            return self.realport()

    def call(self, *args, **kwargs):
        """
        When called, this means that this port was returned by the
        Service.resolve() but the user intended to call a method.
        The name is used to lookup a method and forwards the invocation
        to the method.
        """
        method = self.resolve(self.name(), strict=False)
        return method(*args, **kwargs)


class Method:
    """
    The I{method} (namespace) object.
    @ivar client: A client object.
    @type client: L{Client}
    @ivar method: A I{wsdl} method.
    @type I{wsdl} Method.
    """

    def __init__(self, client, method):
        """
        @param client: A client object.
        @type client: L{Client}
        @param method: A I{raw} method.
        @type I{raw} Method.
        """
        self.client = client
        self.method = method
        
    def resolve(self, name):
        """
        Error, not permitted.
        @param name: A method attribute to be resolved.
        @type name: str.
        @raise AttributeError: Always.
        """
        raise AttributeError(name)
    
    def call(self, *args, **kwargs):
        """
        Method Invocation.
        """
        clientclass = self.clientclass(kwargs)
        client = clientclass(self.client, self.method)
        if not self.faults():
            try:
                return client.invoke(args, kwargs)
            except WebFault, e:
                return (500, e)
        else:
            return client.invoke(args, kwargs)
        
    def faults(self):
        return self.client.options.faults
        
    def clientclass(self, kwargs):
        if SimClient.simulation(kwargs):
            return SimClient
        else:
            return SoapClient


class SoapClient:
    """
    A lightweight soap based web client B{**not intended for external use}
    @ivar service: The target method.
    @type service: L{Service}
    @ivar method: A target method.
    @type method: L{Method}
    @ivar options: A dictonary of options.
    @type options: dict
    @ivar cookiejar: A cookie jar.
    @type cookiejar: libcookie.CookieJar
    """

    def __init__(self, client, method):
        """
        @param client: A suds client.
        @type client: L{Client}
        @param method: A target method.
        @type method: L{Method}
        """
        self.client = client
        self.method = method
        self.options = client.options
        self.cookiejar = CookieJar()
        
    def invoke(self, args, kwargs):
        """
        Send the required soap message to invoke the specified method
        @param args: A list of args for the method invoked.
        @type args: list
        @param kwargs: Named (keyword) args for the method invoked.
        @type kwargs: dict
        @return: The result of the method invocation.
        @rtype: I{builtin}|I{subclass of} L{Object}
        """
        timer = metrics.Timer()
        timer.start()
        result = None
        binding = self.method.binding.input
        binding.options = self.options
        msg = binding.get_message(self.method, args, kwargs)
        timer.stop()
        metrics.log.debug(
                "message for '%s' created: %s",
                self.method.qname, timer)
        timer.start()
        result = self.send(msg)
        timer.stop()
        metrics.log.debug(
                "method '%s' invoked: %s",
                self.method.qname, timer)
        return result
    
    def send(self, msg):
        """
        Send soap message.
        @param msg: A soap message to send.
        @type msg: basestring
        @return: The reply to the sent message.
        @rtype: I{builtin} or I{subclass of} L{Object}
        """
        result = None
        location = self.location()
        binding = self.method.binding.input
        transport = self.options.transport
        log.debug('sending to (%s)\nmessage:\n%s', location, msg)
        try:
            self.last_sent(Document(msg))
            request = Request(location, str(msg))
            request.headers = self.headers()
            reply = transport.send(request)
            result = self.succeeded(binding, reply.message)
        except TransportError, e:
            if e.httpcode in (202,204):
                result = None
            else:
                log.error(self.last_sent())
                result = self.failed(binding, e)
        return result
    
    def headers(self):
        """
        Get http headers or the http/https request.
        @return: A dictionary of header/values.
        @rtype: dict
        """
        action = self.method.soap.action
        stock = { 'Content-Type' : 'text/xml', 'SOAPAction': action }
        result = dict(stock, **self.options.headers)
        log.debug('headers = %s', result)
        return result
    
    def succeeded(self, binding, reply):
        """
        Request succeeded, process the reply
        @param binding: The binding to be used to process the reply.
        @type binding: L{bindings.binding.Binding}
        @return: The method result.
        @rtype: I{builtin}, L{Object}
        @raise WebFault: On server.
        """
        log.debug('http succeeded:\n%s', reply)
        if len(reply) > 0:
            r, p = binding.get_reply(self.method, reply)
            self.last_received(r)
            if self.options.faults:
                return p
            else:
                return (200, p)
        else:
            if self.options.faults:
                return None
            else:
                return (200, None)
        
    def failed(self, binding, error):
        """
        Request failed, process reply based on reason
        @param binding: The binding to be used to process the reply.
        @type binding: L{suds.bindings.binding.Binding}
        @param error: The http error message
        @type error: L{transport.TransportError}
        """
        status, reason = (error.httpcode, tostr(error))
        reply = error.fp.read()
        log.debug('http failed:\n%s', reply)
        if status == 500:
            if len(reply) > 0:
                r, p = binding.get_fault(reply)
                self.last_received(r)
                return (status, p)
            else:
                return (status, None)
        if self.options.faults:
            raise Exception((status, reason))
        else:
            return (status, None)

    def location(self):
        return self.options.get('location', self.method.location)
    
    def last_sent(self, d=None):
        key = 'tx'
        messages = self.client.messages
        if d is None:
            return messages.get(key)
        else:
            messages[key] = d
        
    def last_received(self, d=None):
        key = 'rx'
        messages = self.client.messages
        if d is None:
            return messages.get(key)
        else:
            messages[key] = d


class SimClient(SoapClient):
    """
    Loopback client used for message/reply simulation.
    """
    
    injkey = '__inject'
    
    @classmethod
    def simulation(cls, kwargs):
        """ get whether loopback has been specified in the I{kwargs}. """
        return kwargs.has_key(SimClient.injkey)
        
    def invoke(self, args, kwargs):
        """
        Send the required soap message to invoke the specified method
        @param args: A list of args for the method invoked.
        @type args: list
        @param kwargs: Named (keyword) args for the method invoked.
        @type kwargs: dict
        @return: The result of the method invocation.
        @rtype: I{builtin} or I{subclass of} L{Object}
        """
        simulation = kwargs[self.injkey]
        msg = simulation.get('msg')
        reply = simulation.get('reply')
        fault = simulation.get('fault')
        if msg is None:
            if reply is not None:
                return self.__reply(reply, args, kwargs)
            if fault is not None:
                return self.__fault(fault)
            raise Exception('(reply|fault) expected when msg=None')
        msg = Parser().parse(string=msg)
        return self.send(msg)
    
    def __reply(self, reply, args, kwargs):
        """ simulate the reply """
        binding = self.method.binding.input
        binding.options = self.options
        msg = binding.get_message(self.method, args, kwargs)
        log.debug('inject (simulated) send message:\n%s', msg)
        binding = self.method.binding.output
        binding.options = self.options
        return self.succeeded(binding, reply)
    
    def __fault(self, reply):
        """ simulate the (fault) reply """
        binding = self.method.binding.output
        binding.options = self.options
        if self.options.faults:
            r, p = binding.get_fault(reply)
            self.last_received(r)
            return (500, p)
        else:
            return (500, None)
