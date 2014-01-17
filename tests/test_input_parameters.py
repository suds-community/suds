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


class Element:
    """Represents elements in our XSD map test data."""

    def __init__(self, name):
        self.name = name


class XSDType:
    """Unwrapped parameter XSD type test data."""

    def __init__(self, xsd, xsd_map):
        self.xsd = xsd
        self.xsd_map = xsd_map


# Test data shared between different tests in this module.

choice_choice = XSDType("""\
    <xsd:complexType>
      <xsd:sequence>
        <xsd:choice>
          <xsd:element name="aString1" type="xsd:string" />
          <xsd:element name="anInteger1" type="xsd:integer" />
        </xsd:choice>
        <xsd:choice>
          <xsd:element name="aString2" type="xsd:string" />
          <xsd:element name="anInteger2" type="xsd:integer" minOccurs="0" />
        </xsd:choice>
      </xsd:sequence>
    </xsd:complexType>""", [
    "complex_type", [
        "sequence", [
            "choice_1", [
                Element("aString1"),
                Element("anInteger1")],
            "choice_2", [
                Element("aString2"),
                Element("anInteger2")]]]])

choice_element_choice = XSDType("""\
    <xsd:complexType>
      <xsd:sequence>
        <xsd:choice>
          <xsd:element name="aString1" type="xsd:string" />
          <xsd:element name="anInteger1" type="xsd:integer" />
        </xsd:choice>
        <xsd:element name="separator" type="xsd:string" />
        <xsd:choice>
          <xsd:element name="aString2" type="xsd:string" />
          <xsd:element name="anInteger2" type="xsd:integer" minOccurs="0" />
        </xsd:choice>
      </xsd:sequence>
    </xsd:complexType>""", [
    "complex_type", [
        "sequence", [
            "choice_1", [
                Element("aString1"),
                Element("anInteger1")],
            Element("separator"),
            "choice_2", [
                Element("aString2"),
                Element("anInteger2")]]]])

choice_simple_nonoptional = XSDType("""\
    <xsd:complexType>
      <xsd:choice>
        <xsd:element name="aString" type="xsd:string" />
        <xsd:element name="anInteger" type="xsd:integer" />
      </xsd:choice>
    </xsd:complexType>""", [
    "complex_type", [
        "choice", [
            Element("aString"),
            Element("anInteger")]]])

choice_with_element_and_two_element_sequence = XSDType("""\
    <xsd:complexType>
      <xsd:choice>
        <xsd:element name="a" type="xsd:integer" />
        <xsd:sequence>
          <xsd:element name="b1" type="xsd:integer" />
          <xsd:element name="b2" type="xsd:integer" />
        </xsd:sequence>
      </xsd:choice>
    </xsd:complexType>""", [
    "complex_type", [
        "choice", [
            Element("a"),
            "sequence", [
                Element("b1"),
                Element("b2")]]]])

empty_sequence = XSDType("""\
    <xsd:complexType>
      <xsd:sequence />
    </xsd:complexType>""", [
    "complex_type", [
        "sequence"]])

sequence_choice_with_element_and_two_element_sequence = XSDType("""\
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
    </xsd:complexType>""", [
    "complex_type", [
        "sequence_1", [
            "choice", [
                Element("a"),
                "sequence_2", [
                    Element("b1"),
                    Element("b2")]]]]])

sequence_with_five_elements = XSDType("""\
    <xsd:complexType>
      <xsd:sequence>
        <xsd:element name="p1" type="xsd:string" />
        <xsd:element name="p2" type="xsd:integer" />
        <xsd:element name="p3" type="xsd:string" />
        <xsd:element name="p4" type="xsd:integer" />
        <xsd:element name="p5" type="xsd:string" />
      </xsd:sequence>
    </xsd:complexType>""", [
    "complex_type", [
        "sequence", [
            Element("p1"),
            Element("p2"),
            Element("p3"),
            Element("p4"),
            Element("p5")]]])

sequence_with_one_element = XSDType("""\
    <xsd:complexType>
      <xsd:sequence>
        <xsd:element name="param" type="xsd:integer" />
      </xsd:sequence>
    </xsd:complexType>""", [
    "complex_type", [
        "sequence", [
            Element("param")]]])

sequence_with_two_elements = XSDType("""\
    <xsd:complexType>
      <xsd:sequence>
        <xsd:element name="aString" type="xsd:string" />
        <xsd:element name="anInteger" type="xsd:integer" />
      </xsd:sequence>
    </xsd:complexType>""", [
    "complex_type", [
        "sequence", [
            Element("aString"),
            Element("anInteger")]]])


