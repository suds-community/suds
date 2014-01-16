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

The module tested here implements generic argument parsing and validation, not
specific to a particular web service operation binding.

"""

if __name__ == "__main__":
    import __init__
    __init__.runUsingPyTest(globals())


import suds
import suds.argparser
import tests

import pytest


class MockAncestor:
    """
    Represents a web service operation parameter ancestry item.

    Implements parts of the suds library's web service operation ancestry item
    interface required by the argument parser functionality.

    """

    def __init__(self, is_choice=False):
        self.__is_choice = is_choice

    def choice(self):
        return self.__is_choice


class MockParamProcessor:
    """
    Mock parameter processor that gets passed argument parsing results.

    Collects received parameter information so it may be checked after argument
    parsing has completed.

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
    interface required by the argument parsing implementation tested in this
    module.

    """

    def __init__(self, optional):
        self.optional_ = optional

    def optional(self):
        return self.optional_


@pytest.mark.parametrize("binding_style", (
    "document",
    #TODO: Suds library's RPC binding implementation should be updated to use
    # the argument parsing functionality. This will remove code duplication
    # between different binding implementations and make their features more
    # balanced.
    pytest.mark.xfail(reason="Not yet implemented.")("rpc")
    ))
def test_binding_uses_argument_parsing(monkeypatch, binding_style):
    """
    Calling web service operations should use the generic argument parsing
    functionality independent of the operation's specific binding style.

    """
    class MyException(Exception):
        pass
    def raise_exception(*args, **kwargs):
        raise MyException
    monkeypatch.setattr(suds.argparser._ArgParser, "__init__", raise_exception)

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


@pytest.mark.parametrize(("param_optional", "args"), (
    # Operations taking no parameters.
    ((), (1,)),
    ((), (1, 2)),
    ((), (1, 2, None)),
    # Operations taking a single parameter.
    ((True,), (1, 2)),
    ((False,), (1, 2)),
    ((True,), ("2", 2, None)),
    ((False,), ("2", 2, None)),
    ((True,),  (object(), 2, None, None)),
    ((False,), (object(), 2, None, None)),
    ((True,), (None, 2, None, None, "5")),
    ((False,), (None, 2, None, None, "5")),
    # Operations taking multiple parameters.
    ((True, True), (1, 2, 3)),
    ((False, True), (1, 2, 3)),
    ((True, False), (1, 2, 3)),
    ((False, False), (1, 2, 3)),
    ((False, True), ("2", 2, None)),
    ((False, False), ("2", 2, None)),
    ((True, True), ("2", 2, None)),
    ((True, True, True), (object(), 2, None, None)),
    ((False, False, False), (object(), 2, None, None)),
    ((True, False, False), (None, 2, None, None, "5")),
    ((True, False, True), (None, 2, None, None, "5")),
    ((True, True, True), (None, 2, None, None, "5"))))
def test_extra_positional_arguments(param_optional, args):
    """
    Test passing extra positional arguments for an operation expecting more
    than one.

    """
    param_count = len(param_optional)
    params = []
    expected_args_min = 0
    for i, optional in enumerate(param_optional):
        if not optional:
            expected_args_min += 1
        param_name = "p%d" % (i,)
        param_type = MockParamType(optional)
        params.append((param_name, param_type))
    param_processor = MockParamProcessor()

    takes_plural_suffix = "s"
    if expected_args_min == param_count:
        takes = param_count
        if param_count == 1:
            takes_plural_suffix = ""
    else:
        takes = "%d to %d" % (expected_args_min, param_count)
    was_were = "were"
    if len(args) == 1:
        was_were = "was"
    expected = "fru-fru() takes %s positional argument%s but %d %s given" % (
        takes, takes_plural_suffix, len(args), was_were)
    _expect_error(TypeError, expected, suds.argparser.parse_args, "fru-fru",
        params, args, {}, param_processor.process, True)

    assert len(param_processor.params()) == param_count
    processed_params = param_processor.params()
    for expected_param, param, value in zip(params, processed_params, args):
        assert param[0] is expected_param[0]
        assert param[1] is expected_param[1]
        assert not param[2]
        assert param[3] is value


@pytest.mark.parametrize(("param_names", "args", "kwargs"), (
    (["a"], (1,), {"a":5}),
    ([["a"]], (1,), {"a":5}),
    (["a"], (None, 1, 2, 7), {"a":5}),
    ([["a"]], (None, 1, 2, 7), {"a":5}),
    (["a", ["b"], "c"], (None, None, None), {"a":1, "b":2, "c":3}),
    ([["a"], ["b"], ["c"]], (None, None, None), {"a":1, "b":2, "c":3}),
    (["a"], ("x",), {"a":None}),
    (["a", ["b"], ["c"]], (1,), {"a":None}),
    (["a", "b", ["c"]], (None, 2), {"b":None})))
def test_multiple_value_for_single_parameter_error(param_names, args, kwargs):
    """
    Test how multiple value for a single parameter errors are reported.

    This report takes precedence over any extra positional argument errors.

    Optional parameters are marked by specifying their names as single element
    lists or tuples.

    """
    params = []
    duplicates = []
    args_count = len(args)
    for n, param_name in enumerate(param_names):
        optional = False
        if param_name.__class__ in (tuple, list):
            optional = True
            param_name = param_name[0]
        if n < args_count and param_name in kwargs:
            duplicates.append(param_name)
        params.append((param_name, MockParamType(optional)))
    message = "q() got multiple values for parameter '%s'"
    expected = [message % (x,) for x in duplicates]
    if len(expected) == 1:
        expected = expected[0]
    _expect_error(TypeError, expected, suds.argparser.parse_args, "q", params,
        args, kwargs, _do_nothing, True)


def test_not_reporting_extra_argument_errors():
    """
    When ArgParser has been configured not to report extra argument errors as
    exceptions, it should simply ignore any such extra arguments. This matches
    the suds library behaviour from before extra argument error reporting was
    implemented.

    """
    x = MockAncestor()
    c = MockAncestor(is_choice=True)
    params = [
        ("p1", MockParamType(False), [x]),
        ("p2", MockParamType(True), [x, c]),
        ("p3", MockParamType(False), [x, c])]
    args = list(range(5))
    kwargs = {"p1":"p1", "p3":"p3", "x":666}
    param_processor = MockParamProcessor()
    args_required, args_allowed = suds.argparser.parse_args("w", params, args,
        kwargs, param_processor.process, False)

    assert args_required == 1
    assert args_allowed == 3
    processed_params = param_processor.params()
    assert len(processed_params) == len(params)
    for expected_param, param, value in zip(params, processed_params, args):
        assert param[0] is expected_param[0]
        assert param[1] is expected_param[1]
        assert param[2] == (c in expected_param[2])
        assert param[3] is value


@pytest.mark.parametrize(("param_names", "args", "kwargs"), (
    ([], (), {"x":5}),
    ([], (None, 1, 2, 7), {"x":5}),
    ([], (), {"x":1, "y":2, "z":3}),
    (["a"], (), {"x":None}),
    ([["a"]], (), {"x":None}),
    (["a"], (1,), {"x":None}),
    ([["a"]], (1,), {"x":None}),
    (["a"], (), {"a":"spank me", "x":5}),
    (["a"], (), {"x":5, "a":"spank me"}),
    (["a"], (), {"a":"spank me", "x":5, "wuwu":None}),
    (["a", "b", "c"], (1, 2), {"w":666}),
    (["a", ["b"], ["c"]], (1,), {"c":None, "w":666}),
    (["a", "b", ["c"]], (None,), {"b":None, "_":666})))
def test_unexpected_keyword_argument(param_names, args, kwargs):
    """
    Test how unexpected keyword arguments are reported.

    This report takes precedence over any extra positional argument errors.

    Optional parameters are marked by specifying their names as single element
    lists or tuples.

    """
    params = []
    arg_count = len(args)
    for n, param_name in enumerate(param_names):
        optional = False
        if param_name.__class__ in (tuple, list):
            optional = True
            param_name = param_name[0]
        if n < arg_count:
            assert param_name not in kwargs
        else:
            kwargs.pop(param_name, None)
        params.append((param_name, MockParamType(optional)))
    message = "pUFf() got an unexpected keyword argument '%s'"
    expected = [message % (x,) for x in kwargs]
    if len(expected) == 1:
        expected = expected[0]
    _expect_error(TypeError, expected, suds.argparser.parse_args, "pUFf",
        params, args, kwargs, _do_nothing, True)


@pytest.mark.parametrize(("expect_required", "expect_allowed", "param_defs"), (
    # No parameters.
    (0, 0, []),
    # Single parameter.
    (1, 1, [("p1", False, [1, 2, 3, 4])]),
    (0, 1, [("p1", True, [1, 2, 3, 4])]),
    (1, 1, [("p1", False, [1, 2, 3, [4]])]),
    (0, 1, [("p1", True, [1, 2, 3, [4]])]),
    (1, 1, [("p1", False, [1, [2], 3, 4])]),
    (0, 1, [("p1", True, [1, [2], 3, 4])]),
    (1, 1, [("p1", False, [1, [2], 3, [4]])]),
    (0, 1, [("p1", True, [1, [2], 3, [4]])]),
    # Multiple parameters.
    (4, 4, [
        ("a", False, [1]),
        ("b", False, [1]),
        ("c", False, [1]),
        ("d", False, [1])]),
    (0, 4, [
        ("a", True, [1]),
        ("b", True, [1]),
        ("c", True, [1]),
        ("d", True, [1])]),
    (2, 4, [
        ("a", True, [1]),
        ("b", False, [1]),
        ("c", True, [1]),
        ("d", False, [1])]),
    (2, 4, [
        ("a", False, [1]),
        ("b", True, [1]),
        ("c", False, [1]),
        ("d", True, [1])]),
    (3, 4, [
        ("a", False, [1]),
        ("b", False, [1]),
        ("c", False, [1]),
        ("d", True, [1])]),
    (3, 4, [
        ("a", True, [1]),
        ("b", False, [1]),
        ("c", False, [1]),
        ("d", False, [1])]),
    # Choice containing only simple members.
    (1, 2, [
        ("a", False, [[1]]),
        ("b", False, [[1]])]),
    (0, 2, [
        ("a", True, [[1]]),
        ("b", False, [[1]])]),
    (0, 2, [
        ("a", False, [[1]]),
        ("b", True, [[1]])]),
    (0, 2, [
        ("a", True, [[1]]),
        ("b", True, [[1]])]),
    # Choice containing a non-empty sequence.
    (1, 3, [
        ("a", False, [1, 2, 3, [4]]),
        ("b1", False, [1, 2, 3, [4], 5]),
        ("b2", False, [1, 2, 3, [4], 5])]),
    # Choice with more than one required parameter.
    (2, 4, [
        ("a1", False, [[1], 2]),
        ("a2", False, [[1], 2]),
        ("b1", False, [[1], 3]),
        ("b2", False, [[1], 3])]),
    (2, 5, [
        ("a1", False, [[1], 2]),
        ("a2", False, [[1], 2]),
        ("b1", False, [[1], 3]),
        ("b2", False, [[1], 3]),
        ("b3", False, [[1], 3])]),
    (2, 5, [
        ("a1", False, [[1], 2]),
        ("a2", False, [[1], 2]),
        ("a3", False, [[1], 2]),
        ("b1", False, [[1], 3]),
        ("b2", False, [[1], 3])]),
    (3, 6, [
        ("a1", False, [[1], 2]),
        ("a2", False, [[1], 2]),
        ("a3", False, [[1], 2]),
        ("b1", False, [[1], 3]),
        ("b2", False, [[1], 3]),
        ("b3", False, [[1], 3])]),
    (2, 6, [
        ("a1", False, [[1], 2]),
        ("a2", True, [[1], 2]),
        ("a3", False, [[1], 2]),
        ("b1", False, [[1], 3]),
        ("b2", False, [[1], 3]),
        ("b3", False, [[1], 3])]),
    # Sequence containing multiple choices.
    (2, 4, [
        ("a1", False, [0, [1]]),
        ("a2", False, [0, [1]]),
        ("b1", False, [0, [2]]),
        ("b2", False, [0, [2]])]),
    (1, 4, [
        ("a1", False, [0, [1]]),
        ("a2", False, [0, [1]]),
        ("b1", False, [0, [2]]),
        ("b2", True, [0, [2]])]),
    (3, 5, [
        ("a1", False, [0, [1]]),
        ("a2", False, [0, [1]]),
        ("x", False, [0]),
        ("b1", False, [0, [2]]),
        ("b2", False, [0, [2]])]),
    # Choice containing optional parameters.
    (0, 3, [
        ("a", False, [1, [2]]),
        ("b", True, [1, [2]]),
        ("c", False, [1, [2]])]),
    (0, 3, [
        ("a", False, [1, [2]]),
        ("b1", True, [1, [2], 3]),
        ("b2", True, [1, [2], 3])]),
    (1, 3, [
        ("a", False, [1, [2]]),
        ("b1", False, [1, [2], 3]),
        ("b2", True, [1, [2], 3])]),
    # Choices within choices next to choices.
    (3, 14, [
        ("p01", False, [1]),
        ("p02", False, [1, [2], 3]),
        ("p03", False, [1, [2], 3]),
        ("p04", False, [1, [2], 4, 5, 6]),
        ("p05", False, [1, [2], 4, 5, 6, [7]]),
        ("p06", False, [1, [2], 4, 5, 6, [7], [8]]),
        ("p07", False, [1, [2], 4, 5, 6, [7], 9]),
        ("p08", False, [1, [2], 4, 5, 6, [7], 9]),
        ("p09", False, [1, [2], 4, [10], 11]),
        ("p10", False, [1, [2], 4, [10], 11]),
        ("p11", False, [1, [2], 4, [10], 12]),
        ("p12", False, [1, [2], 4, [10], 12]),
        ("p13", False, [1, [2], 4, [10], 12]),
        ("p14", False, [1, [2], 4, [13]])]),
    ))
def test_unwrapped_arg_counts(expect_required, expect_allowed, param_defs):
    """
    Test required & allowed argument count for unwrapped parameters.

    Expected 'param_defs' structure - list of 3-tuples containing the
    following:
      * Parameter name (string).
      * Optional (boolean).
      * Ancestry (list).
        * Contains integers and/or single element lists containing an integer.
          * Integers represent non-choice ancestry items.
          * Single element lists represent choice ancestry items.
        * Integer values represent ancestry item ids - different integer values
          represent separate ancestry items.

    """
    ancestor_map = {}
    params = []
    for param_name, param_optional, param_ancestry_def in param_defs:
        ancestry = []
        for n, id in enumerate(param_ancestry_def):
            is_choice = False
            if id.__class__ is list:
                assert len(id) == 1, "bad test input"
                id = id[0]
                is_choice = True
            try:
                ancestor, ancestry_def = ancestor_map[id]
            except KeyError:
                ancestor = MockAncestor(is_choice)
                ancestor_map[id] = (ancestor, param_ancestry_def[:n])
            else:
                assert ancestor.choice() == is_choice, "bad test input"
                assert ancestry_def == param_ancestry_def[:n], "bad test input"
            ancestry.append(ancestor)
        params.append((param_name, MockParamType(param_optional), ancestry))
    param_processor = MockParamProcessor()
    args = [object() for x in params]
    args_required, args_allowed = suds.argparser.parse_args("w", params, args,
        {}, param_processor.process, False)

    assert args_required == expect_required
    assert args_allowed == expect_allowed
    processed_params = param_processor.params()
    assert len(processed_params) == len(params)
    for expected_param, param, value in zip(params, processed_params, args):
        assert param[0] is expected_param[0]
        assert param[1] is expected_param[1]
        expected_in_choice_context = False
        for x in expected_param[2]:
            if x.choice():
                expected_in_choice_context = True
                break
        assert param[2] == expected_in_choice_context
        assert param[3] is value


def _do_nothing(*args, **kwargs):
    """Do-nothing function used as a callback where needed during testing."""
    pass


def _expect_error(expected_exception, expected_error_text, test_function,
        *args, **kwargs):
    """
    Assert a test function call raises an expected exception.

    Caught exception is considered expected if its string representation
    matches the given expected error text.

    Expected error text may be given directly or as a list/tuple containing
    valid alternatives.

    """
    e = pytest.raises(expected_exception, test_function, *args, **kwargs).value
    try:
        if expected_error_text.__class__ in (list, tuple):
            assert str(e) in expected_error_text
        else:
            assert str(e) == expected_error_text
    finally:
        del e
