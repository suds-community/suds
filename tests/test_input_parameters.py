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
Suds Python library web service operation input parameter related unit tests.

Suds provides the user with an option to automatically 'hide' wrapper elements
around simple types and allow the user to specify such parameters without
explicitly creating those wrappers. For example: operation taking a parameter
of type X, where X is a sequence containing only a single simple data type
(e.g. string or integer) will be callable by directly passing it that internal
simple data type value instead of first wrapping that value in an object of
type X and then passing that wrapper object instead.

Unit tests in this module make sure suds recognizes an operation's input
parameters in different scenarios as expected. It does not deal with binding
given argument values to an operation's input parameters or constructing an
actual binding specific web service operation invocation request, although they
may use such functionality as tools indicating that suds recognized an
operation's input parameters correctly.

"""

if __name__ == "__main__":
    import __init__
    __init__.runUsingPyTest(globals())


import suds
import tests

import pytest


# Test data shared between different tests in this module.
sequence_choice_with_element_and_two_element_sequence = """\
    <xsd:complexType>
      <xsd:sequence>
        <xsd:choice>
          <xsd:element name="a" type="xsd:integer" />
          <xsd:sequence>
            <xsd:element name="b1" type="xsd:integer" />
            <xsd:element name="b2" type="xsd:integer" />
          </xsd:sequence>
        </xsd:choice>
      </xsd:sequence>
    </xsd:complexType>"""


@pytest.mark.parametrize("part_name", ("parameters", "pipi"))
def test_unwrapped_parameter(part_name):
    """
    Test correctly recognizing unwrapped web service operation input structure
    defined as follows:

      sequence
        |-choice
        |   |-element
        |   |-sequence
        |   |   |-element
        \   \   \-element

    """
    input_schema = sequence_choice_with_element_and_two_element_sequence
    wsdl = _unwrappable_wsdl(part_name, input_schema)
    client = tests.client_from_wsdl(wsdl, nosend=True)

    # Collect references to required WSDL model content.
    method = client.wsdl.services[0].ports[0].methods["f"]
    binding = method.binding.input
    assert binding.__class__ is suds.bindings.document.Document

    # Collect references to expected schema model objects.
    wrapper = client.wsdl.schema.elements["Wrapper", "my-namespace"]
    complex_type = wrapper.rawchildren[0]
    seq_1 = complex_type.rawchildren[0]
    choice = seq_1.rawchildren[0]
    element_a = choice.rawchildren[0]
    seq_2 = choice.rawchildren[1]
    element_b1 = seq_2.rawchildren[0]
    element_b2 = seq_2.rawchildren[1]

    # Construct expected parameter definitions.
    expected_param_defs = [
        ("a", element_a, [wrapper, complex_type, seq_1, choice]),
        ("b1", element_b1, [wrapper, complex_type, seq_1, choice, seq_2]),
        ("b2", element_b2, [wrapper, complex_type, seq_1, choice, seq_2])]

    param_defs = binding.param_defs(method)
    _expect_params(param_defs, expected_param_defs)


@pytest.mark.parametrize("part_name", ("parameters", "pipi"))
def test_explicitly_wrapped_parameter(part_name):
    """
    Test correctly recognizing explicitly wrapped web service operation input
    structure which would otherwise be automatically unwrapped.

    """
    input_schema = sequence_choice_with_element_and_two_element_sequence
    wsdl = _unwrappable_wsdl(part_name, input_schema)
    client = tests.client_from_wsdl(wsdl, nosend=True, unwrap=False)

    # Collect references to required WSDL model content.
    method = client.wsdl.services[0].ports[0].methods["f"]
    binding = method.binding.input
    assert binding.__class__ is suds.bindings.document.Document
    wrapper = client.wsdl.schema.elements["Wrapper", "my-namespace"]

    param_defs = binding.param_defs(method)
    _expect_params(param_defs, [("Wrapper", wrapper)])


@pytest.mark.parametrize("param_names", (
    [],
    ["parameters"],
    ["pipi"],
    ["fifi", "la", "fuff"]))
def test_typed_parameters(param_names):
    """
    Test correctly recognizing web service operation input structure defined
    with 0 or more typed input message part parameters.

    """
    wsdl = ["""\
