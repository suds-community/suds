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

print '_____________________ L O C A L (axis) _________________________'

axis2url = 'http://localhost:8080/axis2/services/BasicService?wsdl'
axisUrl = 'http://localhost:8081/axis/services/basic-rpc-encoded?wsdl'
url = axisUrl

#logger('suds.client').setLevel(logging.DEBUG)
    
print 'url=%s' % url

#
# create a service client using the wsdl.
#
client = Client(url)

#
# print the service (introspection)
#
print client

#
# create a name object using the wsdl
#
print 'create name'
name = client.factory.create('ns2:Name')
name.first = u'jeff'+unichr(1234)
name.last = 'ortel'

print name

#
# create a phone object using the wsdl
#
print 'create phone'
phoneA = client.factory.create('ns2:Phone')
phoneA.npa = 410
phoneA.nxx = 822
phoneA.number = 5138

phoneB = client.factory.create('ns2:Phone')
phoneB.npa = 919
phoneB.nxx = 606
phoneB.number = 4406

#
# create a dog
#
dog = client.factory.create('ns2:Dog')
dog.name = 'Chance'
dog.trained = True

#
# create a person object using the wsdl
#
person = client.factory.create('ns2:Person')

#
# inspect empty person
#
print '{empty} person=\n%s' % person

person.name = name
person.age = 43
person.phone = [phoneA,phoneB]
person.pets = [dog]

#
# inspect person
#
print 'person=\n%s' % person

#
# add the person (using the webservice)
#
print 'addPersion()'
result = client.service.addPerson(person)
print '\nreply(\n%s\n)\n' % result.encode('utf-8')

#
# create a new name object used to update the person
#
newname = client.factory.create('ns2:Name')
newname.first = 'Todd'
newname.last = None

ap = client.factory.create('ns2:AnotherPerson')
ap.name = person.name
ap.age = person.age
ap.phone = person.phone
ap.pets = person.pets

print 'AnotherPerson\n%s' % ap

#
# update the person's name (using the webservice) and print return person object
#
print 'updatePersion()'
result = client.service.updatePerson(ap, newname)
print '\nreply(\n%s\n)\n' % str(result)
result = client.service.updatePerson(ap, None)
print '\nreply(\n%s\n)\n' % str(result)


#
# invoke the echo service
#
print 'echo()'
result = client.service.echo('this is cool')
print '\nreply( %s )\n' % str(result)

print 'echo() with {none}'
result = client.service.echo(None)
print '\nreply( %s )\n' % str(result)

#
# invoke the hello service
#
print 'hello()'
result = client.service.hello()
print '\nreply( %s )\n' % str(result)

#
# invoke the testVoid service
#
try:
    print 'getVoid()'
    result = client.service.getVoid()
    print '\nreply( %s )\n' % str(result)
except Exception, e:
    print e

#
# test list args
#
print 'getList(list)'
mylist = ['my', 'dog', 'likes', 'steak']
result = client.service.printList(mylist)
print '\nreply( %s )\n' % str(result)
# tuple
print 'testListArgs(tuple)'
mylist = ('my', 'dog', 'likes', 'steak')
result = client.service.printList(mylist)
print '\nreply( %s )\n' % str(result)

#
# test list returned
#
print 'getList(str, 1)'
result = client.service.getList('hello', 1)
print '\nreply( %s )\n' % str(result)

print 'getList(str, 3)'
result = client.service.getList('hello', 3)
print '\nreply( %s )\n' % str(result)

print 'addPet()'
dog = client.factory.create('ns2:Dog')
dog.name = 'Chance'
dog.trained = True
print dog
try:
    result = client.service.addPet(person, dog)
    print '\nreply( %s )\n' % str(result)
except Exception, e:
    print e

print '___________________ E X C E P T I O N S __________________________'

#
# test exceptions
#
try:
    print 'throwException() faults=True'
    result = client.service.throwException()
    print '\nreply( %s )\n' % tostr(result)
except Exception, e:
    print e
    
#
# test faults
#
try:
    print 'throwException() faults=False'
    client.service.__client__.faults=False
    result = client.service.throwException()
    print '\nreply( %s )\n' % tostr(result)
except Exception, e:
    print e
    
print '_____________________ PUBLIC (misc) _________________________'
    
client = Client('http://soa.ebrev.info/service.wsdl')
print client

client = Client('https://sec.neurofuzz-software.com/paos/genSSHA-SOAP.php?wsdl')
print client
print client.service.genSSHA('hello', 'sha1')

client = Client('http://www.services.coxnewsweb.com/COXnetUR/URService?WSDL')
print client
try:
    bean = client.service.getUserBean('abc', '123', 'mypassword', 'myusername')
except WebFault, f:
    print f
    
client = Client('http://arcweb.esri.com/services/v2/MapImage.wsdl')
print client
env = client.factory.create('ns2:Envelope')
print env
options = client.factory.create('ns1:MapImageOptions')
print options

url = "http://www.thomas-bayer.com/axis2/services/BLZService?wsdl"
client = Client(url)
print client
try:
    print client.service.getBank("76251020")
except WebFault, f:
    print f

url = "http://webservices.imacination.com/distance/Distance.jws?wsdl"
client = Client(url)
print client
try:
    print client.service.getDistance('27613', '21601')
except WebFault, f:
    print f
    
url = "http://arcweb.esri.com/services/v2/RouteFinder.wsdl"
client = Client(url)
print client
try:
    pass
except WebFault, f:
    print f
    
    
