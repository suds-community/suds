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
Unit tests related to Suds Python library reply processing.

Implemented using the 'pytest' testing framework.

"""

import testutils
if __name__ == "__main__":
    testutils.run_using_pytest(globals())

import suds

import pytest
from six import itervalues, next, u
from six.moves import http_client

import xml.sax


def test_ACCEPTED_and_NO_CONTENT_status_reported_as_None_with_faults():
    client = testutils.client_from_wsdl(_wsdl__simple_f, faults=True)
    def f(reply, status):
        inject = {"reply": suds.byte_str(reply), "status": status}
        return client.service.f(__inject=inject)
    assert f("", None) is None
    pytest.raises(Exception, f, "", http_client.INTERNAL_SERVER_ERROR)
    assert f("", http_client.ACCEPTED) is None
    assert f("", http_client.NO_CONTENT) is None
    assert f("bla-bla", http_client.ACCEPTED) is None
    assert f("bla-bla", http_client.NO_CONTENT) is None


def test_ACCEPTED_and_NO_CONTENT_status_reported_as_None_without_faults():
    client = testutils.client_from_wsdl(_wsdl__simple_f, faults=False)
    def f(reply, status):
        inject = {"reply": suds.byte_str(reply), "status": status}
        return client.service.f(__inject=inject)
    assert f("", None) is not None
    assert f("", http_client.INTERNAL_SERVER_ERROR) is not None
    assert f("", http_client.ACCEPTED) is None
    assert f("", http_client.NO_CONTENT) is None
    assert f("bla-bla", http_client.ACCEPTED) is None
    assert f("bla-bla", http_client.NO_CONTENT) is None


def test_badly_formed_reply_XML():
    for faults in (True, False):
        client = testutils.client_from_wsdl(_wsdl__simple_f, faults=faults)
        pytest.raises(xml.sax.SAXParseException, client.service.f,
            __inject={"reply": suds.byte_str("bad food")})


#TODO: Update the current restriction type output parameter handling so such
# parameters get converted to the correct Python data type based on the
# restriction's underlying data type.
@pytest.mark.xfail
def test_restriction_data_types():
    client_unnamed = testutils.client_from_wsdl(testutils.wsdl("""\
      <xsd:element name="Elemento">
        <xsd:simpleType>
          <xsd:restriction base="xsd:int">
            <xsd:enumeration value="1"/>
            <xsd:enumeration value="3"/>
            <xsd:enumeration value="5"/>
          </xsd:restriction>
        </xsd:simpleType>
      </xsd:element>""", output="Elemento"))

    client_named = testutils.client_from_wsdl(testutils.wsdl("""\
      <xsd:simpleType name="MyType">
        <xsd:restriction base="xsd:int">
          <xsd:enumeration value="1"/>
          <xsd:enumeration value="3"/>
          <xsd:enumeration value="5"/>
        </xsd:restriction>
      </xsd:simpleType>
      <xsd:element name="Elemento" type="ns:MyType"/>""", output="Elemento"))

    client_twice_restricted = testutils.client_from_wsdl(testutils.wsdl("""\
      <xsd:simpleType name="MyTypeGeneric">
        <xsd:restriction base="xsd:int">
          <xsd:enumeration value="1"/>
          <xsd:enumeration value="2"/>
          <xsd:enumeration value="3"/>
          <xsd:enumeration value="4"/>
          <xsd:enumeration value="5"/>
        </xsd:restriction>
      </xsd:simpleType>
      <xsd:simpleType name="MyType">
        <xsd:restriction base="ns:MyTypeGeneric">
          <xsd:enumeration value="1"/>
          <xsd:enumeration value="3"/>
          <xsd:enumeration value="5"/>
        </xsd:restriction>
      </xsd:simpleType>
      <xsd:element name="Elemento" type="ns:MyType"/>""", output="Elemento"))

    for client in (client_unnamed, client_named, client_twice_restricted):
        response = client.service.f(__inject=dict(reply=suds.byte_str("""\
<?xml version="1.0"?>
<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
  <Body>
    <Elemento xmlns="my-namespace">5</Elemento>
  </Body>
</Envelope>""")))
        assert response.__class__ is int
        assert response == 5


def test_disabling_automated_simple_interface_unwrapping():
    client = testutils.client_from_wsdl(testutils.wsdl("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="Elemento" type="xsd:string"/>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", output="Wrapper"), unwrap=False)
    assert not _isOutputWrapped(client, "f")

    response = client.service.f(__inject=dict(reply=suds.byte_str("""\
<?xml version="1.0"?>
<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
  <Body>
    <Wrapper xmlns="my-namespace">
        <Elemento>La-di-da-da-da</Elemento>
    </Wrapper>
  </Body>
