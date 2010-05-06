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
# This test requires installation or visability to an RHQ server.
# ( http://www.rhq-project.org )
#

import sys
sys.path.append('../')

import logging
import traceback as tb
import suds.metrics as metrics
from tests import *
from suds import null, WebFault
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


def rhqTest():
    
    global errors
    
    url = 'http://localhost.localdomain:7080/rhq-rhq-enterprise-server-ejb3/WebservicesManagerBean?wsdl'
    start(url)
    client = Client(url, cache=None)
    print client

    try:

        #
        # create name
        #
        name = client.factory.create('name')
        name.first = u'Jeff'+unichr(1234)
        name.last = 'Ortel &amp;lt; Company'
        #
        # create a phone object using the wsdl
        #
        phoneA = client.factory.create('phone')
        phoneA.npa = 410
        phoneA.nxx = 555
        phoneA.number = 5138
        phoneB = client.factory.create('phone')
        phoneB.npa = 919
        phoneB.nxx = 555
        phoneB.number = 4406
        #
        # lets add some animals
        #
        dog = client.factory.create('dog')
        dog.name = 'rover'
        dog.age = 3
        cat = client.factory.create('cat')
        cat.name = 'kitty'
        cat.age = 4
        #
        # create a person object using the wsdl
        #
        person = client.factory.create('person')
        print person
        person.name = name
        person.age = 43
        person.phone.append(phoneA)
        person.phone.append(phoneB)
        person.pet.append(dog)
        person.pet.append(cat)
        print person       
        #
        # addPerson()
        #
        print 'addPersion()'
        result = client.service.addPerson(person)
        sent = client.last_sent()
        rcvd = client.last_received()
        print '\nreply(\n%s\n)\n' % result
        #
        # create a new name object used to update the person
        #
        newname = client.factory.create('name')
        newname.first = 'Todd'
        newname.last = None
        #
        # update the person's name (using the webservice)
        #
        print 'updatePersion()'
        result = client.service.updatePerson(person, newname)
        print '\nreply(\n%s\n)\n' % str(result)
        result = client.service.updatePerson(person, None)
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
        result = client.service.testVoid()
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
        mylist = ['my', 'dog', 'likes', 'steak']
        print 'testListArgs(%s)' % mylist
        result = client.service.testListArg(mylist)
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
            if len(result) != n:
                errors += 1
                print 'expected (%d), reply (%d)' % (n, len(result))
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
        result = client.service.testExceptions()
        print '\nreply( %s )\n' % tostr(result)
        raise Exception('Fault expected and not raised')
    except WebFault, f:
        print f
        print f.fault
        print f.document
    except Exception, e:
        errors += 1
        print e
        tb.print_exc()

        
if __name__ == '__main__':
    errors = 0
    rhqTest()
    print '\nFinished: errors=%d' % errors
