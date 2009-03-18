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
Contains transport interface (classes) and reference implementation.
"""

from logging import getLogger

log = getLogger(__name__)


#
# Transport Interface
#


class TransportError(Exception):
    def __init__(self, reason, httpcode, fp=None):
        Exception.__init__(self, reason)
        self.httpcode = httpcode
        self.fp = fp

class Request:
    """
    A transport request
    @ivar url: The url for the request.
    @type url: str
    @ivar message: The message to be sent in a POST request.
    @type message: str
    @ivar headers: The http headers to be used for the request.
    @type headers: dict
    """

    def __init__(self, url, message=None):
        """
        @param url: The url for the request.
        @type url: str
        @param message: The (optional) message to be send in the request.
        @type message: str
        """
        self.url = url
        self.headers = {}
        self.message = message
        
    def __str__(self):
        s = []
        s.append('URL:%s' % self.url)
        s.append('HEADERS: %s' % self.headers)
        s.append('MESSAGE:')
        s.append(self.message)
        return '\n'.join(s)


class Reply:
    """
    A transport reply
    @ivar code: The http code returned.
    @type code: int
    @ivar message: The message to be sent in a POST request.
    @type message: str
    @ivar headers: The http headers to be used for the request.
    @type headers: dict
    """

    def __init__(self, code, headers, message):
        """
        @param code: The http code returned.
        @type code: int
        @param headers: The http returned headers.
        @type headers: dict
        @param message: The (optional) reply message received.
        @type message: str
        """
        self.code = code
        self.headers = headers
        self.message = message
        
    def __str__(self):
        s = []
        s.append('CODE: %s' % self.code)
        s.append('HEADERS: %s' % self.headers)
        s.append('MESSAGE:')
        s.append(self.message)
        return '\n'.join(s)


class Transport:
    """
    The transport I{interface}.
    """
    
    def __init__(self, options=None):
        """
        @param options: A suds options object.
        @type options: L{suds.options.Options}
        """
        if options is None:
            from suds.options import Options
            self.options = Options()
            del Options
        else:
            self.options = options
    
    def open(self, request):
        """
        Open the url in the specified request.
        @param request: A transport request.
        @type request: L{Request}
        @return: An input stream.
        @rtype: stream
        @raise TransportError: On all transport errors.
        """
        raise Exception('not-implemented')
    
    def send(self, request):
        """
        Send soap message.  Implementations are expected to handle:
            - proxies
            - I{http} headers
            - cookies
            - sending message
            - brokering exceptions into L{TransportError}
        @param request: A transport request.
        @type request: L{Request}
        @return: The reply
        @rtype: L{Reply}
        @raise TransportError: On all transport errors.
        """
        raise Exception('not-implemented')


#
# Transport Implementation
#

import urllib2 as u2
from urlparse import urlparse
from cookielib import CookieJar

class HttpTransport(Transport):
    """
    urllib2 transport implementation.
    """
    
    def __init__(self, options=None):
        Transport.__init__(self, options)
        self.cookiejar = CookieJar()
        self.urlopener = None
        
    def open(self, request):
        try:
            url = request.url
            log.debug('opening (%s)', url)
            u2request = u2.Request(url)
            self.__setproxy(url, u2request)
            return self.__open(u2request)
        except u2.HTTPError, e:
            raise TransportError(str(e), e.code, e.fp)

    def send(self, request):
        result = None
        url = request.url
        msg = request.message
        headers = request.headers
        try:
            u2request = u2.Request(url, msg, headers)
            self.__addcookies(u2request)
            self.__setproxy(url, u2request)
            request.headers.update(u2request.headers)
            log.debug('sending:\n%s', request)
            fp = self.__open(u2request)
            self.__getcookies(fp, u2request)
            result = Reply(fp.code, fp.headers.dict, fp.read())
            log.debug('received:\n%s', result)
        except u2.HTTPError, e:
            if e.code in (202,204):
                result = None
            else:
                raise TransportError(e.msg, e.code, e.fp)
        return result

    def __addcookies(self, u2request):
        self.cookiejar.add_cookie_header(u2request)
        
    def __getcookies(self, fp, u2request):
        self.cookiejar.extract_cookies(fp, u2request)
        
    def __open(self, u2request):
        if self.urlopener is None:
            return u2.urlopen(u2request)
        else:
            return self.urlopener.open(u2request)
        
    def __setproxy(self, url, u2request):
        protocol = urlparse(url)[0]
        proxy = self.options.proxy.get(protocol, None)
        if proxy is None:
            return
        protocol = u2request.type
        u2request.set_proxy(proxy, protocol)
        

class HttpAuthenticated(HttpTransport):
    """
    Provides basic http authentication.
    @ivar pm: The password manager.
    @ivar handler: The authentication handler.
    """
    
    def __init__(self, options):
        HttpTransport.__init__(self, options)
        self.pm = u2.HTTPPasswordMgrWithDefaultRealm()
        self.handler = u2.HTTPBasicAuthHandler(self.pm)
        self.urlopener = u2.build_opener(self.handler)
        
    def open(self, request):
        self.__addcredentials(request)
        return  HttpTransport.open(self, request)

    def send(self, request):
        self.__addcredentials(request)
        return HttpTransport.send(self, request)
    
    def __addcredentials(self, request):
        user = self.options.username
        pwd = self.options.password
        if user is not None:
            self.pm.add_password(None, request.url, user, pwd)
            
