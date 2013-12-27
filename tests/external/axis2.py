# This program is free software; you can redistribute it and/or modify it under
# the terms of the (LGPL) GNU Lesser General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Library Lesser General Public License
# for more details at ( http://www.gnu.org/licenses/lgpl.html ).
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
# written by: Jeff Ortel ( jortel@redhat.com )

import sys
sys.path.append('../../')

from tests import *
from suds import *
from suds.client import Client
from datetime import datetime


errors = 0
url = 'http://localhost:8080/axis2/services/BasicService?wsdl'
print 'url=%s' % url

#
# create a service client using the wsdl.
#
client = Client(url)

#
# print the service (introspection)
#
print client

print 'printList()'
print client.service.printList(['a','b'])

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
print dog
dog.name = 'Chance'
dog.trained = True
print dog

#
# create a person object using the wsdl
#
person = client.factory.create('ns2:Person')

#
# inspect empty person
#
print '{empty} person=\n%s' % person

person.name = name
person.age = None
person.birthday = datetime.now()
person.phone.append(phoneA)
person.phone.append(phoneB)
person.pets.append(dog)

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

#
# update the person's name (using the webservice) and print return person object
#
print 'updatePersion()'
result = client.service.updatePerson(person, newname)
print '\nreply(\n%s\n)\n' % str(result)
result = client.service.updatePerson(person, None)
print '\nreply(\n%s\n)\n' % str(result)


#
# invoke the echo service
#
print 'echo()'
client.service.echo(None)
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
for n in range(0, 3):
    print 'getList(str, %d)' % n
    result = client.service.getList('hello', n)
    print '\nreply( %s )\n' % str(result)
    assert ( isinstance(result, list) and len(result) == n )

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
    client.set_options(faults=False)
    result = client.service.throwException()
    print '\nreply( %s )\n' % tostr(result)
except Exception, e:
    print e

print '\nfinished: errors=%d' % errors
