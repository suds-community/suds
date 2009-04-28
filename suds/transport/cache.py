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

import os
from tempfile import gettempdir as tmp
from urlparse import urlparse
from suds.transport import *
from datetime import datetime as dt
from datetime import timedelta
from logging import getLogger

log = getLogger(__name__)


class FileCache(Cache):
    """
    A file-based URL cache.
    @cvar fnprefix: The file name prefix.
    @type fnprefix: str
    @cvar fnsuffix: The file name suffix.
    @type fnsuffix: str
    @ivar duration: The cached file duration which defines how
        long the file will be cached.
    @type duration: (unit, value)
    @ivar location: The directory for the cached files.
    @type location: str
    """
    
    fnprefix = 'suds'
    fnsuffix = 'http'
    units = ('months', 'weeks', 'days', 'hours', 'minutes', 'seconds')
    
    def __init__(self, location=None, **duration):
        """
        @param location: The directory for the cached files.
        @type location: str
        @param duration: The cached file duration which defines how
            long the file will be cached.  A duration=0 means forever.
            The duration may be: (months|weeks|days|hours|minutes|seconds).
        @type duration: {unit:value}
        """
        if location is None:
            location = os.path.join(tmp(), 'suds')
        self.location = location
        self.duration = (None, 0)
        self.setduration(**duration)
        
    def setduration(self, **duration):
        """
        Set the caching duration which defines how long the 
        file will be cached.
        @param duration: The cached file duration which defines how
            long the file will be cached.  A duration=0 means forever.
            The duration may be: (months|weeks|days|hours|minutes|seconds).
        @type duration: {unit:value}
        """
        if len(duration) == 1:
            arg = duration.items()[0]
            if not arg[0] in self.units:
                raise Exception('must be: %s' % str(self.units))
            self.duration = arg
        return self
    
    def setlocation(self, location):
        """
        Set the location (directory) for the cached files.
        @param location: The directory for the cached files.
        @type location: str
        """
        self.location = location
            
    def mktmp(self):
        """
        Make the I{location} directory if it doesn't already exits.
        """
        try:
            if not os.path.isdir(self.location):
                os.makedirs(self.location)
        except:
            log.debug(self.location, exc_info=1)
        return self
    
    def put(self, url, fp):
        """
        Put (add) the page to the cache.
        @param url: An http URL.
        @type url: str
        @param fp: An open file stream.
        @type fp: file stream
        @return: The cached file stream.
        @rtype: file stream
        """
        try:
            fn = self.__fn(url)
            f = self.open(fn, 'w')
            f.write(fp.read())
            f.close()
            return open(fn)
        except:
            log.debug(url, exc_info=1)
            return fp
    
    def get(self, url):
        """
        Get the cached contents for I{url}.
        @param url: An http URL.
        @type url: str
        @return: An open file stream for the cached contents.
        @rtype: file stream. 
        """
        try:
            fn = self.__fn(url)
            self.validate(fn)
            return self.open(fn)
        except:
            pass
        
    def validate(self, fn):
        """
        Validate that the file has not expired based on the I{duration}.
        @param fn: The file name.
        @type fn: str
        """
        if self.duration[1] < 1:
            return
        created = dt.fromtimestamp(os.path.getctime(fn))
        d = {self.duration[0] : self.duration[1]}
        expired = created+timedelta(**d)
        if expired < dt.now():
            log.debug('%s expired, deleted', fn)
            os.remove(fn)
 
    def clear(self):
        """
        Clear the cache which removes all cached files.
        """
        for fn in os.listdir(self.location):
            if os.path.isDir(fn):
                continue
            if fn.startswith(self.prefix) and fn.endswith(self.suffix):
                log.debug('deleted: %s', fn)
                os.remove(fn)
                
    def open(self, fn, *args):
        """
        Open the cache file making sure the directory is created.
        """
        self.mktmp()
        return open(fn, *args)
    
    def __fn(self, url):
        if self.__ignored(url):
            raise Exception('URL %s, ignored')
        fn = '%s-%s.%s' % (self.fnprefix, abs(hash(url)), self.fnsuffix)
        return os.path.join(self.location, fn)
    
    def __ignored(self, url):
        """ ignore urls based on protocol """
        protocol = urlparse(url)[0]
        return protocol in ('file',)