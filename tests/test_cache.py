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
Suds Python library document caching unit tests.

Implemented using the 'pytest' testing framework.

"""

if __name__ == "__main__":
    import __init__
    __init__.runUsingPyTest(globals())


import suds
import suds.cache
import suds.sax.parser

import pytest

import datetime
import os
import tempfile


class MyException(Exception):
    """Local exception class used in the tests in this module."""
    pass


class InvisibleMan:
    """Dummy class used for pickling related tests."""
    def __init__(self, x):
        self.x = x


class MockFile:
    """
    Wrapper around a regular file object allowing controlled file operation
    failures.

    """

    def __init__(self, opener, file, fail_read):
        self.__opener = opener
        self.__file = file
        self.__fail_read = fail_read

    def __getattr__(self, *args, **kwargs):
        return getattr(self.__file, *args, **kwargs)

    def read(self, *args, **kwargs):
        self.__opener.read_counter += 1
        if self.__fail_read:
            raise MyException
        return self.__file.read(*args, **kwargs)


class MockFileOpener:
    """
    Mock open() function for the suds.cache module.

    May cause such calls to fail or to return our MockFile objects prepared so
    some of their functions fail in a controlled manner.

    """

    def __init__(self, fail_open=False, fail_read=False):
        self.__previous = None
        self.__fail_open = fail_open
        self.__fail_read = fail_read
        self.counter = 0
        self.read_counter = 0

    def __call__(self, *args, **kwargs):
        self.counter += 1
        if self.__fail_open:
            raise MyException
        file = self.__previous(*args, **kwargs)
        return MockFile(self, file, fail_read=self.__fail_read)

    def apply(self, monkeypatch):
        """Monkeypatch suds.cache module's open() global."""
        try:
            self.__previous = suds.cache.open
        except AttributeError:
            self.__previous = open
        monkeypatch.setitem(suds.cache.__dict__, "open", self)

    def reset(self):
        self.counter = 0
        self.read_counter = 0


class MockParse:
    """Mock object causing suds.sax.parser.Parser.parse() failures."""

    def __init__(self):
        self.counter = 0

    def __call__(self, *args, **kwargs):
        self.counter += 1
        raise MyException

    def apply(self, monkeypatch):
        """Monkeypatch suds SAX Parser's parse() method."""
        monkeypatch.setattr(suds.sax.parser.Parser, "parse", self)

    def reset(self):
        self.counter = 0


class MockPickleLoad:
    """Mock object causing suds.cache module's pickle load failures."""

    def __init__(self):
        self.counter = 0

    def __call__(self, *args, **kwargs):
        self.counter += 1
        raise MyException

    def apply(self, monkeypatch):
        """Monkeypatch suds.cache module's pickle.load()."""
        monkeypatch.setattr(suds.cache.pickle, "load", self)

    def reset(self):
        self.counter = 0


# Hardcoded values used in different caching test cases.
value_empty = suds.byte_str("")
value_f2 = suds.byte_str("fifi2")
value_f22 = suds.byte_str("fifi22")
value_f3 = suds.byte_str("fifi3")
value_p1 = suds.byte_str("pero1")
value_p11 = suds.byte_str("pero11")
value_p111 = suds.byte_str("pero111")
value_p2 = suds.byte_str("pero2")
value_p22 = suds.byte_str("pero22")
value_unicode = suds.byte_str(u"€ 的 čćžšđČĆŽŠĐ")


# FileCache item expiration test data - duration, current_time, expect_remove.
# Reused for different testing different FileCache derived classes.
file_cache_item_expiration_test_data = ([
    # Infinite cache entry durations.
    ({}, datetime.datetime.min, False),
    ({}, datetime.timedelta(days=-21), False),
    ({}, -datetime.datetime.resolution, False),
    ({}, datetime.timedelta(), False),
    ({}, datetime.datetime.resolution, False),
    ({}, datetime.timedelta(days=7), False),
    ({}, datetime.datetime.max, False)] +
    # Finite cache entry durations.
    [(duration, current_time, expect_remove)
        for duration in (
            {"minutes": 7},
            {"microseconds": 1},
            {"microseconds": -1},
            {"hours": -7})
        for current_time, expect_remove in (
            (datetime.datetime.min, False),
            (datetime.timedelta(days=-21), False),
            (-datetime.datetime.resolution, False),
            (datetime.timedelta(), False),
            (datetime.datetime.resolution, True),
            (datetime.timedelta(days=7), True),
            (datetime.datetime.max, True))])

