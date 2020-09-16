==========================
Modeling XSD types in suds
==========================
:Authors: Jurko Gospodnetić
:Date: 2014-01-29

XSD types can be one of the following:

built-in
  Defined in the XSD specification.

user defined
  Constructed by composing built-in and other user defined types according to
  rules defined in the XSD specification.

XSD elements represent specific input/output data in suds. Each XSD element is
of a particular XSD type.

In suds an XSD element can be *resolved* - process returning an object
representing the element's type.

Built-in types are represented in suds using different ``XType`` classes defined
in the ``suds.xsd.sxbuiltin module``, e.g. ``XFloat``, ``XInteger`` or
``XString``. Such classes define their ``translate()`` methods, implementing
transformations between Python objects and their XSD type value representations,
i.e. their representation as used in SOAP XML documents.

User code can defined additional or replacement ``XType`` classes and register
them with suds for a specific XSD type using the
``suds.xsd.sxbuiltin.Factory.maptag()`` method. This way suds can be extended
with additional functionality.

Example:
--------

You can define a replacement ``XFloat`` implementation allowing you to pass a
``fractions.Fraction`` arguments to a web service operation taking an
``xsd:float`` input parameter.
