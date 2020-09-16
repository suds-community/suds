================================
WSDL SOAP binding research notes
================================
:Authors: Jurko Gospodnetić
:Date: 2014-06-30


WS-I Basic Profile notes
------------------------

Operations defined using the document/literal SOAP binding style should use at
most one message part and, if such a message part is defined, it should
reference an existing top-level XSD schema element and not a type.

There are different interpretations as to what to do about SOAP web service
operations that do not comply with WS-I Basic Profile recommendations and
either:

* use document/literal binding style with multiple message parts
* use document/literal binding style operations with a message part referencing
  an XSD type


WSDL message parts referencing an XSD type
------------------------------------------

When a WSDL message part references an XSD type and not an element, as in::

  <wsdl:message name="MyMessage">
    <wsdl:part name="parameter" type="MyElement"/>
  </wsdl:message>

as opposed to::

  <wsdl:message name="MyMessage">
    <wsdl:part name="parameter" element="MyElement"/>
  </wsdl:message>

then it acts as an XSD element of that type, as if it referenced an actual
top-level XSD element defined in the XSD schema.


XML namespace for SOAP message tags corresponding to a WSDL message part
------------------------------------------------------------------------

If a WSDL message part references an actual XSD element then the namespace is
defined by the XSD element's ``target namespace`` property and by whether the
element is considered qualified or not.

If a WSDL message part references an XSD type, then we have not been able to
find a clear standard specification stating what namespace corresponding SOAP
message tags should be qualified with. Since such WSDL message parts do not live
inside a specific XSD schema, there are no schema ``targetNamespace`` or
``elementFormDefault`` attributes to consult, and since it does not have a
``form`` attribute, there does not seem to be a way to explicitly state whether
and which namespace its instances should be qualified with.

There seem to be several options here on how to qualify the corresponding SOAP
message tags:

* with the WSDL schema's target namespace
* with the WSDL schema's default namespace
* with no namespace

Both SoapUI (checked using versions 4.6.1 & 5.0.0) & the original suds
implementation choose to use the 'no namespace' version in this case.

Some other sources suggest different handling for single-part messages whose
operations use document/literal SOAP binding and whose single message part
references an XSD type - simply using the type to define the SOAP envelope's
``<body>`` element structure instead of adding an additional wrapper element
beneath it. Note though that this usage contradicts WS-I Basic Profile
recommendation ``R2204``.
