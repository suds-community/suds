OVERVIEW

The "Suds" web services client is a lightweight soap-based client for python
the is licensed under LGPL.

For details, visit:

  * Project site: https://fedorahosted.org/suds/
  * Documentation: https://fedorahosted.org/suds/wiki/Documentation
  * Epydocs: http://jortel.fedorapeople.org/suds/doc/
   

RELEASE-NOTES:
=================================================

version 0.3.6 (04-31-09):
  * Change hard coded /tmp/suds to tempfile.gettempdir() and create suds/ on demand.
  * Fix return type for Any.get_attribute().
  * Update http caching to ignore file:// urls.
  * Better logging of messages when only the reply is injected.
  * Fix XInteger and XFloat types to translate returned arrays properly.
  * Fix xs:import schema with same namespace.
  * Update parser to not load external references and add Import.bind() for XMLSchema.xsd location.
  * Add schema doctor - used to patch XSDs at runtime. (See Option.doctor)
  * Fix deprecation warnings in python 2.6.
  * Add behavior for @default defined on <element/>.
  * Change @xsi:type value to always be qualified for doc/literal. (reverts 0.3.5 change).
  * Add Option.xstq option to control when @xsi:type is qualified.
  * Fixed Tickets: #64, #129, #205, #206, #217, #221, #222, #224, #225, #228, #229, #230 

version 0.3.5 (04-16-09):
  * Adds http caching. Default is (1) day. Does not apply to method invocation. See: documentation for details.
  * Removed checking fedora version check in spec since no longer building < fc9.
  * Updated makefile to roll tarball with tar.sh.
  * Moved bare/wrapped determination to wsdl for document/literal.
  * Refactored Transport into a package (provides better logging of http headers).
  * Fixed Tickets: #207, #209, #210, #212, #214, #215 

version 0.3.4 (02-24-09):
  * Static (automatic) Import.bind('http://schemas.xmlsoap.org/soap/encoding/'),
      users no longer need to do this.
  * Basic ws-security with {{{UsernameToken}}} and clear-text password only.
  * Add support for ''sparse'' soap headers via passing dictionary
  * Add support for arbitrary user defined soap headers
  * Fixes service operations with multiple soap header entries.
  * Schema loading and dereferencing algorithm enhancements.
  * Nested soap multirefs fixed.
  * Better (true) support for elementFormDefault="unqualified" provides more 
      accurate namespaing.
  * WSDL part types no longer default to WSDL targetNamespace.
  * Fixed Tickets: #4, #6, #21, #32, #62, #66, #71, #72, #114, #155, #201.

version 0.3.3 (11-31-08):
  * No longer installs (tests) package.
  * Implements API-3 proposal ( https://fedorahosted.org/suds/wiki/Api3Proposal )
     - Pluggable transport
    - Keyword method arguments
    - Baisc http authentication in default transport
  * Add namespace prefix normalization in soap message.
  * Better soap message pruning of empty nodes.
  * Fixed Tickets: #51 - #60

  
version 0.3.2 (11-7-08):
  * SOAP {{{MultiRef}}} support ''(1st pass added r300)''
  * Add support for new schema tags:
     * <xs:include/>
     * <xs:simpleContent/>
     * <xs:group/>
     * <xs:attributeGroup/>
  * Added support for new xs <--> python type conversions:
     * xs:int
     * xs:long
     * xs:float
     * xs:double
  * Revise marshaller and binding to further sharpen the namespacing of nodes produced.
  * Infinite recursion fixed in ''xsd'' package dereference() during schema loading.
  * Add support for <wsdl:import/> of schema files into the wsdl root <definitions/>.
  * Fix double encoding of (&)
  * Add Client API:
     * setheaders() - same as keyword but works for all invocations.
     * addprefix() - mapping of namespace prefixes.
    * setlocation() - Override the location in the wsdl; same as keyword except for all calls.
    * setproxy() - same as proxy keyword but for all invocations.
  * Add proper namespace prefix for soap headers.
  * Fixed Tickets: #5, #12, #34, #37, #40, #44, #45, #46, #48, #49, #50, #51

  
version 0.3.1 (10-1-08):

 * Quick follow up to the 0.3 release that made working multi-port service definitions
    harder then necessary.  After consideration (and a good night sleep),
    it seemed obvious that a few changes would make this much easier: 1) filter out 
    the non-soap bindings - they were causing the real trouble;  2) since most servers
    are happy with any of the soap bindings (soap 1.1 and 1.2), ambigious references to methods 
    when invoking then without the port qualification will work just fine in almost every
    case.  So, why not just allow suds to select the port.  Let's not make the user do it 
    when it's not necessary.  In most cases, uses on 0.2.9 and earlier will not have to
    update there code when moving to 0.3.1 as they might have in 0.3.

    
