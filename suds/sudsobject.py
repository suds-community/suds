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

#
# EXPERIMENTAL alternative to the Property object and is highly
# subject to change/removal.
# The (Base) class is a {simpler} replacement for the Property class.
# The (Factory) class is an experiment on dynamically creating a class
#   and not sure if there is any value in the factory or not.
#

from suds import *
from new import classobj, function, instancemethod

class Base(object):
    
    @classmethod
    def subclass(cls, name):
        myclass = classobj(name,(cls,),{})
        init = '__init__'
        src = 'def %s(self):\n' % init
        src += '\t%s.%s(self)\n' % (cls.__name__,init)
        code = compile(src, '', 'exec')
        code = code.co_consts[0]
        fn = function(code, globals())
        m =  instancemethod(fn, None, myclass)
        setattr(myclass, name, m)
        return myclass

    def __init__(self):
        self.__keylist__ = []
        self.__printer__ = Printer()
        self.__metadata__ = {}

    def items(self):
        for k in self.__keylist__:
            v = self.__dict__[k]
            yield (k,v)
            
    def dict(self):
        d = {}
        for item in self.items():
            d[item[0]] = item[1]
        return d

    def __setattr__(self, k, v):
        builtin =  k.startswith('__') and k.endswith('__')
        if not builtin and \
            k not in self.__keylist__:
            self.__keylist__.append(k)
        self.__dict__[k] = v

    def __len__(self):
        return len(self.__keylist__)

    def __str__(self):
        return unicode(self).encode('utf-8')
    
    def __unicode__(self):
        cls = self.__class__.__name__
        rep = self.__printer__.tostr(self)
        return u'(%s)%s' % (cls,rep)


class Printer:
    
    """ Pretty printing of a Base object. """
    
    def __init__(self):
        self.indent = (lambda n :  '%*s'%(n*3,' '))
    
    def tostr(self, object, indent=-2):
        """ get s string representation of object """
        return self.process(object, indent)
    
    def process(self, object, n=0, nl=False):
        """ print object using the specified indent (n) and newline (nl). """
        if object is None:
            return 'None'
        if self.complex(object):
            if isinstance(object, (Base, dict)):
                return self.print_complex(object, n+2, nl)
            if isinstance(object, (list,tuple)):
                return self.print_collection(object, n+2)
        if isinstance(object, Base):
            object = object.dict()
        if isinstance(object, (dict,list,tuple)):
            if len(object) > 0:
                return tostr(object)
            else:
                return '<empty>'
        return '(%s)' % tostr(object)
    
    def print_complex(self, d, n, nl=False):
        """ print complex using the specified indent (n) and newline (nl). """
        s = []
        if nl:
            s.append('\n')
            s.append(self.indent(n))
        s.append('{')
        for item in d.items():
            s.append('\n')
            s.append(self.indent(n+1))
            if isinstance(item[1], (list,tuple)):            
                s.append(item[0])
                s.append('[]')
            else:
                s.append(item[0])
            s.append(' = ')
            s.append(self.process(item[1], n, True))
        s.append('\n')
        s.append(self.indent(n))
        s.append('}')
        return ''.join(s)

    def print_collection(self, c, n):
        """ print collection using the specified indent (n) and newline (nl). """
        s = []
        for item in c:
            s.append('\n')
            s.append(self.indent(n))
            s.append(self.process(item, n-2))
            s.append(',')
        return ''.join(s)
    
    def complex(self, object):
        """ get whether the object is a complex type """
        if isinstance(object, (Base, dict)):
            if len(object) > 1:
                return True
            for item in object.items():
                if self.complex(item[1]):
                    return True
        if isinstance(object, (list,tuple)):
            if len(object) > 1: return True
            for c in object:
                if self.complex(c):
                    return True
            return False
        return False

#
# Experimental
# Just testing some random things here
#

if __name__ == '__main__':

    A = Base.subclass('A')
    a = A()
    a.name='jeff'
    print a
    
    class B(A):
        def __init__(self):
            A.__init__(self)
    
    b = B()
    b.age=10
    print b
    
    class C(Base):
        def __init__(self):
            Base.__init__(self)
            
    c = C()
    c.doors = 4
    c.hatchback=True
    c.mpg = 30
    c.b = b
    print c
    
    c = C()
    c.name = 'funny car'
    setattr(c, 'doors', 2)
    setattr(c, 'hatchback', True)
    print c
    
    d = Base.subclass('D')()
    d.name = 'Elvis'
    d.age = '66'
    print d