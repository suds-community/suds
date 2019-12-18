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
Suds Python library suds.client.Client related unit tests.

Implemented using the 'pytest' testing framework.

"""

import testutils
if __name__ == "__main__":
    testutils.run_using_pytest(globals())

import suds
import suds.cache
import suds.store
import suds.transport
import suds.transport.https

import pytest
from six import b, binary_type, iteritems, itervalues, next
from six.moves import http_client


class MyException(Exception):
    """Local exception class used in this testing module."""
    pass


class MockCache(suds.cache.Cache):
    """
    Mock cache structure used in the tests in this module.

    Implements an in-memory cache and allows the test code to test the exact
    triggered cache operations. May be configured to allow or not adding
    additional entries to the cache, thus allowing our tests complete control
    over the cache's content.

    """

    """Enumeration for specific mock operation configurations."""
    ALLOW = 0
    IGNORE = 1
    FAIL = 2

    def __init__(self):
        self.mock_data = {}
        self.mock_log = []
        self.mock_put_config = MockCache.ALLOW
        super(MockCache, self).__init__()

    def clear(self):
        self.mock_log.append(("clear", []))
        pytest.fail("Unexpected MockCache.clear() operation call.")

    def get(self, id):
        self.mock_log.append(("get", [id]))
        return self.mock_data.get(id, None)

    def purge(self, id):
        self.mock_log.append(("purge", [id]))
        pytest.fail("Unexpected MockCache.purge() operation call.")

    def put(self, id, object):
        self.mock_log.append(("put", [id, object]))
        if self.mock_put_config == MockCache.FAIL:
            pytest.fail("Unexpected MockCache.put() operation call.")
        if self.mock_put_config == MockCache.ALLOW:
            self.mock_data[id] = object
        else:
            assert self.mock_put_config == MockCache.IGNORE


class MockDocumentStore(suds.store.DocumentStore):
    """Mock DocumentStore tracking all of its operations."""

    def __init__(self, *args, **kwargs):
        self.mock_log = []
        self.mock_fail = kwargs.pop("mock_fail", False)
        super(MockDocumentStore, self).__init__(*args, **kwargs)

    def open(self, url):
        self.mock_log.append(url)
        if self.mock_fail:
            raise MyException
        return super(MockDocumentStore, self).open(url)

    def reset(self):
        self.mock_log = []


class MockTransport(suds.transport.Transport):
    """
    Mock Transport used by the tests implemented in this module.

    Allows the tests to check which transport operations got triggered and to
    control what each of them returns.

    open/send output data may be given either as a single value or a list of
    values to be used in order. Specifying a single value is a shortcut with
    the same semantics as specifying a single element list containing that
    value. Each of the value items may be either a simple byte string to be
    returned or an Exception subclass or instance indicating an exception to be
    raised from a particular operation call.

    """

    def __init__(self, open_data=None, send_data=None):
        if open_data is None:
            open_data = []
        elif open_data.__class__ is not list:
            open_data = [open_data]
        if send_data is None:
            send_data = []
        elif send_data.__class__ is not list:
            send_data = [send_data]
        self.mock_log = []
        self.mock_requests = []
        self.mock_open_data = open_data
        self.mock_send_data = send_data
        super(MockTransport, self).__init__()

    def open(self, request):
        self.mock_log.append(("open", [request.url]))
        self.mock_requests.append(request)
        if not self.mock_open_data:
            pytest.fail("Unexpected MockTransport.open() operation call.")
        result = self.__next_operation_result(self.mock_open_data)
        return suds.BytesIO(result)

    def send(self, request):
        self.mock_log.append(("send", [request.url, request.message]))
        self.mock_requests.append(request)
        if not self.mock_send_data:
            pytest.fail("Unexpected MockTransport.send() operation call.")
        status = http_client.OK
        headers = {}
        data = self.__next_operation_result(self.mock_send_data)
        return suds.transport.Reply(status, headers, data)

    @staticmethod
    def __next_operation_result(data_list):
        value = data_list.pop(0)
        if isinstance(value, Exception):
            raise value
        if value.__class__ is type and issubclass(value, Exception):
            raise value()
        assert value.__class__ is binary_type, "bad test data"
        return value


# Test data used in different tests in this module testing suds WSDL schema
# import implementation.
wsdl_imported_wsdl_namespace = "goodbye"

def wsdl_imported_format(schema_content="",
        target_namespace=wsdl_imported_wsdl_namespace,
        target_xsd_namespace="ice-scream"):
    return b("""\
<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="%(tns)s"
    xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
    xmlns:tns="%(tns)s"
    xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/">
  <wsdl:types>
    <xsd:schema targetNamespace="%(tns_xsd)s"
        elementFormDefault="qualified"
        attributeFormDefault="unqualified"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema">
%(schema_content)s
    </xsd:schema>
  </wsdl:types>
  <wsdl:portType name="dummyPortType">
    <wsdl:operation name="f"/>
  </wsdl:portType>
  <wsdl:binding name="dummy" type="tns:dummyPortType">
    <soap:binding style="document"
        transport="http://schemas.xmlsoap.org/soap/http"/>
    <wsdl:operation name="f">
      <soap:operation soapAction="my-soap-action" style="document"/>
    </wsdl:operation>
  </wsdl:binding>
</wsdl:definitions>""" % dict(schema_content=schema_content,
        tns_xsd=target_xsd_namespace, tns=target_namespace))

def wsdl_import_wrapper_format(url_imported,
        imported_reference_ns=wsdl_imported_wsdl_namespace,
        target_namespace="hello"):
    return b("""\
