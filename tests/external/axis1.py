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

#
# This test requires installation or visibility to my local axis(1) server.
#

import sys
sys.path.append('../../')

import traceback as tb
from tests import *
from suds import WebFault
from suds.client import Client
from suds.sudsobject import Object
from suds.transport.https import HttpAuthenticated
from suds.plugin import *


errors = 0
credentials = dict(username='jortel', password='abc123')


class MyInitPlugin(InitPlugin):

    def initialized(self, context):
        print 'PLUGIN (init): initialized: ctx=%s' % context.__dict__


class MyDocumentPlugin(DocumentPlugin):

    def loaded(self, context):
        print 'PLUGIN (document): loaded: ctx=%s' % context.__dict__

    def parsed(self, context):
        print 'PLUGIN (document): parsed: ctx=%s' % context.__dict__


class MyMessagePlugin(MessagePlugin):

    def marshalled(self, context):
        print 'PLUGIN (message): marshalled: ctx=%s' % context.__dict__

    def sending(self, context):
        print 'PLUGIN (message): sending: ctx=%s' % context.__dict__

    def received(self, context):
        print 'PLUGIN (message): received: ctx=%s' % context.__dict__

    def parsed(self, context):
        print 'PLUGIN (message): parsed: ctx=%s' % context.__dict__

    def unmarshalled(self, context):
        print 'PLUGIN: (massage): unmarshalled: ctx=%s' % context.__dict__


myplugins = (
    MyInitPlugin(),
    MyDocumentPlugin(),
    MyMessagePlugin(),
)


def start(url):
    global errors
    print '\n________________________________________________________________\n'
    print 'Test @ ( %s )\nerrors = %d\n' % (url, errors)

try:
    url = 'http://localhost:8081/axis/services/basic-rpc-encoded?wsdl'
    start(url)
    t = HttpAuthenticated(**credentials)
    client = Client(url, transport=t, cache=None, plugins=myplugins)
    print client
    #
    # create a name object using the wsdl
    #
    print 'create name'
    name = client.factory.create('ns0:Name')
    name.first = u'jeff'+unichr(1234)
    name.last = 'ortel'
    print name
    #
    # create a phone object using the wsdl
    #
    print 'create phone'
    phoneA = client.factory.create('ns0:Phone')
    phoneA.npa = 410
    phoneA.nxx = 555
    phoneA.number = 5138
    phoneB = client.factory.create('ns0:Phone')
    phoneB.npa = 919
    phoneB.nxx = 555
    phoneB.number = 4406
    phoneC = {
        'npa':205,
        'nxx':777,
        'number':1212
    }
    #
    # create a dog
    #
    dog = client.factory.create('ns0:Dog')
    dog.name = 'Chance'
    dog.trained = True
    #
    # create a person object using the wsdl
    #
    person = client.factory.create('ns0:Person')
    print '{empty} person=\n%s' % person
    person.name = name
    person.age = 43
    person.phone = [phoneA,phoneB,phoneC]
    person.pets = [dog]
    print 'person=\n%s' % person
    #
    # add the person (using the webservice)
    #
    print 'addPersion()'
    result = client.service.addPerson(person)
    print '\nreply(\n%s\n)\n' % str(result)

    #
    # Async
    #
    client.options.nosend=True
    reply = '<?xml version="1.0" encoding="utf-8"?><soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><soapenv:Body><ns1:addPersonResponse soapenv:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:ns1="http://basic.suds.fedora.org"><addPersonReturn xsi:type="xsd:string">person (jeff&#x4D2;,ortel) at age 43 with phone numbers (410-555-5138,919-555-4406,205-777-1212, and pets (Chance,) - added.</addPersonReturn></ns1:addPersonResponse></soapenv:Body></soapenv:Envelope>'
    request = client.service.addPerson(person)
    result = request.succeeded(reply)
    error = Object()
    error.httpcode = '500'
    client.options.nosend=False
#    request.failed(error)

    #
    #
    # create a new name object used to update the person
    #
    newname = client.factory.create('ns0:Name')
    newname.first = 'Todd'
    newname.last = None
    #
    # create AnotherPerson using Person
    #
    ap = client.factory.create('ns0:AnotherPerson')
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
    url = 'http://localhost:8081/axis/services/basic-rpc-encoded?wsdl'
    start(url)
    t = HttpAuthenticated(**credentials)
    client = Client(url, transport=t, cache=None)
    print client
    #
    # create a name object as dict
    #
    print 'create name'
    name = {}
    name['first'] = 'Elmer'
    name['last'] = 'Fudd'
    print name
    #
    # create a phone as dict
    #
    print 'create phone'
    phoneA = {}
    phoneA['npa'] = 410
    phoneA['nxx'] = 555
    phoneA['number'] = 5138
    phoneB = {}
    phoneB['npa'] = 919
    phoneB['nxx'] = 555
    phoneB['number'] = 4406
    phoneC = {
        'npa':205,
        'nxx':777,
        'number':1212
    }
    #
    # create a dog
    #
    dog = {
        'name':'Chance',
        'trained':True,
    }
    #
    # create a person as dict
    #
    person = {}
    print '{empty} person=\n%s' % person
    person['name'] = name
    person['age'] = 43
    person['phone'] = [phoneA,phoneB, phoneC]
    person['pets'] = [dog]
    print 'person=\n%s' % person
    #
    # add the person (using the webservice)
    #
    print 'addPersion()'
    result = client.service.addPerson(person)
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
    print "echo(' this is cool ')"
    result = client.service.echo('this is cool')
    print '\nreply( "%s" )\n' % str(result)
    print 'echo(None)'
    result = client.service.echo(None)
    print '\nreply( "%s" )\n' % str(result)
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
    print '** new style arrays **'
    words = ['my', 'dog', 'likes', 'steak']
    result = client.service.printList(words)
    print '\nreply( %s )\n' % str(result)

    print '** old style arrays **'
    array = client.factory.create('ArrayOf_xsd_string')
    print 'ArrayOf_xsd_string=\n%s' % array
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
        assert ( isinstance(result, list) and len(result) == n )
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
