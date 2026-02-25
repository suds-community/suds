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

import xml.etree.ElementTree as ET

import testutils

if __name__ == "__main__":
    testutils.run_using_pytest(globals())

import suds
import suds.store

import pytest

def test_string_preserved():
    def client(xsd, *input):
        wsdl = testutils.wsdl(xsd, input=input, xsd_target_namespace="toolyan",
            operation_name="f")
        return testutils.client_from_wsdl(wsdl, nosend=True, prettyxml=True)

    client_bare_single = client("""<xsd:element name="Elemento" type="xsd:string"/>""", "Elemento")

    data = "Maestro n=\n r=\r rn=\r\n tada!"
    def call_single(c):
        return c.service.f(data)

    msg = call_single(client_bare_single)
    print(msg.envelope)
    
    root = ET.fromstring(msg.envelope)
    print(root)

    namespaces = {'SOAP-ENV': 'http://schemas.xmlsoap.org/soap/envelope/','ns0':"http://schemas.xmlsoap.org/soap/envelope/", 'ns1' : 'toolyan'} # add more as needed
    assert root.find("ns0:Body/ns1:Elemento", namespaces).text == data