version 0.3 (9-30-08):

  * Extends the support for multi-port services introduced in 0.2.9.  This addition,
     provides for multiple services to define the *same* method and suds will
     handle it properly.  See section 'SERVICES WITH MULTIPLE PORTS:'
     
  * Add support for multi-document document/literal soap binding style.
     See section 'MULTI-DOCUMENT Docuemnt/Literal:'
  
  * Add support for (xs:group, xs:attributeGroup) tags.
  
  * Add Client.last_sent() and Client.last_received().
    
version 0.2.9 (9-09-08):
   
   * Support for multiple ports within a service.
   * Attribute references <xs:attribute ref=""/>
   * Make XML special character encoder in sax package - pluggable 


version 0.2.8 (8-28-08):

   * Update document/literal binding to always send the document root referenced by the <part/>.
      After yet another review of the space and user input, seems like the referenced 
      element is ALWAYS the document root.

   * Add support for 'binding' schemaLocations to namespace-uri.  
     This is for imports that don's specify a schemaLocation and still expect the schema 
     to be downloaded.  Eg: Axis references 'http://schemas.xmlsoap.org/soap/encoding/' 
     without a schemaLocation.  So, by doing this:
        >
        > from suds.xsd.sxbasic import Import.
        > Import.bind('http://schemas.xmlsoap.org/soap/encoding/')
        >
     The schema is bound to a schemaLocation and it is downloaded.

   * Basic unmarshaller doesn't need a /schema/. 
      Should have been removed during refactoring but was missed.

   * Update client to pass kwargs to send() and add /location/ kwarg for overriding the
      service location in the wsdl.

   * Update marshaller to NOT emit XML for object attributes that represent elements and/or attributes that
      are *both* optional and value=None.
         * Update factory (builder) to include all attributes.
         * Add optional() method to SchemaObject.

   * Update wsdl to override namespace in operation if specified.
   
   * Fix schema loading issue - build all schemas before processing imports.
   
   * Update packaging in preparation of submission to fedora

      
version 0.2.7 (8-11-08):

   * Add detection/support for document/literal - wrapped and unwrapped.
   * Update document/literal {wrapped} to set document root (under <body/>) to be the
      wrapper element (w/ proper namespace).
   * Add support for <sequence/>, <all/> and <choice/> having maxOccurs and have the
      which causes the unmarshaller to set values for elements contained in an unbounded
      collection as a list.
   * Update client.factory (builder) to omit children of <choice/> since the 'user' really needs
      to decide which children to include.
   * Update flattening algorithm to prevent re-flattening of types from imported schemas.
   * Adjustments to flattening/merging algorithms.
   

version 0.2.6 (8-5-08):

   * Fix ENUMs broken during xsd package overhaul.
   * Fix type as defined in ticket #24.
   * Fix duplicate param names in method signatures as reported in ticket #30.
   * Suds licensed as LGPL.
   * Remove logging setup in suds.__init__() as suggested by patch in ticket #31.  Users will
      now need to configure the logger.
   * Add support for Client.Factory.create() alt: syntax for fully qualifying the type to be
      built as: {namespace}name.  Eg: client.factory.create('{http://blabla.com/ns}Person')


version 0.2.5 (8-01-08):

   * Overhauled the (XSD) package.  This new (merging) approach is simpler and should be
      more reliable and maintainable.  Also, should provide better performance since the merged
      schema performes lookups via dictionary lookup.
      
      This overhaul should fix current TypeNotFound and <xs:extension/> problems, I hope :-).
      
   * Fixed dateTime printing bug.

   * Added infinite recursion prevention in builder.Builder for xsd types that contain themselves.


