# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
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

import sys
sys.path.append('../')

from suds import logger, WebFault
import logging
from suds.client import Client
import urllib2

errors = 0

#logger('suds.client').setLevel(logging.DEBUG)

def opener():
    baseurl = 'http://localhost:9090/'
    username = 'jasperadmin'
    password = 'jasperadmin'
    passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
    passman.add_password(None, baseurl, username, password)
    authhandler = urllib2.HTTPBasicAuthHandler(passman)
    return urllib2.build_opener(authhandler)

def start(url):
    print '\n________________________________________________________________\n' 
    print 'Test @ ( %s )' % url
    
try:
    url = 'http://localhost:9090/jasperserver-pro/services/repository?wsdl'
    start(url)
    client = Client(url, opener=opener())
    print client
    print client.service.list('')

except WebFault, f:
    errors += 1
    print f
    print f.fault
except Exception, e:
    errors += 1
    print e

print '\nFinished: errors = %d' % errors