class TestUnsupportedParameterDefinitions:
    """
    Tests performed on WSDL schema's containing input parameter type
    definitions that can not be modeled using the currently implemented suds
    library input parameter definition structure.

    The tests included in this group, most of which are expected to fail,
    should serve as an illustration of what type of input parameter definitions
    still need to be better modeled. Once this has been done, they should be
    refactored into separate argument parsing, input parameter definition
    structure and binding specific request construction tests.

    """

    def expect_error(self, expected_error_text, *args, **kwargs):
        """
        Assert a test function call raises an expected TypeError exception.

        Caught exception is considered expected if its string representation
        matches the given expected error text.

        Expected error text may be given directly or as a list/tuple containing
        valid alternatives.

        Web service operation 'f' invoker is used as the default test function.
        An alternate test function may be specified using the 'test_function'
        keyword argument.

        """
        try:
            test_function = kwargs.pop("test_function")
        except KeyError:
            test_function = self.service.f
        e = pytest.raises(TypeError, test_function, *args, **kwargs).value
        try:
            if expected_error_text.__class__ in (list, tuple):
                assert str(e) in expected_error_text
            else:
                assert str(e) == expected_error_text
        finally:
            del e

    def init_function_params(self, params, **kwargs):
        """
        Initialize a test in this group with the given parameter definition.

        Constructs a complete WSDL schema based on the given function parameter
        definition (defines a single web service operation named 'f' by
        default), and creates a suds Client object to be used for testing
        suds's web service operation invocation.

        An alternate operation name may be given using the 'operation_name'
        keyword argument.

        May only be invoked once per test.

        """
        input = '<xsd:element name="Wrapper">%s</xsd:element>' % (params,)
        assert not hasattr(self, "service")
        wsdl = tests.wsdl_input(input, "Wrapper", **kwargs)
        client = tests.client_from_wsdl(wsdl, nosend=True)
        self.service = client.service

    @pytest.mark.parametrize("test_args_required", (
        pytest.mark.xfail(reason="empty choice member items not supported")(
            True),
        False))
    def test_choice_containing_an_empty_sequence(self, test_args_required):
        """
        Test reporting extra input parameters passed to a function taking a
        choice parameter group containing an empty sequence subgroup.

        """
        self.init_function_params("""\
          <xsd:complexType>
            <xsd:choice>
              <xsd:element name="a" type="xsd:integer" />
              <xsd:sequence>
              </xsd:sequence>
            </xsd:choice>
          </xsd:complexType>""")

        expected = "f() takes 0 to 1 positional arguments but 3 were given"
        if not test_args_required:
            expected = [expected,
                "f() takes 1 positional argument but 3 were given"]
        self.expect_error(expected, 1, None, None)

    @pytest.mark.parametrize("choice", (
        # Explicitly marked as optional and containing only non-optional
        # elements.
        pytest.mark.xfail(reason="suds does not yet support minOccurs/"
            "maxOccurs attributes on all/choice/sequence order indicators")(
        """\
          <xsd:complexType>
            <xsd:choice minOccurs="0">
              <xsd:element name="aString" type="xsd:string" />
              <xsd:element name="anInteger" type="xsd:integer" />
            </xsd:choice>
          </xsd:complexType>"""),
        # Explicitly marked as optional and containing at least one
        # non-optional element.
        """\
          <xsd:complexType>
            <xsd:choice minOccurs="0">
              <xsd:element name="aString" type="xsd:string" minOccurs="0" />
              <xsd:element name="anInteger" type="xsd:integer" />
            </xsd:choice>
          </xsd:complexType>""",
        """\
          <xsd:complexType>
            <xsd:choice minOccurs="0">
              <xsd:element name="aString" type="xsd:string" />
              <xsd:element name="anInteger" type="xsd:integer" minOccurs="0" />
            </xsd:choice>
          </xsd:complexType>""",
        """\
          <xsd:complexType>
            <xsd:choice minOccurs="0">
              <xsd:element name="aString" type="xsd:string" minOccurs="0" />
              <xsd:element name="anInteger" type="xsd:integer" minOccurs="0" />
            </xsd:choice>
          </xsd:complexType>"""))
    def test_choice_explicitly_marked_as_optional(self, choice):
        """
        Test reporting extra input parameters passed to a function taking a
        single optional choice parameter group.

        """
        self.init_function_params(choice)
        expected = "f() takes 0 to 2 positional arguments but 3 were given"
        self.expect_error(expected, "one", None, 3)


@pytest.mark.parametrize("part_name", ("uno", "due", "quatro"))
def test_builtin_typed_element_parameter(part_name):
    """
    Test correctly recognizing web service operation input structure defined by
    a built-in typed element.

    """
    wsdl = suds.byte_str("""\
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
      <xsd:element name="MyElement" type="xsd:integer" />
    </xsd:schema>
  </wsdl:types>
  <wsdl:message name="fRequestMessage">
    <wsdl:part name="%s" element="ns:MyElement" />
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
</wsdl:definitions>""" % (part_name,))
    client = tests.client_from_wsdl(wsdl, nosend=True)

    # Collect references to required WSDL model content.
    method = client.wsdl.services[0].ports[0].methods["f"]
    assert not method.soap.input.body.wrapped
    binding = method.binding.input
    assert binding.__class__ is suds.bindings.document.Document
    my_element = client.wsdl.schema.elements["MyElement", "my-namespace"]

    param_defs = binding.param_defs(method)
    _expect_params(param_defs, [("MyElement", my_element)])


