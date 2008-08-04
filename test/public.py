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

import suds.metrics as metrics
from suds import logger, WebFault
import logging
from suds.client import Client
from traceback import print_exc

errors = 0

#logger('suds.client').setLevel(logging.DEBUG)
#logger('suds.metrics').setLevel(logging.DEBUG)
#logger('suds').setLevel(logging.DEBUG)

def start(url):
    print '\n________________________________________________________________\n' 
    print 'Test @ ( %s )' % url
    
try:
    url = 'http://www.zenfolio.com/zf/api/zfapi.asmx?wsdl'
    start(url)
    client = Client(url)
    print client
    group = client.factory.create('Group')
    print 'Group:\n%s' % group
    print 'LoadGroupHierarchy("demo")'
    groupHierarchy = client.service.LoadGroupHierarchy("demo")
    print 'result:\n%s' % groupHierarchy
except WebFault, f:
    errors += 1
    print f
    print f.fault
except Exception, e:
    errors += 1
    print e
    print_exc()
    
try:
    url = 'http://cert.synxis.com/interface/ChannelConnect.asmx?WSDL'
    start(url)
    client = Client(url)
    print client
    guest_count = client.factory.create('ns0:GuestCount')
    print 'gc:\n%s' % guest_count
    sp = client.factory.create('ns0:StateProv')
    print 'sp:\n%s' % sp
    sp._StateCode = 'OR'
    print 'sp:\n%s' % sp
except WebFault, f:
    errors += 1
    print f
    print f.fault
except Exception, e:
    errors += 1
    print e
    print_exc()
    
try:
    url = 'http://www.netunitysoftware.com/wsrp2interop/wsrpproducer.asmx?Operation=WSDL&WsrpVersion=Two'
    start(url)
    client = Client(url)
    print client
except WebFault, f:
    errors += 1
    print f
    print f.fault
except Exception, e:
    errors += 1
    print e
    print_exc()

try:
    url = 'https://sec.neurofuzz-software.com/paos/genSSHA-SOAP.php?wsdl'
    start(url)
    client = Client(url)
    print client
    print client.service.genSSHA('hello', 'sha1')
except WebFault, f:
    errors += 1
    print f
    print f.fault
except Exception, e:
    errors += 1
    print e
    print_exc()

try:
    url = 'http://ap1314-dsr.compmed.ucdavis.edu/dataserver/Aperio.Images/Image?method=wsdl'
    start(url)
    client = Client(url)
    print client.factory.resolver.schema
    print client
    print 'Logon()'
    reply = client.service.Logon('testuser','test')
    print reply
except WebFault, f:
    errors += 1
    print f
    print f.fault
except Exception, e:
    errors += 1
    print e

try:
    url = 'http://soa.ebrev.info/service.wsdl'
    start(url)
    client = Client(url)
    print client
except WebFault, f:
    errors += 1
    print f
    print f.fault
except Exception, e:
    errors += 1
    print e

try:
    url = 'http://www.services.coxnewsweb.com/COXnetUR/URService?WSDL'
    start(url)
    client = Client(url)
    print client
    bean = client.service.getUserBean('abc', '123', 'mypassword', 'myusername')
except WebFault, f:
    errors += 1
    print f
    print f.fault
except Exception, e:
    errors += 1
    print e

try:
    url = 'http://arcweb.esri.com/services/v2/MapImage.wsdl'
    start(url)
    client = Client(url)
    print client
    env = client.factory.create('ns0:Envelope')
    print env
    options = client.factory.create('ns1:MapImageOptions')
    print options
except WebFault, f:
    errors += 1
    print f
    print f.fault
except Exception, e:
    errors += 1
    print e

try:
    url = "http://www.thomas-bayer.com/axis2/services/BLZService?wsdl"
    start(url)
    client = Client(url)
    print client
    print client.service.getBank("76251020")
except WebFault, f:
    errors += 1
    print f
    print f.fault
except Exception, e:
    errors += 1
    print e

try:
    url = "http://webservices.imacination.com/distance/Distance.jws?wsdl"
    start(url)
    client = Client(url)
    print client
    print client.service.getDistance('27613', '21601')
except WebFault, f:
    errors += 1
    print f
    print f.fault
except Exception, e:
    errors += 1
    print e
    
try:
    url = "http://arcweb.esri.com/services/v2/RouteFinder.wsdl"
    start(url)
    client = Client(url)
    print client
except WebFault, f:
    errors += 1
    print f
    print f.fault
except Exception, e:
    errors += 1
    print e

timer = metrics.Timer()

try:
    url = "https://www.e-conomic.com/secure/api1/EconomicWebService.asmx?WSDL"
    start(url)
    timer.start()
    client = Client(url)
    timer.stop()
    print 'create client: %s' % timer
    timer.start()
    s = str(client)
    timer.stop()
    print 'str(client): %s' % timer
    print 'client:\n%s' % s
    print 'Account_GetAll()'
    logger('suds.metrics').setLevel(logging.DEBUG)
    a = client.service.Account_GetAll()
    print a
except WebFault, f:
    errors += 1
    print f
    print f.fault
except Exception, e:
    errors += 1
    print e

print '\nFinished: errors = %d' % errors