<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
xmlns:ns="my-namespace"
xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types>
    <xsd:schema targetNamespace="my-namespace"
    elementFormDefault="qualified"
    attributeFormDefault="unqualified"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:complexType name="MyType">
        <xsd:sequence>
          <xsd:element name="a" type="xsd:integer" />
        </xsd:sequence>
      </xsd:complexType>
    </xsd:schema>
  </wsdl:types>
  <wsdl:message name="fRequestMessage">"""]
    for x in param_names:
        part_def = '\n    <wsdl:part name="%s" type="ns:MyType" />' % (x,)
        wsdl.append(part_def)
    wsdl.append("""
  </wsdl:message>
  <wsdl:portType name="dummyPortType">
    <wsdl:operation name="f">
      <wsdl:input message="ns:fRequestMessage" />
    </wsdl:operation>
  </wsdl:portType>
  <wsdl:binding name="dummy" type="ns:dummyPortType">
    <soap:binding style="document"
    transport="http://schemas.xmlsoap.org/soap/http" />
    <wsdl:operation name="f">
      <soap:operation soapAction="my-soap-action" style="document" />
      <wsdl:input><soap:body use="literal" /></wsdl:input>
    </wsdl:operation>
  </wsdl:binding>
  <wsdl:service name="dummy">
    <wsdl:port name="dummy" binding="ns:dummy">
      <soap:address location="unga-bunga-location" />
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>""")
    wsdl = suds.byte_str("".join(wsdl))
    client = tests.client_from_wsdl(wsdl, nosend=True)

    # Collect references to required WSDL model content.
    method = client.wsdl.services[0].ports[0].methods["f"]
    binding = method.binding.input
    assert binding.__class__ is suds.bindings.document.Document
    my_type = client.wsdl.schema.types["MyType", "my-namespace"]

    # Construct expected parameter definitions.
    expected_param_defs = [
        (param_name, [suds.bindings.binding.PartElement, param_name, my_type])
        for param_name in param_names]

    param_defs = binding.param_defs(method)
    _expect_params(param_defs, expected_param_defs)


def _expect_params(param_defs, expected_param_defs):
    """
    Assert the given parameter definition content.

    Given expected parameter definition content may contain the expected
    parameter type instance or it may contain a list/tuple describing the type
    instead.

    Type description list/tuple is expected to contain the following:
      1. type object's class reference
      2. type object's 'name' attribute value.
      3. type object's resolved type instance reference

    """
    assert param_defs.__class__ is list
    assert len(param_defs) == len(expected_param_defs)
    for pdef, expected_pdef in zip(param_defs, expected_param_defs):
        assert len(expected_pdef) in (2, 3), "bad test data"
        assert pdef[0] == expected_pdef[0]  # name
        if expected_pdef[1].__class__ in (list, tuple):
            # type - class/name/type instance
            assert pdef[1].__class__ is expected_pdef[1][0]
            assert pdef[1].name == expected_pdef[1][1]
            assert pdef[1].resolve() is expected_pdef[1][2]
        else:
            assert pdef[1] is expected_pdef[1]  # type - exact instance
        assert pdef[2:] == expected_pdef[2:]  # ancestry - optional


def _unwrappable_wsdl(part_name, param_schema):
    """
    Return a WSDL schema byte string.

    The returned WSDL schema defines a single service definition with a single
    port containing a single function named 'f' taking automatically
    unwrappable input parameter using document/literal binding.

    The input parameter is defined as a single named input message part (name
    given via the 'part_name' argument) referencing an XSD schema element named
    'Wrapper' located in the 'my-namespace' namespace.

    The wrapper element's type definition (XSD schema string) is given via the
    'param_schema' argument.

    """
    return suds.byte_str("""\
<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
xmlns:ns="my-namespace"
xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types>
    <xsd:schema targetNamespace="my-namespace"
    elementFormDefault="qualified"
    attributeFormDefault="unqualified"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:element name="Wrapper">
%(param_schema)s
      </xsd:element>
    </xsd:schema>
  </wsdl:types>
  <wsdl:message name="fRequestMessage">
    <wsdl:part name="%(part_name)s" element="ns:Wrapper" />
  </wsdl:message>
  <wsdl:portType name="dummyPortType">
    <wsdl:operation name="f">
      <wsdl:input message="ns:fRequestMessage" />
    </wsdl:operation>
  </wsdl:portType>
  <wsdl:binding name="dummy" type="ns:dummyPortType">
    <soap:binding style="document"
    transport="http://schemas.xmlsoap.org/soap/http" />
    <wsdl:operation name="f">
      <soap:operation soapAction="my-soap-action" style="document" />
      <wsdl:input><soap:body use="literal" /></wsdl:input>
    </wsdl:operation>
  </wsdl:binding>
  <wsdl:service name="dummy">
    <wsdl:port name="dummy" binding="ns:dummy">
      <soap:address location="unga-bunga-location" />
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>""" % {"param_schema":param_schema, "part_name":part_name})