<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="%(tns)s"
    xmlns:imported_reference_ns="%(imported_reference_ns)s"
    xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
    xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/">
  <wsdl:import namespace="%(imported_ns)s" location="%(url_imported)s"/>
  <wsdl:service name="dummy">
    <wsdl:port name="dummy" binding="imported_reference_ns:dummy">
      <soap:address location="unga-bunga-location"/>
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>""" % dict(imported_ns=wsdl_imported_wsdl_namespace,
        imported_reference_ns=imported_reference_ns,
        tns=target_namespace,
        url_imported=url_imported))


# Test URL data used by several tests in this test module.
test_URL_data = (
    "sudo://make-me-a-sammich",
    "http://my little URL",
    "https://my little URL",
    "xxx://my little URL",
    "xxx:my little URL",
    "xxx:")


class TestCacheStoreTransportUsage:
    """
    suds.client.Client cache/store/transport component usage interaction tests.

    """

    class TestCachedWSDLObjectUsage:
        """
        Using a WSDL object read from the cache should not attempt to fetch any
        of its referenced external documents from either the cache, the
        document store or using the registered transport.

        """

        def test_avoid_imported_WSDL_fetching(self):
            # Prepare data.
            url_imported = "suds://wsdl_imported"
            wsdl_import_wrapper = wsdl_import_wrapper_format(url_imported)
            wsdl_imported = wsdl_imported_format()

            # Add to cache.
            cache = MockCache()
            store1 = MockDocumentStore(wsdl=wsdl_import_wrapper,
                wsdl_imported=wsdl_imported)
            c1 = suds.client.Client("suds://wsdl", cachingpolicy=1,
                cache=cache, documentStore=store1, transport=MockTransport())
            assert store1.mock_log == ["suds://wsdl", "suds://wsdl_imported"]
            assert len(cache.mock_data) == 1
            wsdl_object_id, wsdl_object = next(iteritems(cache.mock_data))
            assert wsdl_object.__class__ is suds.wsdl.Definitions

            # Reuse from cache.
            cache.mock_log = []
            store2 = MockDocumentStore(wsdl=wsdl_import_wrapper)
            c2 = suds.client.Client("suds://wsdl", cachingpolicy=1,
                cache=cache, documentStore=store2, transport=MockTransport())
            assert cache.mock_log == [("get", [wsdl_object_id])]
            assert store2.mock_log == []

        def test_avoid_external_XSD_fetching(self):
            # Prepare document content.
            xsd_target_namespace = "balancana"
            wsdl = testutils.wsdl("""\
              <xsd:import schemaLocation="suds://imported_xsd"/>
              <xsd:include schemaLocation="suds://included_xsd"/>""",
                xsd_target_namespace=xsd_target_namespace)
            external_xsd_format = """\
<?xml version='1.0' encoding='UTF-8'?>
<schema xmlns="http://www.w3.org/2001/XMLSchema">
    <element name="external%d" type="string"/>
