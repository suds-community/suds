# -*- coding: utf-8 -*-

# This program is free software; you can redistribute it and/or modify it under
# the terms of the (LGPL) GNU Lesser General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Library Lesser General Public License
# for more details at ( http://www.gnu.org/licenses/lgpl.html ).
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
# written by: Jurko Gospodnetić ( jurko.gospodnetic@pke.hr )

"""
Suds library's built-in XSD type handling unit tests.

Implemented using the 'pytest' testing framework.

Detailed date/time related unit tests extracted into a separate test module.

"""

if __name__ == "__main__":
    import __init__
    __init__.runUsingPyTest(globals())


import suds.client
from suds.xsd.sxbuiltin import Factory, XBuiltin, XInteger, XFloat, XString
import tests

import pytest


class _Dummy:
    """Class for testing unknown object class handling."""
    pass


# Built-in XSD data types as defined in 'XML Schema Part 2: Datatypes Second
# Edition' (http://www.w3.org/TR/2004/REC-xmlschema-2-20041028).
builtins = [
    "anySimpleType",
    "anyType",
    "anyURI",
    "base64Binary",
    "boolean",
    "byte",
    "date",
    "dateTime",
    "decimal",
    "double",
    "duration",
    "ENTITIES",
    "ENTITY",
    "float",
    "gDay",
    "gMonth",
    "gMonthDay",
    "gYear",
    "gYearMonth",
    "hexBinary",
    "ID",
    "IDREF",
    "IDREFS",
    "int",
    "integer",
    "language",
    "long",
    "Name",
    "NCName",
    "negativeInteger",
    "NMTOKEN",
    "NMTOKENS",
    "nonNegativeInteger",
    "nonPositiveInteger",
    "normalizedString",
    "NOTATION",
    "positiveInteger",
    "QName",
    "short",
    "string",
    "time",
    "token",
    "unsignedByte",
    "unsignedInt",
    "unsignedLong",
    "unsignedShort",
    ]

# XML namespaces where all the built-in type names live, as defined in 'XML
# Schema Part 2: Datatypes Second Edition'
# (http://www.w3.org/TR/2004/REC-xmlschema-2-20041028).
builtin_namespaces = [
    "http://www.w3.org/2001/XMLSchema",
    "http://www.w3.org/2001/XMLSchema-datatypes"]


@pytest.mark.parametrize(("xsd_type_name", "xsd_type"), (
    ("integer", XInteger),
    ("string", XString),
    ("float", XFloat),
    ("...unknown...", XBuiltin)))
def test_create_builtin_type_schema_objects(xsd_type_name, xsd_type):
    schema = _create_dummy_schema()
    xsd_object = Factory.create(schema, xsd_type_name)
    assert xsd_object.__class__ is xsd_type
    assert xsd_object.name == xsd_type_name
    assert xsd_object.schema is schema


@pytest.mark.parametrize("xsd_type_name", ("tonkica-polonkica", "integer"))
def test_create_custom_mapped_builtin_type_schema_objects(xsd_type_name,
        monkeypatch):
    """User code can add or update built-in XSD type registrations."""
    _monkeypatch_builtin_XSD_type_registry(monkeypatch)
    class MockType:
        def __init__(self, schema, name):
            self.schema = schema
            self.name = name
    schema = _Dummy()
    Factory.maptag(xsd_type_name, MockType)
    xsd_object = Factory.create(schema, xsd_type_name)
    assert xsd_object.__class__ is MockType
    assert xsd_object.name == xsd_type_name
    assert xsd_object.schema is schema


@pytest.mark.parametrize("name", builtins)
def test_do_not_recognize_builtin_types_in_unknown_namespace(name):
    schema = _create_dummy_schema()
    assert not schema.builtin((name, ""))
    assert not schema.builtin((name, " "))
    assert not schema.builtin((name, "some-dummy-namespace"))


@pytest.mark.parametrize(("name", "namespace"), (
    ("", builtin_namespaces[0]),
    ("", builtin_namespaces[1]),
    ("", ""),
    ("", " "),
    ("", "some-dummy-namespace"),
    ("x", builtin_namespaces[0]),
    ("x", builtin_namespaces[1]),
    ("x", ""),
    ("x", " "),
    ("xyz", "some-dummy-namespace"),
    ("xyz", builtin_namespaces[0]),
    ("xyz", builtin_namespaces[1]),
    ("xyz", ""),
    ("xyz", " "),
    ("xyz", "some-dummy-namespace")))
def test_do_not_recognize_unknown_types_as_builtins(name, namespace):
    schema = _create_dummy_schema()
    assert not schema.builtin((name, namespace))