</Envelope>""")))

    assert response.__class__.__name__ == "Wrapper"
    assert len(response.__class__.__bases__) == 1
    assert response.__class__.__bases__[0] is suds.sudsobject.Object
    assert response.Elemento.__class__ is suds.sax.text.Text
    assert response.Elemento == "La-di-da-da-da"


def test_empty_reply():
    client = testutils.client_from_wsdl(_wsdl__simple_f, faults=False)
    def f(status=None, description=None):
        inject = dict(reply=suds.byte_str(), status=status,
            description=description)
        return client.service.f(__inject=inject)
    status, reason = f()
    assert status == http_client.OK
    assert reason is None
    status, reason = f(http_client.OK)
    assert status == http_client.OK
    assert reason is None
    status, reason = f(http_client.INTERNAL_SERVER_ERROR)
    assert status == http_client.INTERNAL_SERVER_ERROR
    assert reason == "injected reply"
    status, reason = f(http_client.FORBIDDEN)
    assert status == http_client.FORBIDDEN
    assert reason == "injected reply"
    status, reason = f(http_client.FORBIDDEN, "kwack")
    assert status == http_client.FORBIDDEN
    assert reason == "kwack"


def test_fault_reply_with_unicode_faultstring(monkeypatch):
    monkeypatch.delitem(locals(), "e", False)

    unicode_string = u("\u20AC Jurko Gospodneti\u0107 "
        "\u010C\u0106\u017D\u0160\u0110"
        "\u010D\u0107\u017E\u0161\u0111")
    fault_xml = suds.byte_str(u("""\
<?xml version="1.0"?>
<env:Envelope xmlns:env="http://schemas.xmlsoap.org/soap/envelope/">
  <env:Body>
    <env:Fault>
      <faultcode>env:Client</faultcode>
      <faultstring>%s</faultstring>
    </env:Fault>
  </env:Body>
</env:Envelope>
""") % (unicode_string,))

    client = testutils.client_from_wsdl(_wsdl__simple_f, faults=True)
    inject = dict(reply=fault_xml, status=http_client.INTERNAL_SERVER_ERROR)
    e = pytest.raises(suds.WebFault, client.service.f, __inject=inject).value
    try:
        assert e.fault.faultstring == unicode_string
        assert e.document.__class__ is suds.sax.document.Document
    finally:
        del e  # explicitly break circular reference chain in Python 3

    client = testutils.client_from_wsdl(_wsdl__simple_f, faults=False)
    status, fault = client.service.f(__inject=dict(reply=fault_xml,
        status=http_client.INTERNAL_SERVER_ERROR))
    assert status == http_client.INTERNAL_SERVER_ERROR
    assert fault.faultstring == unicode_string


def test_invalid_fault_namespace(monkeypatch):
    monkeypatch.delitem(locals(), "e", False)

    fault_xml = suds.byte_str("""\
<?xml version="1.0"?>
<env:Envelope xmlns:env="http://schemas.xmlsoap.org/soap/envelope/" xmlns:p="x">
  <env:Body>
    <p:Fault>
      <faultcode>env:Client</faultcode>
      <faultstring>Dummy error.</faultstring>
      <detail>
        <errorcode>ultimate</errorcode>
      </detail>
    </p:Fault>
  </env:Body>
</env:Envelope>
""")
    client = testutils.client_from_wsdl(_wsdl__simple_f, faults=False)
    inject = dict(reply=fault_xml, status=http_client.OK)
    e = pytest.raises(Exception, client.service.f, __inject=inject).value
    try:
        assert e.__class__ is Exception
        assert str(e) == "<faultcode/> not mapped to message part"
    finally:
        del e  # explicitly break circular reference chain in Python 3

    for http_status in (http_client.INTERNAL_SERVER_ERROR,
        http_client.PAYMENT_REQUIRED):
        status, reason = client.service.f(__inject=dict(reply=fault_xml,
            status=http_status, description="trla baba lan"))
        assert status == http_status
        assert reason == "trla baba lan"


def test_missing_wrapper_response():
    """
    Suds library's automatic structure unwrapping should not be applied to
    interpreting received SOAP Response XML.

    """
    client = testutils.client_from_wsdl(testutils.wsdl("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="fResponse" type="xsd:string"/>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", output="Wrapper"))
    assert _isOutputWrapped(client, "f")

    response_with_missing_wrapper = client.service.f(__inject=dict(
        reply=suds.byte_str("""<?xml version="1.0"?>
<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
  <Body>
    <fResponse xmlns="my-namespace">Anything</fResponse>
  </Body>