</schema>"""
            external_xsd1 = b(external_xsd_format % (1,))
            external_xsd2 = b(external_xsd_format % (2,))

            # Add to cache.
            cache = MockCache()
            store1 = MockDocumentStore(wsdl=wsdl, imported_xsd=external_xsd1,
                included_xsd=external_xsd2)
            c1 = suds.client.Client("suds://wsdl", cachingpolicy=1,
                cache=cache, documentStore=store1, transport=MockTransport())
            assert store1.mock_log == ["suds://wsdl", "suds://imported_xsd",
                "suds://included_xsd"]
            assert len(cache.mock_data) == 1
            wsdl_object_id, wsdl_object = next(iteritems(cache.mock_data))
            assert wsdl_object.__class__ is suds.wsdl.Definitions

            # Reuse from cache.
            cache.mock_log = []
            store2 = MockDocumentStore(wsdl=wsdl)
            c2 = suds.client.Client("suds://wsdl", cachingpolicy=1,
                cache=cache, documentStore=store2, transport=MockTransport())
            assert cache.mock_log == [("get", [wsdl_object_id])]
            assert store2.mock_log == []

    @pytest.mark.parametrize("importing_WSDL_cached", (False, True))
    def test_importing_WSDL_from_cache_avoids_store_avoids_transport(self,
            importing_WSDL_cached):
        """
        When a requested WSDL schema is located in the client's cache, it
        should be read from there instead of fetching its data from the
        client's document store or using its registered transport.

        When it is is not located in the cache but can be found in the client's
        document store, it should be fetched from there but not using the
        client's registered transport.

        Note that this test makes sense only when caching raw XML documents
        (cachingpolicy == 0) and not when caching final WSDL objects
        (cachingpolicy == 1).

        """
        # Prepare test data.
        url_imported = "suds://wsdl_imported"
        imported_xsd_namespace = "imported WSDL's XSD namespace"
        wsdl_import_wrapper = wsdl_import_wrapper_format(url_imported)
        wsdl_imported = wsdl_imported_format(
            '<xsd:element name="Pistachio" type="xsd:string"/>',
            target_xsd_namespace=imported_xsd_namespace)
        wsdl_imported_element_id = ("Pistachio", imported_xsd_namespace)

        # Add to cache, making sure the imported WSDL schema is read from the
        # document store and not fetched using the client's registered
        # transport.
        cache = MockCache()
        store1 = MockDocumentStore(wsdl=wsdl_import_wrapper,
            wsdl_imported=wsdl_imported)
        c1 = suds.client.Client("suds://wsdl", cachingpolicy=0, cache=cache,
            documentStore=store1, transport=MockTransport())
        assert [x for x, y in cache.mock_log] == ["get", "put"] * 2
        id_wsdl = cache.mock_log[0][1][0]
        assert cache.mock_log[1][1][0] == id_wsdl
        id_wsdl_imported = cache.mock_log[2][1][0]
        assert cache.mock_log[3][1][0] == id_wsdl_imported
        assert id_wsdl_imported != id_wsdl
        assert store1.mock_log == ["suds://wsdl", "suds://wsdl_imported"]
        assert len(cache.mock_data) == 2
        wsdl_imported_document = cache.mock_data[id_wsdl_imported]
        cached_definitions_element = wsdl_imported_document.root().children[0]
        cached_schema_element = cached_definitions_element.children[0]
        cached_external_element = cached_schema_element.children[0]
        schema = c1.wsdl.schema
        external_element = schema.elements[wsdl_imported_element_id].root
        assert cached_external_element is external_element

        # Import the WSDL schema from the cache without fetching it using the
        # document store or the transport.
        cache.mock_log = []
        if importing_WSDL_cached:
            cache.mock_put_config = MockCache.FAIL
            store2 = MockDocumentStore(mock_fail=True)
        else:
            del cache.mock_data[id_wsdl]
            assert len(cache.mock_data) == 1
            store2 = MockDocumentStore(wsdl=wsdl_import_wrapper)
        c2 = suds.client.Client("suds://wsdl", cachingpolicy=0, cache=cache,
            documentStore=store2, transport=MockTransport())
        expected_cache_operations = [("get", id_wsdl)]
        if not importing_WSDL_cached:
            expected_cache_operations.append(("put", id_wsdl))
        expected_cache_operations.append(("get", id_wsdl_imported))
        cache_operations = [(x, y[0]) for x, y in cache.mock_log]
        assert cache_operations == expected_cache_operations
        if not importing_WSDL_cached:
            assert store2.mock_log == ["suds://wsdl"]
        assert len(cache.mock_data) == 2
        assert cache.mock_data[id_wsdl_imported] is wsdl_imported_document
        schema = c2.wsdl.schema
        external_element = schema.elements[wsdl_imported_element_id].root
        assert cached_external_element is external_element

    @pytest.mark.parametrize("caching_policy", (0, 1))
    def test_using_cached_WSDL_avoids_store_avoids_transport(self,
            caching_policy):
        """
        When a client's WSDL schema is located in the cache, it should be read
        from there instead of fetching its data from the client's document
        store or using its registered transport.

        When it is is not located in the cache but can be found in the client's
        document store, it should be fetched from there but not using the
        client's registered transport.

        """
        # Add to cache, making sure the WSDL schema is read from the document
        # store and not fetched using the client's registered transport.
        cache = MockCache()
        store1 = MockDocumentStore(umpala=testutils.wsdl(""))
        c1 = suds.client.Client("suds://umpala", cachingpolicy=caching_policy,
            cache=cache, documentStore=store1, transport=MockTransport())
        assert [x for x, y in cache.mock_log] == ["get", "put"]
        id = cache.mock_log[0][1][0]
        assert id == cache.mock_log[1][1][0]
        assert len(cache.mock_data) == 1
        if caching_policy == 0:
            # Cache contains SAX XML documents.
            wsdl_document = next(itervalues(cache.mock_data))
            assert wsdl_document.__class__ is suds.sax.document.Document
            wsdl_cached_root = wsdl_document.root()
        else:
            # Cache contains complete suds WSDL objects.
            wsdl = next(itervalues(cache.mock_data))
            assert wsdl.__class__ is suds.wsdl.Definitions
            wsdl_cached_root = wsdl.root
        assert c1.wsdl.root is wsdl_cached_root

        # Make certain the same WSDL schema is fetched from the cache and not
        # using the document store or the transport.
        cache.mock_log = []
        cache.mock_put_config = MockCache.FAIL
        store2 = MockDocumentStore(mock_fail=True)
        c2 = suds.client.Client("suds://umpala", cachingpolicy=caching_policy,
            cache=cache, documentStore=store2, transport=MockTransport())
        assert cache.mock_log == [("get", [id])]
        assert c2.wsdl.root is wsdl_cached_root

    @pytest.mark.parametrize("external_reference_tag", ("import", "include"))
    @pytest.mark.parametrize("main_WSDL_cached", (False, True))
    def test_using_cached_XSD_schema_avoids_store_avoids_transport(self,
            external_reference_tag, main_WSDL_cached):
        """
        When an imported or included XSD schema is located in the client's
        cache, it should be read from there instead of fetching its data from
        the client's document store or using its registered transport.

        When it is is not located in the cache but can be found in the client's
        document store, it should be fetched from there but not using the
        client's registered transport.

        Note that this test makes sense only when caching raw XML documents
        (cachingpolicy == 0) and not when caching final WSDL objects
        (cachingpolicy == 1).

        """
        # Prepare document content.
        xsd_target_namespace = "my xsd namespace"
        wsdl = testutils.wsdl('<xsd:%s schemaLocation="suds://external"/>' % (
            external_reference_tag,),
            xsd_target_namespace=xsd_target_namespace)
        external_schema = b("""\
<?xml version='1.0' encoding='UTF-8'?>
<schema xmlns="http://www.w3.org/2001/XMLSchema">
  <element name="external" type="string"/>
