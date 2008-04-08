# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
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
from suds.serviceproxy import ServiceProxy
from suds.schema import Schema
from suds.property import Property
from suds.wsdl import WSDL
from suds.bindings.binding import Binding
from suds.bindings.literal.marshaller import Marshaller
from suds.bindings.literal.unmarshaller import Unmarshaller
from suds.sax import Parser


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
    
    def test_misc(self):
        service = ServiceProxy(get_url('test'))
        marshaller = Marshaller(service.binding)
        unmarshaller = Unmarshaller(service.binding)
        
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
        service.binding.nil_supported = True
        p = unmarshaller.process(node)
        print p
        service.binding.nil_supported = False
        p = unmarshaller.process(node)
        print p
        service.binding.nil_supported = True
        print marshaller.process('dog', p)
        service.binding.nil_supported = False
        print marshaller.process('dog', p)

        
        p = Property()
        p2 = Property()
        p2.msg='hello'
        p2.xx =10
        p.name = ['jeff', p2]
        print p
        
        

        p = Property()
        p.first = u'jeff'+unichr(1234)
        p.age = u'44'
        x = str( p)

        p = unmarshaller.process(Parser().parse(file='/home/jortel/Desktop/x.xml'))
        print p
    
    def basic_test(self):
        
        #
        # create a service proxy using the wsdl.
        #
        service = ServiceProxy(get_url('test'))
        
        #
        # print the service (introspection)
        #
        print service
        
        #
        # create a name object using the wsdl
        #
        name = service.get_instance('tns:name')
        name.first = u'jeff'+unichr(1234)
        name.middle = None
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
        print '\nreply(\n%s\n)\n' % result.encode('utf-8')
        
        #
        # create a new name object used to update the person
        #
        newname = service.get_instance('name')
        newname.first = 'Todd'
        newname.last = None
        
        #
        # update the person's name (using the webservice) and print return person object
        #
        print 'updatePersion()'
        result = service.updatePerson(person, newname)
        print '\nreply(\n%s\n)\n' % str(result)
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
        # test list args
        #
        print 'testListArgs(list)'
        mylist = ['my', 'dog', 'likes', 'steak']
        result = service.testListArg(mylist)
        print '\nreply( %s )\n' % str(result)
        # tuple
        print 'testListArgs(tuple)'
        mylist = ('my', 'dog', 'likes', 'steak')
        result = service.testListArg(mylist)
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
            
    def rpc_test(self):
        
        #
        # create a service proxy using the wsdl.
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
        # update the person's name (using the webservice) and print return person object
        #
        print 'updatePersion()'
        result = service.updatePerson(person, newname)
        print '\nreply(\n%s\n)\n' % str(result)
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
        # test exceptions
        #
        try:
            print 'testExceptions()'
            result = service.testExceptions()
            print '\nreply( %s )\n' % str(result)
        except Exception, e:
            print e

            
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
        
        marshaller = Marshaller(service.binding)
        print marshaller.process('subject', subject)
        
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
        resourceCategory = service.get_enum('resourceCategory')
        print 'Enumeration (resourceCategory):\n%s' % resourceCategory
        
        
        #
        # get resource by category
        #
        print 'getResourcesByCategory()'
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
        service = ServiceProxy(get_url('perspectives'))

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
        
        configuration = service.get_instance('configuration')
        entry = service.get_instance('configuration.tns:properties.entry')
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


def test1():
    wsdl = WSDL(get_url('test'))
    schema = Schema(wsdl.definitions_schema())
    print schema.build('person')
    
def test2():
    wsdl = WSDL(get_url('contentsource'))
    schema = Schema(wsdl.definitions_schema())
    print schema.build('configuration')
    
def test3():
    wsdl = WSDL(get_url('contentsource'))
    schema = Schema(wsdl.definitions_schema())
    #print schema.build('property')
    #print schema.build('configuration.properties.entry')
    simple =  schema.build('propertySimple')
    print simple
    simple.name = 'userid'
    simple.stringValue = 'jortel'
    simple.id = 43
    print simple
    print DocumentWriter().tostring(simple.__type__, simple)

def test4():
    hint = Hint(addtag = True)
    hint.sequences = ('/root/test',)
    xml = '<root><name>jeff</name><age xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="int">20</age><test/></root>'
    reader = DocumentReader(hint=hint)
    writer = DocumentWriter()
    d = reader.read(string=xml)
    print d
    print d.age.get_metadata('_type')
    print writer.tostring('test', d)
    
def test5():
    wsdl = WSDL(get_url('auth'))
    schema = Schema(wsdl.definitions_schema())
    hint = schema.get_hint('loginResponse')
    print 'hint_____________________'
    for p in hint.sequences:
        print p
    hint = schema.get_hint('loginResponse')
    print 'hint_____________________'
    for p in hint.sequences:
        print p
        
if __name__ == '__main__':
    #logger('serviceproxy').setLevel(logging.DEBUG)
    #test4()
    #test5()
    #test3()
    test = Test()
    test.test_misc()
    test.basic_test()
    test.rpc_test()
    test.auth_test()
    test.resource_test()
    test.perspectives_test()
    test.contentsource_test()
