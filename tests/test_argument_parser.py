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