</schema>
""")

        # Imported XSD schema items retain their namespace, while included ones
        # get merged into the target namespace.
        external_element_namespace = None
        if external_reference_tag == "include":
            external_element_namespace = xsd_target_namespace
        external_element_id = ("external", external_element_namespace)

        # Add to cache.
        cache = MockCache()
        store1 = MockDocumentStore(wsdl=wsdl, external=external_schema)
        c1 = suds.client.Client("suds://wsdl", cachingpolicy=0, cache=cache,
            documentStore=store1, transport=MockTransport())
        assert [x for x, y in cache.mock_log] == ["get", "put"] * 2
        id_wsdl = cache.mock_log[0][1][0]
        assert id_wsdl == cache.mock_log[1][1][0]
        id_xsd = cache.mock_log[2][1][0]
        assert id_xsd == cache.mock_log[3][1][0]
        assert len(cache.mock_data) == 2
        wsdl_document = cache.mock_data[id_wsdl]
        assert c1.wsdl.root is wsdl_document.root()
        # Making sure id_xsd refers to the actual external XSD is a bit tricky
        # due to the fact that the WSDL object merged in the external XSD
        # content and lost the reference to the external XSD object itself. As
        # a workaround we make sure that the XSD schema XML element read from
        # the XSD object cached as id_xsd matches the one read from the WSDL
        # object's XSD schema.
        xsd_imported_document = cache.mock_data[id_xsd]
        cached_external_element = xsd_imported_document.root().children[0]
        external_element = c1.wsdl.schema.elements[external_element_id].root
        assert cached_external_element is external_element

        # Make certain the same external XSD document is fetched from the cache
        # and not using the document store or the transport.
        cache.mock_log = []
        if main_WSDL_cached:
            cache.mock_put_config = MockCache.FAIL
            store2 = MockDocumentStore(mock_fail=True)
        else:
            del cache.mock_data[id_wsdl]
            assert len(cache.mock_data) == 1
            store2 = MockDocumentStore(wsdl=wsdl)
        c2 = suds.client.Client("suds://wsdl", cachingpolicy=0, cache=cache,
            documentStore=store2, transport=MockTransport())
        expected_cache_operations = [("get", id_wsdl)]
        if not main_WSDL_cached:
            expected_cache_operations.append(("put", id_wsdl))
        expected_cache_operations.append(("get", id_xsd))
        cache_operations = [(x, y[0]) for x, y in cache.mock_log]
        assert cache_operations == expected_cache_operations
        if not main_WSDL_cached:
            assert store2.mock_log == ["suds://wsdl"]
        assert len(cache.mock_data) == 2
        assert cache.mock_data[id_xsd] is xsd_imported_document
        external_element = c2.wsdl.schema.elements[external_element_id].root
        assert cached_external_element is external_element


class TestCacheUsage:
    """suds.client.Client cache component usage tests."""

    @pytest.mark.parametrize("cache", (
        None,
        suds.cache.NoCache(),
        suds.cache.ObjectCache()))
    def test_avoiding_default_cache_construction(self, cache, monkeypatch):
        """Explicitly specified cache avoids default cache construction."""
        def construct_default_cache(*args, **kwargs):
            pytest.fail("Unexpected default cache instantiation.")
        class MockStore(suds.store.DocumentStore):
            def open(self, *args, **kwargs):
                raise MyException
        monkeypatch.setattr(suds.cache, "ObjectCache", construct_default_cache)
        monkeypatch.setattr(suds.store, "DocumentStore", MockStore)
        pytest.raises(MyException, suds.client.Client, "suds://some_URL",
            documentStore=MockStore(), cache=cache)

    def test_default_cache_construction(self, monkeypatch):
        """
        Test when and how client creates its default cache object.

        We use a dummy store to get an expected exception rather than
        attempting to access the network, in case the test fails and the
        expected default cache object does not get created or gets created too
        late.

        """
        def construct_default_cache(days):
            assert days == 1
            raise MyException
        class MockStore(suds.store.DocumentStore):
            def open(self, *args, **kwargs):
                pytest.fail("Default cache not created in time.")
        monkeypatch.setattr(suds.cache, "ObjectCache", construct_default_cache)
        monkeypatch.setattr(suds.store, "DocumentStore", MockStore)
        pytest.raises(MyException, suds.client.Client, "suds://some_URL",
            documentStore=MockStore())

    @pytest.mark.parametrize("cache", (object(), MyException()))
    def test_reject_invalid_cache_class(self, cache, monkeypatch):
        monkeypatch.delitem(locals(), "e", False)
        e = pytest.raises(AttributeError, suds.client.Client,
            "suds://some_URL", cache=cache).value
        try:
            expected_error = '"cache" must be: (%r,)'
            assert str(e) == expected_error % (suds.cache.Cache,)
        finally:
            del e  # explicitly break circular reference chain in Python 3


class TestStoreUsage:
    """suds.client.Client document store component usage tests."""

    @pytest.mark.parametrize("store", (object(), suds.cache.NoCache()))
    def test_reject_invalid_store_class(self, store, monkeypatch):
        monkeypatch.delitem(locals(), "e", False)
        e = pytest.raises(AttributeError, suds.client.Client,
            "suds://some_URL", documentStore=store, cache=None).value
        try:
            expected_error = '"documentStore" must be: (%r,)'
            assert str(e) == expected_error % (suds.store.DocumentStore,)
        finally:
            del e  # explicitly break circular reference chain in Python 3


class TestTransportUsage:
    """suds.client.Client transport component usage tests."""

    def test_default_transport(self):
        client = testutils.client_from_wsdl(testutils.wsdl(""))
        expected = suds.transport.https.HttpAuthenticated
        assert client.options.transport.__class__ is expected

    @pytest.mark.parametrize("exception", (
        MyException(),  # non-TransportError exception
        suds.transport.TransportError("huku", 666)))
    def test_error_on_open(self, monkeypatch, exception):
        monkeypatch.delitem(locals(), "e_info", False)
        transport = MockTransport(open_data=exception)
        e_info = pytest.raises(exception.__class__, suds.client.Client, "url",
            cache=None, transport=transport)
        try:
            assert e_info.value is exception
        finally:
            del e_info  # explicitly break circular reference chain in Python 3

    def test_error_on_send__non_transport(self):
        e = MyException()
        t = MockTransport(send_data=e)
        store = MockDocumentStore(wsdl=testutils.wsdl("", operation_name="g"))
        client = suds.client.Client("suds://wsdl", documentStore=store,
            cache=None, transport=t)
        assert pytest.raises(MyException, client.service.g).value is e

    #TODO: The test_error_on_send__transport() test should be made much more
    # detailed. suds.transport.TransportError exceptions get handled in a much
    # more complex way then is demonstrated here, for example:
    #  - some HTTP status codes result in an exception being raised and some in
    #    different handling
    #  - an exception may be raised or returned depending on the
    #    suds.options.faults suds option
    # Also, the whole concept of re-raising a TransportError exception as a
    # simple Exception instance seems like bad design. For now this rough test
    # just demonstrates that suds.transport.TransportError exceptions get
    # handled differently from other exception types.
    def test_error_on_send__transport(self, monkeypatch):
        monkeypatch.delitem(locals(), "e", False)
        t = MockTransport(send_data=suds.transport.TransportError("huku", 666))
        store = MockDocumentStore(wsdl=testutils.wsdl("", operation_name="g"))
        client = suds.client.Client("suds://wsdl", documentStore=store,
            cache=None, transport=t)
        e = pytest.raises(Exception, client.service.g).value
        try:
            assert e.__class__ is Exception
            assert e.args == ((666, "huku"),)
        finally:
            del e  # explicitly break circular reference chain in Python 3

    def test_nosend_should_avoid_transport_sends(self):
        wsdl = testutils.wsdl("")
        t = MockTransport()
        client = testutils.client_from_wsdl(wsdl, nosend=True, transport=t)
        client.service.f()

    def test_operation_request_and_reply(self):
        xsd_content = '<xsd:element name="Data" type="xsd:string"/>'
        web_service_URL = "Great minds think alike"
        xsd_target_namespace = "omicron psi"
        wsdl = testutils.wsdl(xsd_content, operation_name="pi",
            xsd_target_namespace=xsd_target_namespace, input="Data",
            output="Data", web_service_URL=web_service_URL)
        test_input_data = "Riff-raff"
        test_output_data = "La-di-da-da-da"
        store = MockDocumentStore(wsdl=wsdl)
        transport = MockTransport(send_data=b("""\
