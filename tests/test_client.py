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

if __name__ == "__main__":
    import __init__
    __init__.run_using_pytest(globals())


import suds
import suds.cache
import suds.store
import suds.transport
import suds.transport.https
import tests

import pytest


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
        self.mock_operation_log = []
        self.mock_put_config = MockCache.ALLOW
        super(MockCache, self).__init__()

    def clear(self):
        self.mock_operation_log.append(("clear", []))
        pytest.fail("Unexpected MockCache.clear() operation call.")

    def get(self, id):
        self.mock_operation_log.append(("get", [id]))
        return self.mock_data.get(id, None)

    def purge(self, id):
        self.mock_operation_log.append(("purge", [id]))
        pytest.fail("Unexpected MockCache.purge() operation call.")

    def put(self, id, object):
        self.mock_operation_log.append(("put", [id, object]))
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

    """

    def __init__(self, open_data=None, send_data=None):
        if open_data is None:
            open_data = []
        elif open_data.__class__ is not list:
            assert open_data.__class__ is suds.byte_str_class
            open_data = [open_data]
        if send_data is None:
            send_data = []
        elif send_data.__class__ is not list:
            assert send_data.__class__ is suds.byte_str_class
            send_data = [send_data]
        self.mock_operation_log = []
        self.mock_open_data = open_data
        self.mock_send_config = send_data
        super(MockTransport, self).__init__()

    def open(self, request):
        self.mock_operation_log.append(("open", request.url))
        if self.mock_open_data:
            return suds.BytesIO(self.mock_open_data.pop(0))
        pytest.fail("Unexpected MockTransport.open() operation call.")

    def send(self, request):
        self.mock_operation_log.append(("send", request.url))
        if self.mock_send_data:
            return suds.BytesIO(self.mock_send_data.pop(0))
        pytest.fail("Unexpected MockTransport.send() operation call.")


class TestCacheStoreTransportUsage:
    """
    suds.client.Client cache/store/transport component usage interaction tests.

    """

    def test_fetching_wsdl_from_cache_should_avoid_store_and_transport(self):
        """
        When a requested WSDL schema is located in the client's cache, it
        should be read from there instead of fetching its data from the
        client's document store or using its registered transport.

        """
        # Add to cache.
        cache = MockCache()
        store1 = MockDocumentStore(umpala=tests.wsdl(""))
        c1 = suds.client.Client("suds://umpala", cache=cache,
            documentStore=store1, transport=MockTransport())
        assert [x for x, y in cache.mock_operation_log] == ["get", "put"]
        id = cache.mock_operation_log[0][1][0]
        assert id == cache.mock_operation_log[1][1][0]
        assert len(cache.mock_data) == 1
        wsdl_document = cache.mock_data.values()[0]
        assert c1.wsdl.root is wsdl_document.root()

        # Make certain the same WSDL schema is fetched from the cache and not
        # using the document store or the transport.
        cache.mock_operation_log = []
        cache.mock_put_config = MockCache.FAIL
        store2 = MockDocumentStore(mock_fail=True)
        c2 = suds.client.Client("suds://umpala", cache=cache,
            documentStore=store2, transport=MockTransport())
        assert cache.mock_operation_log == [("get", [id])]
        assert c2.wsdl.root is wsdl_document.root()

    def test_fetching_wsdl_from_store_should_avoid_transport(self):
        store = MockDocumentStore(umpala=tests.wsdl(""))
        url = "suds://umpala"
        t = MockTransport()
        suds.client.Client(url, cache=None, documentStore=store, transport=t)
        assert store.mock_log == [url]

    def test_import_XSD_from_cache_should_avoid_store_and_transport(self):
        """
        When an imported XSD schema is located in the client's cache, it should
        be read from there instead of fetching its data from the client's
        document store or using its registered transport.

        Note that this test makes sense only when caching raw XML documents
        (cachingpolicy == 0) and not when caching final WSDL objects
        (cachingpolicy == 1).

        """
        # Prepare document content.
        wsdl_import = tests.wsdl(
            '<xsd:import namespace="xxx" schemaLocation="suds://imported"/>')
        imported_schema = suds.byte_str("""\
<?xml version='1.0' encoding='UTF-8'?>
<schema xmlns="http://www.w3.org/2001/XMLSchema" targetNamespace="xxx">
  <element name="external" type="string"/>