@pytest.mark.parametrize(("method_name", "params"), (
    ("clear", []),
    ("get", ["id"]),
    ("purge", ["id"]),
    ("put", ["id", "object"])))
def test_Cache_methods_abstract(monkeypatch, method_name, params):
    monkeypatch.delitem(locals(), "e", False)
    cache = suds.cache.Cache()
    f = getattr(cache, method_name)
    e = pytest.raises(Exception, f, *params).value
    assert e.__class__ is Exception
    assert str(e) == "not-implemented"


# TODO: DocumentCache class interface seems silly. Its get() operation returns
# an XML document while its put() operation takes an XML element. The put()
# operation also silently ignores passed data of incorrect type.
class TestDocumentCache:

    def compare_document_to_content(self, document, content):
        """Assert that the given XML document and content match."""
        assert document.__class__ is suds.sax.document.Document
        elements = document.getChildren()
        assert len(elements) == 1
        element = elements[0]
        assert element.__class__ is suds.sax.element.Element
        assert suds.byte_str(str(element)) == content

    def construct_XML(self, element_name="Elemento"):
        """
        Construct XML content and an Element wrapping it.

        Constructed content may be parametrized with the given element name.

        """
        # TODO: Update the tests in this group to no longer depend on the exact
        # input XML data formatting. They currently expect it to be formatted
        # exactly as what gets read back from their DocumentCache.
        content = suds.byte_str("""\
<xsd:element name="%s">
   <xsd:simpleType>
      <xsd:restriction base="xsd:string">
         <xsd:enumeration value="alfa"/>
         <xsd:enumeration value="beta"/>
         <xsd:enumeration value="gamma"/>
      </xsd:restriction>
   </xsd:simpleType>
</xsd:element>""" % (element_name,))
        xml = suds.sax.parser.Parser().parse(suds.BytesIO(content))
        children = xml.getChildren()
        assert len(children) == 1
        assert children[0].__class__ is suds.sax.element.Element
        return content, children[0]

    def test_basic(self, tmpdir):
        cache = suds.cache.DocumentCache(tmpdir.strpath)
        assert isinstance(cache, suds.cache.FileCache)
        assert cache.get("unga1") is None
        content, element = self.construct_XML()
        cache.put("unga1", element)
        self.compare_document_to_content(cache.get("unga1"), content)

    def test_file_open_failure(self, tmpdir, monkeypatch):
        """
        File open failure should cause no cached object to be found, but any
        existing underlying cache file should be kept around.

        """
        mock_open = MockFileOpener(fail_open=True)

        cache_folder = tmpdir.strpath
        cache = suds.cache.DocumentCache(cache_folder)
        content1, element1 = self.construct_XML("One")
        content2, element2 = self.construct_XML("Two")
        assert content1 != content2
        cache.put("unga1", element1)

        mock_open.apply(monkeypatch)
        assert cache.get("unga1") is None
        monkeypatch.undo()
        assert mock_open.counter == 1
        assert not _is_empty_cache_folder(cache_folder)
        self.compare_document_to_content(cache.get("unga1"), content1)

        mock_open.apply(monkeypatch)
        assert cache.get("unga2") is None
        monkeypatch.undo()
        assert mock_open.counter == 2
        assert not _is_empty_cache_folder(cache_folder)
        self.compare_document_to_content(cache.get("unga1"), content1)
        assert cache.get("unga2") is None

        cache.put("unga2", element2)
        assert mock_open.counter == 2

        mock_open.apply(monkeypatch)
        assert cache.get("unga1") is None
        monkeypatch.undo()
        assert mock_open.counter == 3
        assert not _is_empty_cache_folder(cache_folder)

        self.compare_document_to_content(cache.get("unga1"), content1)
        self.compare_document_to_content(cache.get("unga2"), content2)
        assert mock_open.counter == 3

    @pytest.mark.parametrize(("mock", "extra_checks"), (
        (MockParse(), [lambda x: True] * 4),
        (MockFileOpener(fail_read=True), [
            lambda x: x.read_counter != 0,
            lambda x: x.read_counter == 0,
            lambda x: x.read_counter != 0,
            lambda x: x.read_counter == 0])))
    def test_file_operation_failure(self, tmpdir, monkeypatch, mock,
            extra_checks):
        """
        File operation failures such as reading failures or failing to parse
        data read from such a file should cause no cached object to be found
        and the related cache file to be removed.

        """
        cache_folder = tmpdir.strpath
        cache = suds.cache.DocumentCache(cache_folder)
        content1, element1 = self.construct_XML("Eins")
        content2, element2 = self.construct_XML("Zwei")
        cache.put("unga1", element1)

        mock.apply(monkeypatch)
        assert cache.get("unga1") is None
        monkeypatch.undo()
        assert mock.counter == 1
        assert extra_checks[0](mock)
        assert _is_empty_cache_folder(cache_folder)

        mock.reset()
        assert cache.get("unga1") is None
        cache.put("unga1", element1)
        cache.put("unga2", element2)
        assert mock.counter == 0
        assert extra_checks[1](mock)

        mock.reset()
        mock.apply(monkeypatch)
        assert cache.get("unga1") is None
        monkeypatch.undo()
        assert mock.counter == 1
        assert extra_checks[2](mock)
        assert not _is_empty_cache_folder(cache_folder)

        mock.reset()
        assert cache.get("unga1") is None
        self.compare_document_to_content(cache.get("unga2"), content2)
        assert mock.counter == 0
        assert extra_checks[3](mock)

    @pytest.mark.parametrize(("duration", "current_time", "expect_remove"),
        file_cache_item_expiration_test_data)
    def test_item_expiration(self, tmpdir, monkeypatch, duration, current_time,
            expect_remove):
        """See TestFileCache.item_expiration_test_worker() for more info."""
        cache = suds.cache.DocumentCache(tmpdir.strpath, **duration)
        content, element = self.construct_XML()
        cache.put("willy", element)
        TestFileCache.item_expiration_test_worker(cache, "willy", monkeypatch,
            current_time, expect_remove)

    def test_repeated_reads(self, tmpdir):
        cache = suds.cache.DocumentCache(tmpdir.strpath)
        content, element = self.construct_XML()
        cache.put("unga1", element)
        read_XML = cache.get("unga1").str()
        assert read_XML == cache.get("unga1").str()
        assert cache.get(None) is None
        assert cache.get("") is None
        assert cache.get("unga2") is None
        assert read_XML == cache.get("unga1").str()


