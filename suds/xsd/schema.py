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

"""
The I{schema} module provides a intelligent representation of
an XSD schema.  The I{raw} model is the XML tree and the I{model}
is the denormalized, objectified and intelligent view of the schema.
Most of the I{value-add} provided by the model is centered around
tranparent referenced type resolution and targeted denormalization.
"""

from logging import getLogger
import suds.metrics
from suds import *
from suds.xsd import *
from suds.xsd.sxbuiltin import *
from suds.xsd.sxbasic import Factory as BasicFactory
from suds.xsd.sxbuiltin import Factory as BuiltinFactory
from suds.xsd.sxbase import SchemaObject
from suds.sax import splitPrefix, Namespace

log = getLogger(__name__)


class SchemaCollection:
    """
    A collection of schema objects.  This class is needed because WSDLs 
    may contain more then one <schema/> node.
    @ivar wsdl: A wsdl object.
    @type wsdl: L{suds.wsdl.Definitions}
    @ivar children: A list contained schemas.
    @type children: [L{Schema},...]
    @ivar namespaces: A dictionary of contained schemas by namespace.
    @type namespaces: {str:L{Schema}}
    """
    
    def __init__(self, wsdl):
        """
        @param wsdl: A wsdl object.
        @type wsdl: L{suds.wsdl.Definitions}
        """
        self.wsdl = wsdl
        self.children = []
        self.namespaces = {}
        
    def add(self, schema):
        """
        Add a schema node to the collection.
        @param schema: A <schema/> entry.
        @type schema: (L{suds.wsdl.Definitions},L{sax.element.Element})
        """
        root, wsdl = schema
        child = Schema(root, wsdl.url, self)
        self.children.append(child)
        self.namespaces[child.tns[1]] = child
        
    def load(self):
        """
        Load the schema objects for the root nodes.
            - de-references schemas
            - flatten schemas
            - merge schemas
        @return: The merged schema.
        @rtype: L{Schema}
        """
        for child in self.children:
            child.build()
        for child in self.children:
            child.open_imports()
        log.debug('loaded:\n%s', self)
        merged = self.merge()
        log.debug('merged\n%s', merged)
        merged.dereference()
        merged.flatten()
        log.debug('flattened-merged\n%s', merged)
        return merged
        
    def locate(self, ns):
        """
        Find a schema by namespace.  Only the URI portion of
        the namespace is compared to each schema's I{targetNamespace}
        @param ns: A namespace.
        @type ns: (prefix,URI)
        @return: The schema matching the namesapce, else None.
        @rtype: L{Schema}
        """
        return self.namespaces.get(ns[1])
    
    def merge(self):
        """
        Merge the contained schemas into one.
        @return: The merged schema.
        @rtype: L{Schema}
        """
        if len(self):
            schema = self.children[0]
            for s in self.children[1:]:
                schema.merge(s)
            return schema
        else:
            return None
    
    def __len__(self):
        return len(self.children)
    
    def __str__(self):
        return unicode(self).encode('utf-8')
    
    def __unicode__(self):
        result = ['\nschema collection']
        for s in self.children:
            result.append(s.str(1))
        return '\n'.join(result)