<?xml version="1.0"?>
<env:Envelope xmlns:env="http://schemas.xmlsoap.org/soap/envelope/">
  <env:Body>
    <Data xmlns="%s">%s</Data>
  </env:Body>
</env:Envelope>""" % (xsd_target_namespace, test_output_data)))
        client = suds.client.Client("suds://wsdl", documentStore=store,
            cache=None, transport=transport)
        assert transport.mock_log == []
        reply = client.service.pi(test_input_data)
        assert len(transport.mock_log) == 1
        assert transport.mock_log[0][0] == "send"
        assert transport.mock_log[0][1][0] == web_service_URL
        request_message = transport.mock_log[0][1][1]
        assert b(xsd_target_namespace) in request_message
        assert b(test_input_data) in request_message
        assert reply == test_output_data

    @pytest.mark.parametrize("transport", (object(), suds.cache.NoCache()))
    def test_reject_invalid_transport_class(self, transport, monkeypatch):
        monkeypatch.delitem(locals(), "e", False)
        e = pytest.raises(AttributeError, suds.client.Client,
            "suds://some_URL", transport=transport, cache=None).value
        try:
            expected_error = '"transport" must be: (%r,)'
            assert str(e) == expected_error % (suds.transport.Transport,)
        finally:
            del e  # explicitly break circular reference chain in Python 3

    @pytest.mark.parametrize("url", test_URL_data)
    def test_WSDL_transport(self, url):
        store = MockDocumentStore()
        t = MockTransport(open_data=testutils.wsdl(""))
        suds.client.Client(url, cache=None, documentStore=store, transport=t)
        assert t.mock_log == [("open", [url])]

    def test_WSDL_transport_headers(self):
        url = test_URL_data[0]
        store = MockDocumentStore()
        t = MockTransport(open_data=testutils.wsdl(""))
        headers = {'foo': 'bar'}
        t.options.headers = headers # since we create a custom client, options must be set explicitly
        suds.client.Client(url, cache=None, documentStore=store, transport=t)
        assert len(t.mock_requests) == 1
        assert t.mock_requests[0].headers == headers

    @pytest.mark.parametrize("url", test_URL_data)
    def test_imported_WSDL_transport(self, url):
        wsdl_import_wrapper = wsdl_import_wrapper_format(url)
        wsdl_imported = wsdl_imported_format("")
        store = MockDocumentStore(wsdl=wsdl_import_wrapper)
        t = MockTransport(open_data=wsdl_imported)
        suds.client.Client("suds://wsdl", cache=None, documentStore=store,
            transport=t)
        assert t.mock_log == [("open", [url])]

    @pytest.mark.parametrize("url", test_URL_data)
    @pytest.mark.parametrize("external_reference_tag", ("import", "include"))
    def test_external_XSD_transport(self, url, external_reference_tag):
        xsd_content = '<xsd:%(tag)s schemaLocation="%(url)s"/>' % dict(
            tag=external_reference_tag, url=url)
        store = MockDocumentStore(wsdl=testutils.wsdl(xsd_content))
        t = MockTransport(open_data=b("""\
