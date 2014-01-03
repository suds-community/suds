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
Suds Python library request construction related unit tests.

Suds provides the user with an option to automatically 'hide' wrapper elements
around simple types and allow the user to specify such parameters without
explicitly creating those wrappers. For example: function taking a parameter of
type X, where X is a sequence containing only a single simple data type (e.g.
string or integer) will be callable by directly passing it that internal simple
data type value instead of first wrapping that value in an object of type X and
then passing that wrapper object instead.

"""

if __name__ == "__main__":
    import __init__
    __init__.runUsingPyTest(globals())


import suds
import suds.store
import tests

import pytest


class TestExtraParameters:
    """
    Extra input parameters should be rejected correctly.

    Non-choice parameters should be treated as regular Python function
    arguments.

    Parameters belonging to a single choice parameter structure may each be
    specified but at most one one of those may have its value set to something
    other than None.

    Positional arguments are mapped to choice group parameters the same as done
    for a simple sequence group - each in turn, except that at most one of them
    may be given a value other than None.

    """

    def expect_error(self, expected_error_text, *args, **kwargs):
        """
        Assert an expected TypeError exception is raised from a test function
        call with the given input parameters. Caught exception is considered
        expected if its string representation matches the given expected error
        text.

        """
        def assertion(exception):
            assert expected_error_text == str(exception)
        self._expect_error(assertion, *args, **kwargs)

    def expect_error_containing(self, expected_error_text, *args, **kwargs):
        """
        Assert an expected TypeError exception is raised from a test function
        call with the given input parameters. Caught exception is considered
        expected if its string representation contains the given expected error
        text as a substring.

        """
        def assertion(exception):
            assert expected_error_text in str(exception)
        self._expect_error(assertion, *args, **kwargs)

    def expect_no_error(self, *args, **kwargs):
        """
        Assert a test function call with the given input parameters does not
        raise an exception.

        """
        self.service.f(*args, **kwargs)

    def init_function_params(self, params):
        """
        Initialize a test in this group with the given parameter definition.

        Constructs a complete WSDL schema based on the given function parameter
        definition (used to define a single function named 'f'), and creates a
        suds Client object to be used for testing suds's web service operation
        invocation.

        May only be invoked once per test.

        """
        # Using an empty 'xsd:element' XML element here when passed an empty
        # params string seems to cause suds not to recognize the web service
        # operation described in the given WSDL schema as using 'wrapped' input
        # parameters. Whether or not this is the correct behaviour is not up to
        # the tests in this test group to decide so we make sure we at least
        # add a single space as the element's data.
        if not params:
            params = " "
        input = '<xsd:element name="Wrapper">%s</xsd:element>' % (params,)
        assert not hasattr(self, "service")
        self.service = _service_from_wsdl(tests.wsdl_input(input, "Wrapper"))

    def test_choice_parameter_containing_a_sequence(self):
        """
        Test reporting extra input parameters passed to a function taking a
        choice parameter group containing a sequence subgroup.

        """
        self.init_function_params("""\
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
          </xsd:complexType>""")

        expected = "f() takes 1 to 3 arguments but 5 were given"
        self.expect_error(expected, 1, None, None, "4", "5")

        expected = ("f() got multiple arguments belonging to a single choice "
            "parameter group.")
        self.expect_error(expected, 1, 2)
        self.expect_error(expected, a=1, b1=2)
        self.expect_error(expected, a=1, b2=2)
        self.expect_error(expected, a=1, b1=None, b2=2)
        self.expect_error(expected, a=1, b1=2, b2=3)
        self.expect_error(expected, 1, 2, 3)
        self.expect_error(expected, 1, 2, b2=3)
        self.expect_error(expected, 1, b1=2, b2=3)

        self.expect_no_error(1)
        self.expect_no_error(a=1)
        self.expect_no_error(1, b1=None, b2=None)

    def test_multiple_consecutive_choice_parameters(self):
        """
        Test reporting extra input parameters passed to a function taking
        multiple choice parameter groups directly following each other.

        """
        self.init_function_params("""\
          <xsd:complexType>
            <xsd:sequence>
                <xsd:choice>
                  <xsd:element name="aString1" type="xsd:string" />
                  <xsd:element name="anInteger1" type="xsd:integer" />
                </xsd:choice>
                <xsd:choice>
                  <xsd:element name="aString2" type="xsd:string" />
                  <xsd:element name="anInteger2" type="xsd:integer"
                    minOccurs="0" />
                </xsd:choice>
            </xsd:sequence>
          </xsd:complexType>""")

        expected = "f() takes 1 to 4 arguments but 5 were given"
        self.expect_error(expected, None, 2, "three", None, "five")

        expected = ("f() got multiple arguments belonging to a single choice "
            "parameter group.")
        self.expect_error(expected, aString1="one", anInteger1=2, anInteger2=3)
        self.expect_error(expected, aString1="one", aString2="2", anInteger2=3)
        self.expect_error(expected, anInteger1=1, aString2="two", anInteger2=3)
        self.expect_error(expected, "one", anInteger1=2, aString2="three")
        self.expect_error(expected, "one", aString2="two", anInteger1=3)
        self.expect_error(expected, "one", None, "two", 3)
        self.expect_error(expected, "one", None, "two", anInteger2=3)

        expected = "f() got an unexpected keyword argument 'x'"
        self.expect_error(expected, "one", None, "two", x=666)
        self.expect_error(expected, aString1="one", anInteger2=2, x=666)
        self.expect_error(expected, anInteger1=1, x=666, aString2="two")
        self.expect_error(expected, x=666, aString1="one", aString2="two")
        self.expect_error(expected, x=666, anInteger1=1, anInteger2=2)

        expected = "f() got multiple values for argument 'aString1'"
        self.expect_error(expected, "one", aString1="two", anInteger2=3)
        self.expect_error(expected, "one", None, "two", aString1="three")

        expected = "f() got multiple values for argument 'anInteger1'"
        self.expect_error(expected, None, 2, "three", anInteger1=22)

        expected = "f() got multiple values for argument 'aString2'"
        self.expect_error(expected, None, 2, None, aString2=22)
        self.expect_error(expected, None, 2, None, None, aString2=22)

        expected = "f() got multiple values for argument 'anInteger2'"
        self.expect_error(expected, None, 2, None, None, anInteger2=22)

    def test_multiple_optional_parameters(self):
        """
        Test how extra parameters are handled in an operation taking multiple
        optional parameters.

        """
        self.init_function_params("""\
          <xsd:complexType>
            <xsd:sequence>
              <xsd:element name="aString" type="xsd:string" minOccurs="0" />
              <xsd:element name="anInteger" type="xsd:integer" minOccurs="0" />
            </xsd:sequence>
          </xsd:complexType>""")

        expected = "f() takes 0 to 2 arguments but 3 were given"
        self.expect_error(expected, "one", 2, 3)
        self.expect_error(expected, "one", 2, "three")

        expected = "f() got multiple values for argument 'aString'"
        self.expect_error(expected, "one", aString="two", anInteger=3)
        self.expect_error(expected, None, 1, aString="two")
        self.expect_error(expected, "one", 2, aString=None)

        expected = "f() got an unexpected keyword argument '"
        self.expect_error_containing(expected, "one", 2, x=3, y=4, z=5)

    def test_multiple_parameters(self):
        """
        Test how extra parameters are handled in an operation taking more than
        one input parameter.

        """
        self.init_function_params("""\
          <xsd:complexType>
            <xsd:sequence>
              <xsd:element name="aString" type="xsd:string" />
              <xsd:element name="anInteger" type="xsd:integer" />
            </xsd:sequence>
          </xsd:complexType>""")

        expected = "f() takes 2 arguments but 3 were given"
        self.expect_error(expected, "one", 2, 3)
        self.expect_error(expected, "one", 2, "three")

        expected = "f() got an unexpected keyword argument 'x'"
        self.expect_error(expected, "one", 2, x=3)
        self.expect_error(expected, aString="one", anInteger=2, x=3)
        self.expect_error(expected, aString="one", x=3, anInteger=2)
        self.expect_error(expected, x=3, aString="one", anInteger=2)

        expected = "f() got multiple values for argument 'aString'"
        self.expect_error(expected, "one", aString="two", anInteger=3)
        self.expect_error(expected, None, 1, aString="two")
        self.expect_error(expected, "one", 2, aString=None)

        expected = "f() got an unexpected keyword argument '"
        self.expect_error_containing(expected, "one", 2, x=3, y=4, z=5)

    def test_multiple_separated_choice_parameters(self):
        """
        Test reporting extra input parameters passed to a function taking
        multiple choice parameter groups with at least one non-choice separator
        element between them.

        """
        self.init_function_params("""\
          <xsd:complexType>
            <xsd:sequence>
                <xsd:choice>
                  <xsd:element name="s1" type="xsd:string" />
                  <xsd:element name="i1" type="xsd:integer" />
                </xsd:choice>
                <xsd:element name="separator" type="xsd:string" />
                <xsd:choice>
                  <xsd:element name="s2" type="xsd:string" />
                  <xsd:element name="i2" type="xsd:integer"
                    minOccurs="0" />
                </xsd:choice>
            </xsd:sequence>
          </xsd:complexType>""")

        expected = "f() takes 2 to 5 arguments but 6 were given"
        self.expect_error(expected, None, 2, "three", "four", None, "six")

        expected = ("f() got multiple arguments belonging to a single choice "
            "parameter group.")
        self.expect_error(expected, s1="one", i1=2, separator="", i2=3)
        self.expect_error(expected, s1="one", separator="", s2="2", i2=3)
        self.expect_error(expected, i1=1, separator="", s2="two", i2=3)
        self.expect_error(expected, "one", 2, "", "three")
        self.expect_error(expected, "one", 2, separator="", s2="three")
        self.expect_error(expected, "one", i1=2, separator="", s2="three")
        self.expect_error(expected, "one", None, "", "two", 3)
        self.expect_error(expected, "one", None, "", "two", i2=3)

        expected = "f() got an unexpected keyword argument 'x'"
        self.expect_error(expected, "one", None, "", "two", x=666)
        self.expect_error(expected, s1="one", separator="", i2=2, x=666)
        self.expect_error(expected, i1=1, separator="", x=666, s2="two")
        self.expect_error(expected, x=666, s1="one", separator="", s2="two")
        self.expect_error(expected, x=666, i1=1, separator="", i2=2)

        expected = "f() got multiple values for argument 's1'"
        self.expect_error(expected, "one", s1="two", separator="", i2=3)
        self.expect_error(expected, "one", None, "", "two", s1="three")

        expected = "f() got multiple values for argument 'i1'"
        self.expect_error(expected, None, 2, "", "three", i1=22)

        expected = "f() got multiple values for argument 'separator'"
        self.expect_error(expected, "one", None, "", "two", separator=None)
        self.expect_error(expected, "one", None, None, "two", separator=None)
        self.expect_error(expected, "1", None, "", "2", separator="x")
        self.expect_error(expected, "1", None, None, "2", separator="x")
        self.expect_error(expected, "1", None, "x", "2", separator=None)
        self.expect_error(expected, "1", None, "x", "2", separator="y")

        expected = "f() got multiple values for argument 's2'"
        self.expect_error(expected, None, 2, "", None, s2=22)
        self.expect_error(expected, None, 2, "", None, None, s2=22)

        expected = "f() got multiple values for argument 'i2'"
        self.expect_error(expected, None, 2, "", None, None, i2=22)

    def test_no_parameters(self):
        """
        Test how extra parameters are handled in an operation taking no input
        parameters.

        """
        self.init_function_params("")

        expected = "f() takes 0 arguments but 1 was given"
        self.expect_error(expected, 1)

        expected = "f() takes 0 arguments but 2 were given"
        self.expect_error(expected, 1, "two")

        expected = "f() takes 0 arguments but 5 were given"
        self.expect_error(expected, 1, "two", 3, "four", object())

        expected = "f() got an unexpected keyword argument 'x'"
        self.expect_error(expected, x=3)

        expected = "f() got an unexpected keyword argument '"
        self.expect_error_containing(expected, x=1, y=2, z=3)

    def test_nonoptional_and_optional_parameters(self):
        """
        Test how extra parameters are handled in an operation taking both
        non-optional and optional input parameters.

        """
        self.init_function_params("""\
          <xsd:complexType>
            <xsd:sequence>
              <xsd:element name="one" type="xsd:string" />
              <xsd:element name="two" type="xsd:string" minOccurs="0" />
              <xsd:element name="three" type="xsd:string" />
              <xsd:element name="four" type="xsd:string" minOccurs="0" />
            </xsd:sequence>
          </xsd:complexType>""")

        expected = "f() takes 2 to 4 arguments but 5 were given"
        self.expect_error(expected, "one", "two", "three", "four", "five")

        expected = "f() takes 2 to 4 arguments but 5 were given"
        self.expect_error(expected, "one", None, "three", "four", None)

        expected = "f() got multiple values for argument 'one'"
        self.expect_error(expected, "one", three="three", one=None)

        expected = "f() got multiple values for argument 'three'"
        self.expect_error(expected, "one", None, "three", "four", three="3")
        self.expect_error(expected, "one", None, None, "four", three="3")
        self.expect_error(expected, "one", None, "three", "four", three=None)
        self.expect_error(expected, "one", None, "three", four="4", three=None)

        expected = "f() got an unexpected keyword argument '"
        self.expect_error_containing(expected, "one", three="3", x=5, y=6, z=7)

    def test_single_nonoptional_choice_parameter(self):
        """
        Test reporting extra input parameters passed to a function taking a
        single non-optional choice parameter group.

        """
        self.init_function_params("""\
          <xsd:complexType>
            <xsd:choice>
              <xsd:element name="aString" type="xsd:string" />
              <xsd:element name="anInteger" type="xsd:integer" />
            </xsd:choice>
          </xsd:complexType>""")

        expected = "f() takes 1 to 2 arguments but 3 were given"
        self.expect_error(expected, "one", None, 3)
        self.expect_error(expected, "one", None, None)

        expected = "f() takes 1 to 2 arguments but 4 were given"
        self.expect_error(expected, "one", None, 3, 4)
        self.expect_error(expected, None, 2, "three", 4)

        expected = ("f() got multiple arguments belonging to a single choice "
            "parameter group.")
        self.expect_error(expected, aString="one", anInteger=2)
        self.expect_error(expected, anInteger=1, aString="two")
        self.expect_error(expected, "one", anInteger=2)

        expected = "f() got an unexpected keyword argument 'x'"
        self.expect_error(expected, "one", x=666)
        self.expect_error(expected, aString="one", x=666)
        self.expect_error(expected, anInteger=1, x=666)
        self.expect_error(expected, x=666, aString="one")
        self.expect_error(expected, x=666, anInteger=1)

        expected = "f() got multiple values for argument 'aString'"
        self.expect_error(expected, "one", aString="two")
        self.expect_error(expected, "one", None, aString="two")
        self.expect_error(expected, None, aString="two")
        self.expect_error(expected, None, None, aString="two")

    def test_single_nonoptional_parameter(self):
        """
        Test how extra parameters are handled in an operation taking a single
        non-optional input parameter.

        """
        self.init_function_params("""\
          <xsd:complexType>
            <xsd:sequence>
              <xsd:element name="param" type="xsd:integer" />
            </xsd:sequence>
          </xsd:complexType>""")

        expected = "f() takes 1 argument but 2 were given"
        self.expect_error(expected, 1, 2)
        self.expect_error(expected, 1, "two")

        expected = "f() takes 1 argument but 3 were given"
        self.expect_error(expected, 1, "two", 666)

        expected = "f() got an unexpected keyword argument 'x'"
        self.expect_error(expected, 1, x=666)
        self.expect_error(expected, param=1, x=666)
        self.expect_error(expected, x=666, param=2)

        expected = "f() got multiple values for argument 'param'"
        self.expect_error(expected, 1, param=2)
        self.expect_error(expected, None, param=1)
        self.expect_error(expected, 1, param=None)

        expected = "f() got an unexpected keyword argument '"
        self.expect_error_containing(expected, 1, x=2, y=3, z=4)

    @pytest.mark.parametrize("choice", (
        # Explicitly marked as optional and containing only non-optional
        # elements.
        pytest.mark.xfail(reason="suds does not yet support minOccurs/"
            "maxOccurs attributes on all/choice/sequence order indicator "
            "elements")(
        """\
          <xsd:complexType>
            <xsd:choice minOccurs="0">
              <xsd:element name="aString" type="xsd:string" />
              <xsd:element name="anInteger" type="xsd:integer" />
            </xsd:choice>
          </xsd:complexType>"""),
        # Not explicitly marked as optional but containing at least one
        # non-optional element.
        """\
          <xsd:complexType>
            <xsd:choice>
              <xsd:element name="aString" type="xsd:string" minOccurs="0" />
              <xsd:element name="anInteger" type="xsd:integer" />
            </xsd:choice>
          </xsd:complexType>""",
        """\
          <xsd:complexType>
            <xsd:choice>
              <xsd:element name="aString" type="xsd:string" />
              <xsd:element name="anInteger" type="xsd:integer" minOccurs="0" />
            </xsd:choice>
          </xsd:complexType>""",
        """\
          <xsd:complexType>
            <xsd:choice>
              <xsd:element name="aString" type="xsd:string" minOccurs="0" />
              <xsd:element name="anInteger" type="xsd:integer" minOccurs="0" />
            </xsd:choice>
          </xsd:complexType>""",
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
    def test_single_optional_choice_parameter(self, choice):
        """
        Test reporting extra input parameters passed to a function taking a
        single optional choice parameter group.

        """
        self.init_function_params(choice)
        expected = "f() takes 0 to 2 arguments but 3 were given"
        self.expect_error(expected, "one", None, 3)

    def test_single_optional_parameter(self):
        """
        Test how extra parameters are handled in an operation taking a single
        optional input parameter.

        """
        self.init_function_params("""\
          <xsd:complexType>
            <xsd:sequence>
              <xsd:element name="param" type="xsd:string" minOccurs="0" />
            </xsd:sequence>
          </xsd:complexType>""")

        expected = "f() takes 0 to 1 arguments but 2 were given"
        self.expect_error(expected, "one", 2)

        expected = "f() takes 0 to 1 arguments but 5 were given"
        self.expect_error(expected, "one", 2, "three", object(), None)

        expected = "f() got multiple values for argument 'param'"
        self.expect_error(expected, "one", param="two")
        self.expect_error(expected, None, param="one")
        self.expect_error(expected, "one", param=None)

        expected = "f() got an unexpected keyword argument '"
        self.expect_error_containing(expected, "one", x=3, y=4, z=5)

    def _expect_error(self, assertion, *args, **kwargs):
        """
        Assert an expected TypeError exception is raised from a test function
        call with the given input parameters. Caught exception is tested using
        the given assertion function.

        """
        try:
            self.service.f(*args, **kwargs)
            pytest.fail("Expected exception not raised.")
        except TypeError, e:
            assertion(e)


# TODO: Update the current restriction type output parameter handling so such
# parameters get converted to the correct Python data type based on the
# restriction's underlying data type.
@pytest.mark.xfail
def test_bare_input_restriction_types():
    client_unnamed = tests.client_from_wsdl(tests.wsdl_input("""\
      <xsd:element name="Elemento">
        <xsd:simpleType>
          <xsd:restriction base="xsd:string">
            <xsd:enumeration value="alfa" />
            <xsd:enumeration value="beta" />
            <xsd:enumeration value="gamma" />
          </xsd:restriction>
        </xsd:simpleType>
      </xsd:element>""", "Elemento"))

    client_named = tests.client_from_wsdl(tests.wsdl_input("""\
      <xsd:simpleType name="MyType">
        <xsd:restriction base="xsd:string">
          <xsd:enumeration value="alfa" />
          <xsd:enumeration value="beta" />
          <xsd:enumeration value="gamma" />
        </xsd:restriction>
      </xsd:simpleType>
      <xsd:element name="Elemento" type="ns:MyType" />""", "Elemento"))

    assert not _isInputWrapped(client_unnamed, "f")
    assert not _isInputWrapped(client_named, "f")


def test_disabling_automated_simple_interface_unwrapping():
    client = tests.client_from_wsdl(tests.wsdl_input("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="Elemento" type="xsd:string" />
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", "Wrapper"), nosend=True, prettyxml=True, unwrap=False)
    assert not _isInputWrapped(client, "f")
    wrapper = client.factory.create("Wrapper")
    wrapper.Elemento = "Wonderwall"
    _check_request(client.service.f(Wrapper=wrapper), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper>
         <ns0:Elemento>Wonderwall</ns0:Elemento>
      </ns0:Wrapper>
   </ns1:Body>
</SOAP-ENV:Envelope>""")