</Envelope>""")))
    assert response_with_missing_wrapper is None


def test_reply_error_with_detail_with_fault(monkeypatch):
    monkeypatch.delitem(locals(), "e", False)

    client = testutils.client_from_wsdl(_wsdl__simple_f, faults=True)

    for http_status in (http_client.OK, http_client.INTERNAL_SERVER_ERROR):
        inject = dict(reply=_fault_reply__with_detail, status=http_status)
        e = pytest.raises(suds.WebFault, client.service.f, __inject=inject)
        try:
            e = e.value
            _test_fault(e.fault, True)
            assert e.document.__class__ is suds.sax.document.Document
            assert str(e) == "Server raised fault: 'Dummy error.'"
        finally:
            del e  # explicitly break circular reference chain in Python 3

    inject = dict(reply=_fault_reply__with_detail,
        status=http_client.BAD_REQUEST, description="quack-quack")
    e = pytest.raises(Exception, client.service.f, __inject=inject).value
    try:
        assert e.__class__ is Exception
        assert e.args[0][0] == http_client.BAD_REQUEST
        assert e.args[0][1] == "quack-quack"
    finally:
        del e  # explicitly break circular reference chain in Python 3


def test_reply_error_with_detail_without_fault():
    client = testutils.client_from_wsdl(_wsdl__simple_f, faults=False)

    for http_status in (http_client.OK, http_client.INTERNAL_SERVER_ERROR):
        status, fault = client.service.f(__inject=dict(
            reply=_fault_reply__with_detail, status=http_status))
        assert status == http_client.INTERNAL_SERVER_ERROR
        _test_fault(fault, True)

    status, fault = client.service.f(__inject=dict(
        reply=_fault_reply__with_detail, status=http_client.BAD_REQUEST))
    assert status == http_client.BAD_REQUEST
    assert fault == "injected reply"

    status, fault = client.service.f(__inject=dict(
        reply=_fault_reply__with_detail, status=http_client.BAD_REQUEST,
        description="haleluja"))
    assert status == http_client.BAD_REQUEST
    assert fault == "haleluja"


def test_reply_error_without_detail_with_fault(monkeypatch):
    monkeypatch.delitem(locals(), "e", False)

    client = testutils.client_from_wsdl(_wsdl__simple_f, faults=True)

    for http_status in (http_client.OK, http_client.INTERNAL_SERVER_ERROR):
        inject = dict(reply=_fault_reply__without_detail, status=http_status)
        e = pytest.raises(suds.WebFault, client.service.f, __inject=inject)
        try:
            e = e.value
            _test_fault(e.fault, False)
            assert e.document.__class__ is suds.sax.document.Document
            assert str(e) == "Server raised fault: 'Dummy error.'"
        finally:
            del e  # explicitly break circular reference chain in Python 3

    inject = dict(reply=_fault_reply__with_detail,
        status=http_client.BAD_REQUEST, description="quack-quack")
    e = pytest.raises(Exception, client.service.f, __inject=inject).value
    try:
        assert e.__class__ is Exception
        assert e.args[0][0] == http_client.BAD_REQUEST
        assert e.args[0][1] == "quack-quack"
    finally:
        del e  # explicitly break circular reference chain in Python 3


def test_reply_error_without_detail_without_fault():
    client = testutils.client_from_wsdl(_wsdl__simple_f, faults=False)

    for http_status in (http_client.OK, http_client.INTERNAL_SERVER_ERROR):
        status, fault = client.service.f(__inject=dict(
            reply=_fault_reply__without_detail, status=http_status))
        assert status == http_client.INTERNAL_SERVER_ERROR
        _test_fault(fault, False)

    status, fault = client.service.f(__inject=dict(
        reply=_fault_reply__without_detail, status=http_client.BAD_REQUEST,
        description="kung-fu-fui"))
    assert status == http_client.BAD_REQUEST
    assert fault == "kung-fu-fui"


def test_simple_bare_and_wrapped_output():
    # Prepare web service proxies.
    client_bare = testutils.client_from_wsdl(testutils.wsdl("""\
      <xsd:element name="fResponse" type="xsd:string"/>""",
        output="fResponse"))
    client_wrapped = testutils.client_from_wsdl(testutils.wsdl("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="fResponse" type="xsd:string"/>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", output="Wrapper"))

    # Make sure suds library inteprets our WSDL definitions as wrapped or bare
    # output interfaces as expected.
    assert not _isOutputWrapped(client_bare, "f")
    assert _isOutputWrapped(client_wrapped, "f")

    # Both bare & wrapped single parameter output web service operation results
    # get presented the same way even though the wrapped one actually has an
    # extra wrapper element around its received output data.
    data = "The meaning of life."
    def get_response(client, x):
        return client.service.f(__inject=dict(reply=suds.byte_str(x)))

    response_bare = get_response(client_bare, """<?xml version="1.0"?>
<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
  <Body>
    <fResponse xmlns="my-namespace">%s</fResponse>
  </Body>