<?xml version='1.0' encoding='UTF-8'?>
<schema xmlns="http://www.w3.org/2001/XMLSchema"/>
"""))
        suds.client.Client("suds://wsdl", cache=None, documentStore=store,
            transport=t)
        assert t.mock_log == [("open", [url])]


class TestWSDLImportWithDifferentTargetNamespaces:
    """
    Import WSDL with different target namespace variations.

    """

    def test_imported_entity_reference_with_same_imported_and_base_ns(self):
        tns = "my shared WSDL schema namespace"
        url_imported = "suds://wsdl_imported"
        wsdl_import_wrapper = wsdl_import_wrapper_format(url_imported,
            imported_reference_ns=tns, target_namespace=tns);
        wsdl_imported = wsdl_imported_format(target_namespace=tns)
        store = MockDocumentStore(wsdl=wsdl_import_wrapper,
            wsdl_imported=wsdl_imported)
        suds.client.Client("suds://wsdl", cache=None, documentStore=store)

    def test_imported_entity_reference_using_base_namespace(self):
        """
        Imported WSDL entity references using base namespace should not work.

        """
        tns_import_wrapper = "my wrapper WSDL schema"
        tns_imported = "my imported WSDL schema"
        url_imported = "suds://wsdl_imported"
        wsdl_import_wrapper = wsdl_import_wrapper_format(url_imported,
            imported_reference_ns=tns_import_wrapper,
            target_namespace=tns_import_wrapper);
        wsdl_imported = wsdl_imported_format(target_namespace=tns_imported)
        store = MockDocumentStore(wsdl=wsdl_import_wrapper,
            wsdl_imported=wsdl_imported)
        e = pytest.raises(Exception, suds.client.Client, "suds://wsdl",
            cache=None, documentStore=store).value
        try:
            assert e.__class__ is Exception
            assert str(e) == "binding 'imported_reference_ns:dummy', not-found"
        finally:
            del e  # explicitly break circular reference chain in Python 3

    def test_imported_entity_reference_using_correct_namespace(self):
        """
        Imported WSDL entity references using imported namespace should work.

        """
        tns_import_wrapper = "my wrapper WSDL schema"
        tns_imported = "my imported WSDL schema"
        url_imported = "suds://wsdl_imported"
        wsdl_import_wrapper = wsdl_import_wrapper_format(url_imported,
            imported_reference_ns=tns_imported,
            target_namespace=tns_import_wrapper);
        wsdl_imported = wsdl_imported_format(target_namespace=tns_imported)
        store = MockDocumentStore(wsdl=wsdl_import_wrapper,
            wsdl_imported=wsdl_imported)
        suds.client.Client("suds://wsdl", cache=None, documentStore=store)


#TODO: extract WSDL processing tests to a separate test module
def test_resolving_references_to_later_entities_in_XML():
    """
    Referencing later entities in XML should be supported.

    When we reference another entity in our WSDL, there should be no
    difference whether that entity has been defined before or after the
    referencing entity in the underlying XML structure.

    """
    wsdl = b("""\
<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="tns-ns"
    xmlns:ns="xsd-ns"
    xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
    xmlns:tns="tns-ns"
    xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/">
  <wsdl:service name="my-service">
    <wsdl:port name="my-port" binding="tns:my-binding">
      <soap:address location="somewhere-under-a-rainbow"/>
    </wsdl:port>
  </wsdl:service>
  <wsdl:binding name="my-binding" type="tns:my-port-type">
    <soap:binding style="document"
        transport="http://schemas.xmlsoap.org/soap/http"/>
    <wsdl:operation name="f">
      <soap:operation soapAction="my-soap-action" style="document"/>
      <wsdl:input><soap:body use="literal"/></wsdl:input>
    </wsdl:operation>
  </wsdl:binding>
  <wsdl:portType name="my-port-type">
    <wsdl:operation name="f">
      <wsdl:input message="tns:fRequestMessage"/>
    </wsdl:operation>
  </wsdl:portType>
  <wsdl:message name="fRequestMessage">
    <wsdl:part name="parameters" element="ns:Lollypop"/>
  </wsdl:message>
  <wsdl:types>
    <xsd:schema targetNamespace="xsd-ns"
        elementFormDefault="qualified"
        attributeFormDefault="unqualified"
        xmlns:xsd="http://www.w3.org/2001/XMLSchema">
      <xsd:element name="Lollypop" type="xsd:string"/>
    </xsd:schema>
  </wsdl:types>
</wsdl:definitions>""")
    store = MockDocumentStore(wsdl=wsdl)
    c = suds.client.Client("suds://wsdl", cache=None, documentStore=store)
    service = c.wsdl.services[0]
    port = service.ports[0]
    binding = port.binding
    port_type = binding.type
    operation = port_type.operations['f']
    input_data = operation.input
    input_part = input_data.parts[0]
    input_element = input_part.element
    assert input_element == ('Lollypop', 'xsd-ns')


def test_sortnamespaces_default():
    """
    Option to not sort namespaces.
    """
    wsdl = b("""\
