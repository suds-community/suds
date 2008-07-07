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

"""
The I{sxbasic} module provides classes that represent
I{basic} schema objects.
"""

from suds import *
from suds.xsd import *
from suds.xsd.sxbase import SchemaObject, Polymorphic
from suds.sudsobject import Factory
from suds.sax import Parser, splitPrefix, Namespace
from urlparse import urljoin

log = logger(__name__)

class Complex(SchemaObject):
    """
    Represents an (xsd) schema <xs:complexType/> node.
    @cvar valid_children: A list of valid child node names
    @type valid_children: (I{str},...)
    """
    
    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{schema.Schema}
        @param root: The xml root node.
        @type root: L{sax.Element}
        """
        SchemaObject.__init__(self, schema, root)
        
    def valid_children(self):
        """
        Get a list of valid child tag names.
        @return: A list of child tag names.
        @rtype: [str,...]
        """
        return ('attribute', 'sequence', 'all', 'complexContent', 'any')
        
    def get_name(self):
        """ gets the <xs:complexType name=""/> attribute value """
        return self.root.get('name')
    
    def __init0__(self):
        """ update derived flag """
        for c in self.children:
            if c.__class__ in (Extension, ComplexContent):
                self.derived = True
                break
        
    def __init2__(self):
        """ promote grand-children """
        self.promote_grandchildren()
    
    def __lt__(self, other):
        """ <element/> first """
        return ( not isinstance(other, Element) )


class Simple(SchemaObject):
    """
    Represents an (xsd) schema <xs:simpleType/> node
    """
    
    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{schema.Schema}
        @param root: The xml root node.
        @type root: L{sax.Element}
        """
        SchemaObject.__init__(self, schema, root)

    def valid_children(self):
        """
        Get a list of valid child tag names.
        @return: A list of child tag names.
        @rtype: [str,...]
        """
        return ('restriction', 'any',)

    def get_name(self):
        """ gets the <xs:simpleType name=""/> attribute value """
        return self.root.get('name')

    def ref(self):
        """ gets the <xs:simpleType xsi:type=""/> attribute value """
        return self.root.get('type')
    
    def enum(self):
        for c in self.children:
            if isinstance(c, Restriction):
                for gc in c.children:
                    if isinstance(gc, Enumeration):
                        return True
        return False

   
class Restriction(SchemaObject):
    """
    Represents an (xsd) schema <xs:restriction/> node
    """
    
    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{schema.Schema}
        @param root: The xml root node.
        @type root: L{sax.Element}
        """
        SchemaObject.__init__(self, schema, root)
        
    def get_name(self):
        return self.__class__.__name__

    def valid_children(self):
        """
        Get a list of valid child tag names.
        @return: A list of child tag names.
        @rtype: [str,...]
        """
        return ('enumeration',)


class Sequence(SchemaObject):
    """
    Represents an (xsd) schema <xs:sequence/> node.
    """

    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{schema.Schema}
        @param root: The xml root node.
        @type root: L{sax.Element}
        """
        SchemaObject.__init__(self, schema, root)

    def valid_children(self):
        """
        Get a list of valid child tag names.
        @return: A list of child tag names.
        @rtype: [str,...]
        """
        return ('element', 'any',)


class All(Sequence):
    """
    Represents an (xsd) schema <xs:all/> node.
    """

    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{schema.Schema}
        @param root: The xml root node.
        @type root: L{sax.Element}
        """
        Sequence.__init__(self, schema, root)


class ComplexContent(SchemaObject):
    """
    Represents an (xsd) schema <xs:complexContent/> node.
    """
    
    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{schema.Schema}
        @param root: The xml root node.
        @type root: L{sax.Element}
        """
        SchemaObject.__init__(self, schema, root)
        
    def valid_children(self):
        """
        Get a list of valid child tag names.
        @return: A list of child tag names.
        @rtype: [str,...]
        """
        return ('extension',)

    def __init2__(self):
        """ promote grand-children """
        self.promote_grandchildren()


