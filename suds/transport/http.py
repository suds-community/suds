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

import urllib2 as u2
import base64
from suds.transport import *
from urlparse import urlparse
from cookielib import CookieJar
from logging import getLogger

log = getLogger(__name__)


class HttpTransport(Transport):
    """
    HTTP transport using urllib2.  Provided basic http transport
    that provides for cookies, proxies but no authentication.
    """
    
    def __init__(self, **kwargs):
        """
        @param kwargs: Keyword arguments.
            - B{proxy} - An http proxy to be specified on requests.
                 The proxy is defined as {protocol:proxy,}
                    - type: I{dict}
                    - default: {}
            - B{cache} - The http I{transport} cache.  May be set (None) for no caching.
                    - type: L{Cache}
                    - default: L{NoCache}
        """
        Transport.__init__(self)
        self.options.set(**kwargs)
        self.cookiejar = CookieJar()
        self.urlopener = None
        
    def open(self, request):
        try:
            url = request.url
            cache = self.options.cache
            fp = cache.get(url)
            if fp is not None:
                log.debug('opening (%s), cached', url)
                return fp
            log.debug('opening (%s)', url)
            u2request = u2.Request(url)
            self.__setproxy(url, u2request)
            fp = self.__open(u2request)
            return cache.put(url, fp)
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
            result = Reply(200, fp.headers.dict, fp.read())
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
    Provides basic http authentication for servers that don't follow
    the specified challenge / response model.  This implementation
    appends the I{Authorization} http header with base64 encoded
    credentials on every http request.
    """
    
    def send(self, request):
        credentials = self.credentials()
        if not (None in credentials):
            encoded = base64.encodestring(':'.join(credentials))
            basic = 'Basic %s' % encoded[:-1]
            request.headers['Authorization'] = basic
        return HttpTransport.send(self, request)
                 
    def credentials(self):
        return (self.options.username, self.options.password)