</Envelope>""" % (data,))
    assert response_bare.__class__ is suds.sax.text.Text
    assert response_bare == data

    response_wrapped = get_response(client_wrapped, """<?xml version="1.0"?>
<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
  <Body>
    <Wrapper xmlns="my-namespace">
      <fResponse>%s</fResponse>
    </Wrapper>
  </Body>
</Envelope>""" % (data,))
    assert response_wrapped.__class__ is suds.sax.text.Text
    assert response_wrapped == data


def test_allow_unknown_message_parts():
    # Prepare web service proxies.
    client = testutils.client_from_wsdl(testutils.wsdl("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="fResponse" type="xsd:string"/>
            <xsd:element name="gResponse" type="xsd:string"/>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", output="Wrapper"))

    client.set_options(allowUnknownMessageParts=True)

    data = "The meaning of life."
    def get_response(client, x):
        return client.service.f(__inject=dict(reply=suds.byte_str(x)))

    response = get_response(client, """<?xml version="1.0"?>
<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
  <Body>
    <Wrapper xmlns="my-namespace">
      <fResponse>%s</fResponse>
      <gResponse></gResponse>
      <hResponse></hResponse>
    </Wrapper>
  </Body>
</Envelope>""" % (data,))
    assert response.fResponse == data
    assert response.gResponse == None
    # hResponse ignored


def test_wrapped_sequence_output():
    client = testutils.client_from_wsdl(testutils.wsdl("""\
      <xsd:element name="Wrapper">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="result1" type="xsd:string"/>
            <xsd:element name="result2" type="xsd:string"/>
            <xsd:element name="result3" type="xsd:string"/>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", output="Wrapper"))
    assert _isOutputWrapped(client, "f")

    response = client.service.f(__inject=dict(reply=suds.byte_str("""\
<?xml version="1.0"?>
<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
  <Body>
    <Wrapper xmlns="my-namespace">
        <result1>Uno</result1>
        <result2>Due</result2>
        <result3>Tre</result3>
    </Wrapper>
  </Body>
</Envelope>""")))

    # Composite replies always get unmarshalled as a dynamically constructed
    # class named 'reply'.
    assert len(response.__class__.__bases__) == 1
    assert response.__class__.__name__ == "reply"
    assert response.__class__.__bases__[0] is suds.sudsobject.Object

    # Check response content.
    assert len(response) == 3
    assert response.result1 == "Uno"
    assert response.result2 == "Due"
    assert response.result3 == "Tre"
    assert response.result1.__class__ is suds.sax.text.Text
    assert response.result2.__class__ is suds.sax.text.Text
    assert response.result3.__class__ is suds.sax.text.Text


def _attributes(object):
    result = set()
    for x in object:
        result.add(x[0])
    return result


def _isOutputWrapped(client, method_name):
    assert len(client.wsdl.bindings) == 1
    binding = next(itervalues(client.wsdl.bindings))
    operation = binding.operations[method_name]
    return operation.soap.output.body.wrapped


def _test_fault(fault, has_detail):
    assert fault.faultcode == "env:Client"
    assert fault.faultstring == "Dummy error."
    assert hasattr(fault, "detail") == has_detail
    assert not has_detail or fault.detail.errorcode == "ultimate"
    assert not hasattr(fault, "nonexisting")
    expected_attributes = set(("faultcode", "faultstring"))
    if has_detail:
        expected_attributes.add("detail")
    assert _attributes(fault) == expected_attributes
    assert not has_detail or _attributes(fault.detail) == set(("errorcode",))


_fault_reply__with_detail = suds.byte_str("""\
<?xml version="1.0"?>
<env:Envelope xmlns:env="http://schemas.xmlsoap.org/soap/envelope/">
  <env:Body>
    <env:Fault>
      <faultcode>env:Client</faultcode>
      <faultstring>Dummy error.</faultstring>
      <detail>
        <errorcode>ultimate</errorcode>
      </detail>
    </env:Fault>
  </env:Body>
</env:Envelope>
""")

_fault_reply__without_detail = suds.byte_str("""\
<?xml version="1.0"?>
<env:Envelope xmlns:env="http://schemas.xmlsoap.org/soap/envelope/">
  <env:Body>
    <env:Fault>
      <faultcode>env:Client</faultcode>
      <faultstring>Dummy error.</faultstring>
    </env:Fault>
  </env:Body>
</env:Envelope>
""")

_wsdl__simple_f = testutils.wsdl("""\
      <xsd:element name="fResponse">
        <xsd:complexType>
          <xsd:sequence>
            <xsd:element name="output_i" type="xsd:integer"/>
            <xsd:element name="output_s" type="xsd:string"/>
          </xsd:sequence>
        </xsd:complexType>
      </xsd:element>""", output="fResponse", operation_name="f")