version 0.2.4 (7-28-08):

   * Added support for WSDL imports: <wsdl:import/>
   * Added support for xsd<->python type conversions (thanks: Nathan Van Gheem) for:
      * xs:date
      * xs:time
      * xs:dateTime
   * Fixed:
      * Bug: Schema <import/> with schemaLocation specified.
      * Bug: Namespaces specified in service description not valid until client/proxy is printed.


version 0.2.3 (7-23-08):

   * Optimizations.


version 0.2.2 (7-8-08):

   * Update exceptions to be more /standard/ python by using Exception.__init__() to set Exception.message as
     suggested by Ticket #14; update bindings to raise WebFault passing (p)
   
   * Add capability in bindings to handle multiple root nodes in the returned values;
     returned as a composite object unlike when lists are returned
   
   * Fix soapAction to be enclosed by quotes
   
   * Add support for <xs:all/>
   
   * Fix unbounded() method in SchemaObject
   
   * Refactored schema into new (xsd) package.  Files just getting too big. Added execute() to
     Query and retrofitted suds to execute() query instead of using Schema.find() directly.  
     Also, move hokey start() methods from schema, as well as, query incrementation.
   
   * Add inject keyword used to inject outbound soap messages and/or inbound reply messages.
      Refactor SoapClient and 
        1) rename send() to invoke()
        2) split message sending from invoke() and place in send();
      Add TestClient which allows for invocation kwargs to have inject={'msg=, and reply='} for message
      and reply injection
     
   * Add Namespace class to sax for better management of namespace behavior;
     retrofix suds to import and use Namespace
   
   * Change the default namespace used to resolve referenced types (having attribues @base="",@type="")
      so that when no prefix is specified: uses XML (node) namesapce instead of the targetNamespace.
   
   * Apply fix as defined by davidglick@onenw.org in ticket #13
   
   * Update service definition to print to display service methods as ' my_method(xs:int arg0, Person arg1) '
      instead of ' my_method(arg0{xs:int}, arg1{Person}) ' which is more like traditional method signatures
   
   * Add xsd/python type converstion to unmarshaller (XBoolean only); refactor unmarshaller to use Content
      class which makes apis cleaner, adds symmetry between marshaller(s) and unmarshaller(s),
      provides good mechanism for schema-property based type conversions
   
   * Refactor marshaller with Appenders; add nobuiltin flag to resolve() to support fix for
      returned_type() and returnes_collection() in bindings.
   
   * Add support for (202,204) http codes
   
   * Add XBoolean and mappings; add findattr() to TreeResolver in preparation for type conversions
   
   * Updated schema and schema property loading (deep recusion stopped); Changed Imported schemas so then no
      longer copy imported schemas, rather the import proxies find requests; Add ServiceDefinition class which
      provides better service inspection; also provides namespace mapping and show types; schema property api simplified;
      support for xs:any and xs:anyType added; Some schema lookup problems fixed; Binding classes refactored slightly;
      A lot of debug logging added (might have to comment some out for performance - some of the args are expensive).
   
   * Add sudsobject.Property; a property is a special Object that contains a (value) attributeand is returned by the
      Builder (factory) for schema-types without children such as: <element/> and <simpleType/>; Builder, Marshallers
      and Resolvers updated to handle Properties; Resolver, Schema also updated to handle attribute lookups (this was missing)
   
   * Add groundwork for user defined soap headers.
   
   * Fix elementFormDefault per ticket #7
   
   * Remove unused kwargs from bindings; cache bindings in wsdl; retrofit legacy ServiceProxy to delegate to {new} Client API;
      remove keyword nil_supported in favor of natural handling by 'nillable' attribute on <element/> within schemas
   
   * Add support for <element/> attribute flags (nillable and form)
   
   * Add the Proxy (2nd generation API) class
   
   * Add accessor/conversion functions to that user don't need to access __x__ attributes.
      Also add todict() and get_items() for easy conversion to dictionary and iteration
   
   * Search top-level elements for @ref before looking deeper
   
   * Add derived() to SchemaObject.  This is needed to ensure that all derived types (wsdl classes)
      are qualified by xsi:type without specifying the xsi:type for all custom types as did in earlier
      releases of suds.  Update the literal marshaller to only add the xsi:type when the type needs
      to be specified.
   
   * Change ns promotion in sax to prevent ns promoted to parent when parent has the prefix.
   
   * Changed binding returned_type() to return the (unresolved) Element 
   
   * In order to support the new features and fix reported bugs,
      I'm in the process of refactoring and hopefully evolving the components
      in Suds that provide the input/output translations:
   
     * Builder ( translates: XSD objects => python objects )
     * Marshaller ( translates: python objects => XML/SOAP )
     * Unmarshaller ( translates: soap/xml => python objects )
   
     This evolution will provide better symmetry between these components as follows:
   
     The Builder and Unmarshaller will produce python
     (subclass of sudsobject.Object) objects with:
   
     *  __metadata__.__type__ = XSD type (SchemaObject)
     * subclass name ( __class__.__name__ ) = schema-type name.
   
     and
   
     The Marshaller(s), while consuming python objects produced by the Builder or
     Unmarshaller, will leverage this standard information to
     produce the appropriate output ( XML/SOAP ).
   
     The 0.2.1 code behaves *mostly* like this but ... not quite.
     Also, the implementations have some redundancy.
   
     While doing this, it made sense to factor out the common schema-type "lookup"
     functionality used by the Builder, Marshallers and Unmarshaller classes into a
     hierarchy of "Resolver" classes.  This reduces the complexity and redundancy
     of the Builder, Marshallers and Unmarshaller classes and allows for better
     modularity.  Once this refactoring was complete, the difference between the
     literal/encoded Marshallers became very small.  Given that the amount of code
     in the bindings.literal and bindings.encoded packages was small (and getting smaller)
     and in the interest of keeping the Suds code base compact, I moved all of the
     marshalling classes to the bindings.marshaller module.
     All of the bindings.XX sub-packages will be removed.
   
     The net effect:
   
     All of the Suds major components:
   
     * client (old: service proxy)
     * wsdl
       * schema (xsd package)
       * resolvers
     * output (marshalling)
     * builder
     * input (unmarshalling)
   
     Now have better:
   
      * modularity
      * symmetry with regard to Object metadata.
      * code re-use (< 1% code duplication --- i hope)
      * looser coupling
   
     ... and better provide for the following features/bug-fixes:
   
     * (fix) Proper level of XML element qualification based on
        <schema elementFormDefault=""/> attribute.  This will ensure that when
        elementFormDefault="qualified", Suds will include the proper namespace on
        root elements for both literal and encoded bindings.  In order for this to
        work properly, the literal marshaller (like the encoded marshaller) needed
        to be schema-type aware.  Had i added the same schema-type lookup as the
        encoded marshaller instead of the refactoring described above, the two
        classes would have been almost a complete duplicate of each other :-(
   
   * The builder and unmarshaller used the schema.Schema.find()
     to resolve schema-types.  They constructed a path as "person.name.first"
     to resolve types in proper context.  Since the Schema.find() was stateless,
     it resolved the intermediate path elements on every call.  The new resolver
     classes are statefull and resolve child types *much* more efficiently.
   
   * Prevent name collisions in sudsobject.Object like the items() method.  I've moved all
     methods (including class methods) to a Factory class that is included in the Object class
     as a class attr ( __factory__ ).  Now that *all* attributes have python built-in naming,
     we should not have any more name collisions.  This of course assumes that no wsdl/schema
     entity names will have a name with the python built-in naming convention
     but I have to draw the line somewhere :-)
     

