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
from suds.transport import *
from datetime import datetime as dt
from datetime import timedelta
from logging import getLogger

log = getLogger(__name__)


class FileCache(Cache):
    
    fnprefix = 'suds'
    fnsuffix = 'http'
    units = ('hours', 'minutes', 'seconds')
    
    def __init__(self, location='/tmp', **kwargs):            
        self.location = location
        self.duration = (None, 0)
        if len(kwargs) == 1:
            arg = kwargs.items()[0]
            if not arg[0] in self.units:
                raise Exception('must be: ' % self.units)
            self.duration = arg
    
    def put(self, url, fp):
        try:
            fn = self.__fn(url)
            f = open(fn, 'w')
            f.write(fp.read())
            f.close()
            return open(fn)
        except Exception, e:
            return fp
    
    def get(self, url):
        try:
            fn = self.__fn(url)
            self.validate(fn)
            return open(fn)
        except Exception, e:
            pass
        
    def validate(self, fn):
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
            if os.path.isDir(fn):
                continue
            if fn.startswith(self.prefix) and fn.endswith(self.suffix):
                log.debug('deleted: %s', fn)
                os.remove(fn)
    
    def __fn(self, url):
        fn = '%s-%s.%s' % (self.fnprefix, abs(hash(url)), self.fnsuffix)
        return os.path.join(self.location, fn)