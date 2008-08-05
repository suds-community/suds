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

import sys
sys.path.append('../')

import logging
import traceback as tb
import urllib2
import suds.metrics as metrics
from tests import *
from suds import WebFault
from suds.client import Client

errors = 0

setup_logging()

#logging.getLogger('suds.client').setLevel(logging.DEBUG)

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