</schema>
""")

        # Add to cache.
        cache = MockCache()
        store1 = MockDocumentStore(wsdl=wsdl_import, imported=imported_schema)
        c1 = suds.client.Client("suds://wsdl", cachingpolicy=0,
            cache=cache, documentStore=store1, transport=MockTransport())
        assert [x for x, y in cache.mock_operation_log] == ["get", "put"] * 2
        id1 = cache.mock_operation_log[0][1][0]
        assert id1 == cache.mock_operation_log[1][1][0]
        id2 = cache.mock_operation_log[2][1][0]
        assert id2 == cache.mock_operation_log[3][1][0]
        assert len(cache.mock_data) == 2
        wsdl_document = cache.mock_data[id1]
        assert c1.wsdl.root is wsdl_document.root()
        # Making sure that id2 refers to the actually imported XSD is a bit
        # tricky due to the fact that the WSDL object merged in the imported
        # XSD content and lost the reference to the imported XSD object itself.
        # As a workaround we make sure that the XSD schema XML element read
        # from the XSD object cached as id2 matches the one read from the WSDL
        # object's XSD schema.
        cached_imported_element = cache.mock_data[id2].root().children[0]
        imported_element = c1.wsdl.schema.elements["external", "xxx"].root
        assert cached_imported_element is imported_element

        # Make certain the same imported document is fetched from the cache and
        # not using the document store or the transport.
        del cache.mock_data[id1]
        assert len(cache.mock_data) == 1
        cache.mock_operation_log = []
        store2 = MockDocumentStore(wsdl=wsdl_import)
        c2 = suds.client.Client("suds://wsdl", cache=cache,
            documentStore=store2, transport=MockTransport())
        assert [(x, y[0]) for x, y in cache.mock_operation_log] == [
            ("get", id1), ("put", id1), ("get", id2)]
        assert len(cache.mock_data) == 2
        assert store2.mock_log == ["suds://wsdl"]
        imported_element = c2.wsdl.schema.elements["external", "xxx"].root
        assert cached_imported_element is imported_element

    @pytest.mark.parametrize("url", (
        "sudo://make-me-a-sammich",
        "http://my little URL",
        "https://my little URL",
        "xxx://my little URL",
        "xxx:my little URL",
        "xxx:"))
    def test_wsdl_not_found_in_cache_or_store_should_be_transported(self, url):
        store = MockDocumentStore()
        t = MockTransport(open_data=tests.wsdl(""))
        suds.client.Client(url, cache=None, documentStore=store, transport=t)
        assert t.mock_operation_log == [("open", url)]


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
        expected_error = '"cache" must be: (%r,)'
        assert str(e) == expected_error % (suds.cache.Cache,)


class TestStoreUsage:
    """suds.client.Client document store component usage tests."""

    @pytest.mark.parametrize("store", (object(), suds.cache.NoCache()))
    def test_reject_invalid_store_class(self, store, monkeypatch):
        monkeypatch.delitem(locals(), "e", False)
        e = pytest.raises(AttributeError, suds.client.Client,
            "suds://some_URL", documentStore=store).value
        expected_error = '"documentStore" must be: (%r,)'
        assert str(e) == expected_error % (suds.store.DocumentStore,)


class TestTransportUsage:
    """suds.client.Client transport component usage tests."""

    def test_default_transport(self):
        client = tests.client_from_wsdl(tests.wsdl(""))
        expected = suds.transport.https.HttpAuthenticated
        assert client.options.transport.__class__ is expected

    def test_nosend_should_avoid_transport_sends(self):
        wsdl = tests.wsdl("")
        t = MockTransport()
        client = tests.client_from_wsdl(wsdl, nosend=True, transport=t)
        client.service.f()

    @pytest.mark.parametrize("transport", (object(), suds.cache.NoCache()))
    def test_reject_invalid_transport_class(self, transport, monkeypatch):
        monkeypatch.delitem(locals(), "e", False)
        e = pytest.raises(AttributeError, suds.client.Client,
            "suds://some_URL", transport=transport).value
        expected_error = '"transport" must be: (%r,)'
        assert str(e) == expected_error % (suds.transport.Transport,)
