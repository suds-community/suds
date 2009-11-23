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
import suds.metrics as metrics
from tests import *
from suds import WebFault
from suds.client import Client

errors = 0

setup_logging()

#logging.getLogger('suds.client').setLevel(logging.DEBUG)
#logging.getLogger('suds.metrics').setLevel(logging.DEBUG)
#logging.getLogger('suds').setLevel(logging.DEBUG)


def start(url):
    global errors
    print '\n________________________________________________________________\n' 
    print 'Test @ ( %s ) %d' % (url, errors)

try:
    url = 'http://mssoapinterop.org/asmx/simple.asmx?WSDL'
    start(url)
    client = Client(url)
    print client
    # string
    input = "42"
    d = dict(inputString=input)
    result = client.service.echoString(**d)
    print 'echoString() =  %s' % result
    assert result == input
    # int
    input = 42
    result = client.service.echoInteger(input)
    print 'echoInteger() = %s' % result
    assert result == input
    # float
    input = 4.2
    result = client.service.echoFloat(input)
    print 'echoFloat() = %s' % result
    assert result == input
    input = [1,2,3,4]
    # suds 0.3.8+
    result = client.service.echoIntegerArray(input)
    print 'echoIntegerArray() = %s' % result
    # looks like umx package needs an 'encoded' unmarshaller
    # that respects arrayType="" and creates a python [].
    # assert result == input
except WebFault, f:
    errors += 1
    print f
    print f.fault
except Exception, e: 
    errors += 1
    print e
    tb.print_exc()
    
try:
    url = 'http://jira.atlassian.com/rpc/soap/jirasoapservice-v2?wsdl'
    start(url)
    client = Client(url)
    print client
    token = client.service.login('soaptester', 'soaptester')
    print 'token="%s"' % token
    user = client.service.getUser(token, 'soaptester')
    print 'user="%s"' % user
except WebFault, f:
    errors += 1
    print f
    print f.fault
except Exception, e: 
    errors += 1
    print e
    tb.print_exc()
    
try:
    url = 'http://jira.atlassian.com/rpc/soap/jirasoapservice-v2?wsdl'
    start(url+'  ** cloned **')
    client = Client(url).clone()
    print client
    token = client.service.login('soaptester', 'soaptester')
    print 'token="%s"' % token
    user = client.service.getUser(token, 'soaptester')
    print 'user="%s"' % user
except WebFault, f:
    errors += 1
    print f
    print f.fault
except Exception, e: 
    errors += 1
    print e
    tb.print_exc()
    
try:
    url = ' http://www.boyzoid.com/comp/randomQuote.cfc?wsdl '
    start(url)
    client = Client(url)
    print client
    print client.service.getQuote(False)
except WebFault, f:
    errors += 1
    print f
    print f.fault
except Exception, e:
    errors += 1
    print e
    tb.print_exc()
    
try:
    url = 'http://www.zenfolio.com/zf/api/zfapi.asmx?wsdl'
    start(url)
    client = Client(url)
    print client
    #client.setport(0)
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
    tb.print_exc()
    
try:
    url = 'http://cert.synxis.com/interface/ChannelConnect.asmx?WSDL'
    start(url)
    client = Client(url)
    print client
    #client.setport(0)
    tpa = client.factory.create('ns1:TPA_Extensions')
    print client.service.Ping(tpa, "hello")
except WebFault, f:
    errors += 1
    print f
    print f.fault
except Exception, e:
    errors += 1
    print e
    tb.print_exc()

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
    tb.print_exc()

try:
    url = 'http://ap1314-dsr.compmed.ucdavis.edu/dataserver/Aperio.Images/Image?method=wsdl'
    start(url)
    client = Client(url)
    #print client.factory.resolver.schema
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
    tb.print_exc()

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
    tb.print_exc()

try:
    url = 'http://arcweb.esri.com/services/v2/MapImage.wsdl'
    start(url)
    client = Client(url)
    print client
    env = client.factory.create('ns2:Envelope')
    print env
    options = client.factory.create('ns4:MapImageOptions')
    print options
except WebFault, f:
    errors += 1
    print f
    print f.fault
except Exception, e:
    errors += 1
    print e
    tb.print_exc()

try:
    url = "http://www.thomas-bayer.com/axis2/services/BLZService?wsdl"
    start(url)
    client = Client(url)
    print client
    #client.setport(0)
    print client.service.getBank("76251020")
except WebFault, f:
    errors += 1
    print f
    print f.fault
except Exception, e:
    errors += 1
    print e
    tb.print_exc()
    
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
    tb.print_exc()

timer = metrics.Timer()

try:
    url = "https://www.e-conomic.com/secure/api1/EconomicWebService.asmx?WSDL"
    start(url)
    timer.start()
    client = Client(url)
    #client.setport(0)
    timer.stop()
    print 'create client: %s' % timer
    timer.start()
    s = str(client)
    timer.stop()
    print 'str(client): %s' % timer
    print 'client:\n%s' % s
except WebFault, f:
    errors += 1
    print f
    print f.fault
except Exception, e:
    errors += 1
    print e
    tb.print_exc()

print '\nFinished: errors = %d' % errors