class Schema:
    """
    The schema is an objectification of a <schema/> (xsd) definition.
    It provides inspection, lookup and type resolution.
    @ivar root: The root node.
    @type root: L{sax.element.Element}
    @ivar baseurl: The I{base} URL for this schema.
    @type baseurl: str
    @ivar container: A schema collection containing this schema.
    @type container: L{SchemaCollection}
    @ivar types: A schema types cache.
    @type types: {name:L{SchemaObject}}
    @ivar groups: A schema groups cache.
    @type groups: {name:L{SchemaObject}}
    @ivar children: A list of children.
    @type children: [L{SchemaObject},...]
    @ivar imports: A list of import objects.
    @type imports: [L{SchemaObject},...]
    @ivar merged: A flag indicating this schema has been merged.
    @type merged: bool
    @ivar form_qualified: The flag indicating:
        (@elementFormDefault).
    @type form_qualified: bool
    """
    
    def __init__(self, root, baseurl, container=None):
        """
        @param root: The xml root.
        @type root: L{sax.element.Element}
        @param baseurl: The base url used for importing.
        @type baseurl: basestring
        @param container: An optional container.
        @type container: L{SchemaCollection}
        """
        self.root = root
        self.id = objid(self)
        self.tns = self.mktns()
        self.baseurl = baseurl
        self.container = container
        self.children = []
        self.types = {}
        self.imports = []
        self.elements = {}
        self.attributes = {}
        self.groups = {}
        self.agrps = {}
        self.merged = False
        form = self.root.get('elementFormDefault')
        if form is None:
            self.form_qualified = False
        else:
            self.form_qualified = ( form == 'qualified' )
        if container is None:
            self.build()
            self.open_imports()
            self.dereference()
            self.flatten()
                
    def mktns(self):
        """
        Make the schema's target namespace.
        @return: The namespace representation of the schema's
            targetNamespace value.
        @rtype: (prefix, uri)
        """
        tns = [None, self.root.get('targetNamespace')]
        if tns[1] is not None:
            tns[0] = self.root.findPrefix(tns[1])
        return tuple(tns)
                
    def build(self):
        """
        Build the schema (object graph) using the root node
        using the factory.
            - Build the graph.
            - Collate the children.
        """
        attributes, self.children = BasicFactory.build(self.root, self)
        collated = BasicFactory.collate(attributes)
        self.attributes = collated[2]
        collated = BasicFactory.collate(self.children)
        self.children = collated[0]
        self.imports = collated[1]
        self.elements = collated[3]
        self.types = collated[4]
        self.groups = collated[5]
        self.agrps = collated[6]
        
    def merge(self, schema):
        """
        Merge the contents from the schema.  Only objects not already contained
        in this schema's collections are merged.  This is to provide for bidirectional
        import which produce cyclic includes.
        @returns: self
        @rtype: L{Schema} 
        """
        for item in schema.attributes.items():
            if item[0] in self.attributes:
                continue
            self.attributes[item[0]] = item[1]
        for item in schema.elements.items():
            if item[0] in self.elements:
                continue
            self.elements[item[0]] = item[1]
            self.children.append(item[1])
        for item in schema.types.items():
            if item[0] in self.types:
                continue
            self.types[item[0]] = item[1]
            self.children.append(item[1])
        for item in schema.groups.items():
            if item[0] in self.groups:
                continue
            self.groups[item[0]] = item[1]
            self.children.append(item[1])
        for item in schema.agrps.items():
            if item[0] in self.agrps:
                continue
            self.agrps[item[0]] = item[1]
            self.children.append(item[1])
        schema.merged = True
        return self
        
    def open_imports(self):
        """
        Instruct all contained L{sxbasic.Import} children to import
        the schema's which they reference.  The contents of the
        imported schema are I{merged} in.
        """
        for imp in self.imports:
            imported = imp.open()
            if imported is None:
                continue
            imported.open_imports()
            self.merge(imported)
        
    def locate(self, ns):
        """
        Find a schema by namespace.  Only the URI portion of
        the namespace is compared to each schema's I{targetNamespace}.
        The request is passed to the container.
        @param ns: A namespace.
        @type ns: (prefix,URI)
        @return: The schema matching the namesapce, else None.
        @rtype: L{Schema}
        """
        if self.container is not None:
            return self.container.locate(ns)
        else:
            return None
            
    def dereference(self):
        """
        Instruct all children to perform dereferencing.
        """
        for c in self.children:
            c.dereference()
        
    def flatten(self):
        """
        Instruct all children to I{flatten}.
        """
        for c in self.children:
            c.flatten()

    def custom(self, ref, context=None):
        """
        Get whether the specified reference is B{not} an (xs) builtin.
        @param ref: A str or qref.
        @type ref: (str|qref)
        @return: True if B{not} a builtin, else False.
        @rtype: bool 
        """
        if ref is None:
            return True
        else:
            return ( not self.builtin(ref, context) )
    
    def builtin(self, ref, context=None):
        """
        Get whether the specified reference is an (xs) builtin.
        @param ref: A str or qref.
        @type ref: (str|qref)
        @return: True if builtin, else False.
        @rtype: bool 
        """
        w3 = 'http://www.w3.org'
        try:
            if isqref(ref):
                ns = ref[1]
                return ns.startswith(w3)
            if context is None:
                context = self.root    
            prefix = splitPrefix(ref)[0]
            prefixes = context.findPrefixes(w3, 'startswith')
            return (prefix in prefixes)
        except:
            return False
        
    def instance(self, root, url):
        """
        Create and return an new schema object using the
        specified I{root} and I{url}.
        @param root: A schema root node.
        @type root: L{sax.element.Element}
        @param url: A base URL.
        @type url: str
        @return: The newly created schema object.
        @rtype: L{Schema}
        @note: This is only used by Import children.
        """
        return Schema(root, url)

    def str(self, indent=0):
        tab = '%*s'%(indent*3, '')
        result = []
        result.append('%s%s' % (tab, self.id))
        result.append('%s(raw)' % tab)
        result.append(self.root.str(indent+1))
        result.append('%s(model)' % tab)
        for c in self.children:
            result.append(c.str(indent+1))
        result.append('')
        return '\n'.join(result)
        
    def __repr__(self):
        myrep = '<%s tns="%s"/>' % (self.id, self.tns[1])
        return myrep.encode('utf-8')
    
    def __str__(self):
        return unicode(self).encode('utf-8')
    
    def __unicode__(self):
        return self.str()



