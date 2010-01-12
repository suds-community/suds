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
Contains basic caching classes.
"""

import os
from tempfile import gettempdir as tmp
from suds.transport import *
from datetime import datetime as dt
from datetime import timedelta
from cStringIO import StringIO
from logging import getLogger
try:
    import cPickle as pickle
except:
    import pickle

log = getLogger(__name__)


class ByteCache:
    """
    The URL caching object.
    """
    
    def put(self, id, fp):
        """
        Put an item into the cache.
        @param id: A file ID.
        @type id: str
        @param fp: A file stream.
        @type fp: stream
        @return: The stream.
        @rtype: stream
        """
        raise Exception('not-implemented')
    
    def get(self, id):
        """
        Get an item from the cache by id.
        @param id: A file ID.
        @type id: str
        @return: A stream when found, else None.
        @rtype: stream
        """
        raise Exception('not-implemented')
    
    def purge(self, id):
        """
        Purge a file from the cache by id.
        @param id: A file ID.
        @type id: str        
        """
        raise Exception('not-implemented')
    
    def clear(self):
        """
        @param id: A file ID.
        @type id: str
        """
        raise Exception('not-implemented')


class FileCache(ByteCache):
    """
    A file-based URL cache.
    @cvar fnprefix: The file name prefix.
    @type fnprefix: str
    @ivar fnsuffix: The file name suffix.
    @type fnsuffix: str
    @ivar duration: The cached file duration which defines how
        long the file will be cached.
    @type duration: (unit, value)
    @ivar location: The directory for the cached files.
    @type location: str
    """
    fnprefix = 'suds'
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
        self.fnsuffix = 'xml'
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
    
    def put(self, id, fp):
        try:
            fn = self.__fn(id)
            f = self.open(fn, 'w')
            f.write(fp.read())
            f.close()
            return open(fn)
        except:
            log.debug(id, exc_info=1)
            return fp
    
    def get(self, id):
        try:
            fn = self.__fn(id)
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
        for fn in os.listdir(self.location):
            if os.path.isdir(fn):
                continue
            if fn.startswith(self.fnprefix) and fn.endswith(self.fnsuffix):
                log.debug('deleted: %s', fn)
                os.remove(os.path.join(self.location, fn))
                
    def purge(self, id):
        fn = self.__fn(id)
        try:
            os.remove(fn)
        except:
            pass
                
    def open(self, fn, *args):
        """
        Open the cache file making sure the directory is created.
        """
        self.mktmp()
        return open(fn, *args)
    
    def __fn(self, id):
        fn = '%s-%s.%s' % (self.fnprefix, abs(hash(id)), self.fnsuffix)
        return os.path.join(self.location, fn)


class Cache:
    """
    The XML document cache.
    """

    def get(self, id):
        """
        Get a document from the store by ID.
        @param id: The document ID.
        @type id: str
        @return: The document, else None
        @rtype: I{Document}
        """
        raise Exception('not-implemented')
    
    def put(self, id, document):
        """
        Put a document into the store.
        @param id: The document ID.
        @type id: str
        @param document: The document to add.
        @type document: I{Document}
        """
        raise Exception('not-implemented')
    
    def purge(self, id):
        """
        Purge a document from the cache by id.
        @param id: A document ID.
        @type id: str        
        """
        raise Exception('not-implemented')
    
    def clear(self):
        """
        Clear all documents from the cache.
        """
        raise Exception('not-implemented')
    

class NoCache(Cache):
    """
    The passthru document cache.
    """
    
    def get(self, id):
        return None
    
    def put(self, id, document):
        pass
    

class DocumentStore(Cache):
    
    def __init__(self, location=None, **duration):
        """
        @param location: The directory for the cached documents.
        @type location: str
        @param duration: The cached file duration which defines how
            long the document will be cached.  A duration=0 means forever.
            The duration may be: (months|weeks|days|hours|minutes|seconds).
        @type duration: {unit:value}
        """
        cache = FileCache(location, **duration)
        cache.fnsuffix = 'pxd'
        self.cache = cache
    
    def get(self, id):
        try:
            fp = self.cache.get(id)
            if fp is None:
                return None
            else:
                return pickle.load(fp)
        except:
            self.cache.purge(id)
    
    def put(self, id, document):
        ostr = StringIO()
        pickle.dump(document, ostr)
        istr = StringIO(ostr.getvalue())
        fp = self.cache.put(id, istr)
        fp.close()
        return document