<?xml version='1.0' encoding='UTF-8'?>
<definitions targetNamespace="urn:wsdl" xmlns="http://schemas.xmlsoap.org/wsdl/" xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/" xmlns:soap12="http://schemas.xmlsoap.org/wsdl/soap12/" xmlns:tns="urn:wsdl" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
    <types>
        <xs:schema elementFormDefault="qualified" targetNamespace="urn:wsdl" xmlns:ns1="urn:wsdl:common" xmlns:ns2="urn:wsdl:account" xmlns:tns="urn:wsdl" xmlns:xs="http://www.w3.org/2001/XMLSchema">
            <xs:import namespace="urn:wsdl:common"/>
            <xs:import namespace="urn:wsdl:account"/>
            <xs:element name="PingRequest">
                <xs:complexType>
                    <xs:complexContent>
                        <xs:extension base="ns1:RequestMessage"/>
                    </xs:complexContent>
                </xs:complexType>
            </xs:element>
            <xs:element name="PingResponse">
                <xs:complexType>
                    <xs:complexContent>
                        <xs:extension base="ns1:ResponseMessage"/>
                    </xs:complexContent>
                </xs:complexType>
            </xs:element>
            <xs:complexType name="CustomField">
                <xs:sequence>
                    <xs:element name="FieldId" type="xs:long"/>
                </xs:sequence>
            </xs:complexType>
        </xs:schema>
        <xs:schema elementFormDefault="qualified" targetNamespace="urn:wsdl:common" xmlns:tns="urn:wsdl:common" xmlns:xs="http://www.w3.org/2001/XMLSchema">
            <xs:complexType name="RequestMessage">
                <xs:sequence>
                    <xs:element minOccurs="0" name="MessageHeader" type="tns:MessageHeader"/>
                    <xs:element minOccurs="0" name="SessionId" type="xs:string"/>
                </xs:sequence>
            </xs:complexType>
            <xs:complexType name="ResponseMessage">
                <xs:sequence>
                    <xs:element minOccurs="0" name="MessageHeader" type="tns:MessageHeader"/>
                    <xs:element maxOccurs="unbounded" minOccurs="0" name="ErrorList" type="tns:ErrorResponse"/>
                    <xs:element name="hasErrors" type="xs:boolean"/>
                </xs:sequence>
            </xs:complexType>
            <xs:complexType name="MessageHeader">
                <xs:sequence>
                    <xs:element minOccurs="0" name="Trace" type="xs:int"/>
                </xs:sequence>
            </xs:complexType>
            <xs:complexType name="ErrorResponse">
                <xs:sequence>
                    <xs:element name="ErrorCode" type="xs:int"/>
                    <xs:element name="ErrorMessage" type="xs:string"/>
                </xs:sequence>
            </xs:complexType>
            <xs:complexType name="Email">
                <xs:sequence>
                    <xs:element name="EmailAddress" type="xs:string"/>
                </xs:sequence>
            </xs:complexType>
        </xs:schema>
        <xs:schema elementFormDefault="qualified" targetNamespace="urn:wsdl:account" xmlns:msg="urn:wsdl:common" xmlns:tns="urn:wsdl:account" xmlns:xs="http://www.w3.org/2001/XMLSchema">
            <xs:import namespace="urn:wsdl:common" />
            <xs:simpleType name="UserAccess">
                <xs:restriction base="xs:string">
                    <xs:enumeration value="NO_ACCESS"/>
                </xs:restriction>
            </xs:simpleType>
        </xs:schema>
    </types>
    <message name="PingRequest">
        <part element="tns:PingRequest" name="body"/>
    </message>
    <message name="PingResponse">
        <part element="tns:PingResponse" name="body"/>
    </message>
    <portType name="Service">
        <operation name="Ping">
            <input message="tns:PingRequest"/>
            <output message="tns:PingResponse"/>
        </operation>
    </portType>
    <binding name="ServiceBinding" type="tns:Service">
        <soap:binding style="document" transport="http://schemas.xmlsoap.org/soap/http"/>
        <operation name="Ping">
            <soap:operation soapAction="" style="document"/>
            <input>
                <soap:body use="literal"/>
            </input>
            <output>
                <soap:body use="literal"/>
            </output>
        </operation>
    </binding>
    <service name="Service">
        <port binding="tns:ServiceBinding" name="ServicePort">
            <soap:address location="/services/Service/"/>
        </port>
    </service>
</definitions>
""")
    store = MockDocumentStore(wsdl=wsdl)
    client = suds.client.Client("suds://wsdl", cache=None, documentStore=store)
    prefixes = client.sd[0].prefixes
    assert str(prefixes[0][1]) == 'urn:wsdl'
    assert str(prefixes[1][1]) == 'urn:wsdl:account'
    assert str(prefixes[2][1]) == 'urn:wsdl:common'


def test_sortnamespaces_turned_off():
    """
    Option to not sort namespaces.
    """
    wsdl = b("""\
<?xml version='1.0' encoding='UTF-8'?>
<definitions targetNamespace="urn:wsdl" xmlns="http://schemas.xmlsoap.org/wsdl/" xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/" xmlns:soap12="http://schemas.xmlsoap.org/wsdl/soap12/" xmlns:tns="urn:wsdl" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
    <types>
        <xs:schema elementFormDefault="qualified" targetNamespace="urn:wsdl" xmlns:ns1="urn:wsdl:common" xmlns:ns2="urn:wsdl:account" xmlns:tns="urn:wsdl" xmlns:xs="http://www.w3.org/2001/XMLSchema">
            <xs:import namespace="urn:wsdl:common"/>
            <xs:import namespace="urn:wsdl:account"/>
            <xs:element name="PingRequest">
                <xs:complexType>
                    <xs:complexContent>
                        <xs:extension base="ns1:RequestMessage"/>
                    </xs:complexContent>
                </xs:complexType>
            </xs:element>
            <xs:element name="PingResponse">
                <xs:complexType>
                    <xs:complexContent>
                        <xs:extension base="ns1:ResponseMessage"/>
                    </xs:complexContent>
                </xs:complexType>
            </xs:element>
            <xs:complexType name="CustomField">
                <xs:sequence>
                    <xs:element name="FieldId" type="xs:long"/>
                </xs:sequence>
            </xs:complexType>
        </xs:schema>
        <xs:schema elementFormDefault="qualified" targetNamespace="urn:wsdl:common" xmlns:tns="urn:wsdl:common" xmlns:xs="http://www.w3.org/2001/XMLSchema">
            <xs:complexType name="RequestMessage">
                <xs:sequence>
                    <xs:element minOccurs="0" name="MessageHeader" type="tns:MessageHeader"/>
                    <xs:element minOccurs="0" name="SessionId" type="xs:string"/>
                </xs:sequence>
            </xs:complexType>
            <xs:complexType name="ResponseMessage">
                <xs:sequence>
                    <xs:element minOccurs="0" name="MessageHeader" type="tns:MessageHeader"/>
                    <xs:element maxOccurs="unbounded" minOccurs="0" name="ErrorList" type="tns:ErrorResponse"/>
                    <xs:element name="hasErrors" type="xs:boolean"/>
                </xs:sequence>
            </xs:complexType>
            <xs:complexType name="MessageHeader">
                <xs:sequence>
                    <xs:element minOccurs="0" name="Trace" type="xs:int"/>
                </xs:sequence>
            </xs:complexType>
            <xs:complexType name="ErrorResponse">
                <xs:sequence>
                    <xs:element name="ErrorCode" type="xs:int"/>
                    <xs:element name="ErrorMessage" type="xs:string"/>
                </xs:sequence>
            </xs:complexType>
            <xs:complexType name="Email">
                <xs:sequence>
                    <xs:element name="EmailAddress" type="xs:string"/>
                </xs:sequence>
            </xs:complexType>
        </xs:schema>
        <xs:schema elementFormDefault="qualified" targetNamespace="urn:wsdl:account" xmlns:msg="urn:wsdl:common" xmlns:tns="urn:wsdl:account" xmlns:xs="http://www.w3.org/2001/XMLSchema">
            <xs:import namespace="urn:wsdl:common" />
            <xs:simpleType name="UserAccess">
                <xs:restriction base="xs:string">
                    <xs:enumeration value="NO_ACCESS"/>
                </xs:restriction>
            </xs:simpleType>
        </xs:schema>
    </types>
    <message name="PingRequest">
        <part element="tns:PingRequest" name="body"/>
    </message>
    <message name="PingResponse">
        <part element="tns:PingResponse" name="body"/>
    </message>
    <portType name="Service">
        <operation name="Ping">
            <input message="tns:PingRequest"/>
            <output message="tns:PingResponse"/>
        </operation>
    </portType>
    <binding name="ServiceBinding" type="tns:Service">
        <soap:binding style="document" transport="http://schemas.xmlsoap.org/soap/http"/>
        <operation name="Ping">
            <soap:operation soapAction="" style="document"/>
            <input>
                <soap:body use="literal"/>
            </input>
            <output>
                <soap:body use="literal"/>
            </output>
        </operation>
    </binding>
    <service name="Service">
        <port binding="tns:ServiceBinding" name="ServicePort">
            <soap:address location="/services/Service/"/>
        </port>
    </service>
