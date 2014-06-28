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
Suds library's XSD Element note unit tests.

Implemented using the 'pytest' testing framework.

"""

if __name__ == "__main__":
    import testutils
    testutils.run_using_pytest(globals())


import suds
import suds.options
import suds.sax.parser
import suds.store
import suds.xsd.schema

import pytest
from six import b

import types


@pytest.mark.parametrize("form_default, form, expected", (
    # default - not explicitly specified anywhere
    (None, None, False),

    # specified on the element only
    (None, "qualified", True),
    (None, "unqualified", False),
    (None, "invalid", False),
    (None, "", False),

    # specified on the schema only
    ("qualified", None, True),
    ("unqualified", None, False),
    ("invalid", None, False),
    ("", None, False),

    # specified on the schema, overruled on the element
    ("qualified", "qualified", True),
    ("qualified", "unqualified", False),
    ("qualified", "invalid", False),
    ("qualified", "", False),
    ("unqualified", "qualified", True),
    ("unqualified", "unqualified", False),
    ("unqualified", "invalid", False),
    ("unqualified", "", False),
    ("invalid", "qualified", True),
    ("invalid", "unqualified", False),
    ("invalid", "invalid", False),
    ("invalid", "", False),
    ("", "qualified", True),
    ("", "unqualified", False),
    ("", "invalid", False),
    ("", "", False)))
def test_element_form__non_ref(form_default, form, expected):
    """Test XSD non-ref element's form setting."""
    element_name = "Elemento"
    namespace = "tns"
    schema_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<schema xmlns="http://www.w3.org/2001/XMLSchema"
        targetNamespace="%(namespace)s"%(form_default)s>
    <element name="%(element_name)s"%(form)s/>
</schema>""" % {
        "namespace": namespace,
        "element_name": element_name,
        "form": _attribute_xml("form", form),
        "form_default": _attribute_xml("elementFormDefault", form_default)}
    schema = _parse_schema_xml(b(schema_xml))
    element = schema.elements[element_name, namespace]
    assert bool(element.form_qualified) == expected


@pytest.mark.parametrize("form_referenced, form_referencing, expected", (
    # default - not explicitly specified anywhere
    (None, None, False),

    # specified on the referencing only
    (None, "qualified", False),
    (None, "unqualified", False),
    (None, "invalid", False),
    (None, "", False),

    # specified on the referenced only
    ("qualified", None, True),
    ("unqualified", None, False),
    ("invalid", None, False),
    ("", None, False),

    # specified on the referencing, overruled on the element
    ("qualified", "qualified", True),
    ("qualified", "unqualified", True),
    ("qualified", "invalid", True),
    ("qualified", "", True),
    ("unqualified", "qualified", False),
    ("unqualified", "unqualified", False),
    ("unqualified", "invalid", False),
    ("unqualified", "", False),
    ("invalid", "qualified", False),
    ("invalid", "unqualified", False),
    ("invalid", "invalid", False),
    ("invalid", "", False),
    ("", "qualified", False),
    ("", "unqualified", False),
    ("", "invalid", False),
    ("", "", False)))
def test_element_form__ref(form_referenced, form_referencing, expected):
    """Test XSD ref element's form setting."""
    referencing_parent_name = "Referencing"
    referenced_name = "Referenced"
    namespace = "tns"
    schema_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<schema xmlns="http://www.w3.org/2001/XMLSchema"
        targetNamespace="%(namespace)s"
        xmlns:tns="%(namespace)s">
    <element name="%(referenced_name)s"%(form_referenced)s/>
    <element name="%(referencing_parent_name)s">
        <complexType>
            <sequence>
                <element ref="tns:%(referenced_name)s"%(form_referencing)s/>
            </sequence>
        </complexType>
    </element>
</schema>""" % {
        "namespace": namespace,
        "referenced_name": referenced_name,
        "referencing_parent_name": referencing_parent_name,
        "form_referenced": _attribute_xml("form", form_referenced),
        "form_referencing": _attribute_xml("form", form_referencing)}
    schema = _parse_schema_xml(b(schema_xml))
    referenced_element = schema.elements[referenced_name, namespace]
    referencing_parent = schema.elements[referencing_parent_name, namespace]
    referencing_element = referencing_parent.get_child(referenced_name)[0]
    assert referenced_element.ref is None
    assert referencing_element.ref == (referenced_name, namespace)
    assert bool(referenced_element.form_qualified) == expected
    assert bool(referencing_element.form_qualified) == expected


def test_element_form__ref_from_different_schema__to_qualified():
    """Referencing a qualified element in a separate schema."""
    schema_xml_here = """\
