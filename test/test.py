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

from suds import *
from suds.client import Client
from suds.serviceproxy import ServiceProxy
from suds.schema import Schema
from suds.sudsobject import Object
from suds.wsdl import WSDL
from suds.bindings.binding import Binding
from suds.bindings.marshaller import Marshaller
from suds.bindings.unmarshaller import *
from suds.sax import Parser, Element


urlfmt = 'http://localhost:7080/rhq-rhq-enterprise-server-ejb3/%s?wsdl'

services = \
{ 
    'test':'WebServiceTestBean', 
    'rpc':'RPCEncodedBean', 
    'auth':'SubjectManagerBean', 
    'resources':'ResourceManagerBean', 
    'perspectives':'PerspectiveManagerBean', 
    'content':'ContentManagerBean', 
    'contentsource':'ContentSourceManagerBean'
}

def get_url(name):
    return urlfmt % services[name]

class Test:
    
    def test_promote_prefixes(self):
        
        nsA = ('tns', 'tnsA')
        nsC = ('tns', 'tnsC')
        a = Element('A', ns=nsA)
        b = Element('tns:B')
        c = Element('tns:C')
        c.addPrefix(nsC[0], nsC[1])
        b.append(c)
        a.append(b)
        print a
        a.promotePrefixes()
        print a


    def test_misc(self):
        
        try:
            client = Client('http://efm.members.corpu.com/ws/projectdata.asmx?WSDL')
            print client
        except Exception, e:
            print e
        
        client = Client('file:///home/jortel/Desktop/misc/suds_files/jespern.wsdl.xml')
        print client
        try:
            print "login"
            print client.service.login('a','b')
        except WebFault, f:
            print f
        try:
            print "getCheckbox"
            user = client.factory.create('ns2:UserID')
            client.service.getCheckbox(user, 1)
        except WebFault, f:
            print f
        
        client = Client('http://soa.ebrev.info/service.wsdl')
        print client
        
        service = ServiceProxy('https://sec.neurofuzz-software.com/paos/genSSHA-SOAP.php?wsdl')
        print service
        print service.genSSHA('hello', 'sha1')
        
        client = Client('http://www.services.coxnewsweb.com/COXnetUR/URService?WSDL')
        print client
        try:
            bean = client.service.getUserBean('abc', '123', 'mypassword', 'myusername')
        except WebFault, f:
            print f
            
        client = Client('file:///home/jortel/Desktop/misc/suds_files/WebServiceTestBean.wsdl.xml')
        print client
        person = client.factory.create('person')
        print person
        first = client.factory.create('person.name.first')
        print first
        jeff = client.factory.create('person.jeff')
        print jeff
        authdog_id = client.factory.create('authdog.@id')
        print authdog_id
        try:
            logger('suds.client').setLevel(logging.DEBUG)
            print 'addPersion()'
            h = client.factory.create('authdog')
            h.set('hello doggy')
            h._id = 100
            result = client.service.addPerson(person, soapheaders=(h,))
            print '\nreply(\n%s\n)\n' % result.encode('utf-8')
        except Exception, e:
            print e
        logger('suds.client').setLevel(logging.ERROR)
        return
            
        return
        
        service = ServiceProxy(get_url('test'))
        
        marshaller = Marshaller(service.binding)
        encoder = Encoder(service.binding)
        unmarshaller = TypedBuilder(service.binding)
        
        p = service.get_instance('person')
        p.name.first='jeff'
        p.name.last='ortel'
        p.age = 21
        ph = service.get_instance('phone')
        ph.nxx = 919
        ph.npa = 606
        ph.number = None
        p.phone.append(ph)
        print p
        print encoder.process('person', p)
        sys.exit()
        
        x = """
        <person xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <name>
                <first>jeff</first>
                <middle/>
                <last xsi:nil="true"/>
            </name>
        </person>
        """
        node = Parser().parse(string=x).root()
        p = unmarshaller.process(node)
        print p
        p = unmarshaller.process(node)
        print p
        print marshaller.process('dog', p)
        print marshaller.process('dog', p)

        p = Object()
        p2 = Object()
        p2.msg='hello'
        p2.xx =10
        p.name = ['jeff', p2]
        print p

        p = Object()
        p.first = u'jeff'+unichr(1234)
        p.age = u'44'
        x = str(p)

        p = unmarshaller.process(Parser().parse(file='/home/jortel/Desktop/x.xml'))
        print p
    
    def basic_test(self):
        
        #
        # create a service client using the wsdl.
        #
        client = Client(get_url('test'))
        
        #
        # print the service (introspection)
        #
        print client
        
        #
        # create a name object using the wsdl
        #
        name = client.factory.create('tns:name')
        name.first = u'jeff'+unichr(1234)
        name.last = 'ortel'
        
        #
        # create a phone object using the wsdl
        #
        phoneA = client.factory.create('phone')
        phoneA.npa = 410
        phoneA.nxx = 822
        phoneA.number = 5138

        phoneB = client.factory.create('phone')
        phoneB.npa = 919
        phoneB.nxx = 606
        phoneB.number = 4406
        
        #
        # create a person object using the wsdl
        #
        person = client.factory.create('person')
        
        #
        # inspect empty person
        #
        print '{empty} person=\n%s' % person
        
        person.name = name
        person.age = 43
        person.phone.append(phoneA)
        #person.phone.append(phoneB)
        
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
        newname = client.factory.create('name')
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
            print 'testVoid()'
            result = client.service.testVoid()
            print '\nreply( %s )\n' % str(result)
        except Exception, e:
            print e

        #
        # test list args
        #
        print 'testListArgs(list)'
        mylist = ['my', 'dog', 'likes', 'steak']
        result = client.service.testListArg(mylist)
        print '\nreply( %s )\n' % str(result)
        # tuple
        print 'testListArgs(tuple)'
        mylist = ('my', 'dog', 'likes', 'steak')
        result = client.service.testListArg(mylist)
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
        
        #
        # test exceptions
        #
        try:
            print 'testExceptions() faults=True'
            result = client.service.testExceptions()
            print '\nreply( %s )\n' % tostr(result)
        except Exception, e:
            print e
            
        #
        # test faults
        #
        try:
            print 'testExceptions() faults=False'
            client = Client(get_url('test'), faults=False)
            result = client.service.testExceptions()
            print '\nreply( %s )\n' % tostr(result)
        except Exception, e:
            print e
            
    def rpc_test(self):
        
        #
        # create a service client using the wsdl.
        #
        service = ServiceProxy(get_url('rpc'))
        
        #
        # print the service (introspection)
        #
        print service
        
        #
        # create a name object using the wsdl
        #
        name = service.get_instance('tns:name')
        name.first = 'jeff'
        name.last = 'ortel'
        
        #
        # create a phone object using the wsdl
        #
        phoneA = service.get_instance('phone')
        phoneA.npa = 410
        phoneA.nxx = 822
        phoneA.number = 5138

        phoneB = service.get_instance('phone')
        phoneB.npa = 919
        phoneB.nxx = 606
        phoneB.number = 4406
        
        #
        # create a person object using the wsdl
        #
        person = service.get_instance('person')
        
        #
        # inspect empty person
        #
        print '{empty} person=\n%s' % person
        
        person.name = name
        person.age = 43
        person.phone.append(phoneA)
        person.phone.append(phoneB)
        
        #
        # inspect person
        #
        print 'person=\n%s' % person
        
        #
        # add the person (using the webservice)
        #
        print 'addPersion()'
        result = service.addPerson(person)
        print '\nreply(\n%s\n)\n' % str(result)
        
        #
        # create a new name object used to update the person
        #
        newname = service.get_instance('name')
        newname.first = 'Todd'
        newname.last = 'Sanders'
        
        #
        # create a person object using the wsdl
        #
        another_person = service.get_instance('anotherPerson')
        
        #
        # inspect empty person
        #
        print '{empty} another_person=\n%s' % another_person
        
        person.name = name
        person.age = 43
        person.phone.append(phoneA)
        person.phone.append(phoneB)
        
        #
        # inspect person
        #
        print 'another_person=\n%s' % another_person
        
        #
        # update the person's name (using the webservice) and print return person object
        #
        print 'updatePersion()'
        result = service.updatePerson(another_person, newname)
        print '\nreply(\n%s\n)\n' % str(result)
        print 'updatePersion() newperson = None'
        result = service.updatePerson(person, None)
        print '\nreply(\n%s\n)\n' % str(result)
        
        #
        # invoke the echo service
        #
        print 'echo()'
        result = service.echo('this is cool')
        print '\nreply( %s )\n' % str(result)
        
        #
        # invoke the hello service
        #
        print 'hello()'
        result = service.hello()
        print '\nreply( %s )\n' % str(result)
        
        #
        # invoke the testVoid service
        #
        try:
            print 'testVoid()'
            result = service.testVoid()
            print '\nreply( %s )\n' % str(result)
        except Exception, e:
            print e
            
        #
        # test list returned
        #
        print 'getList(str, 1)'
        result = client.service.getList('hello', 1)
        print '\nreply( %s )\n' % str(result)
        
        print 'getList(str, 3)'
        result = client.service.getList('hello', 3)
        print '\nreply( %s )\n' % str(result)
        
        #
        # test exceptions
        #
        try:
            print 'testExceptions()'
            result = service.testExceptions()
            print '\nreply( %s )\n' % str(result)
        except Exception, e:
            print e



    def rpc_enctest(self):        

        try:
            service = ServiceProxy('http://test.closingmarket.com/ClosingMarketService/cminterface.asmx?WSDL')
            print service
            token = service.Login( 'DVTest1@bbwcdf.com', 'DevTest1')
            print token
        except Exception, e:
            print e
            
        print '************ JEFF ***************'
        
        #
        # create a service proxy using the wsdl.
        #
        service = ServiceProxy('http://127.0.0.1:8080/axis/services/Jeff?wsdl')
        
        #
        # print the service (introspection)
        #
        #print service
        
        #
        # create a person object using the wsdl
        #
        person = service.get_instance('Person')
        
        #
        # inspect empty person
        #
        print '{empty} person=\n%s' % person
        
        person.name = 'jeff ortel'
        person.age = 43
        
        #
        # inspect person
        #
        print 'person=\n%s' % person
        
        #
        # add the person (using the webservice)
        #
        print 'addPersion()'
        result = service.addPerson(person)
        print '\nreply(\n%s\n)\n' % str(result)


    def auth_test(self):
        
        service = ServiceProxy(get_url('auth'))
        
        #
        # print the service (introspection)
        #
        print service
            
        #
        # login
        #
        print 'login()'
        subject = service.login('rhqadmin', 'rhqadmin')
        print '\nreply(\n%s\n)\n' % str(subject)
        
        #
        # create page control and get all subjects
        #
        pc = service.get_instance('pageControl')
        pc.pageNumber = 0
        pc.pageSize = 0
        
        print 'getAllSubjects()'
        users = service.getAllSubjects(pc)
        print 'Reply:\n(\n%s\n)\n' % str(users)
        
        #
        # get user preferences
        #
        print 'loadUserConfiguration()'
        id = subject.id
        print subject
        prefs = service.loadUserConfiguration(id)
        print 'Reply:\n(\n%s\n)\n' % str(prefs)
        

    def resource_test(self):
        
        print 'testing resources (service) ...'
        
        #
        # create a service proxy using the wsdl.
        #
        service = ServiceProxy(get_url('resources'))

        #
        # print the service (introspection)
        #
        print service

        #
        # login
        #
        print 'login()'
        subject = ServiceProxy(get_url('auth')).login('rhqadmin', 'rhqadmin')
        
        #
        # create page control and get all subjects
        #
        pc = service.get_instance('pageControl')
        pc.pageNumber = 0
        pc.pageSize = 0
        
        #
        # get enumerations
        #
        resourceCategory = service.get_instance('resourceCategory')
        print 'Enumeration (resourceCategory):\n%s' % resourceCategory
        
        
        #
        # get resource by category
        #
        print 'getResourcesByCategory()'
        logger('suds.client').setLevel(logging.DEBUG)
        platforms = service.getResourcesByCategory(subject, resourceCategory.PLATFORM, 'COMMITTED', pc)
        print 'Reply:\n(\n%s\n)\n' % str(platforms)
        
        #
        # get resource tree
        #
        for p in platforms:
            print 'getResourcesTree()'
            tree = service.getResourceTree(p.id)
            print 'Reply:\n(\n%s\n)\n' % str(tree)
            
    def perspectives_test(self):
        
        print 'testing perspectives (service) ...'
        
        #
        # create a service proxy using the wsdl.
        #
        url = get_url('perspectives')
        print url
        service = ServiceProxy(url)
        
        gtr = service.get_instance('getTasksResponse.return')
        print gtr

        #
        # print the service (introspection)
        #
        print service

        #
        # login
        #
        print 'login()'
        auth = ServiceProxy(get_url('auth'))
        print auth
        subject = auth.login('rhqadmin', 'rhqadmin')

        #
        # get all perspectives
        #
        print 'getPerspective()'
        perspectives = service.getPerspective("content")
        print 'perspectives: ', str(perspectives)
        
        print 'getAllPerspective()'
        perspectives = service.getAllPerspectives()
        print 'perspectives: ', str(perspectives)
        
    def contentsource_test(self):
        
        print 'testing content source (service) ...'
        
        #
        # create a service proxy using the wsdl.
        #
        service = ServiceProxy(get_url('contentsource'))

        #
        # print the service (introspection)
        #
        print service
        print service.__client__.service.__client__.schema
        
        configuration = service.get_instance('configuration')
        entry = service.get_instance('configuration.tns:properties.tns:entry')
        simple = service.get_instance('propertySimple')
        entry.key = 'location'
        simple.name = 'location'
        simple.stringValue = 'http://download.skype.com/linux/repos/fedora/updates/i586'
        entry.value = simple
        configuration.properties.entry.append(entry)
        configuration.notes = 'SkipeAdapter'
        configuration.version = 1234
        print configuration
        
        name = 'SkipeAdapter'
        description = 'The skipe adapter'
        type = 'YumSource'

        #
        # login
        #
        print 'login()'
        subject = ServiceProxy(get_url('auth')).login('rhqadmin', 'rhqadmin')

        #
        # get all perspectives
        #
        try:
            print 'createContentSource()'
            result = service.createContentSource(subject, name, description, type, configuration, False)
            print 'createContentSource: ', str(result)
        except Exception, e:
            print e

if __name__ == '__main__':
    
    #logger('suds.schema').setLevel(logging.DEBUG)
    #logger('suds.resolver').setLevel(logging.DEBUG)
    #logger('suds.serviceproxy').setLevel(logging.DEBUG)
    #logger('suds.client').setLevel(logging.DEBUG)
    #logger('suds.bindings.marshaller').setLevel(logging.DEBUG)
    test = Test()
    test.test_misc()
    test.basic_test()
    test.rpc_test()
    #test.rpc_enctest()
    #test.auth_test()
    #test.resource_test()
    #test.perspectives_test()
    #test.contentsource_test()