</definitions>
""")
    store = MockDocumentStore(wsdl=wsdl)
    client = suds.client.Client("suds://wsdl", cache=None, documentStore=store, sortNamespaces=False)
    prefixes = client.sd[0].prefixes
    assert str(prefixes[0][1]) == 'urn:wsdl:common'
    assert str(prefixes[1][1]) == 'urn:wsdl'
    assert str(prefixes[2][1]) == 'urn:wsdl:account'


class TestRecursiveWSDLImport:
    """
    Test different recursive WSDL import variations.

    As WSDL imports are nothing but forward declarations, and not component
    inclusions, recursive WSDL imports are well defined and should be
    supported.

    """

    @staticmethod
    def __wsdl_binding(tns_binding, tns_main, url_main):
        return b("""\
<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="%(tns)s"
    xmlns:main_ns="%(tns_imported)s"
    xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
    xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/">
  <wsdl:import namespace="%(tns_imported)s" location="%(url_imported)s"/>
  <wsdl:binding name="my-binding" type="main_ns:my-port-type">
    <soap:binding style="document"
        transport="http://schemas.xmlsoap.org/soap/http"/>
    <wsdl:operation name="f">
      <soap:operation soapAction="my-soap-action" style="document"/>
    </wsdl:operation>
  </wsdl:binding>
</wsdl:definitions>""" % dict(tns=tns_binding, tns_imported=tns_main,
            url_imported=url_main))

    @staticmethod
    def __wsdl_no_binding(tns_main, tns_binding, url_binding):
        return b("""\
<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="%(tns)s"
    xmlns:binding_ns="%(tns_imported)s"
    xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
    xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/">
  <wsdl:import namespace="%(tns_imported)s" location="%(url_imported)s"/>
  <wsdl:portType name="my-port-type">
    <wsdl:operation name="f"/>
  </wsdl:portType>
  <wsdl:service name="my-service">
    <wsdl:port name="my-port" binding="binding_ns:my-binding">
      <soap:address location="somewhere-under-a-rainbow"/>
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>""" % dict(tns=tns_main, tns_imported=tns_binding,
            url_imported=url_binding))

    def test_recursive_WSDL_import_with_single_URL_per_WSDL(self):
        url_main = "suds://wsdl_main"
        tns_main = "main-wsdl"
        url_binding = "suds://wsdl_binding"
        tns_binding = "binding-wsdl"

        wsdl_binding = self.__wsdl_binding(tns_binding, tns_main, url_main)
        wsdl_main = self.__wsdl_no_binding(tns_main, tns_binding, url_binding)

        store = MockDocumentStore(wsdl_main=wsdl_main,
            wsdl_binding=wsdl_binding)
        suds.client.Client(url_main, cache=None, documentStore=store)

    def test_recursive_WSDL_import_with_multiple_URLs_per_WSDL(self):
        url_main1 = "suds://wsdl_main_1"
        url_main2 = "suds://wsdl_main_2"
        tns_main = "main-wsdl"
        url_binding = "suds://wsdl_binding"
        tns_binding = "binding-wsdl"

        wsdl_binding = self.__wsdl_binding(tns_binding, tns_main, url_main2)
        wsdl_main = self.__wsdl_no_binding(tns_main, tns_binding, url_binding)

        store = MockDocumentStore(wsdl_main_1=wsdl_main, wsdl_main_2=wsdl_main,
            wsdl_binding=wsdl_binding)
        suds.client.Client(url_main1, cache=None, documentStore=store)

    def test_WSDL_self_import(self):
        url = "suds://wsdl"
        wsdl = b("""\
<?xml version='1.0' encoding='UTF-8'?>
<wsdl:definitions targetNamespace="my-namespace"
    xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
    xmlns:tns="my-namespace"
    xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/">
  <wsdl:import namespace="my-namespace" location="%(url_imported)s"/>
  <wsdl:portType name="my-port-type">
    <wsdl:operation name="f"/>
  </wsdl:portType>
  <wsdl:binding name="my-binding" type="tns:my-port-type">
    <soap:binding style="document"
        transport="http://schemas.xmlsoap.org/soap/http"/>
    <wsdl:operation name="f">
      <soap:operation soapAction="my-soap-action" style="document"/>
    </wsdl:operation>
  </wsdl:binding>
  <wsdl:service name="my-service">
    <wsdl:port name="my-port" binding="tns:my-binding">
      <soap:address location="how I wish... how I wish you were here..."/>
    </wsdl:port>
  </wsdl:service>
</wsdl:definitions>""" % dict(url_imported=url))

        store = MockDocumentStore(wsdl=wsdl)
        suds.client.Client(url, cache=None, documentStore=store)