@pytest.mark.parametrize("part_name", ("parameters", "pipi"))
def test_explicitly_wrapped_parameter(part_name):
    """
    Test correctly recognizing explicitly wrapped web service operation input
    structure which would otherwise be automatically unwrapped.

    """
    input_schema = sequence_choice_with_element_and_two_element_sequence.xsd
    wsdl = _unwrappable_wsdl(part_name, input_schema)
    client = tests.client_from_wsdl(wsdl, nosend=True, unwrap=False)

    # Collect references to required WSDL model content.
    method = client.wsdl.services[0].ports[0].methods["f"]
    assert not method.soap.input.body.wrapped
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
    assert not method.soap.input.body.wrapped
    binding = method.binding.input
    assert binding.__class__ is suds.bindings.document.Document
    my_type = client.wsdl.schema.types["MyType", "my-namespace"]

    # Construct expected parameter definitions.
    expected_param_defs = [
        (param_name, [suds.bindings.binding.PartElement, param_name, my_type])
        for param_name in param_names]

    param_defs = binding.param_defs(method)
    _expect_params(param_defs, expected_param_defs)


@pytest.mark.parametrize("xsd_type", (
    choice_choice,
    choice_element_choice,
    choice_simple_nonoptional,
    choice_with_element_and_two_element_sequence,
    empty_sequence,
    sequence_choice_with_element_and_two_element_sequence,
    sequence_with_five_elements,
    sequence_with_one_element,
    sequence_with_two_elements))
def test_unwrapped_parameter(xsd_type):
    """Test recognizing unwrapped web service operation input structures."""
    input_schema = sequence_choice_with_element_and_two_element_sequence.xsd
    wsdl = _unwrappable_wsdl("part_name", input_schema)
    client = tests.client_from_wsdl(wsdl, nosend=True)

    # Collect references to required WSDL model content.
    method = client.wsdl.services[0].ports[0].methods["f"]
    assert method.soap.input.body.wrapped
    binding = method.binding.input
    assert binding.__class__ is suds.bindings.document.Document
    wrapper = client.wsdl.schema.elements["Wrapper", "my-namespace"]

    # Construct expected parameter definitions.
    xsd_map = sequence_choice_with_element_and_two_element_sequence.xsd_map
    expected_param_defs = _parse_schema_model(wrapper, xsd_map)

    param_defs = binding.param_defs(method)
    _expect_params(param_defs, expected_param_defs)


@pytest.mark.parametrize("part_name", ("parameters", "pipi"))
def test_unwrapped_parameter_part_name(part_name):
    """
    Unwrapped parameter's part name should not affect its parameter definition.

    """
    input_schema = sequence_choice_with_element_and_two_element_sequence.xsd
    wsdl = _unwrappable_wsdl(part_name, input_schema)
    client = tests.client_from_wsdl(wsdl, nosend=True)

    # Collect references to required WSDL model content.
    method = client.wsdl.services[0].ports[0].methods["f"]
    assert method.soap.input.body.wrapped
    binding = method.binding.input
    assert binding.__class__ is suds.bindings.document.Document
    wrapper = client.wsdl.schema.elements["Wrapper", "my-namespace"]

    # Construct expected parameter definitions.
    xsd_map = sequence_choice_with_element_and_two_element_sequence.xsd_map
    expected_param_defs = _parse_schema_model(wrapper, xsd_map)

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


def _parse_schema_model(root, schema_model_map):
    """
    Utility function for preparing the expected parameter definition structure
    based on an unwrapped input parameter's XSD type schema.

    Parses the XSD schema definition under a given XSD schema item and returns
    the expected parameter definition structure based on the given schema map.

    The schema map describes the expected hierarchy of items in the given XSD
    schema. Even though this information could be deduced from the XSD schema
    itself, that would require a much more complex implementation and this is
    supposed to be a simple testing utility.

    """
    schema_items = {}
    param_defs = []
    _parse_schema_model_r(schema_items, param_defs, [], root, schema_model_map)
    return param_defs


def _parse_schema_model_r(schema_items, param_defs, ancestry, parent,
        schema_model_map):
    """Recursive implementation detail for _parse_schema_model()."""
    prev = None
    ancestry = list(ancestry)
    ancestry.append(parent)
    n = 0
    for x in schema_model_map:
        if x.__class__ in (list, tuple):
            assert prev is not None, "bad schema model map"
            _parse_schema_model_r(schema_items, param_defs, ancestry, prev, x)
            continue
        item = parent.rawchildren[n]
        if isinstance(x, Element):
            x = x.name
            prev = None
            param_defs.append((x, item, ancestry))
        else:
            assert isinstance(x, str), "bad schema model map"
            prev = item
        assert x not in schema_items, "duplicate schema map item names"
        schema_items[x] = item
        n += 1
    assert len(parent.rawchildren) == n


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