class Enumeration(SchemaObject):
    """
    Represents an (xsd) schema <xs:enumeration/> node
    """

    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{schema.Schema}
        @param root: The xml root node.
        @type root: L{sax.Element}
        """
        SchemaObject.__init__(self, schema, root)
        
    def get_name(self):
        """ gets the <xs:enumeration value=""/> attribute value """
        return self.root.get('value')

    
class Element(Polymorphic):
    """
    Represents an (xsd) schema <xs:element/> node.
    """
    
    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{schema.Schema}
        @param root: The xml root node.
        @type root: L{sax.Element}
        """
        Polymorphic.__init__(self, schema, root)
        form = root.get('form')
        self.form_qualified = self.__form_qualified()
        self.nillable = self.__nillable()
        
    def valid_children(self):
        """
        Get a list of valid child tag names.
        @return: A list of child tag names.
        @rtype: [str,...]
        """
        return ('attribute', 'complexType', 'any',)
        
    def get_name(self):
        """ gets the <xs:element name=""/> attribute value """
        return self.root.get('name')
    
    def ref(self):
        """ gets the <xs:element type=""/> attribute value """
        return self.root.get('type')
    
    def unbounded(self):
        """ get whether the element has a maxOccurs > 1 or unbounded """
        max = self.root.get('maxOccurs', default='1')
        if max.isdigit():
            return (int(max) > 1)
        else:
            return ( max == 'unbounded' )
    
    def __form_qualified(self):
        """ get @form = (qualified) """
        form = self.root.get('form')
        if form is None:
            return self.form_qualified
        else:
            return ( form.lower() == 'qualified' )
        
    def __nillable(self):
        """ get @nillable = (1|true) """
        nillable = self.root.get('nillable')
        if nillable is None:
            return self.nillable
        else:
            return ( nillable.lower() in ('1', 'true') )

    def __lt__(self, other):
        """ <simpleType/> first """
        return ( not isinstance(other, Simple) )
    
    def __init2__(self):
        """
        if referenced (@ref) then promote the referenced
        node; then replace my children with those of the
        referenced node; otherwise, promote my grand-children
        @see: L{SchemaObject.__init2__()}
        """
        if self.referenced is not None:
            self.referenced.init(self.stage)
            self.root = self.referenced.root
            self.children = self.referenced.children
            self.attributes = self.referenced.attributes
        else:
            self.promote_grandchildren()
        self.derived = self.resolve().derived


class Extension(Complex):
    """
    Represents an (xsd) schema <xs:extension/> node.
    """
    
    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{schema.Schema}
        @param root: The xml root node.
        @type root: L{sax.Element}
        """
        Complex.__init__(self, schema, root)
        self.super = None
        
    def __init1__(self):
        """ lookup superclass  """
        Complex.__init1__(self)
        base = self.root.get('base')
        ref = qualified_reference(base, self.root, self.root.namespace())
        query = self.factory.create(query=ref)
        self.super = query.execute(self.schema)
        if self.super is None:
            raise TypeNotFound(base)
        
    def __init2__(self):
        """ add base type's children as my own """
        Complex.__init2__(self)
        index = 0
        self.super.init(self.stage)
        super = self.super.resolve()
        for c in super.children:
            self.children.insert(index, c)
            index += 1


