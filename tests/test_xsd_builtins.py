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
import suds.xsd.sxbuiltin
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
    ("integer", suds.xsd.sxbuiltin.XInteger),
    ("string", suds.xsd.sxbuiltin.XString),
    ("float", suds.xsd.sxbuiltin.XFloat),
    ("...unknown...", suds.xsd.sxbuiltin.XBuiltin)))
def test_create_builtin_type_schema_objects(xsd_type_name, xsd_type):
    schema = _create_dummy_schema()
    xsd_object = suds.xsd.sxbuiltin.Factory.create(schema, xsd_type_name)
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
    suds.xsd.sxbuiltin.Factory.maptag(xsd_type_name, MockType)
    xsd_object = suds.xsd.sxbuiltin.Factory.create(schema, xsd_type_name)
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
    suds.xsd.sxbuiltin.Factory.maptag(name, _Dummy)
    assert schema.builtin((name, builtin_namespaces[0]))


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
    tags = suds.xsd.sxbuiltin.Factory.tags
    assert tags.__class__ is dict
    monkeypatch.setattr(suds.xsd.sxbuiltin.Factory, "tags", dict(tags))
