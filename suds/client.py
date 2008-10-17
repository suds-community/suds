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
from urllib2 import Request, HTTPError, urlopen, urlparse
from suds import *
from suds.servicedefinition import ServiceDefinition
from suds import sudsobject
from sudsobject import Factory as InstFactory, Object
from suds.resolver import PathResolver
from suds.builder import Builder
from suds.wsdl import Definitions
from suds.sax.document import Document
from sax.parser import Parser

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
    """

    def __init__(self, url, **kwargs):
        """
        @param url: The URL for the WSDL.
        @type url: str
        @param kwargs: keyword arguments.
        @keyword faults: Raise faults raised by server (default:True),
                else return tuple from service method invocation as (http code, object).
        @type faults: boolean
        @keyword proxy: An http proxy to be specified on requests (default:{}).
                The proxy is defined as {protocol:proxy,}
        @type proxy: dict
        @keyword opener: A urllib2 opener to be used to open urls.
        @type opener: A I{urllib2.Opener}
        """
        client = SoapClient(url, kwargs)
        self.wsdl = client.wsdl
        self.service = Service(client)
        self.factory = Factory(client.wsdl)
        self.sd = ServiceDefinition(client.wsdl)
        
    def setport(self, name):
        """
        Set the default service port name.  This should only be set when the service
        defines multiple ports and you want to invoke method within a particular
        port only without specifying a qualified name as: <port>.<method>.
        The default port may be I{unset} by setting the value to None.
        @param name: A service port name.
        @type name: str|int
        """
        if name is None:
            self.service.__dport__ = None
            return
        if isinstance(name, basestring):
            self.service.__dport__ = self.wsdl.service.port(name)
            return
        if isinstance(name, (int, long)):
            self.service.__dport__ = self.wsdl.service.ports[name]
            return
        
    def setlocation(self, url, names=None):
        """
        Override the invocation location (url) for service method.
        @param url: A url location.
        @type url: A url.
        @param names:  A list of method names.  None=ALL
        @type names: [str,..]
        """
        self.wsdl.service.setlocation(url, names)
        
    def last_sent(self):
        """
        Get last sent I{soap} message.
        @return: The last sent I{soap} message.
        @rtype: L{Document}
        """
        return self.service.__client__.last_sent
    
    def last_received(self):
        """
        Get last received I{soap} message.
        @return: The last received I{soap} message.
        @rtype: L{Document}
        """
        return self.service.__client__.last_received
        
    def items(self, sobject):
        """
        Extract the I{items} from a suds object much like the
        items() method works on I{dict}.
        @param sobject: A suds object
        @type sobject: L{Object}
        @return: A list of items contained in I{sobject}.
        @rtype: [(key, value),...]
        """
        return sudsobject.items(sobject)
    
    def dict(self, sobject):
        """
        Convert a sudsobject into a dictionary.
        @param sobject: A suds object
        @type sobject: L{Object}
        @return: A python dictionary containing the
            items contained in I{sobject}.
        @rtype: dict
        """
        return sudsobject.asdict(sobject)
    
    def metadata(self, sobject):
        """
        Extract the metadata from a suds object.
        @param sobject: A suds object
        @type sobject: L{Object}
        @return: The object's metadata
        @rtype: L{sudsobject.Metadata}
        """
        return sobject.__metadata__
 
    def __str__(self):
        return unicode(self)
        
    def __unicode__(self):
        ver = properties.get('version')
        build = properties.get('build', '')
        desc = unicode(self.sd)
        return 'Suds - Web Service Client, %s %s\n\n%s'  % (ver, build, desc)


class Service:
    """ 
    Service I{wrapper} object.
    B{See:}  L{Method} for Service.I{method()} invocation API.
    @ivar __client__: The soap client.
    @type __client__: L{SoapClient}
    @ivar __dport__: The default service port name.
    @type __dport__: str
    """
    
    def __init__(self, client):
        """
        @param client: A service client.
        @type client: L{SoapClient}
        """
        self.__client__ = client
        self.__dport__ = None
    
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
        service = self.__client__.wsdl.service
        if self.__dport__ is None:
            log.debug('lookup service-method using "%s"', name)
            method = service.method(name)
            if method is not None:
                return Method(self.__client__, method)
            log.debug('lookup service-port using "%s"', name)
            port = service.port(name)
            if port is not None:
                return Port(self.__client__, port)
        else:
            port = self.__dport__
            port = Port(self.__client__, port)
            return getattr(port, name)
        raise MethodNotFound(name)
        
    
    def __str__(self):
        return str(self.__client__)
        
    def __unicode__(self):
        return unicode(self.__client__)
    
    
class Port(object):
    """ 
    Service port I{wrapper} object.
    B{See:}  L{Method} for Service.I{method()} invocation API.
    @ivar __client__: The soap client.
    @type __client__: L{SoapClient}
    @ivar __port__: The service port.
    @type __port__: I{service.Port}
    """
    
    def __init__(self, client, port):
        """
        @param client: A service client.
        @type client: L{SoapClient}
        @param port: A service port.
        @type port: I{service.Port}
        """
        self.__client__ = client
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
        service = self.__client__.wsdl.service
        qname = ':'.join((self.__port__.name, name))
        method = service.method(qname)
        return Method(self.__client__, method)


class Method(object):
    
    """
    Method invocation wrapper
    @ivar client: A soap client.
    @type client: L{SoapClient}
    @ivar name: The method name.
    @type name: basestring
    """ 
    
    def __init__(self, client, method):
        """
        @param client: A client object.
        @type client: L{SoapClient}
        @param method: The (wsdl) method.
        @type method: I{method}
        """
        self.client = client
        self.method = method
        
    def __call__(self, *args, **kwargs):
        """
        Call (invoke) the method.
        @param args: A list of args for the method invoked.
        @type args: list
        @param kwargs: Keyword args to be processed by suds.
        @type kwargs: dict
        @keyword soapheaders: Optional soap headers to be included in the
            soap message.
        @type soapheaders: list( L{sudsobject.Object}|L{sudsobject.Property} )
        @keyword inject: Inject the specified (msg|reply|fault) into the soap message stream.
        @type inject: dict(B{msg}=soap-message|B{reply}=soap-reply|B{fault}=soap-fault)
        @keyword location: Override the location (url) for the service.
        @type location: str
        """
        result = None
        try:
            if SimClient.simulation(kwargs):
                simulator = SimClient(self.client)
                result = simulator.invoke(self.method, args, kwargs)
            else:
                result = self.client.invoke(self.method, args, kwargs)
        except WebFault, e:
            if self.client.arg.faults:
                log.debug('raising (%s)', e)
                raise e
            else:
                log.debug('fault (%s)', e)
                result = (500, e)
        return result

    
class Factory:
    
    """ A factory for instantiating types defined in the wsdl """
    
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



class SoapClient:
    
    """
    A lightweight soap based web client B{**not intended for external use}
    @ivar arg: A object containing custom args.
    @type arg: L{Object}
    @ivar wsdl: A WSDL object.
    @type wsdl: L{Definitions}
    @ivar schema: A schema object.
    @type schema: L{xsd.schema.Schema}
    @ivar builder: A builder object used to build schema types.
    @type builder: L{Builder}
    @ivar cookiejar: A cookie jar.
    @type cookiejar: libcookie.CookieJar
    """

    def __init__(self, url, kwargs):
        """
        @param url: The URL for a WSDL.
        @type url: str
        @keyword faults: Raise faults raised by server (default:True),
                else return tuple from service method invocation as (http code, object).
        @type faults: boolean
        @keyword proxy: An http proxy to be specified on requests (default:{}).
                The proxy is defined as {protocol:proxy,}
        @type proxy: dict
        @keyword opener: A urllib2 opener to be used to open urls.
        @type opener: A I{urllib2.Opener}
        """
        self.arg = Object()
        self.arg.faults = kwargs.get('faults', True)
        self.arg.proxies = kwargs.get('proxy', {})
        self.arg.opener = kwargs.get('opener', None)
        self.wsdl = Definitions(url, self.arg.opener)
        self.schema = self.wsdl.schema
        self.builder = Builder(self.wsdl)
        self.cookiejar = CookieJar()
        self.last_sent = None
        self.last_received = None
        
    def invoke(self, method, args, kwargs):
        """
        Send the required soap message to invoke the specified method
        @param method: A method object to be invoked.
        @type method: I{service.Method}
        @param args: Arguments
        @type args: [arg,...]
        @param kwargs: Keyword Arguments
        @type kwargs: I{dict}
        @return: The result of the method invocation.
        @rtype: I{builtin} or I{subclass of} L{Object}
        """
        timer = metrics.Timer()
        timer.start()
        result = None
        binding = method.binding.input
        binding.faults = self.arg.faults
        soapheaders = kwargs.get('soapheaders', ())
        msg = binding.get_message(method, args, soapheaders)
        timer.stop()
        metrics.log.debug("message for '%s' created: %s", method.qname, timer)
        timer.start()
        result = self.send(method, msg, kwargs)
        timer.stop()
        metrics.log.debug("method '%s' invoked: %s", method.qname, timer)
        return result
    
    def send(self, method, msg, kwargs):
        """
        Send soap message.
        @param method: The method being invoked.
        @type method: I{service.Method}
        @param msg: A soap message to send.
        @type msg: basestring
        @param kwargs: keyword args
        @type kwargs: {}
        @return: The reply to the sent message.
        @rtype: I{builtin} or I{subclass of} L{Object}
        """
        result = None
        headers = self.headers(method)
        location = method.location
        location = kwargs.get('location', location)
        binding = method.binding.input
        log.debug('sending to (%s)\nmessage:\n%s', location, msg)
        try:
            self.last_sent = Document(msg)
            request = Request(location, str(msg), headers)
            self.cookiejar.add_cookie_header(request) 
            self.set_proxies(location, request)
            fp = self.urlopen(request)
            self.cookiejar.extract_cookies(fp, request)
            reply = fp.read()
            result = self.succeeded(binding, method, reply)
        except HTTPError, e:
            if e.code in (202,204):
                result = None
            else:
                log.error(self.last_sent)
                result = self.failed(binding, e)
        return result
    
    def urlopen(self, request):
        """
        Open the url as specified by the request using either the default
        urllib2 opener or the opener specified by the user.
        @param request: An http request object.
        @type request: L{Request}
        """
        if self.arg.opener is None:
            return urlopen(request)
        else:
            return self.arg.opener.open(request)
    
    def set_proxies(self, location, request):
        """
        Set the proxies for the request.
        @param location: A URL location of the service method
        @type location: str
        @param request: A soap request object to be sent.
        @type request: urllib2.Request
        """
        protocol = urlparse.urlparse(location)[0]
        proxy = self.arg.proxies.get(protocol, None)
        if proxy is not None:
            log.debug('proxy %s used for %s', proxy, location)
            request.set_proxy(proxy, protocol)
    
    def headers(self, method):
        """
        Get http headers or the http/https request.
        @param method: The method being invoked.
        @type method: I{service.Method}
        @return: A dictionary of header/values.
        @rtype: dict
        """
        action = method.soap.action
        result = { 'Content-Type' : 'text/xml', 'SOAPAction': action }
        log.debug('headers = %s', result)
        return result
    
    def succeeded(self, binding, method, reply):
        """
        Request succeeded, process the reply
        @param binding: The binding to be used to process the reply.
        @type binding: L{bindings.binding.Binding}
        @param method: The service method that was invoked.
        @type method: I{service.Method}
        @return: The method result.
        @rtype: I{builtin}, L{Object}
        @raise WebFault: On server.
        """
        log.debug('http succeeded:\n%s', reply)
        if len(reply) > 0:
            r, p = binding.get_reply(method, reply)
            self.last_received = r
            if self.arg.faults:
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
        @type error: urllib2.HTTPException
        """
        status, reason = (error.code, error.msg)
        reply = error.fp.read()
        log.debug('http failed:\n%s', reply)
        if status == 500:
            if len(reply) > 0:
                r, p = binding.get_fault(reply)
                self.last_received = r
                return (status, p)
            else:
                return (status, None)
        if self.arg.faults:
            raise Exception((status, reason))
        else:
            return (status, None)


