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

#
# This test requires installation or visability to my local axis(1) server.
#

import sys
sys.path.append('../')

import logging
import traceback as tb
import suds.metrics as metrics
from tests import *
from suds import WebFault
from suds.client import Client

errors = 0

credentials = dict(username='jortel', password='abc123')

setup_logging()

from suds.xsd.sxbasic import Import
Import.bind('http://schemas.xmlsoap.org/soap/encoding/')


logging.getLogger('suds.client').setLevel(logging.DEBUG)

def start(url):
    global errors
    print '\n________________________________________________________________\n' 
    print 'Test @ ( %s )\nerrors = %d\n' % (url, errors)

try:
    url = 'http://localhost:8081/axis/services/basic-rpc-encoded?wsdl'
    client = Client(url, **credentials)
    print client
    #
    # create a name object using the wsdl
    #
    print 'create name'
    name = client.factory.create('ns1:Name')
    name.first = u'jeff'+unichr(1234)
    name.last = 'ortel'
    print name
    #
    # create a phone object using the wsdl
    #
    print 'create phone'
    phoneA = client.factory.create('ns1:Phone')
    phoneA.npa = 410
    phoneA.nxx = 555
    phoneA.number = 5138
    phoneB = client.factory.create('ns1:Phone')
    phoneB.npa = 919
    phoneB.nxx = 555
    phoneB.number = 4406
    #
    # create a dog
    #
    dog = client.factory.create('ns1:Dog')
    dog.name = 'Chance'
    dog.trained = True
    #
    # create a person object using the wsdl
    #
    person = client.factory.create('ns1:Person')
    print '{empty} person=\n%s' % person
    person.name = name
    person.age = 43
    person.phone = [phoneA,phoneB]
    person.pets = [dog]
    print 'person=\n%s' % person
    #
    # add the person (using the webservice)
    #
    print 'addPersion()'
    result = client.service.addPerson(person)
    print '\nreply(\n%s\n)\n' % str(result)
    #
    # create a new name object used to update the person
    #
    newname = client.factory.create('ns1:Name')
    newname.first = 'Todd'
    newname.last = None
    #
    # create AnotherPerson using Person
    #
    ap = client.factory.create('ns1:AnotherPerson')
    ap.name = person.name
    ap.age = person.age
    ap.phone = person.phone
    ap.pets = person.pets
    print 'AnotherPerson\n%s' % ap
    #
    # update the person's name (using the webservice)
    #
    print 'updatePersion()'
    result = client.service.updatePerson(ap, newname)
    print '\nreply(\n%s\n)\n' % str(result)
    result = client.service.updatePerson(ap, None)
    print '\nreply(\n%s\n)\n' % str(result)
except WebFault, f:
    errors += 1
    print f
    print f.fault
except Exception, e:
    errors += 1
    print e
    tb.print_exc()
    
try:
    print "echo('this is cool')"
    result = client.service.echo('this is cool')
    print '\nreply( %s )\n' % str(result)
    print 'echo(None)'
    result = client.service.echo(None)
    print '\nreply( %s )\n' % str(result)
except WebFault, f:
    errors += 1
    print f
    print f.fault
except Exception, e:
    errors += 1
    print e
    tb.print_exc()
    
try:
    print 'hello()'
    result = client.service.hello()
    print '\nreply( %s )\n' % str(result)
except WebFault, f:
    errors += 1
    print f
    print f.fault
except Exception, e:
    errors += 1
    print e
    tb.print_exc()

try:
    print 'testVoid()'
    result = client.service.getVoid()
    print '\nreply( %s )\n' % str(result)
except WebFault, f:
    errors += 1
    print f
    print f.fault
except Exception, e:
    errors += 1
    print e
    tb.print_exc()

try:
    array = client.factory.create('ArrayOf_xsd_string')
    array.item = ['my', 'dog', 'likes', 'steak']
    result = client.service.printList(array)
    print '\nreply( %s )\n' % str(result)
except WebFault, f:
    errors += 1
    print f
    print f.fault
except Exception, e:
    errors += 1
    print e
    tb.print_exc()

try:
    s = 'hello'
    for n in range(0, 3):
        print 'getList(%s, %d)' % (s, n)
        result = client.service.getList(s, n)
        print '\nreply( %s )\n' % str(result)
except WebFault, f:
    errors += 1
    print f
    print f.fault
except Exception, e:
    errors += 1
    print e
    tb.print_exc()

try:
    print 'testExceptions()' 
    result = client.service.throwException()
    print '\nreply( %s )\n' % tostr(result)
    raise Exception('Fault expected and not raised')
except WebFault, f:
    print f
    print f.fault
except Exception, e:
    errors += 1
    print e
    tb.print_exc()

try:
    url = 'http://localhost:8081/axis/services/basic-rpc-encoded?wsdl'
    start(url)
    client = Client(url, faults=False, **credentials)
    print 'testExceptions()'
    result = client.service.throwException()
    print '\nreply( %s )\n' % str(result)
except WebFault, f:
    errors += 1
    print f
    print f.fault
except Exception, e:
    errors += 1
    print e
    tb.print_exc()
    
print '\nFinished: errors=%d' % errors