class TestFileCache:

    @staticmethod
    def item_expiration_test_worker(cache, id, monkeypatch, current_time,
            expect_remove):
        """
        Test how a FileCache & its derived classes expire their item entries.

        Facts tested:
        * 0 duration should cause cache items never to expire.
        * Expired item files should be automatically removed from the cache
          folder.
        * Negative durations should be treated the same as positive ones.

        Requirements on the passed cache object:
        * Configures with the correct duration for this test.
        * Contains a valid cached item with the given id and its ctime
          timestamp + cache.duration must fall into the valid datetime.datetime
          value range.
        * Must use only public & protected FileCache interfaces to access its
          cache item data files.

        'current_time' values are expected to be either datetime.datetime or
        datetime.timedelta instances with the latter interpreted relative to
        the test file's expected expiration time.

        """
        assert isinstance(cache, suds.cache.FileCache)
        filepath = cache._FileCache__filename(id)
        assert os.path.isfile(filepath)
        file_timestamp = os.path.getctime(filepath)
        file_time = datetime.datetime.fromtimestamp(file_timestamp)

        class MockDateTime(datetime.datetime):
            """
            MockDateTime class monkeypatched to replace datetime.datetime.

            Allows us to control the exact built-in datetime.datetime.now()
            return value. Note that Python does not allow us to monkeypatch
            datetime.datetime.now() directly as it is a built-in function.

            """
            mock_counter = 0
            @staticmethod
            def now(*args, **kwargs):
                MockDateTime.mock_counter += 1
                return MockDateTime.mock_value

        if isinstance(current_time, datetime.timedelta):
            expire_time = file_time + cache.duration
            MockDateTime.mock_value = expire_time + current_time
        else:
            MockDateTime.mock_value = current_time
        monkeypatch.setattr(datetime, "datetime", MockDateTime)
        assert (cache._getf(id) is None) == expect_remove
        monkeypatch.undo()
        if cache.duration:
            assert MockDateTime.mock_counter == 1
        else:
            assert MockDateTime.mock_counter == 0
        assert os.path.isfile(filepath) == (not expect_remove)

    def test_basic_construction(self):
        cache = suds.cache.FileCache()
        assert isinstance(cache, suds.cache.Cache)
        assert cache.duration.__class__ is datetime.timedelta

    def test_cached_content_empty(self, tmpdir):
        cache_folder = tmpdir.strpath
        cache = suds.cache.FileCache(cache_folder)
        cache.put("unga1", value_empty)
        assert cache.get("unga1") == value_empty
        assert not _is_empty_cache_folder(cache_folder)

    def test_cached_content_unicode(self, tmpdir):
        cache_folder = tmpdir.strpath
        cache = suds.cache.FileCache(cache_folder)
        cache.put("unga1", value_unicode)
        assert cache.get("unga1") == value_unicode
        assert not _is_empty_cache_folder(cache_folder)

    def test_clear(self, tmpdir):
        cache_folder1 = tmpdir.join("fungus").strpath
        cache1 = suds.cache.FileCache(cache_folder1)
        cache1.put("unga1", value_p1)
        assert not _is_empty_cache_folder(cache_folder1)
        cache1.put("unga2", value_p2)
        assert not _is_empty_cache_folder(cache_folder1)
        assert cache1.get("unga1") == value_p1
        assert cache1.get("unga2") == value_p2
        assert not _is_empty_cache_folder(cache_folder1)
        cache1.clear()
        assert _is_empty_cache_folder(cache_folder1)
        assert cache1.get("unga1") is None
        assert cache1.get("unga2") is None
        assert _is_empty_cache_folder(cache_folder1)
        cache1.put("unga1", value_p11)
        cache1.put("unga2", value_p2)
        assert not _is_empty_cache_folder(cache_folder1)
        assert cache1.get("unga1") == value_p11
        assert cache1.get("unga2") == value_p2
        assert not _is_empty_cache_folder(cache_folder1)

        cache_folder2 = tmpdir.join("broccoli").strpath
        cache2 = suds.cache.FileCache(cache_folder2)
        cache2.put("unga2", value_f2)
        assert cache2.get("unga2") == value_f2
        assert cache1.get("unga2") == value_p2
        cache2.clear()
        assert not _is_empty_cache_folder(cache_folder1)
        assert _is_empty_cache_folder(cache_folder2)
        assert cache2.get("unga2") is None
        assert cache1.get("unga1") == value_p11
        assert cache1.get("unga2") == value_p2
        cache2.put("unga2", value_p22)
        assert cache2.get("unga2") == value_p22

    def test_close_leaves_cached_files_behind(self, tmpdir):
        cache_folder1 = tmpdir.join("ana").strpath
        cache1 = suds.cache.FileCache(cache_folder1)
        cache1.put("unga1", value_p1)
        cache1.put("unga2", value_p2)

        cache_folder2 = tmpdir.join("nan").strpath
        cache2 = suds.cache.FileCache(cache_folder2)
        cache2.put("unga2", value_f2)
        cache2.put("unga3", value_f3)

        del cache1

        cache11 = suds.cache.FileCache(cache_folder1)
        assert cache11.get("unga1") == value_p1
        assert cache11.get("unga2") == value_p2
        assert cache2.get("unga2") == value_f2
        assert cache2.get("unga3") == value_f3

    def test_get_put(self, tmpdir):
        cache_folder1 = tmpdir.join("firefly").strpath
        cache1 = suds.cache.FileCache(cache_folder1)
        assert _is_empty_cache_folder(cache_folder1)
        assert cache1.get("unga1") is None
        cache1.put("unga1", value_p1)
        assert not _is_empty_cache_folder(cache_folder1)
        assert cache1.get("unga1") == value_p1
        assert cache1.get("unga2") is None
        cache1.put("unga1", value_p11)
        assert cache1.get("unga1") == value_p11
        assert cache1.get("unga2") is None
        cache1.put("unga2", value_p2)
        assert cache1.get("unga1") == value_p11
        assert cache1.get("unga2") == value_p2

        cache_folder2 = tmpdir.join("semper fi").strpath
        cache2 = suds.cache.FileCache(cache_folder2)
        assert _is_empty_cache_folder(cache_folder2)
        assert cache2.get("unga2") is None
        cache2.put("unga2", value_f2)
        assert not _is_empty_cache_folder(cache_folder2)
        assert cache2.get("unga2") == value_f2
        assert cache2.get("unga3") is None
        cache2.put("unga2", value_f22)
        assert cache2.get("unga2") == value_f22
        assert cache2.get("unga3") is None
        cache2.put("unga3", value_f3)
        assert cache2.get("unga2") == value_f22
        assert cache2.get("unga3") == value_f3

        assert not _is_empty_cache_folder(cache_folder1)
        assert not _is_empty_cache_folder(cache_folder2)
        assert cache1.get("unga1") == value_p11
        assert cache1.get("unga2") == value_p2
        assert cache1.get("unga3") is None
        assert cache2.get("unga1") is None
        assert cache2.get("unga2") == value_f22
        assert cache2.get("unga3") == value_f3

    @pytest.mark.parametrize(("duration", "current_time", "expect_remove"),
        file_cache_item_expiration_test_data)
    def test_item_expiration(self, tmpdir, monkeypatch, duration, current_time,
            expect_remove):
        """See TestFileCache.item_expiration_test_worker() for more info."""
        cache = suds.cache.FileCache(tmpdir.strpath, **duration)
        cache.put("unga1", value_p1)
        TestFileCache.item_expiration_test_worker(cache, "unga1", monkeypatch,
            current_time, expect_remove)

    def test_location(self, tmpdir):
        FileCache = suds.cache.FileCache

        defaultLocation = os.path.join(tempfile.gettempdir(), "suds")
        cache = FileCache()
        assert os.path.isdir(cache.location)
        assert cache.location == defaultLocation
        assert FileCache().location == defaultLocation
        assert cache.location == defaultLocation

        cache_folder1 = tmpdir.join("flip-flop1").strpath
        assert not os.path.isdir(cache_folder1)
        assert FileCache(location=cache_folder1).location == cache_folder1
        assert _is_empty_cache_folder(cache_folder1)

        cache_folder2 = tmpdir.join("flip-flop2").strpath
        assert not os.path.isdir(cache_folder2)
        assert FileCache(cache_folder2).location == cache_folder2
        assert _is_empty_cache_folder(cache_folder2)

    def test_purge(self, tmpdir):
        cache_folder1 = tmpdir.join("flamenco").strpath
        cache1 = suds.cache.FileCache(cache_folder1)
        cache1.put("unga1", value_p1)
        assert cache1.get("unga1") == value_p1
        cache1.purge("unga1")
        assert _is_empty_cache_folder(cache_folder1)
        assert cache1.get("unga1") is None
        cache1.put("unga1", value_p11)
        cache1.put("unga2", value_p2)
        assert cache1.get("unga1") == value_p11
        assert cache1.get("unga2") == value_p2
        cache1.purge("unga1")
        assert cache1.get("unga1") is None
        assert cache1.get("unga2") == value_p2
        cache1.put("unga1", value_p111)

        cache_folder2 = tmpdir.join("shadow").strpath
        cache2 = suds.cache.FileCache(cache_folder2)
        cache2.put("unga2", value_f2)
        cache2.purge("unga2")
        assert _is_empty_cache_folder(cache_folder2)
        assert cache1.get("unga1") == value_p111
        assert cache1.get("unga2") == value_p2
        assert cache2.get("unga2") is None

    def test_reused_cache_folder(self, tmpdir):
        cache_folder = tmpdir.strpath
        cache1 = suds.cache.FileCache(cache_folder)
        assert _is_empty_cache_folder(cache_folder)
        assert cache1.get("unga1") is None
        cache1.put("unga1", value_p1)
        assert cache1.get("unga1") == value_p1
        assert cache1.get("unga2") is None
        cache1.put("unga1", value_p11)
        assert cache1.get("unga1") == value_p11
        assert cache1.get("unga2") is None
        cache1.put("unga2", value_p2)
        assert cache1.get("unga1") == value_p11
        assert cache1.get("unga2") == value_p2

        cache2 = suds.cache.FileCache(cache_folder)
        assert cache2.get("unga1") == value_p11
        assert cache2.get("unga2") == value_p2
        cache2.put("unga2", value_f2)
        cache2.put("unga3", value_f3)
        assert cache1.get("unga2") == value_f2
        assert cache1.get("unga3") == value_f3
        cache1.purge("unga2")
        assert cache2.get("unga2") is None
        cache1.clear()
        assert cache2.get("unga1") is None
        assert cache2.get("unga3") is None

    @pytest.mark.parametrize("params", (
        {},
        {"microseconds": 1},
        {"milliseconds": 1},
        {"seconds": 1},
        {"minutes": 1},
        {"hours": 1},
        {"days": 1},
        {"weeks": 1},
        {"microseconds": -1},
        {"milliseconds": -1},
        {"seconds": -1},
        {"minutes": -1},
        {"hours": -1},
        {"days": -1},
        {"weeks": -1},
        {"weeks": 1, "days": 2, "hours": 7, "minutes": 0, "seconds": -712}))
    def test_set_durations(self, tmpdir, params):
        cache = suds.cache.FileCache(tmpdir.strpath, **params)
        assert cache.duration == datetime.timedelta(**params)

    def test_version(self, tmpdir):
        fake_version_info = "--- fake version info ---"
        assert suds.__version__ != fake_version_info

        version_file = tmpdir.join("version")
        cache_folder = tmpdir.strpath
        cache = suds.cache.FileCache(cache_folder)
        assert version_file.read() == suds.__version__
        cache.put("unga1", value_p1)

        version_file.write(fake_version_info)
        assert cache.get("unga1") == value_p1

        cache2 = suds.cache.FileCache(cache_folder)
        assert _is_empty_cache_folder(cache_folder)
        assert cache.get("unga1") is None
        assert cache2.get("unga1") is None
        assert version_file.read() == suds.__version__
        cache.put("unga1", value_p11)
        cache.put("unga2", value_p22)

        version_file.remove()
        assert cache.get("unga1") == value_p11
        assert cache.get("unga2") == value_p22

        cache3 = suds.cache.FileCache(cache_folder)
        assert _is_empty_cache_folder(cache_folder)
        assert cache.get("unga1") is None
        assert cache.get("unga2") is None
        assert cache2.get("unga1") is None
        assert cache3.get("unga1") is None
        assert version_file.read() == suds.__version__