@pytest.mark.parametrize("name", builtins)
def test_recognize_builtin_types(name):
    schema = _create_dummy_schema()
    for namespace in builtin_namespaces:
        assert schema.builtin((name, namespace))


def test_recognize_custom_mapped_builtins(monkeypatch):
    """User code can register additional XSD built-ins."""
    _monkeypatch_builtin_XSD_type_registry(monkeypatch)
    schema = _create_dummy_schema()
    name = "trla-baba-lan"
    assert not schema.builtin((name, builtin_namespaces[0]))
    Factory.maptag(name, _Dummy)
    assert schema.builtin((name, builtin_namespaces[0]))


def test_resolving_builtin_types(monkeypatch):
    _monkeypatch_builtin_XSD_type_registry(monkeypatch)
    class MockXInteger(XInteger):
        pass
    Factory.maptag("osama", MockXInteger)

    wsdl = tests.wsdl_input('<xsd:element name="wu" type="xsd:osama"/>', "wu")
    client = tests.client_from_wsdl(wsdl, nosend=True)

    # Check suds client's information on the 'wu' input parameter.
    element, schema_object = client.sd[0].params[0]
    assert element.name == "wu"
    assert element.type == ("osama", "http://www.w3.org/2001/XMLSchema")
    assert schema_object.__class__ is MockXInteger
    assert schema_object.name == "osama"
    assert schema_object.schema is client.wsdl.schema


def test_translation(monkeypatch):
    """Python <--> XML representation translation on marshall/unmarshall."""
    anObject = object()
    class MockType(XBuiltin):
        def __init__(self, *args, **kwargs):
            self._mock_translate_log = []
            super(MockType, self).__init__(*args, **kwargs)
        def translate(self, value, topython=True):
            self._mock_translate_log.append((value, topython))
            if topython:
                return anObject
            return "'ollywood"
    _monkeypatch_builtin_XSD_type_registry(monkeypatch)
    Factory.maptag("woof", MockType)

    wsdl = tests.wsdl("""\
      <xsd:element name="wi" type="xsd:woof"/>
      <xsd:element name="wo" type="xsd:woof"/>""", input="wi", output="wo")
    client = tests.client_from_wsdl(wsdl, nosend=True, prettyxml=True)

    # Check suds library's XSD schema input parameter information.
    schema = client.wsdl.schema
    element_in = schema.elements["wi", "my-namespace"]
    assert element_in.name == "wi"
    element_out = schema.elements["wo", "my-namespace"]
    assert element_out.name == "wo"
    schema_object_in = element_in.resolve()
    schema_object_out = element_out.resolve()
    assert element_in is client.sd[0].params[0][0]
    assert schema_object_in is client.sd[0].params[0][1]
    assert schema_object_in.__class__ is MockType
    assert schema_object_in._mock_translate_log == []
    assert schema_object_out.__class__ is MockType
    assert schema_object_out._mock_translate_log == []

    # Construct operation invocation request.
    request = client.service.f(55)
    assert schema_object_in._mock_translate_log == [(55, False)]
    assert schema_object_out._mock_translate_log == []
    assert tests.compare_xml_to_string(request.original_envelope, """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace"
    xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:wi>&apos;ollywood</ns0:wi>
   </ns1:Body>
</SOAP-ENV:Envelope>""")

    # Process operation response.
    response = client.service.f(__inject=dict(reply=suds.byte_str("""\
<?xml version="1.0"?>
<env:Envelope xmlns:env="http://schemas.xmlsoap.org/soap/envelope/">
  <env:Body>
    <wo xmlns="my-namespace">fri-fru</wo>
  </env:Body>
</env:Envelope>""")))
    assert response is anObject
    assert schema_object_in._mock_translate_log == [(55, False)]
    assert schema_object_out._mock_translate_log == [("fri-fru", True)]


def _create_dummy_schema():
    """Constructs a new dummy XSD schema instance."""
    #TODO: Find out how to construct this XSD schema object directly without
    # first having to construct a suds.client.Client from a complete WSDL
    # schema.
    wsdl = tests.wsdl_input('<xsd:element name="dummy"/>', "dummy")
    client = tests.client_from_wsdl(wsdl)
    return client.wsdl.schema


def _monkeypatch_builtin_XSD_type_registry(monkeypatch):
    """
    Monkeypatches the global suds built-in XSD type dictionary.

    After calling this function, a test is free to mess around with suds
    library's built-in XSD type register (register new ones, change classes
    registered for a particular XSD type, remove registrations, and such) and
    any such changes will be automatically undone at the end of the test.

    If a test does not call this function, any such modifications will be left
    valid in the current global application state and may affect tests run
    afterwards.

    """
    tags = Factory.tags
    assert tags.__class__ is dict
    monkeypatch.setattr(Factory, "tags", dict(tags))
