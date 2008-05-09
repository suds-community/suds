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

from suds import *
from new import classobj, function, instancemethod

log = logger(__name__)

class Object:
    
    @classmethod
    def subclass(cls, name):
        name = name.encode('utf-8')
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
    
    @classmethod
    def instance(cls, classname=None, dict={}):
        if classname is not None:
            subclass = cls.subclass(classname)
            inst = subclass()
        else:
            inst = Object()
        for a in dict.items():
            setattr(inst, a[0], a[1])
        return inst
    
    @classmethod
    def metadata(cls):
        return Metadata()

    def __init__(self):
        self.__keylist__ = []
        self.__printer__ = Printer()
        self.__metadata__ = Object.metadata()

    def items(self):
        for k in self.__keylist__:
            v = self.__dict__[k]
            yield (k,v)
            
    def dict(self):
        d = {}
        for item in self.items():
            d[item[0]] = item[1]
        return d

    def __setattr__(self, name, value):
        builtin =  name.startswith('__') and name.endswith('__')
        if not builtin and \
            name not in self.__keylist__:
            self.__keylist__.append(name)
        self.__dict__[name] = value

    def __len__(self):
        return len(self.__keylist__)
    
    def __contains__(self, name):
        return name in self.__keylist__

    def __str__(self):
        return unicode(self).encode('utf-8')
    
    def __unicode__(self):
        cls = self.__class__.__name__
        rep = self.__printer__.tostr(self)
        return u'(%s)%s' % (cls,rep)
    
    
class Metadata(Object):
    def __init__(self):
        self.__keylist__ = []
        self.__printer__ = Printer()


class Printer:
    """ 
    Pretty printing of a Object object.
    """
    
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
            if isinstance(object, (Object, dict)):
                return self.print_complex(object, n+2, nl)
            if isinstance(object, (list,tuple)):
                return self.print_collection(object, n+2)
        if isinstance(object, Object):
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
        if isinstance(object, (Object, dict)):
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