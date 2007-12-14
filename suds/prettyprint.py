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

def prettyprint(object):
    return prettyprinter().tostring(object)

class prettyprinter:
    
    """ Pretty printing of a Property object. """
    
    def tostring(self, object, n=-2):
        """ get the pretty printed string representation of a Property object """
        return self.__print(object, n)
    
    def __print(self, object, n=0, nl=False):
        """ print the specified object using the specified indent (n) and newline (nl). """
        if object is None:
            return 'NONE'
        object = self.__translate(object)
        if self.__complex(object):
            if isinstance(object, dict):
                return self.__print_dict(object, n+2, nl)
            if isinstance(object, list) or isinstance(object, tuple):
                return self.__print_collection(object, n+2)
        if self.__collection(object):
            if len(object) > 0:
                return str(object)
            else:
                return '<empty>'
        return '(%s)' % str(object)
    
    def __print_dict(self, d, n, nl=False):
        """ print the specified dictionary using the specified indent (n) and newline (nl). """
        s = []
        if nl:
            s.append('\n')
            s.append(self.__indent(n))
        s.append('{')
        for item in d.items():
            s.append('\n')
            s.append(self.__indent(n+1))
            if isinstance(item[1], list) or isinstance(item[1], tuple):               
                s.append(item[0])
                s.append('[]')
            else:
                s.append(item[0])
            s.append(' = ')
            s.append(self.__print(item[1], n, True))
        s.append('\n')
        s.append(self.__indent(n))
        s.append('}')
        return ''.join(s)

    def __print_collection(self, c, n):
        """ print the specified list|tuple using the specified indent (n) and newline (nl). """
        s = []
        for item in c:
            s.append('\n')
            s.append(self.__indent(n))
            s.append(self.__print(item, n-2))
            s.append(',')
        return ''.join(s)
    
    def __complex(self, object):
        """ get whether the object is a complex type """
        if isinstance(object, dict) and len(object) > 1:
            return True
        if isinstance(object, list) or isinstance(object, tuple):
            if len(object) > 1: return True
            for v in object:
                if isinstance(v, dict) or isinstance(v, list) or isinstance(v, tuple):
                    return True
            return False
        return False
    
    def __translate(self, object):
        """ attempt to translate the object into a dictionary """
        result = object
        try:
            result = object.dict()
        except:
            pass
        return result
    
    def __collection(self, object):
        """ get whether the object is a collection (list|tuple)."""
        return (  isinstance(object, dict) or isinstance(object, list) or isinstance(object, tuple) )
                
    def __indent(self, n):
        """ generate (n) spaces for indent. """
        return '%*s'% (n*3, ' ')