# This program is free software; you can redistribute it and/or modify
# it under the terms of the (LGPL) GNU Lesser General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library Lesser General Public License for more details at
# ( http://www.gnu.org/licenses/lgpl.html ).
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
# written by: Jeff Ortel ( jortel@redhat.com )

import suds.client
import suds.store

import logging
import sys


def client_from_wsdl(wsdl_content, *args, **kwargs):
    """
    Constructs a non-caching suds Client based on the given WSDL content.

      The wsdl_content is expected to be a raw byte string and not a unicode
    string. This simple structure suits us fine here because XML content holds
    its own embedded encoding identification ('utf-8' if not specified
    explicitly).

      Stores the content directly inside the suds library internal document
    store under a hard-coded id to avoid having to load the data from a
    temporary file.

      Caveats:
        * All files stored under the same id so each new local file overwrites
          the previous one.
        * We need to explicitly disable caching here or otherwise, because we
          use the same id for all our local WSDL documents, suds would always
          reuse the first such local document from its cache.

    """
    # Idea for an alternative implementation:
    #   Custom suds.cache.Cache subclass that would know how to access our
    # locally stored documents or at least not cache them if we are storing
    # them inside the suds library DocumentStore. Not difficult, allows us to
    # have per-client instead of global configuration & allows us to support
    # other cache types but certainly not as short as the current
    # implementation.
    assert wsdl_content.__class__ is suds.byte_str_class
    testFileId = "whatchamacallit"
    suds.store.DocumentStore.store[testFileId] = wsdl_content
    kwargs["cache"] = None
    return suds.client.Client("suds://" + testFileId, *args, **kwargs)


def setup_logging():
    if sys.version_info < (2, 5):
        fmt = '%(asctime)s [%(levelname)s] @%(filename)s:%(lineno)d\n%(message)s\n'
    else:
        fmt = '%(asctime)s [%(levelname)s] %(funcName)s() @%(filename)s:%(lineno)d\n%(message)s\n'
    logging.basicConfig(level=logging.INFO, format=fmt)


def wsdl_input(schema_content, *args):
    """
      Returns a WSDL schema used in different suds library tests, defining a
    single operation named f, taking an externally specified input structure
    and returning no output.

      The first input parameter is the schema part of the WSDL, the rest of the
    parameters identify top level input parameter elements.

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
%s
    </xsd:schema>
  </wsdl:types>
  <wsdl:message name="fRequestMessage">""" % schema_content]

    assert len(args) >= 1
    for arg in args:
        wsdl.append("""\
    <wsdl:part name="parameters" element="ns:%s" />""" % arg)

    wsdl.append("""\
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
      <soap:operation soapAction="f" style="document" />
      <wsdl:input><soap:body use="literal" /></wsdl:input>
    </wsdl:operation>
  </wsdl:binding>
  <wsdl:service name="dummy">
    <wsdl:port name="dummy" binding="ns:dummy">
      <soap:address location="unga-bunga-location" />
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>
""")

    return suds.byte_str("\n".join(wsdl))


def wsdl_output(schema_content, *args):
    """
      Returns a WSDL schema used in different suds library tests, defining a
    single operation named f, taking no input and returning an externally
    specified output structure.

      The first input parameter is the schema part of the WSDL, the rest of the
    parameters identify top level output parameter elements.

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
%s
    </xsd:schema>
  </wsdl:types>
  <wsdl:message name="fResponseMessage">""" % schema_content]

    assert len(args) >= 1
    for arg in args:
        wsdl.append("""\
    <wsdl:part name="parameters" element="ns:%s" />""" % arg)

    wsdl.append("""\
  </wsdl:message>
  <wsdl:portType name="dummyPortType">
    <wsdl:operation name="f">
      <wsdl:output message="ns:fResponseMessage" />
    </wsdl:operation>
  </wsdl:portType>
  <wsdl:binding name="dummy" type="ns:dummyPortType">
    <soap:binding style="document"
    transport="http://schemas.xmlsoap.org/soap/http" />
    <wsdl:operation name="f">
      <soap:operation soapAction="f" style="document" />
      <wsdl:output><soap:body use="literal" /></wsdl:output>
    </wsdl:operation>
  </wsdl:binding>
  <wsdl:service name="dummy">
    <wsdl:port name="dummy" binding="ns:dummy">
      <soap:address location="unga-bunga-location" />
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>
""")

    return suds.byte_str("\n".join(wsdl))
