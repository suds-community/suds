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
Suds library's XSD Element node unit tests.

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


# shared test input data
form_test_values = (None, "qualified", "unqualified", "invalid", "")


class TestElementForm:
    """Test whether specific XSD elements are considered qualified."""

    @pytest.mark.parametrize("form_default, form", [(x, y)
        for x in form_test_values
        for y in form_test_values])
    def test_local_element(self, form_default, form):
        parent_name = "Parent"
        element_name = "Elemento"
        namespace = "tns"
        schema_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<schema xmlns="http://www.w3.org/2001/XMLSchema"
        targetNamespace="%(namespace)s"%(form_default)s>
    <element name="%(parent_name)s">
        <complexType>
            <sequence>
                <element name="%(element_name)s"%(form)s/>
            </sequence>
        </complexType>
    </element>
</schema>""" % {
            "element_name": element_name,
            "form": _attribute_xml("form", form),
            "form_default": _attribute_xml("elementFormDefault", form_default),
            "namespace": namespace,
            "parent_name": parent_name}
        expected = form == "qualified" or (
            (form is None) and (form_default == "qualified"))
        schema = _parse_schema_xml(b(schema_xml))
        parent_element = schema.elements[parent_name, namespace]
        element = parent_element.get_child(element_name)[0]
        assert bool(element.form_qualified) == expected

    @pytest.mark.parametrize("form_default, form, form_referenced", [(x, y, z)
        for x in form_test_values
        for y in form_test_values
        for z in form_test_values])
    def test_reference_to_internal(self, form_default, form, form_referenced):
        """Reference element to an element in the same schema."""
        referenced_name = "Referenced"
        referencing_parent_name = "Referencing"
        namespace = "tns"
        schema_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<schema xmlns="http://www.w3.org/2001/XMLSchema"
        xmlns:tns="%(namespace)s"
        targetNamespace="%(namespace)s"%(form_default)s>
    <element name="%(referenced_name)s"%(form_referenced)s/>
    <element name="%(referencing_parent_name)s">
        <complexType>
            <sequence>
                <element ref="tns:%(referenced_name)s"%(form_referencing)s/>
            </sequence>
        </complexType>
    </element>
</schema>""" % {
            "form_default": _attribute_xml("elementFormDefault", form_default),
            "form_referenced": _attribute_xml("form", form_referenced),
            "form_referencing": _attribute_xml("form", form),
            "namespace": namespace,
            "referenced_name": referenced_name,
            "referencing_parent_name": referencing_parent_name}
        schema = _parse_schema_xml(b(schema_xml))
        parent_element = schema.elements[referencing_parent_name, namespace]
        referencing_element = parent_element.get_child(referenced_name)[0]
        assert referencing_element.form_qualified

    def test_reference_to_external(self):
        """Reference element to an element in an external schema."""
        schema_xml_here = """\
<?xml version='1.0' encoding='UTF-8'?>
<schema xmlns="http://www.w3.org/2001/XMLSchema" xmlns:there="ns-there">
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
        referencing_parent = schema.elements["Referencing", None]
        referencing_element = referencing_parent.get_child("Referenced")[0]
        assert referencing_element.form_qualified

    @pytest.mark.parametrize("form_default, form", [(x, y)
        for x in form_test_values
        for y in form_test_values])
    def test_top_level_element(self, form_default, form):
        element_name = "Elemento"
        namespace = "tns"
        schema_xml = """\
<?xml version='1.0' encoding='UTF-8'?>
<schema xmlns="http://www.w3.org/2001/XMLSchema"
        targetNamespace="%(namespace)s"%(form_default)s>
    <element name="%(element_name)s"%(form)s/>
</schema>""" % {
            "element_name": element_name,
            "form": _attribute_xml("form", form),
            "form_default": _attribute_xml("elementFormDefault", form_default),
            "namespace": namespace}
        schema = _parse_schema_xml(b(schema_xml))
        element = schema.elements[element_name, namespace]
        assert element.form_qualified


def test_reference():
    """Reference to an element in a different schema."""
    schema_xml_here = """\
<?xml version='1.0' encoding='UTF-8'?>
<schema xmlns="http://www.w3.org/2001/XMLSchema" xmlns:there="ns-there">
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
    referencing_parent = schema.elements["Referencing", None]
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