version 0.2.1 (5-8-08):

   * Update the schema.py SchemaProperty loading sequence so that the schema is loaded in 3 steps: 
         1) build the raw tree. 
         2) resolve dependancies such as @ref and @base.  
         3) promote grandchildren as needed to flatten (denormalize) the tree.
         
       The wsdl was also changed to only load the schema once and store it.  The schema collection was 
       changed to load schemas in 2 steps:
         1) create all raw schema objects.
         2) load schemas.  
       
       This ensure that local <import/>'d schemas can be found when referenced out of order.  
       The sax.py Element interface changed: attribute() replaced by get() and set().  
       Also, __getitem__ and __setitem__ can be used to access attribute values.  
       Epydocs updated for sax.py.  And ... last <element ref=/> now supported properly.

   * fix logging by: NOT setting to info in suds.__init__.logger(); set handler on root logger 
      only; moved logger (log) from classes to modules and use __name__ for logger name.
      NOTE: This means that to enable soap message logging:
           >
           > logger('suds.serviceproxy').setLevel(logging.DEBUG)
           > 
         -- instead of --
           >
           > logger('serviceproxy').setLevel(logging.DEBUG)
           >
      
   * Add support for (xsd) schema <attribute/> nodes which primarily affects objects returned by the Builder
   
   * Update serviceproxy.py:set_proxies() to log DEBUG instead of INFO.
   
   * Enhance schema __str__ to show both the raw xml and the model (mostly for debugging).


