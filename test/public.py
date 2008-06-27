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

#logger('suds.client').setLevel(logging.DEBUG)

def start(url):
    print '\n________________________________________________________________\n' 
    print 'Test @ ( %s )' % url

try:
    url = 'http://soa.ebrev.info/service.wsdl'
    start(url)
    client = Client(url)
    print client
except Exception, f:
    print f

try:
    url = 'https://sec.neurofuzz-software.com/paos/genSSHA-SOAP.php?wsdl'
    start(url)
    client = Client(url)
    print client
    print client.service.genSSHA('hello', 'sha1')
except Exception, f:
    print f

try:
    url = 'http://www.services.coxnewsweb.com/COXnetUR/URService?WSDL'
    start(url)
    client = Client(url)
    print client
    bean = client.service.getUserBean('abc', '123', 'mypassword', 'myusername')
except Exception, f:
    print f

try:
    url = 'http://arcweb.esri.com/services/v2/MapImage.wsdl'
    start(url)
    client = Client(url)
    print client
    env = client.factory.create('ns0:Envelope')
    print env
    options = client.factory.create('ns1:MapImageOptions')
    print options
except Exception, f:
    print f

try:
    url = "http://www.thomas-bayer.com/axis2/services/BLZService?wsdl"
    start(url)
    client = Client(url)
    print client
    print client.service.getBank("76251020")
except Exception, f:
    print f

try:
    url = "http://webservices.imacination.com/distance/Distance.jws?wsdl"
    start(url)
    client = Client(url)
    print client
    print client.service.getDistance('27613', '21601')
except Exception, f:
    print f
    
try:
    url = "http://arcweb.esri.com/services/v2/RouteFinder.wsdl"
    start(url)
    client = Client(url)
    print client
except Exception, f:
    print f
