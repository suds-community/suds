================================================
Examples on traversing suds library's data model
================================================
:Authors: Jurko Gospodnetić
:Date: 2014-01-23

Get service from client::

  service = client.service

Get client from service (for debugging purposes only)::

  client = service._ServiceSelector__client

Get XSD schema information from client::

  schema = client.wsdl.schema
  schema.root      # root schema XML element
  schema.all       # all of the schema's imported direct child objects (model)
  schema.children  # all of the schema's direct child objects (model)
  schema.elements  # (name, namespace) --> top level element mapping (model)
  schema.types     # (name, namespace) --> top level type mapping (model)


Get XSD schema model object's direct children (i.e. elements, sequences,
choices, etc.)::

  schema_object.rawchildren