<?xml version='1.0' encoding='UTF-8'?>
<schema xmlns="http://www.w3.org/2001/XMLSchema"
        xmlns:there="ns-there"
        targetNamespace="ns-here">
    <import namespace="ns-there" schemaLocation="suds://there.xsd"/>
    <element name="Referencing">
        <complexType>
            <sequence>
                <element ref="there:Referenced"/>
            </sequence>
        </complexType>
    </element>
</schema>"""
    schema_xml_there = """\
<?xml version='1.0' encoding='UTF-8'?>
<schema xmlns="http://www.w3.org/2001/XMLSchema" targetNamespace="ns-there">
    <element name="Referenced" form="qualified"/>
</schema>"""
    store = suds.store.DocumentStore({"there.xsd": b(schema_xml_there)})
    schema = _parse_schema_xml(b(schema_xml_here), store)
    referenced_element = schema.elements["Referenced", "ns-there"]
    referencing_parent = schema.elements["Referencing", "ns-here"]
    referencing_element = referencing_parent.get_child("Referenced")[0]
    assert referenced_element.form_qualified
    assert referencing_element.form_qualified


def test_element_form__ref_from_different_schema__to_unqualified():
    """Referencing an unqualified element in a separate schema."""
    schema_xml_here = """\
<?xml version='1.0' encoding='UTF-8'?>
<schema xmlns="http://www.w3.org/2001/XMLSchema"
        xmlns:there="ns-there"
        elementFormDefault="qualified"
        targetNamespace="ns-here">
    <import namespace="ns-there" schemaLocation="suds://there.xsd"/>
    <element name="Referencing">
        <complexType>
            <sequence>
                <element ref="there:Referenced"/>
            </sequence>
        </complexType>
    </element>
</schema>"""
    schema_xml_there = """\
<?xml version='1.0' encoding='UTF-8'?>
<schema xmlns="http://www.w3.org/2001/XMLSchema" targetNamespace="ns-there">
    <element name="Referenced"/>
</schema>"""
    store = suds.store.DocumentStore({"there.xsd": b(schema_xml_there)})
    schema = _parse_schema_xml(b(schema_xml_here), store)
    referenced_element = schema.elements["Referenced", "ns-there"]
    referencing_parent = schema.elements["Referencing", "ns-here"]
    referencing_element = referencing_parent.get_child("Referenced")[0]
    assert not referenced_element.form_qualified
    assert not referencing_element.form_qualified


def test_reference():
    """Reference to an element in a different schema."""
    schema_xml_here = """\
<?xml version='1.0' encoding='UTF-8'?>
<schema xmlns="http://www.w3.org/2001/XMLSchema"
        xmlns:there="ns-there"
        targetNamespace="ns-here">
    <import namespace="ns-there" schemaLocation="suds://there.xsd"/>
    <element name="Referencing">
        <complexType>
            <sequence>
                <element ref="there:Referenced"/>
            </sequence>
        </complexType>
    </element>
</schema>"""
    schema_xml_there = """\
<?xml version='1.0' encoding='UTF-8'?>
<schema xmlns="http://www.w3.org/2001/XMLSchema" targetNamespace="ns-there">
    <element name="Referenced"/>
</schema>"""
    store = suds.store.DocumentStore({"there.xsd": b(schema_xml_there)})
    schema = _parse_schema_xml(b(schema_xml_here), store)
    referenced_element = schema.elements["Referenced", "ns-there"]
    referencing_parent = schema.elements["Referencing", "ns-here"]
    referencing_element = referencing_parent.get_child("Referenced")[0]
    assert referenced_element.ref is None
    assert referencing_element.ref == ("Referenced", "ns-there")


###############################################################################
#
# Test utilities.
#
###############################################################################

def _attribute_xml(name, value):
    if value is not None:
        return ' %s="%s"' % (name, value)
    return ""


def _parse_schema_xml(xml, documentStore=None):
    """Test utility constructing an XSD schema model from the given XML."""
    parser = suds.sax.parser.Parser()
    document = parser.parse(string=xml)
    root = document.root()
    url = "somewhere://over.the/rainbow"
    options_kwargs = {}
    if documentStore:
        options_kwargs.update(documentStore=documentStore)
    options = suds.options.Options(**options_kwargs)
    return suds.xsd.schema.Schema(root, url, options)
