==========================
XSD element research notes
==========================
:Authors: Jurko Gospodnetić
:Date: 2014-06-29


Global/local elements
---------------------

XSD schema elements are separated into two disjunct groups:

_`global`
  top-level elements and non-top-level reference elements (such references may
  only reference top-level elements, whether from the same or another schema)

_`local`
  non-top-level non-reference elements


_`Qualified`/_`unqualified` elements
------------------------------------

An XSD element is considered qualified if and only if one of the following
holds:

* it is `global`_
* its ``form`` attribute is set to ``qualified``
* its ``form`` attribute is unset and its schema's ``elementFormDefault``
  attribute is set to ``qualified``

**suds implementation note:** The only allowed ``form`` & ``elementFormDefault``
attribute values are ``qualified`` & ``unqualified`` but ``suds`` interprets any
value other than ``qualified`` as ``unqualified``.


Element's _`target namespace`
-----------------------------

An XSD element may have a `target namespace`_ assigned.

If an XSD element has a `target namespace`_ assigned then an XML element
corresponding to this XSD element must belong to that namespace.

If an XSD element does not have a `target namespace`_ assigned then an XML
element corresponding to this XSD element must not belong to any namespace.

Whether an XSD element has a `target namespace`_ assigned depends on whether it
is `qualified`_ or not, whether it is a reference and on its or its referenced
element schema's ``targetNamespace`` attribute:

* an `unqualified`_ element never has a `target namespace`_ assigned
* a non-reference `qualified`_ element collects its `target namespace`_ from its
  schema's non-empty ``targetNamespace`` attribute or has no `target namespace`_
  if its schema does not have a non-empty ``targetNamespace`` attribute value
  specified
* a reference element (such elements are always `qualified`_) collects its
  `target namespace`_ in the same way but used its referenced element schema
  instead of its own