class Import(SchemaObject):
    """
    Represents an (xsd) schema <xs:import/> node
    """
    
    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{schema.Schema}
        @param root: The xml root node.
        @type root: L{sax.Element}
        """
        SchemaObject.__init__(self, schema, root)
        self.imp = Factory.object('import')
        self.imp.schema = None
        self.imp.ns = (None, root.get('namespace'))
        self.imp.location = root.get('schemaLocation')
        self.imp.external = False
        
    def find(self, ref, classes=()):
        """
        Find a referenced type in the imported schema.
        @param ref: Either a I{qualified reference} or the
                name of a referenced type.
        @type ref: (I{str}|I{qualified reference})
        @param classes: A list of classes used to qualify the match.
        @type classes: [I{class},...] 
        @return: The referenced type.
        @rtype: L{SchemaObject}
        @see: L{qualified_reference()}
        """
        if self.imp.schema is None:
            return None
        if isqref(ref):
            n, ns = ref
        else:
            n, ns = qualified_reference(ref, self.root, self.namespace())
        for c in self.imp.schema.children:
            if c.match(n, ns, classes=classes):
                return c
        qref = (n, ns)
        for c in self.imp.schema.children:
            p = c.find(qref, classes)
            if p is not None:
                return p
        return None
    
    def xsfind(self, query):
        """
        Find a I{type} defined in one of the contained schemas.
        @param query: A query.
        @type query: L{query.Query}
        @return: The found schema type. 
        @rtype: L{qualified_reference()}
        """
        if self.imp.schema is None:
            return None
        marker = self.marker(query)
        if marker in query.history:
            return None
        query.history.append(marker)
        result = None
        log.debug('%s, finding (%s) in:\n%s',
            self.id, 
            query.name,
            repr(self.imp.schema))
        result = self.imp.schema.find(query)
        if result is not None:
            log.debug('%s, found (%s) as %s',
                self.id, 
                query.qname, 
                repr(result))
        return result
    
    def marker(self, query):
        """ get unique search marker """
        search = query.signature()
        sid = self.imp.schema.id
        return 'import-marker:%s/%s' % (sid, search)

    def namespace(self):
        """ get this properties namespace """
        result = self.schema.tns
        if self.imp.schema is not None:
            result = self.imp.schema.tns
        return result
    
    def skip(self):
        """ skip this namespace """
        return \
            Namespace.xs(self.imp.ns) or \
            self.imp.ns[1] == self.schema.tns or \
            self.imp.ns[1] in self.schema.impfilter
            
    def str(self, indent=0):
        """
        Get a string representation of this object.
        @param indent: The indent.
        @type indent: int
        @return: A string.
        @rtype: str
        """
        tab = '%*s'%(indent*3, '')
        result  = []
        result.append('%s<%s' % (tab, self.id))
        result.append(' {%d}' % self.stage)
        result.append(' location="%s"' % self.imp.location)
        if self.imp.schema is None:
            result.append(' schema="n/r"')
        else:
            result.append(' schema="%s"' % self.imp.schema.id)
        result.append('/>')
        return ''.join(result)
            
    def __init0__(self):
        log.debug('%s, import (%s) at: (%s)', self.id, self.imp.ns[1], self.imp.location)
        if self.skip():
            log.debug('%s, import (%s) skipped', self.id, self.imp.ns[1])
            return
        schema = self.schema.schemabyns(self.imp.ns)
        if schema is not None:
            self.imp.schema = schema
            self.__import_succeeded()
        else:
            self.imp.external = True
            self.__import()

    def __import(self):
        """ import the xsd content at the specified url """
        if self.imp.location is None:
            url = self.imp.ns[1]
        else:
            url = self.imp.location
        try:
            if '://' not in url:
                url = urljoin(self.schema.baseurl, url)
            p = Parser()
            root = p.parse(url=url).root()
            self.imp.schema = Schema(root, url, impfilter=self.schema.impfilter)
            self.__import_succeeded()
        except Exception:
            self.__import_failed(url)
            
    def __import_failed(self, url):
        """ import failed """
        self.schema.impfilter.add(self.imp.ns[1])
        msg = \
            'imported schema (%s) at (%s), not-found' \
            (self.imp.ns[1], url)
        log.debug('%s, %s', self.id, msg, exc_info=True)
        if self.imp.location is not None:
            raise Exception(msg)
            
    def __import_succeeded(self):
        """ process the imported schema """
        self.imp.schema.init(0)
        if self.imp.ns[0] is not None:
            ns = self.imp.ns
            self.schema.root.addPrefix(ns[0], ns[1])
            
    def __repr__(self):
        result  = []
        result.append('<%s' % self.id)
        result.append(' {%s}' % self.stage)
        if self.imp.schema is None:
            result.append(' schema="n/r"')
        else:
            result.append(' schema="%s"' % self.imp.schema.id)
            result.append(' tns="%s"' % self.imp.schema.tns[1])
        result.append('/>')
        return ''.join(result)
            
    def __lt__(self, other):
        """ everything else first """
        return False
   
class Attribute(Polymorphic):
    """
    Represents an (xsd) <attribute/> node
    """

    def __init__(self, schema, root):
        """
        @param schema: The containing schema.
        @type schema: L{schema.Schema}
        @param root: The xml root node.
        @type root: L{sax.Element}
        """
        Polymorphic.__init__(self, schema, root)
        
    def isattr(self):
        """ get whether the object is an attribute """
        return True
        
    def get_name(self):
        """ gets the <xs:attribute name=""/> attribute value """
        return self.root.get('name')
    
    def ref(self):
        """ gets the <xs:attribute type=""/> attribute value """
        return self.root.get('type')

    def get_default(self):
        """ gets the <xs:attribute default=""/> attribute value """
        return self.root.get('default', default='')
    
    def required(self):
        """ gets the <xs:attribute use="required"/> attribute value """
        use = self.root.get('use', default='')
        return ( use.lower() == 'required' )

    def __init2__(self):
        """
        Replace the root with the referenced root 
        while preserving @use.
        @see: L{SchemaObject.__init2__()}
        """
        if self.referenced is not None:
            myuse = self.root.get('use')
            self.root = self.referenced.root
            if myuse is not None:
                self.root.set('use', myuse)