class SimClient(SoapClient):
    
    """
    Loopback client used for message/reply simulation.
    """
    
    INJKEY = 'inject'
    
    @classmethod
    def simulation(cls, kwargs):
        """ get whether loopback has been specified in the I{kwargs}. """
        return kwargs.has_key(SimClient.INJKEY)
    
    def __init__(self, super):
        """
        @param super: The SoapClient superclass instance.
        @type super: L{SoapClient}
        """
        for item in super.__dict__.items():
            k,v = item
            if k.startswith('__'): continue
            self.__dict__[k] = v
        
    def invoke(self, method, args, kwargs):
        """
        Send the required soap message to invoke the specified method
        @param method: A method object to be invoked.
        @type method: I{service.Method}
        @param args: Arguments
        @type args: [arg,...]
        @param kwargs: Keyword Arguments
        @type kwargs: I{dict}
        @return: The result of the method invocation.
        @rtype: I{builtin} or I{subclass of} L{Object}
        """
        lb = kwargs[SimClient.INJKEY]
        msg = lb.get('msg')
        reply = lb.get('reply')
        fault = lb.get('fault')
        if msg is None:
            if reply is not None:
                return self.__reply(method, reply)
            if fault is not None:
                return self.__fault(method, fault)
            raise Exception('(reply|fault) expected when msg=None')
        msg = Parser().parse(string=msg)
        return self.send(method, msg, kwargs)
    
    def __reply(self, method, reply):
        """ simulate the reply """
        binding = method.binding.output
        binding.faults = self.arg.faults
        return self.succeeded(binding, method, reply)
    
    def __fault(self, method, reply):
        """ simulate the (fault) reply """
        binding = method.binding.output
        binding.faults = self.arg.faults
        if self.arg.faults:
            r, p = binding.get_fault(reply)
            self.last_received = r
            return (500, p)
        else:
            return (500, None)
        