def test_element_references_to_different_namespaces():
    wsdl = suds.byte_str("""\
<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions
    xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema"
    xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
    xmlns:tns="first-namespace"
    targetNamespace="first-namespace">

  <wsdl:types>
    <xsd:schema
        targetNamespace="first-namespace"
        elementFormDefault="qualified"
        attributeFormDefault="unqualified"
        xmlns:second="second-namespace">
      <xsd:import namespace="second-namespace" schemaLocation="suds://external_schema"/>
      <xsd:element name="local_referenced" type="xsd:string"/>
      <xsd:element name="fRequest">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="local" type="xsd:string"/>
            <xsd:element ref="local_referenced"/>
            <xsd:element ref="second:external"/>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>
    </xsd:schema>
  </wsdl:types>

  <wsdl:message name="fRequestMessage">
    <wsdl:part name="parameters" element="tns:fRequest"/>
  </wsdl:message>

  <wsdl:portType name="DummyServicePortType">
    <wsdl:operation name="f">
      <wsdl:input message="tns:fRequestMessage"/>
    </wsdl:operation>
  </wsdl:portType>

  <wsdl:binding name="DummyServiceBinding" type="tns:DummyServicePortType">
    <soap:binding style="document" transport="http://schemas.xmlsoap.org/soap/http"/>
    <wsdl:operation name="f">
      <soap:operation soapAction="f"/>
      <wsdl:input><soap:body use="literal"/></wsdl:input>
    </wsdl:operation>
  </wsdl:binding>

  <wsdl:service name="DummyService">
    <wsdl:port name="DummyServicePort" binding="tns:DummyServiceBinding">
      <soap:address location="BoogaWooga"/>
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>
""")

    external_schema = suds.byte_str("""\
<?xml version='1.0' encoding='UTF-8'?>
<schema
    xmlns="http://www.w3.org/2001/XMLSchema"
    targetNamespace="second-namespace">
  <element name="external" type="string"/>
</schema>
""")

    store = suds.store.DocumentStore(external_schema=external_schema,
        wsdl=wsdl)
    client = suds.client.Client("suds://wsdl", cache=None, documentStore=store,
        nosend=True, prettyxml=True)
    _check_request(client.service.f(local="--L--", local_referenced="--LR--",
        external="--E--"), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns1="first-namespace" xmlns:ns2="second-namespace" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <SOAP-ENV:Body>
      <ns1:fRequest>
         <ns1:local>--L--</ns1:local>
         <ns1:local_referenced>--LR--</ns1:local_referenced>
         <ns2:external>--E--</ns2:external>
      </ns1:fRequest>
   </SOAP-ENV:Body>
</SOAP-ENV:Envelope>""")


def test_invalid_input_parameter_type_handling():
    """
    Input parameters of invalid type get silently pushed into the constructed
    SOAP request as strings, even though the constructed SOAP request does not
    necessarily satisfy requirements set for it in the web service's WSDL
    schema. It is then left up to the web service implementation to detect and
    report this error.

    """
    client = tests.client_from_wsdl(tests.wsdl_input("""\
      <xsd:complexType name="Freakazoid">
        <xsd:sequence>
          <xsd:element name="freak1" type="xsd:string" />
          <xsd:element name="freak2" type="xsd:string" />
          <xsd:element name="freak3" type="xsd:string" />
        </xsd:sequence>
      </xsd:complexType>
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="p1" type="xsd:string" />
            <xsd:element name="anInteger" type="xsd:integer" />
            <xsd:element name="p2" type="xsd:string" />
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", "Wrapper"), nosend=True, prettyxml=True)

    # Passing an unrelated Python type value.
    class SomeType:
        def __str__(self):
            return "Some string representation."
    _check_request(client.service.f(anInteger=SomeType()), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper>
         <ns0:p1/>
         <ns0:anInteger>Some string representation.</ns0:anInteger>
         <ns0:p2/>
      </ns0:Wrapper>
   </ns1:Body>
</SOAP-ENV:Envelope>""")

    # Passing a value of a WSDL schema defined type.
    value = client.factory.create("Freakazoid")
    value.freak1 = "Tiny"
    value.freak2 = "Miny"
    value.freak3 = "Mo"
    _check_request(client.service.f(anInteger=value), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper>
         <ns0:p1/>
         <ns0:anInteger>
            <ns0:freak1>Tiny</ns0:freak1>
            <ns0:freak2>Miny</ns0:freak2>
            <ns0:freak3>Mo</ns0:freak3>
         </ns0:anInteger>
         <ns0:p2/>
      </ns0:Wrapper>
   </ns1:Body>
</SOAP-ENV:Envelope>""")


def test_missing_parameters():
    """Missing non-optional parameters should get passed as empty values."""
    service = _service_from_wsdl(tests.wsdl_input("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="aString" type="xsd:string" />
            <xsd:element name="anInteger" type="xsd:integer" />
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", "Wrapper"))

    _check_request(service.f(), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper>
         <ns0:aString/>
         <ns0:anInteger/>
      </ns0:Wrapper>
   </ns1:Body>
</SOAP-ENV:Envelope>""")

    _check_request(service.f(u"Pero Ždero"), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper>
         <ns0:aString>Pero Ždero</ns0:aString>
         <ns0:anInteger/>
      </ns0:Wrapper>
   </ns1:Body>
</SOAP-ENV:Envelope>""")

    _check_request(service.f(anInteger=666), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper>
         <ns0:aString/>
         <ns0:anInteger>666</ns0:anInteger>
      </ns0:Wrapper>
   </ns1:Body>
</SOAP-ENV:Envelope>""")

    # None value is treated the same as undefined.
    _check_request(service.f(aString=None, anInteger=666), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper>
         <ns0:aString/>
         <ns0:anInteger>666</ns0:anInteger>
      </ns0:Wrapper>
   </ns1:Body>
</SOAP-ENV:Envelope>""")
    _check_request(service.f(aString="Omega", anInteger=None), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper>
         <ns0:aString>Omega</ns0:aString>
         <ns0:anInteger/>
      </ns0:Wrapper>
   </ns1:Body>
</SOAP-ENV:Envelope>""")


def test_named_parameter():
    class Tester:
        def __init__(self, service, expected_xml):
            self.service = service
            self.expected_xml = expected_xml

        def test(self, *args, **kwargs):
            _check_request(self.service.f(*args, **kwargs), self.expected_xml)

    # Test different ways to make the same web service operation call.
    service = _service_from_wsdl(tests.wsdl_input("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="uno" type="xsd:string" />
            <xsd:element name="due" type="xsd:string" />
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", "Wrapper"))
    t = Tester(service, """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper>
         <ns0:uno>einz</ns0:uno>
         <ns0:due>zwei</ns0:due>
      </ns0:Wrapper>
   </ns1:Body>
</SOAP-ENV:Envelope>""")
    t.test("einz", "zwei")
    t.test(uno="einz", due="zwei")
    t.test(due="zwei", uno="einz")
    t.test("einz", due="zwei")

    #   The order of parameters in the constructed SOAP request should depend
    # only on the initial WSDL schema.
    service = _service_from_wsdl(tests.wsdl_input("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="due" type="xsd:string" />
            <xsd:element name="uno" type="xsd:string" />
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", "Wrapper"))
    t = Tester(service, """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper>
         <ns0:due>zwei</ns0:due>
         <ns0:uno>einz</ns0:uno>
      </ns0:Wrapper>
   </ns1:Body>
</SOAP-ENV:Envelope>""")
    t.test("zwei", "einz")
    t.test(uno="einz", due="zwei")
    t.test(due="zwei", uno="einz")
    t.test("zwei", uno="einz")


def test_optional_parameter_handling():
    """Missing optional parameters should not get passed at all."""
    service = _service_from_wsdl(tests.wsdl_input("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="aString" type="xsd:string" minOccurs="0" />
            <xsd:element name="anInteger" type="xsd:integer" minOccurs="0" />
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", "Wrapper"))

    _check_request(service.f(), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper/>
   </ns1:Body>
</SOAP-ENV:Envelope>""")

    # None is treated as an undefined value.
    _check_request(service.f(None), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper/>
   </ns1:Body>
</SOAP-ENV:Envelope>""")

    # Empty string values are treated as well defined values.
    _check_request(service.f(""), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper>
         <ns0:aString></ns0:aString>
      </ns0:Wrapper>
   </ns1:Body>
</SOAP-ENV:Envelope>""")

    _check_request(service.f("Kiflica"), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper>
         <ns0:aString>Kiflica</ns0:aString>
      </ns0:Wrapper>
   </ns1:Body>
</SOAP-ENV:Envelope>""")

    _check_request(service.f(anInteger=666), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper>
         <ns0:anInteger>666</ns0:anInteger>
      </ns0:Wrapper>
   </ns1:Body>
</SOAP-ENV:Envelope>""")

    _check_request(service.f("Alfa", 9), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper>
         <ns0:aString>Alfa</ns0:aString>
         <ns0:anInteger>9</ns0:anInteger>
      </ns0:Wrapper>
   </ns1:Body>
</SOAP-ENV:Envelope>""")


def test_twice_wrapped_parameter():
    """
      Suds does not recognize 'twice wrapped' data structures and unwraps the
    external one but keeps the internal wrapping structure in place.

    """
    client = tests.client_from_wsdl(tests.wsdl_input("""\
      <xsd:element name="Wrapper1">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="Wrapper2">
              <xsd:complexType>
                <xsd:sequence>
                  <xsd:element name="Elemento" type="xsd:string" />
                </xsd:sequence>
              </xsd:complexType>
            </xsd:element>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", "Wrapper1"), nosend=True, prettyxml=True)

    assert _isInputWrapped(client, "f")

    # Web service operation calls made with 'valid' parameters.
    #
    # These calls are actually illegal and result in incorrectly generated SOAP
    # requests not matching the relevant WSDL schema. To make them valid we
    # would need to pass a more complex value instead of a simple string, but
    # the current simpler solution is good enough for what we want to test
    # here.
    value = "A B C"
    expectedRequest = """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper1>
         <ns0:Wrapper2>%s</ns0:Wrapper2>
      </ns0:Wrapper1>
   </ns1:Body>
</SOAP-ENV:Envelope>""" % (value,)
    _check_request(client.service.f(value), expectedRequest)
    _check_request(client.service.f(Wrapper2=value), expectedRequest)

    # Web service operation calls made with 'invalid' parameters.
    def testInvalidParameter(**kwargs):
        assert len(kwargs) == 1
        element = kwargs.keys()[0]
        expected = "f() got an unexpected keyword argument '%s'" % (element,)
        try:
            client.service.f(**kwargs)
        except TypeError, e:
            assert str(e) == expected
    testInvalidParameter(Elemento="A B C")
    testInvalidParameter(Wrapper1="A B C")


def test_wrapped_parameter():
    # Prepare web service proxies.
    client = lambda *args : tests.client_from_wsdl(tests.wsdl_input(*args),
        nosend=True, prettyxml=True)
    client_bare_single = client("""\
      <xsd:element name="Elemento" type="xsd:string" />""", "Elemento")
    client_bare_multiple_simple = client("""\
      <xsd:element name="Elemento1" type="xsd:string" />
      <xsd:element name="Elemento2" type="xsd:string" />""", "Elemento1",
        "Elemento2")
    client_bare_multiple_wrapped = client("""\
      <xsd:complexType name="Wrapper">
        <xsd:sequence>
          <xsd:element name="Elemento" type="xsd:string" />
        </xsd:sequence>
      </xsd:complexType>
      <xsd:element name="Elemento1" type="ns:Wrapper" />
      <xsd:element name="Elemento2" type="ns:Wrapper" />""", "Elemento1",
        "Elemento2")
    client_wrapped_unnamed = client("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="Elemento" type="xsd:string" />
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", "Wrapper")
    client_wrapped_named = client("""\
      <xsd:complexType name="WrapperType">
        <xsd:sequence>
          <xsd:element name="Elemento" type="xsd:string" />
        </xsd:sequence>
      </xsd:complexType>
      <xsd:element name="Wrapper" type="ns:WrapperType" />""", "Wrapper")

    #   Make sure suds library interprets our WSDL definitions as wrapped or
    # bare input interfaces as expected.
    assert not _isInputWrapped(client_bare_single, "f")
    assert not _isInputWrapped(client_bare_multiple_simple, "f")
    assert not _isInputWrapped(client_bare_multiple_wrapped, "f")
    assert _isInputWrapped(client_wrapped_unnamed, "f")
    assert _isInputWrapped(client_wrapped_named, "f")

    #   Both bare & wrapped single parameter input web service operations get
    # called the same way even though the wrapped one actually has an extra
    # wrapper element around its input data.
    data = "Maestro"
    call_single = lambda c : c.service.f(data)

    _check_request(call_single(client_bare_single), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Elemento>%s</ns0:Elemento>
   </ns1:Body>
</SOAP-ENV:Envelope>""" % data)

    expected_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Wrapper>
         <ns0:Elemento>%s</ns0:Elemento>
      </ns0:Wrapper>
   </ns1:Body>
</SOAP-ENV:Envelope>""" % data
    _check_request(call_single(client_wrapped_unnamed), expected_xml)
    _check_request(call_single(client_wrapped_named), expected_xml)

    #   Suds library's automatic structure unwrapping prevents us from
    # specifying the external wrapper structure directly.
    try:
        client_wrapped_unnamed.service.f(Wrapper="A")
    except TypeError, e:
        assert str(e) == "f() got an unexpected keyword argument 'Wrapper'"

    #   Multiple parameter web service operations are never automatically
    # unwrapped.
    data = ("Unga", "Bunga")
    call_multiple = lambda c : c.service.f(*data)

    _check_request(call_multiple(client_bare_multiple_simple), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Elemento1>%s</ns0:Elemento1>
      <ns0:Elemento2>%s</ns0:Elemento2>
   </ns1:Body>
</SOAP-ENV:Envelope>""" % data)

    _check_request(call_multiple(client_bare_multiple_wrapped), """\
<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:ns0="my-namespace" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
   <SOAP-ENV:Header/>
   <ns1:Body>
      <ns0:Elemento1>%s</ns0:Elemento1>
      <ns0:Elemento2>%s</ns0:Elemento2>
   </ns1:Body>
</SOAP-ENV:Envelope>""" % data)


def _check_request(request, expected_xml):
    tests.compare_xml_to_string(request.original_envelope, expected_xml)


def _isInputWrapped(client, method_name):
    assert len(client.wsdl.bindings) == 1
    operation = client.wsdl.bindings.values()[0].operations[method_name]
    return operation.soap.input.body.wrapped


def _service_from_wsdl(wsdl):
    """
    Construct a suds Client service instance used in tests in this module.

    The constructed Client instance only prepares web service operation
    invocation requests and does not attempt to actually send them.

    """
    client = tests.client_from_wsdl(wsdl, nosend=True, prettyxml=True)
    return client.service
