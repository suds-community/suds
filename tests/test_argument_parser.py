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
Suds Python library web service operation argument parser related unit tests.

Suds library prepares web service operation invocation functions that construct
actual web service operation invocation requests based on the parameters they
receive and their web service operation's definition.

ArgParser class implements generic argument parsing and validation, not
specific to a particular web service operation binding.

"""

if __name__ == "__main__":
    import __init__
    __init__.runUsingPyTest(globals())


import suds
from suds.argparser import ArgParser
import tests

import pytest


class MockParamProcessor:
    """
    Mock parameter processor that gets passed ArgParser results.

    Collects received parameter information so it may be checked after
    ArgParser completes its work.

    """

    def __init__(self):
        self.params_ = []

    def params(self):
        return self.params_

    def process(self, param_name, param_type, in_choice_context, value):
        self.params_.append((param_name, param_type, in_choice_context, value))


class MockParamType:
    """
    Represents a web service operation parameter type.

    Implements parts of the suds library's web service operation parameter type
    interface required by the ArgParser functionality.

    """

    def __init__(self, optional):
        self.optional_ = optional

    def optional(self):
        return self.optional_


@pytest.mark.parametrize("binding_style", (
    "document",
    #TODO: Suds library's RPC binding implementation should be updated to use
    # the ArgParser functionality. This will remove code duplication between
    # different binding implementations and make their features more balanced.
    pytest.mark.xfail(reason="Not yet implemented.")("rpc")
    ))
def test_binding_uses_ArgParser(monkeypatch, binding_style):
    """
    Calling web service operations should use the generic ArgParser
    functionality independent of the operation's specific binding style.

    """
    class MyException(Exception):
        pass
    def raise_my_exception(*args, **kwargs):
        raise MyException
    monkeypatch.setattr(ArgParser, "__init__", raise_my_exception)

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
      <xsd:element name="Bongo" type="xsd:string" />
    </xsd:schema>
  </wsdl:types>
  <wsdl:message name="fRequestMessage">"
    <wsdl:part name="parameters" element="ns:Bongo" />
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
      <soap:operation soapAction="my-soap-action" style="%s" />
      <wsdl:input><soap:body use="literal" /></wsdl:input>
    </wsdl:operation>
  </wsdl:binding>
  <wsdl:service name="dummy">
    <wsdl:port name="dummy" binding="ns:dummy">
      <soap:address location="unga-bunga-location" />
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>
""" % (binding_style,))
    client = tests.client_from_wsdl(wsdl, nosend=True, prettyxml=True)
    pytest.raises(MyException, client.service.f)
    pytest.raises(MyException, client.service.f, "x")
    pytest.raises(MyException, client.service.f, "x", "y")


@pytest.mark.parametrize(("param_count", "args"), (
    (2, (1, 2, 3)),
    (2, ("2", 2, None)),
    (3, (object(), 2, None, None)),
    (3, (None, 2, None, None, "5"))))
def test_extra_positional_argument_when_expecting_multiple(param_count, args):
    """
    Test passing extra positional arguments for an operation expecting more
    than one.

    """
    params = []
    for i in range(param_count):
        param_name = "p%d" % (i,)
        param_type = MockParamType(False)
        params.append((param_name, param_type))
    param_processor = MockParamProcessor()
    arg_parser = ArgParser("fru-fru", False, args, {}, param_processor.process)
    for param_name, param_type in params:
        arg_parser.process_parameter(param_name, param_type)
    expected = "fru-fru() takes %d arguments but %d were given" % (param_count,
        len(args))
    _expect_error(TypeError, expected, arg_parser.finish)
    assert arg_parser.active()
    assert len(param_processor.params()) == param_count
    processed_params = param_processor.params()
    for expected_param, param, value in zip(params, processed_params, args):
        assert param[0] is expected_param[0]
        assert param[1] is expected_param[1]
        assert not param[2]
        assert param[3] is value


@pytest.mark.parametrize(("args", "reported_arg_count"), (
    ((1,), "1 was"),
    ((1, 2), "2 were"),
    ((1, 2, None), "3 were")))
def test_extra_positional_argument_when_expecting_none(args,
        reported_arg_count):
    """
    Test passing extra positional arguments for an operation expecting none.

    """
    param_processor = MockParamProcessor()
    arg_parser = ArgParser("f", False, args, {}, param_processor.process)
    expected = "f() takes 0 arguments but %s given" % (reported_arg_count,)
    _expect_error(TypeError, expected, arg_parser.finish)
    assert arg_parser.active()
    assert not param_processor.params()


@pytest.mark.parametrize(("optional", "args"),
    [(o, a) for o in (False, True) for a in (
        (1, 2),
        ("2", 2, None),
        (object(), 2, None, None),
        (None, 2, None, None, "5"))])
def test_extra_positional_argument_when_expecting_one(optional, args):
    """
    Test passing extra positional arguments for an operation expecting one.

    """
    param_processor = MockParamProcessor()
    arg_parser = ArgParser("gr", False, args, {}, param_processor.process)
    param_type = MockParamType(optional)
    arg_parser.process_parameter("p1", param_type)

    takes = {True:"0 to 1 arguments", False:"1 argument"}[optional]
    expected = "gr() takes %s but %d were given" % (takes, len(args))
    _expect_error(TypeError, expected, arg_parser.finish)

    assert arg_parser.active()
    assert len(param_processor.params()) == 1
    processed_param = param_processor.params()[0]
    assert processed_param[0] is "p1"
    assert processed_param[1] is param_type
    assert not processed_param[2]
    assert processed_param[3] is args[0]


@pytest.mark.parametrize(("wrapped", "ancestry"), (
    (False, [object()]),
    (True, []),
    (True, None)))
def test_inconsistent_wrapped_and_ancestry(wrapped, ancestry):
    """
    Parameter ancestry information should be sent for automatically unwrapped
    web service operation interfaces and only for them.

    """
    expected_error_message = {
        True:"Automatically unwrapped interfaces require ancestry information "
            "specified for all their parameters.",
        False:"Only automatically unwrapped interfaces may have their "
            "parameter ancestry information specified."}
    def do_nothing(*args, **kwargs):
        pass
    arg_parser = ArgParser("gr", wrapped, range(10), {}, do_nothing)
    param_info = ["p0", MockParamType(False), ancestry]
    m = expected_error_message[wrapped]
    _expect_error(RuntimeError, m, arg_parser.process_parameter, *param_info)


def _expect_error(expected_exception, expected_error_text, test_function,
        *args, **kwargs):
    """
    Assert a test function call raises an expected exception.

    Caught exception is considered expected if its string representation
    matches the given expected error text.

    Expected error text may be given directly or as a list/tuple containing
    valid alternatives.

    """
    def assertion(exception):
        if expected_error_text.__class__ in (list, tuple):
            assert str(exception) in expected_error_text
        else:
            assert str(exception) == expected_error_text
    _expect_error_worker(expected_exception, assertion, test_function, *args,
        **kwargs)


def _expect_error_worker(expected_exception, assertion, test_function, *args,
        **kwargs):
    """
    Assert a test function call raises an expected exception.

    Test function is invoked using the given input parameters and the caught
    exception is tested using the given assertion function.

    """
    try:
        test_function(*args, **kwargs)
        pytest.fail("Expected exception not raised.")
    except expected_exception, e:
        assertion(e)