version-0.2 (04-28-08):

  * Contains the first cut at the rpc/encoded soap style.
 
  * Replaced Property class with suds.sudsobject.Object.  The Property class was developed a long time
     ago with a slightly different purpose.  The suds Object is a simpler (more straight forward) approach that 
     requires less code and works better in the debugger. 

  * The Binding (and the encoding) is selected on a per-method basis which is more consistent with the wsdl.
     In <= 0.1.7, the binding was selected when the ServiceProxy was constructed and used for all service
     methods.  The binding was stored as self.binding.  Since the WSDL provides for a separate binding style and
     encoding for each operation, Suds needed to be change to work the same way.
 
  * The (nil_supported) and (faults) flag(s) passed into the service proxy using **kwargs.  In addition to these
     flags, a (http_proxy) flag has been added and is passed to the urllib2.Request object.  The following args
     are supported:
       * faults = Raise faults raised by server (default:True), else return tuple from service method invocation
                        as (http code, object).
       * nil_supported = The bindings will set the xsi:nil="true" on nodes that have a value=None when this
                                      flag is True (default:True).  Otherwise, an empty node <x/> is sent.
       * proxy = An http proxy to be specified on requests (default:{}).
                       The proxy is defined as {protocol:proxy,}
                                      
  * Http proxy supported (see above).
  
  * ServiceProxy refactored to delegate to a SoapClient.  Since the service proxy exposes web services via getattr(),
     any attribute (including methods) provided by the ServiceProxy class hides WS operations defined by the
     wsdl.  So, by moving everything to the SoapClient, wsdl operations are no longer hidden without
     having to use *hoky* names for attributes and methods in the service proxy.  Instead, the service proxy has
     __client__ and __factory__ attributes (which really should be at low risk for name collision).  For now the 
     get_instance() and get_enum() methods have not been moved to preserve backward compatibility.  Although,
     the prefered API change would to replace:
     
     > service = ServiceProxy('myurl')
     > person = service.get_instance('person')
     
     ... with something like ...
     
     > service = ServiceProxy('myurl')
     > person = service.__factory__.get_instance('person')
     
     After a few releases giving time for users to switch the new API, the get_instance() and get_enum()
     methods may be removed with a notice in big letters.
     
   * Fixed problem where a wsdl doesn't define a <schema/> section and Suds can't resolve the prefixes for the
      http://www.w3.org/2001/XMLSchema namespace to detect builtin types such as (xs:string).
      
      
