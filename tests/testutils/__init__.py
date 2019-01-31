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
Package containing different utilities used for suds project testing.

"""

import suds.client
import suds.store

import six

import os
import subprocess
import sys
from .compare_sax import CompareSAX

def _assert_request_content(request, expected_xml):
    CompareSAX.data2data(request.envelope, expected_xml)


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

      Uses a locally created empty document store unless one is provided
    externally using the 'documentStore' keyword argument.

      Explicitly disables caching or otherwise, because we use the same
    hardcoded id for our main WSDL document, suds would always reuse the first
    such local document from its cache instead of fetching it from our document
    store.

    """
    assert wsdl_content.__class__ is suds.byte_str_class, "bad test data"
    store = kwargs.get("documentStore")
    if store is None:
        store = suds.store.DocumentStore()
        kwargs.update(documentStore=store)
    test_file_id = "whatchamacallit"
    store.update({test_file_id: wsdl_content})
    kwargs.update(cache=None)
    return suds.client.Client("suds://" + test_file_id, *args, **kwargs)


def run_test_process(script):
    """
    Runs the given Python test script as a separate process.

    Expects the script to return an exit code 0 and output nothing on either
    stdout or stderr output streams.

    """
    popen = subprocess.Popen([sys.executable], stdin=subprocess.PIPE,
        stderr=subprocess.PIPE, stdout=subprocess.PIPE, cwd=script.dirname,
        universal_newlines=True)
    sys_path = sys.path
    for i in range(len(sys_path)):
        if not sys_path[i]:
            sys_path[i] = os.getcwd()
    out, err = popen.communicate("""\
import sys
sys.path = %(sys.path)s
import suds
if suds.__version__ != %(suds.__version__)r:
    print("Unexpected suds version imported - '%%s'." %% (suds.__version__))
    sys.exit(-2)

if sys.version_info >= (3, 0):
    def exec_file(x):
        e = getattr(__builtins__, "exec")
        return e(open(x).read(), globals(), globals())
else:
    exec_file = execfile
exec_file(%(script)r)
""" % {"suds.__version__": suds.__version__,
    "script": script.basename,
    "sys.path": sys_path})
    if popen.returncode != 0 or err or out:
        if popen.returncode != 0:
            print("Test process exit code: %d" % (popen.returncode,))
        if out:
            print("Test process stdout:")
            print(out)
        if err:
            print("Test process stderr:")
            print(err)
        import pytest
        pytest.fail("Test subprocess failed.")


def run_using_pytest(caller_globals):
    """Run the caller test script using the pytest testing framework."""
    import sys
    # Trick setuptools into not recognizing we are referencing __file__ here.
    # If setuptools detects __file__ usage in a module, any package containing
    # this module will be installed as an actual folder instead of a zipped
    # archive. This __file__ usage is safe since it is used only when a script
    # has been run directly, and that can not be done from a zipped package
    # archive.
    filename = caller_globals.get("file".join(["__"] * 2))
    if not filename:
        sys.exit("Internal error: can not determine test script name.")
    try:
        import pytest
    except ImportError:
        filename = filename or "<unknown-script>"
        sys.exit("'py.test' unit testing framework not available. Can not run "
            "'%s' directly as a script." % (filename,))
    exit_code = pytest.main(["--pyargs", filename] + sys.argv[1:])
    sys.exit(exit_code)


def wsdl(schema_content, input=None, output=None, operation_name="f",
        wsdl_target_namespace="my-wsdl-namespace",
        xsd_target_namespace="my-xsd-namespace",
        web_service_URL="protocol://unga-bunga-location"):
    """
    Returns WSDL schema content used in different suds library tests.

    Defines a single operation taking an externally specified input structure
    and returning an externally defined output structure.

    Constructed WSDL schema's XML namespace prefixes:
      * my_wsdl - the WSDL schema's target namespace.
      * my_xsd - the embedded XSD schema's target namespace.

    input/output parameters accept the following values:
      * None - operation has no input/output message.
      * list/tuple - operation has an input/output message consisting of
        message parts referencing top-level XSD schema elements with the given
        names.
      * Otherwise operation has an input/output message consisting of a single
        message part referencing a top-level XSD schema element with the given
        name.

    """
    assert isinstance(schema_content, six.string_types)

    has_input = input is not None
    has_output = output is not None

    wsdl = ["""\
<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="%(wsdl_target_namespace)s"
    xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
    xmlns:my_wsdl="%(wsdl_target_namespace)s"
    xmlns:my_xsd="%(xsd_target_namespace)s"
    xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/">
  <wsdl:types>
    <xsd:schema targetNamespace="%(xsd_target_namespace)s"
        elementFormDefault="qualified"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema">
%(schema_content)s
    </xsd:schema>
  </wsdl:types>""" % dict(schema_content=schema_content,
        wsdl_target_namespace=wsdl_target_namespace,
        xsd_target_namespace=xsd_target_namespace)]

    if has_input:
        if input.__class__ not in (list, tuple):
            input = [input]
        wsdl.append("""\
  <wsdl:message name="fRequestMessage">""")
        for element in input:
            wsdl.append("""\
    <wsdl:part name="parameters" element="my_xsd:%s" />""" % (element,))
        wsdl.append("""\
  </wsdl:message>""")

    if has_output:
        if output.__class__ not in (list, tuple):
            output = [output]
        wsdl.append("""\
  <wsdl:message name="fResponseMessage">""")
        for element in output:
            wsdl.append("""\
    <wsdl:part name="parameters" element="my_xsd:%s" />""" % (element,))
        wsdl.append("""\
  </wsdl:message>""")

    wsdl.append("""\
  <wsdl:portType name="dummyPortType">
    <wsdl:operation name="%s">""" % (operation_name,))

    if has_input:
        wsdl.append("""\
      <wsdl:input message="my_wsdl:fRequestMessage" />""")
    if has_output:
        wsdl.append("""\
      <wsdl:output message="my_wsdl:fResponseMessage" />""")

    wsdl.append("""\
    </wsdl:operation>
  </wsdl:portType>
  <wsdl:binding name="dummy" type="my_wsdl:dummyPortType">
    <soap:binding style="document"
        transport="http://schemas.xmlsoap.org/soap/http" />
    <wsdl:operation name="%s">
      <soap:operation soapAction="my-soap-action" style="document" />""" %
        (operation_name,))

    if has_input:
        wsdl.append("""\
      <wsdl:input><soap:body use="literal" /></wsdl:input>""")
    if has_output:
        wsdl.append("""\
      <wsdl:output><soap:body use="literal" /></wsdl:output>""")

    wsdl.append("""\
    </wsdl:operation>
  </wsdl:binding>
  <wsdl:service name="dummy">
    <wsdl:port name="dummy" binding="my_wsdl:dummy">
      <soap:address location="%s" />
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>
""" % (web_service_URL,))

    return suds.byte_str("\n".join(wsdl))