def test_NoCache(monkeypatch):
    cache = suds.cache.NoCache()
    assert isinstance(cache, suds.cache.Cache)

    assert cache.get("id") == None
    cache.put("id", "something")
    assert cache.get("id") == None

    # TODO: It should not be an error to call clear() or purge() on a NoCache
    # instance.
    monkeypatch.delitem(locals(), "e", False)
    e = pytest.raises(Exception, cache.purge, "id").value
    assert str(e) == "not-implemented"
    e = pytest.raises(Exception, cache.clear).value
    assert str(e) == "not-implemented"


class TestObjectCache:

    def test_basic(self, tmpdir):
        cache = suds.cache.ObjectCache(tmpdir.strpath)
        assert isinstance(cache, suds.cache.FileCache)
        assert cache.get("unga1") is None
        assert cache.get("unga2") is None
        cache.put("unga1", InvisibleMan(1))
        cache.put("unga2", InvisibleMan(2))
        read1 = cache.get("unga1")
        read2 = cache.get("unga2")
        assert read1.__class__ is InvisibleMan
        assert read2.__class__ is InvisibleMan
        assert read1.x == 1
        assert read2.x == 2

    def test_file_open_failure(self, tmpdir, monkeypatch):
        """
        File open failure should cause no cached object to be found, but any
        existing underlying cache file should be kept around.

        """
        mock_open = MockFileOpener(fail_open=True)

        cache_folder = tmpdir.strpath
        cache = suds.cache.ObjectCache(cache_folder)
        cache.put("unga1", InvisibleMan(1))

        mock_open.apply(monkeypatch)
        assert cache.get("unga1") is None
        monkeypatch.undo()
        assert mock_open.counter == 1
        assert not _is_empty_cache_folder(cache_folder)
        assert cache.get("unga1").x == 1

        mock_open.apply(monkeypatch)
        assert cache.get("unga2") is None
        monkeypatch.undo()
        assert mock_open.counter == 2
        assert not _is_empty_cache_folder(cache_folder)
        assert cache.get("unga1").x == 1
        assert cache.get("unga2") is None

        cache.put("unga2", InvisibleMan(2))
        assert mock_open.counter == 2

        mock_open.apply(monkeypatch)
        assert cache.get("unga1") is None
        monkeypatch.undo()
        assert mock_open.counter == 3
        assert not _is_empty_cache_folder(cache_folder)

        assert cache.get("unga1").x == 1
        assert cache.get("unga2").x == 2
        assert mock_open.counter == 3

    @pytest.mark.parametrize(("mock", "extra_checks"), (
        (MockPickleLoad(), [lambda x: True] * 4),
        (MockFileOpener(fail_read=True), [
            lambda x: x.read_counter != 0,
            lambda x: x.read_counter == 0,
            lambda x: x.read_counter != 0,
            lambda x: x.read_counter == 0])))
    def test_file_operation_failure(self, tmpdir, monkeypatch, mock,
            extra_checks):
        """
        Open file operation failures such as reading failures or failing to
        unpickle the data read from such a file should cause no cached object
        to be found and the related cache file to be removed.

        """
        cache_folder = tmpdir.strpath
        cache = suds.cache.ObjectCache(cache_folder)
        cache.put("unga1", InvisibleMan(1))

        mock.apply(monkeypatch)
        assert cache.get("unga1") is None
        monkeypatch.undo()
        assert mock.counter == 1
        assert extra_checks[0](mock)
        assert _is_empty_cache_folder(cache_folder)

        mock.reset()
        assert cache.get("unga1") is None
        cache.put("unga1", InvisibleMan(1))
        cache.put("unga2", InvisibleMan(2))
        assert mock.counter == 0
        assert extra_checks[1](mock)

        mock.reset()
        mock.apply(monkeypatch)
        assert cache.get("unga1") is None
        monkeypatch.undo()
        assert mock.counter == 1
        assert extra_checks[2](mock)
        assert not _is_empty_cache_folder(cache_folder)

        mock.reset()
        assert cache.get("unga1") is None
        assert cache.get("unga2").x == 2
        assert mock.counter == 0
        assert extra_checks[3](mock)

    @pytest.mark.parametrize(("duration", "current_time", "expect_remove"),
        file_cache_item_expiration_test_data)
    def test_item_expiration(self, tmpdir, monkeypatch, duration, current_time,
            expect_remove):
        """See TestFileCache.item_expiration_test_worker() for more info."""
        cache = suds.cache.ObjectCache(tmpdir.strpath, **duration)
        cache.put("silly", InvisibleMan(666))
        TestFileCache.item_expiration_test_worker(cache, "silly", monkeypatch,
            current_time, expect_remove)


def _is_empty_cache_folder(folder):
    assert os.path.isdir(folder)
    def walkError(error):
        pytest.fail("Error attempting to walk through cache folder contents.")
    count = 0
    for root, folders, files in os.walk(folder, onerror=walkError):
        assert root == folder
        return len(folders) == 0 and len(files) == 1 and files[0] == 'version'
    return False