version-0.1.7 (04-08-08):

  * Added Binding.nil_supported to controls how property values (out) = None and empty tag (in) are processed.
    * service.binding.nil_supported = True -- means that property values = None are marshalled (out) as
      <x xsi:nil=true/> and <x/> is unmarshalled as '' and <x xsi:nil/> is unmarshalled as None.
    * service.binding.nil_supported = False -- means that property values = None are marshalled (out) as
      <x/> and <x/> *and* <x xsi:nil=true/> is unmarshalled as None.
      The xsi:nil is really ignored.
    * THE DEFAULT IS (TRUE)

  * Sax handler updated to handle multiple character() callbacks when the sax parser "chunks" the text.
    When the node.text is None, the node.text is set to the characters.  Else, the characters are appended.
    Thanks - andrea.spinelli@imteam.it
  
  * Replaced special (text) attribute with __text__ to allow for natural elements named "text"
  
  * Add unicode support by:
    * Add __unicode__ to all classes with __str__
    * Replace all str() calls with unicode().
    * __str__() returns UTF-8 encoded result of __unicode__.

  * XML output encoded as UTF-8 which matches the HTTP header and supports unicode.
  
  * SchemaCollection changed to provide the builtin() and custom() methods.  To support this, findPrefixes() was added to the
    Element in sax.py.  This is a better approach anyway since the wsdl and schemas may have many prefixes
    to http://www.w3.org/2001/XMLSchema.  Tested with both doc/lit and rpc/lit bindings
  
  * Refactored bindings packages from document & rpc to literal & encoded
  
  * Contains the completion of *full* namespace support as follows:
  
    * Namespace prefixes are no longer stripped from attribute values that
      reference types defined in the wsdl.
    * Schema's imported using <import/> should properly handle namespace and prefix
      mapping and re-mapping as needed.
    * All types are resolved, using fully qualified (w/ namespaces) lookups.
    * Schema.get_type() supports paths with and without ns prefixes.  When no prefix
      is specified the type is matched using the schema's target namespace.
  
  * Property maintains attribute names (keys) in the order added. This also means
    that get_item() and get_names() return ordered values.
     ( Although, I suspect ordering really needs to be done in the marshaller using the
        order specified in the wsdl/schema )
  
  Major refactoring of the schema.py. The primary goals is perparation for type lookups that are
  fully qualified by namespace.  Once completed, the prefixes on attribute values will not longer
  be stripped (purged).
  Change Summary:
    1) SchemaProperty overlay classes created at __init__ instead of on-demand.
    2) schema imports performed by new Import class instead of by Schema.
    3) Schema loads top level properties using a factory.
    4) All SchemaProperty /children/ lists are sorted by __cmp__ in SchemaProperty derived classes.
       This ensures that types with the same name are resolved in the following order (Import, Complex, Simple, Element).
    5) All /children/ SchemaProperty lists are constructed at __init__ instead of on-demand.
    6) The SchemaGroup created and WSDL class updated.  This works better then having the wsdl aggregate the <schema/>
       nodes which severs linkage to the wsdl parent element that have namespace prefix mapping.
    7) <import/> element handles properly in that both namespace remapping and prefix re-mapping of the imported schema's
       targetNamespace and associated prefix mapping - is performed.
         Eg: SCHMEA-A has prefix (tns) mapped as xmlns:tns=http://nsA and has targetNamespace=http://nsA.
         SCHEMA-B is importing schema A and has prefix (abc) mapped as xmlns:abc=http://nsABC.
         SCHEMA-B imports A as <import namespace=http://nsB xxx schemaLocation=http://nsA/schema-a.xsd>.
         So, since SCHEMA-B will be referencing elements of SCHEMA-A with prefix (abc) such as abc:something, SCHEMA-A's
         targetNamespace must be updated as http://nsABC and all element with type=tns:something must be updated to be
         type=abc:something so then can be resolved.

  * Fixes unmarshalling problem where nodes are added to property as (text, value).  This as introduced when the
    bindings were refactored.

  * Fixed various Property print problems.

  Notes:

    Thanks to Jesper Noehr of Coniuro for the majority of the rpc/literal binding and
    for lots of collaboration on #suds.
    
    
version-0.1.6 (03-06-08):

 * Provides proper handling of wsdls that contain schema sections containing
    xsd schema imports: <import namespace="" schemaLocation=""?>.  The
    referenced schemas are imported when a schemaLocation is specified.
* Raises exceptions for http status codes not already handled.


version-0.1.5( 02-21-08 ):

 * Provides better logging in the modules get logger by hierarchal names.
 * Refactored as needed to truely support other bindings.
 * Add sax module which replaces ElementTree.  This is faster, simpler and
   handles namespaces (prefixes) properly.
   
   
version-0.1.4 (12-21-07):

  * Provides for service method parameters to be None.
  * Add proper handling of method params that are lists of property
    objects.
    
    
version-0.1.3 (12-19-07):

  * Fixes problem where nodes marked as a collection (maxOccurs > 1) not
     creating property objects with value=[] when mapped-in with < 2
     values by the DocumentReader.  Caused by missing the 
     bindings.Document.ReplyHint.stripns() (which uses the DocumentReader.stripns())
     conversion to DocumentReader.stripn() now returning a tuple (ns,tag) as
     of 0.1.2.


version-0.1.2 (12-18-07):

  This release contains an update to property adds:
    * metadata support
    * overrides: __getitem__, __setitem__, __contans__
    * changes property(reader|writer) to use the property.metadata
       to handle namespaces for XML documents.
    * fixes setup.py requires.
    
    
version-0.1.1 (12-17-07):

  This release marks the first release in fedora hosted.
