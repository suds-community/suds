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
from suds.transport import HttpTransport, TransportError, Request
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
        options = Options(transport=HttpTransport())
        options.set(**kwargs)
        self.options = options
        self.wsdl = Definitions(url, options)
        self.service = Service(self)
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
        s.append('Suds - Web Service Client')
        s.append('  project: https://fedorahosted.org/suds/')
        s.append('  version: %s' % properties.get('version'))
        s.append('  build: %s' % properties.get('build', 'n/a'))
        s.append('\n%s' % unicode(self.sd))
        return '\n'.join(s)


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
        self.resolver = PathResolver(wsdl)
        self.builder = Builder(wsdl)
    
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
            for e in type.children:
                enum = e.name
                setattr(result, enum, enum)
        else:
            try:
                result = self.builder.build(type)
            except:
                log.error("create '%s' failed", name, exc_info=True)
                raise BuildError("create '%s' failed" % name)
        timer.stop()
        metrics.log.debug('%s created: %s', name, timer)
        return result


class Service:
    """ 
    Service I{wrapper} object.
    B{See:}  L{Method} for Service.I{method()} invocation API.
    @ivar __client__: A suds client.
    @type __client__: L{Client}
    """
    
    def __init__(self, client):
        """
        @param client: A suds client.
        @type client: L{Client}
        """
        self.__client__ = client
        self.__service__ = client.wsdl.service
    
    def __getattr__(self, name):
        """
        Find and return a service method or port by name depending on how may
        ports are defined for the service.  When only one port is defined (as in most
        cases), it returns the method so users don't have to qualify methods by port.
        @param name: A port/method name.
        @type name: str
        @return: Either a L{Port} or an L{Method}.
        @rtype: L{Port}|L{Method}
        @see: Client.setport()
        """
        builtin =  name.startswith('__') and name.endswith('__')
        if builtin:
            return self.__dict__[name]
        # ports/methods
        service = self.__service__
        options = self.__client__.options
        if options.port is None:
            method = service.method(name)
            if method is None:
                port = service.port(name)
                if port is None:
                    raise MethodNotFound(name)
                else:
                    return Port(self, port)
            else:
                return Method(self, method)
        else:
            port = service.port(options.port)
            if port is None:
                raise PortNotFound(options.port)
            port = Port(self, port)
            return getattr(port, name)
    
    def __str__(self):
        return unicode(self)
        
    def __unicode__(self):
        return unicode(self.__service__)
    
    
class Port(object):
    """ 
    Service port I{wrapper} object.
    B{See:}  L{Method} for Service.I{method()} invocation API.
    @ivar __service__: The service.
    @type __service__: L{Service}
    @ivar __port__: The service port.
    @type __port__: I{service.Port}
    """
    
    def __init__(self, service, port):
        """
        @param service: The service.
        @type service: L{Service}
        @param port: A service port.
        @type port: I{service.Port}
        """
        self.__service__ = service
        self.__port__ = port
        
    def __getattr__(self, name):
        """
        Find and return a service method by name.
        @param name: A method name.
        @type name: str
        @return: a L{Method}.
        @rtype: L{Method}.
        """
        builtin =  name.startswith('__') and name.endswith('__')
        if builtin:
            return self.__dict__[name]
        # methods
        service = self.__service__.__service__
        port = self.__port__
        qname = ':'.join((port.name, name))
        method = service.method(qname)
        return Method(self.__service__, method)
    
    def __str__(self):
        return unicode(self)
        
    def __unicode__(self):
        return unicode(self.__port__)


class Method(object):
    """
    Method invocation wrapper
    @ivar service: The service.
    @type service: L{Service}
    @ivar name: The method name.
    @type name: str
    """ 
    
    def __init__(self, service, method):
        """
        @param service: The service.
        @type service: L{Service}
        @param method: The (wsdl) method.
        @type method: I{method}
        """
        self.service = service
        self.method = method
        
    def __call__(self, *args, **kwargs):
        """
        Call (invoke) the method.
        @param args: A list of args for the method invoked.
        @type args: list
        @param kwargs: Named (keyword) args for the method invoked.
        @type kwargs: dict
        @see: L{Options}
        """
        result = None
        options = self.service.__client__.options
        if SimClient.simulation(kwargs):
            client = SimClient(self, options)
        else:
            client = SoapClient(self, options)
        if not options.faults:
            try:
                return client.invoke(args, kwargs)
            except WebFault, e:
                return (500, e)
        else:
            return client.invoke(args, kwargs)
        
    def __str__(self):
        return unicode(self)
        
    def __unicode__(self):
        return unicode(self.method)


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

    def __init__(self, method, options):
        """
        @param method: A target method.
        @type method: L{Method}
        @param options: A dictonary of options.
        @type options: L{Options}
        """
        self.service = method.service
        self.method = method.method
        self.options = options
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
            request = Request(location, msg)
            request.proxy = self.getproxy()
            request.headers = self.headers()
            reply = transport.send(request)
            result = self.succeeded(binding, reply)
        except TransportError, e:
            if e.httpcode in (202,204):
                result = None
            else:
                log.error(self.last_sent())
                result = self.failed(binding, e)
        return result
    
    def getproxy(self):
        """
        Get the proxy for the request.
        @return: The proxy if one specified.
        @rtype: str
        """
        location = self.location()
        protocol = urlparse(location)[0]
        proxydict = self.options.proxy
        return proxydict.get(protocol, None)
    
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
            return (200, None)
        
    def failed(self, binding, error):
        """
        Request failed, process reply based on reason
        @param binding: The binding to be used to process the reply.
        @type binding: L{suds.bindings.binding.Binding}
        @param error: The http error message
        @type error: L{transport.TransportError}
        """
        status, reason = (error.httpcode, error.message)
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
        messages = self.service.__client__.messages
        if d is None:
            return messages.get(key)
        else:
            messages[key] = d
        
    def last_received(self, d=None):
        key = 'rx'
        messages = self.service.__client__.messages
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
                return self.__reply(reply)
            if fault is not None:
                return self.__fault(fault)
            raise Exception('(reply|fault) expected when msg=None')
        msg = Parser().parse(string=msg)
        return self.send(msg)
    
    def __reply(self, reply):
        """ simulate the reply """
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
