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
The I{schema} module provides a intelligent representation of
an XSD schema.  The I{raw} model is the XML tree and the I{model}
is the denormalized, objectified and intelligent view of the schema.
Most of the I{value-add} provided by the model is centered around
tranparent referenced type resolution and targeted denormalization.
"""

from suds import *
from suds.xsd import *
from suds.xsd.factory import Factory
from suds.xsd.sxbase import SchemaObject
from suds.xsd.sxbasic import Import
from suds.sax import splitPrefix, Namespace

log = logger(__name__)


class SchemaCollection:
    """
    A collection of schema objects.  This class is needed because WSDLs may contain
    more then one <schema/> node.
    @ivar root: A root node used for ns prefix resolution (set to WSDL's root).
    @type root: L{sax.Element}
    @ivar tns: The target namespace (set to WSDL's target namesapce)
    @type tns: (prefix,URI)
    @ivar baseurl: The I{base} URL for this schema.
    @type baseurl: str
    @ivar children: A list contained schemas.
    @type children: [L{Schema},...]
    @ivar impfilter: A list of namespaces B{not} to import.
    @type impfilter: set
    """
    
    def __init__(self, wsdl, impfilter=None):
        """
        @param wsdl: A WSDL object.
        @type wsdl: L{wsdl.WSDL}
        @param impfilter: A list of namespaces B{not} to import.
        @type impfilter: set
        """
        self.root = wsdl.root
        self.id = objid(self)
        self.tns = wsdl.tns
        self.baseurl = wsdl.url
        self.children = []
        self.impfilter = impfilter
        self.namespaces = {}
        
    def add(self, node):
        """
        Add a schema node to the collection.
        @param node: A <schema/> root node.
        @type node: L{sax.Element}
        """
        child = Schema(node, self.baseurl, self, self.impfilter)
        self.children.append(child)
        self.namespaces[child.tns[1]] = child
        
    def load(self):
        """
        Load the schema objects for the root nodes.
        """
        for stage in Schema.init_stages:
            for child in self.children:
                child.init(stage)
        if log.isEnabledFor(logging.DEBUG):
            log.debug('schema (%s):\n%s', self.baseurl, str(self))
        
    def schemabyns(self, ns):
        """
        Find a schema by namespace.  Only the URI portion of
        the namespace is compared to each schema's I{targetNamespace}
        @param ns: A namespace.
        @type ns: (prefix,URI)
        @return: The schema matching the namesapce, else None.
        @rtype: L{Schema}
        """
        return self.namespaces.get(ns[1], None)

    def find(self, query):
        """ @see: L{Schema.find()} """
        result = None
        if query.inprogress():
            for s in self.children:
                log.debug('%s, finding (%s) in %s', self.id, query.name, repr(s))
                result = s.find(query)
                if result is not None:
                    break
        else:
            result = query.execute(self)
        return result
        
    def namedtypes(self):
        """
        Get a list of top level named types.
        @return: A list of types.
        @rtype: [L{SchemaObject},...]
        """
        result = {}
        for s in self.flattened_children():
            for c in s.children:
                name = c.get_name()
                if name is None:
                    continue
                resolved = c.resolve()
                if resolved.builtin():
                    result[name] = c
                else:
                    result[name] = resolved           
        return result.values()
    
    def flattened_children(self):
        result = []
        for s in self.children:
            if s not in result:
                result.append(s)
            for gc in s.grandchildren():
                if gc not in result:
                    result.append(gc)
        return result
    
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
    @type root: L{sax.Element}
    @ivar tns: The target namespace.
    @type tns: (prefix,URI)
    @ivar efdq: The @B{e}lementB{F}ormB{D}efault="B{q}ualified" flag. 
    @type efdq: boolean
    @ivar baseurl: The I{base} URL for this schema.
    @type baseurl: str
    @ivar container: A schema collection containing this schema.
    @type container: L{SchemaCollection}
    @ivar types: A schema types cache.
    @type types: {name:L{SchemaObject}}
    @ivar children: A list of child properties.
    @type children: [L{SchemaObject},...]
    @ivar factory: A property factory.
    @type factory: L{Factory}
    @ivar impfilter: A list of namespaces B{not} to import.
    @type impfilter: set
    """
    
    init_stages = range(0,4)
    
    def __init__(self, root, baseurl, container=None, impfilter=None):
        """
        @param root: The xml root.
        @type root: L{sax.Element}
        @param baseurl: The base url used for importing.
        @type baseurl: basestring
        @param container: An optional container.
        @type container: L{SchemaCollection}
        @param impfilter: A list of namespaces B{not} to import.
        @type impfilter: set
        """
        self.root = root
        self.id = objid(self)
        self.tns = self.__tns()
        self.stage = -1
        self.baseurl = baseurl
        self.container = container
        self.types = {}
        self.children = []
        self.factory = Factory(self)
        self.impfilter = impfilter
        self.form_qualified = self.__form_qualified()
        if container is None:
            self.init(3)
                    
    def __form_qualified(self):
        """ get @elementFormDefault = (qualified) """
        form = self.root.get('elementFormDefault')
        if form is None:
            return False
        else:
            return ( form.lower() == 'qualified' )
                
    def __tns(self):
        """ get the target namespace """
        tns = [None, self.root.get('targetNamespace')]
        if tns[1] is not None:
            tns[0] = self.root.findPrefix(tns[1])
        return tuple(tns)
            
    def init(self, stage):
        """
        Perform I{stage} initialization.
        @param stage: The init stage to complete.
        """
        for n in range(0, (stage+1)):
            if self.stage < n:
                m = '__init%s__' % n
                self.stage = n
                log.debug('%s, init (%d)', self.id, n)
                if not hasattr(self, m): continue
                method = getattr(self, m)
                method()
                for s in self.grandchildren():
                    s.init(n)
                
    def __init0__(self):
        """ create children """
        self.children = self.factory.build(self.root)[1]

    def __init1__(self):
        """ run children through depsolving and child promotion """
        for stage in SchemaObject.init_stages:
            for c in self.children:
                c.init(stage)
        self.children.sort()

    def __init2__(self):
        pass
        
    def schemabyns(self, ns):
        """ find schema by namespace """
        if self.container is not None:
            return self.container.schemabyns(ns)
        else:
            return None
        
    def grandchildren(self):
        """ get I{grandchild} schemas that have been imported """
        for c in self.children:
            if isinstance(c, Import) and \
                c.imp.schema is not None:
                    yield c.imp.schema
        
    def find(self, query):
        """
        Find a I{type} defined in one of the contained schemas.
        @param query: A query.
        @type query: L{query.Query}
        @return: The found schema type. 
        @rtype: L{SchemaObject()}
        """
        if query.inprogress():
            result = self.__process_query(query)
        else:
            result = query.execute(self)
        return result

    def custom(self, ref, context=None):
        """ get whether specified type reference is custom """
        if ref is None:
            return True
        else:
            return (not self.builtin(ref, context))
    
    def builtin(self, ref, context=None):
        """ get whether the specified type reference is an (xsd) builtin """
        w3 = 'http://www.w3.org'
        try:
            if isqref(ref):
                ns = ref[1]
                return ns[1].startswith(w3)
            if context is None:
                context = self.root    
            prefix = splitPrefix(ref)[0]
            prefixes = context.findPrefixes(w3, 'startswith')
            return (prefix in prefixes)
        except:
            return False

    def str(self, indent=0):
        tab = '%*s'%(indent*3, '')
        result = []
        result.append('%s%s' % (tab, self.id))
        result.append('%s(raw)' % tab)
        result.append(self.root.str(indent+1))
        result.append('%s(model {%d})' % (tab, self.stage))
        for c in self.children:
            result.append(c.str(indent+1))
        result.append('')
        return '\n'.join(result)

    def __process_query(self, query):
        """ process the query """
        key = query.signature()
        cached = self.types.get(key, None)
        if cached is not None and \
            not query.filter(cached):
                return cached
        if self.builtin(query.qname):
            b = self.factory.create(builtin=query.name)
            log.debug('%s, found builtin (%s)', self.id, query.name)
            return b
        result = self.__find(query)
        if result is not None:
            if query.resolved:
                result = result.resolve()
            self.types[key] = result
            log.debug('%s, found (%s)\n%s\n%s', self.id, query.name, query, tostr(result))
        else:
            log.debug('%s, (%s) not-found:\n%s', self.id, query.name, query)
        return result
    
    def __find(self, query):
        """ find a schema object by name. """
        result = None
        query.qualify(self.root, self.tns)
        ref, ns = query.qname
        log.debug('%s, finding (%s)\n%s', self.id, query.name, query)
        for child in self.children:
            if isinstance(child, Import):
                log.debug(
                    '%s, searching (import): %s\nfor:\n%s', 
                    self.id, repr(child), query)
                result = child.xsfind(query)
                if result is None:
                    continue
                else:
                    break
            name = child.get_name()
            if name is None:
                log.debug(
                    '%s, searching (child): %s\nfor:\n%s',
                    self.id, repr(child), query)
                result = child.get_child(ref, ns)
                if query.filter(result):
                    result = None
                    continue
                if result is not None:
                    break
            else:
                log.debug(
                    '%s, matching: %s\nfor:\n%s',
                    self.id, repr(child), query)
                if child.match(ref, ns):
                    result = child
                    if query.filter(result):
                        result = None
                    else:
                        break
        return result
        
    def __repr__(self):
        myrep = \
            '<%s {%d} tns="%s"/>' % (self.id, self.stage, self.tns[1])
        return myrep.encode('utf-8')
    
    def __str__(self):
        return unicode(self).encode('utf-8')
    
    def __unicode__(self):
        return self.str()



