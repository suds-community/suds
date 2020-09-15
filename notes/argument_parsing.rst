===================================================================
Notes on input argument usage when invoking a web service operation
===================================================================
:Authors: Jurko Gospodnetić
:Date: 2014-01-23


===========
Definitions
===========

message parts
  WSDL schema defines message parts representing a web service operation's input
  data. Each such part's data structure is defined by mapping the message part
  to XSD element or type.

input parameters
  Suds library's view of a web service operation's input data. Each message part
  may correspond to 1 or more input parameters. See the `Bare/wrapped web
  service operation input parameters`_ section for more detailed information.

input arguments
  Values passed to suds library's Python function or function object invoking a
  web service operation. Suds attempts to map each input argument to a single
  web service operation input parameter.


===================================================
Bare/wrapped web service operation input parameters
===================================================

When suds library models a web service operation, it can be configured to map
each of its message parts to a single input parameter expecting values directly
matching the data type defined for that message part in the web service's WSDL
schema. Such input parameters are called ``bare``.

If a particular message part has a type which is actually a structure containing
a collection of simpler elements, then suds may be configured to map each of
those simpler elements to a single input parameter. Such input parameters are
called 'wrapped'.

If an input parameter is represented by structured XSD element containing other
elements, suds may treat it as either ``bare`` or ``wrapped``. If it is
considered ``wrapped``, then suds library's web service operation invocation
function will take values for the input parameter's internal elements as input
arguments, instead of taking only a single wrapper object as a value for the
external wrapper element.

``wrapped`` input parameter support has been implemented to make the interface
simpler for the user/programmer using suds to invoke web service operations. It
does not affect how the the resulting web service operation invocation request
is constructed, i.e. passing a suds object as a single ``bare`` input parameter
value, or passing matching contained element values as separate wrapped input
parameter values results in the same web service operation invocation request
being constructed.

Example:
--------

Consider an operation taking the following element as its only message part::

  <xsd:element name="unga">
    <sequence>
      <xsd:element name="a" type="xsd:string"/>
      <xsd:element name="b" type="xsd:integer"/>
      <xsd:element name="c" type="MyType"/>
    </xsd:sequence>
  </xsd:element>

Suds may be configured to map that message part into with a single ``bare`` or
three ``wrapped`` input parameters.

If a ``bare`` input parameter is used, the operation invocation function would
take only a single argument:

* a suds object argument for element ``unga``

If ``wrapped`` input parameters are used, the operation invocation function
would take the following input arguments:

* a string argument for element ``a``
* an integer argument for element ``b``
* a suds object argument for element ``c``


==================================================================
Input parameter values in original and current suds implementation
==================================================================

* A user may or may not specify a value for a specific input parameter.
* We refer to unspecified or ``None`` input parameter values as `undefined`.
* We refer to all other input parameter values `defined`.

Original suds library implementation:
-------------------------------------

* An element may be explicitly marked as optional.
* ``choice`` input parameter structures not supported.
* A defined input parameter value is used directly.
* An undefined optional input parameter value is ignored.
* An undefined non-optional input parameter value is interpreted as an empty
  string.
* Multiple values specified for a single input parameter are ignored.
* Extra input arguments are ignored.

Defects:

* ``choice`` input parameter structures not supported correctly. When used,
  result in incorrectly constructed web service operation invocation requests.
* An ``all``/``choice``/``sequence`` input parameter structure may be explicitly
  marked as optional, but this is ignored when deciding whether a specific input
  parameter inside that structure is optional or not.
* No error when multiple values are specified for a single input parameter.
* No error on extra input arguments.

Current suds library implementation:
------------------------------------

* An element may be explicitly marked as optional.
* ``choice`` input parameter structures supported.
* Input parameters contained inside a ``choice`` input parameter structure
  (either directly or indirectly) are always considered optional.
* An input parameter structure containing at least one input parameter with a
  defined value (either directly or indirectly) is considered to have a defined
  value.
* A defined input parameter value is used directly.
* An undefined optional input parameter value is ignored.
* An undefined non-optional input parameters value is treated as an empty
  string.

Configurable features:

* Multiple values specified for a single input parameter may be reported as an
  error.
* ``choice`` input parameter structure directly containing multiple input
  parameters and/or input parameter structures with defined values may be
  reported as an error.
* Extra input argument may be reported as an error.

Defects (demonstrated by existing unit tests):

* An ``all``/``choice``/``sequence`` input parameter structure may be explicitly
  marked as optional, but this is ignored when deciding whether a specific input
  parameter inside that structure is optional or not.
* Undefined value for a non-optional input parameter contained directly inside
  an ``all``/``sequence`` input parameter structure contained inside a
  ``choice`` input parameter structure should be treated as an empty string if
  the ``all``/``sequence`` input parameter structure has a defined value.
* A ``choice`` input parameter structure directly containing an input parameter
  structure with no elements should be considered optional.

Still missing features:
-----------------------

* Non-optional ``choice`` input parameter structure with no defined value should
  be treated as if its first input parameter's value had been specified as an
  empty string.
