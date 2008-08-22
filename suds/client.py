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
from suds import sudsobject
from sudsobject import Factory as InstFactory, Object
from suds.resolver import PathResolver
from suds.builder import Builder
from suds.wsdl import Definitions
from suds.sax import Namespace

log = getLogger(__name__)


class Client(object):
    
    """ 
    A lightweight web services client.
    I{(2nd generation)} API.
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
        self.service = Service(client)
        self.factory = Factory(client.wsdl)
        self.sd = ServiceDefinition(client.wsdl)
        
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
        indent = '%*s' % (4, ' ')
        ver = properties['version']
        desc = unicode(self.sd)
        return 'suds\n%sversion=%s\n%s'  % (indent, ver, desc)


class Service:
    
    """ 
    Service wrapper object.
    
    B{See:}  L{Method} for Service.I{method()} invocation API.
    
    @ivar __client__: The soap client.
    @type __client__: L{SoapClient}
    """
    
    def __init__(self, client):
        """
        @param client: A service client.
        @type client: L{SoapClient}
        """
        self.__client__ = client
    
    def __getattr__(self, name):
        builtin =  name.startswith('__') and name.endswith('__')
        if builtin:
            return self.__dict__[name]
        operation = self.__client__.wsdl.binding().operation(name)
        if operation is None:
            raise MethodNotFound(name)
        method = Method(self.__client__, name)
        return method
    
    def __str__(self):
        return str(self.__client__)
        
    def __unicode__(self):
        return unicode(self.__client__)


class Method(object):
    
    """
    Method invocation wrapper
    @ivar client: A soap client.
    @type client: L{SoapClient}
    @ivar name: The method name.
    @type name: basestring
    """ 
    
    def __init__(self, client, name):
        """
        @param client: A client object.
        @type client: L{SoapClient}
        @param name: The method's name.
        @type name: str
        """
        self.client = client
        self.name = name
        
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
        @keyword inject: Inject the specified (msg|repy) into the soap message stream.
        @type inject: dict(B{msg}=soap-out,B{reply}=soap-in)
        @keyword location: Override the location (url) for the service.
        @type location: str
        """
        result = None
        try:
            if SimClient.simulation(kwargs):
                simulator = SimClient(self.client)
                result = simulator.invoke(self, args, kwargs)
            else:
                result = self.client.invoke(self, args, kwargs)
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
        
    def invoke(self, method, args, kwargs):
        """
        Send the required soap message to invoke the specified method
        @param method: A method object to be invoked.
        @type method: L{Method}
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
        binding = self.wsdl.binding().operation(method.name).binding.input
        binding.faults = self.arg.faults
        soapheaders = kwargs.get('soapheaders', ())
        msg = binding.get_message(method.name, args, soapheaders)
        timer.stop()
        metrics.log.debug("message for '%s' created: %s", method.name, timer)
        timer.start()
        result = self.send(method, msg, kwargs)
        timer.stop()
        metrics.log.debug("method '%s' invoked: %s", method.name, timer)
        return result
    
    def send(self, method, msg, kwargs):
        """
        Send soap message.
        @param method: The method being invoked.
        @type method: L{Method}
        @param msg: A soap message to send.
        @type msg: basestring
        @param kwargs: keyword args
        @type kwargs: {}
        @return: The reply to the sent message.
        @rtype: I{builtin} or I{subclass of} L{Object}
        """
        result = None
        headers = self.headers(method.name)
        location = kwargs.get('location', self.wsdl.service.port.location)
        binding = self.wsdl.binding().operation(method.name).binding.input
        log.debug('sending to (%s)\nmessage:\n%s', location, msg)
        try:
            self.last_sent = msg
            request = Request(location, msg, headers)
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
                result = self.failed(binding, method, e)
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
        @param method: The B{name} of method being invoked.
        @type method: str
        @return: A dictionary of header/values.
        @rtype: dict
        """
        action = self.wsdl.binding().operation(method).soap.action
        result = { 'Content-Type' : 'text/xml', 'SOAPAction': action }
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
            if self.arg.faults:
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
        @type method: L{Method}
        @param args: Arguments
        @type args: [arg,...]
        @param kwargs: Keyword Arguments
        @type kwargs: I{dict}
        @return: The result of the method invocation.
        @rtype: I{builtin} or I{subclass of} L{Object}
        """
        lb = kwargs[SimClient.INJKEY]
        msg = lb.get('msg', None)
        if msg is None:
            reply = lb.get('reply', None)
            result = self.__reply(method, reply)
        else:
            result = self.__send(method, msg, kwargs)
        return result
        
    def __send(self, method, msg, kwargs):
        """ send the supplied soap message """
        result = None
        binding = self.wsdl.binding().operation(method.name).binding.input
        binding.faults = self.arg.faults
        headers = self.headers(method.name)
        location = kwargs.get('location', self.wsdl.service.port.location)
        log.debug('sending to (%s)\nmessage:\n%s', location, msg)
        return self.send(method, binding, msg)
    
    def __reply(self, method, reply):
        """ simulate the reply """
        binding = self.wsdl.binding().operation(method.name).binding.output
        binding.faults = self.arg.faults
        return self.succeeded(binding, method, reply)


class ServiceDefinition:
    
    def __init__(self, wsdl):
        self.wsdl = wsdl
        self.name = wsdl.service.name
        self.methods = []
        self.prefixes = []
        self.types = []
        self.__addmethods(wsdl)
        self.__addtypes()
        self.__pushprefixes()
        
    def get_method(self, name):
        """ get a method by name """
        for m in self.methods:
            if m[0] == name:
                return m
        return None
    
    def __pushprefixes(self):
        """ add our prefixes to the wsdl """
        for ns in self.prefixes:
            self.wsdl.root.addPrefix(ns[0], ns[1])

    def __addmethods(self, w):
        """ create our list of methods """
        timer = metrics.Timer()
        for operation in w.binding().operations.values():
            timer.start()
            m = operation.name
            binding = operation.binding.input
            method = (m, binding.param_defs(m))
            self.methods.append(method)
            timer.stop()
            metrics.log.debug("method '%s' created: %s", m, timer)
        self.methods.sort()
            
    def __addtypes(self):
        """ create our list of top level types """
        namespaces = []
        self.types = []
        for type in self.wsdl.schema.children:
            if type.name is None:
                continue
            self.types.append(type)
        for t in self.types:
            ns = t.namespace()
            if ns in namespaces:
                continue
            namespaces.append(ns)
        i = 0
        namespaces.sort()
        for ns in namespaces:
            p = self.__nextprefix()
            ns = (p, ns[1])
            self.prefixes.append(ns)
        self.types.sort()
        
    def __nextprefix(self):
        """ get the next available prefix  """
        used = [ns[0] for ns in self.prefixes]
        used += [ns[0] for ns in self.wsdl.root.nsprefixes.items()]
        for n in range(0,1024):
            p = 'ns%d'%n
            if p not in used:
                return p
        raise Exception('prefixes exhausted')
    
    def __getprefix(self, u):
        """ get the prefix for the specified namespace (uri) """
        for ns in Namespace.all:
            if u == ns[1]:
                return ns[0]
        for ns in self.prefixes:
            if u == ns[1]:
                return ns[0]
        raise Exception('ns (%s) not mapped'  % u)
    
    def __xlate(self, type):
        """ get a (namespace) translated name for type """
        resolved = type.resolve()
        name = resolved.name
        if type.unbounded():
            name += '[]'
        ns = resolved.namespace()
        if ns[1] == self.wsdl.tns[1]:
            return name
        prefix = self.__getprefix(ns[1])
        return ':'.join((prefix, name))
        
    def description(self):
        """ get a str description of the service """
        s = []
        s.append('service (%s)' % self.name)
        s.append('\tprefixes:')
        for p in self.prefixes:
            s.append('\t\t%s = "%s"' % p)
        s.append('\tmethods (%d):' % len(self.methods))
        for m in self.methods:
            sig = []
            sig.append('\t\t')
            sig.append(m[0])
            sig.append('(')
            for p in m[1]:
                sig.append(self.__xlate(p[1]))
                sig.append(' ')
                sig.append(p[0])
                sig.append(', ')
            sig.append(')')
            s.append(''.join(sig))
        s.append('\ttypes (%d):' % len(self.types))
        for t in self.types:
            s.append('\t\t%s'% self.__xlate(t))
        return '\n'.join(s)
    
    def __str__(self):
        return unicode(self).encode('utf-8')
        
    def __unicode__(self):
        try:
            return self.description()
        except Exception, e:
            log.exception(e)
        return tostr(e)
        



