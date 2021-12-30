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

import testutils
if __name__ == "__main__":
    testutils.run_using_pytest(globals())

import suds
import suds.cache
import suds.sax.parser

import pytest
from six import b, next, u

import datetime
import os
import os.path
import sys


class MyException(Exception):
    """Local exception class used in the tests in this module."""
    pass


class InvisibleMan:
    """Dummy class used for pickling related tests."""
    def __init__(self, x):
        self.x = x


class MockDateTime(datetime.datetime):
    """
    MockDateTime class monkeypatched to replace datetime.datetime.

    Allows us to control the exact built-in datetime.datetime.now() return
    value. Note that Python does not allow us to monkeypatch
    datetime.datetime.now() directly as it is a built-in function.

    """

    mock_counter = 0

    @staticmethod
    def now(*args, **kwargs):
        MockDateTime.mock_counter += 1
        return MockDateTime.mock_value


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
value_empty = b("")
value_f2 = b("fifi2")
value_f22 = b("fifi22")
value_f3 = b("fifi3")
value_p1 = b("pero1")
value_p11 = b("pero11")
value_p111 = b("pero111")
value_p2 = b("pero2")
value_p22 = b("pero22")
value_unicode = u("\u20AC \u7684 "
    "\u010D\u0107\u017E\u0161\u0111"
    "\u010C\u0106\u017D\u0160\u0110").encode("utf-8")


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
    try:
        assert e.__class__ is Exception
        assert str(e) == "not-implemented"
    finally:
        del e  # explicitly break circular reference chain in Python 3


class TestDefaultFileCacheLocation:
    """Default FileCache cache location handling tests."""

    @pytest.mark.parametrize("cache_class", (
        suds.cache.DocumentCache,
        suds.cache.FileCache,
        suds.cache.ObjectCache))
    def test_basic(self, tmpdir, cache_class):
        """
        Test default FileCache folder usage.

        Initial DocumentCache/FileCache/ObjectCache instantiation with no
        explicitly specified location in a process should use
        tempfile.mkdtemp() and that folder should be used as its location.

        After a single DocumentCache/FileCache/ObjectCache instantiation with
        no explicitly specified location, all later DocumentCache/FileCache/
        ObjectCache instantiations with no explicitly specified location in the
        same process should use that same location folder without additional
        tempfile.mkdtemp() calls.

        Both initial & non-initial DocumentCache/FileCache/ObjectCache
        instantiation with an explicitly specified location should use that
        folder as its default location and not make any tempfile.mkdtemp()
        calls.

        """
        cache_folder_name = "my test cache-%s" % (cache_class.__name__,)
        cache_folder = tmpdir.join(cache_folder_name).strpath
        fake_cache_folder_name = "my fake cache-%s" % (cache_class.__name__,)
        fake_cache_folder = tmpdir.join(fake_cache_folder_name).strpath
        test_file = tmpdir.join("test_file.py")
        test_file.write("""\
import os.path

import tempfile
original_mkdtemp = tempfile.mkdtemp
mock_mkdtemp_counter = 0
def mock_mkdtemp(*args, **kwargs):
    global mock_mkdtemp_counter
    mock_mkdtemp_counter += 1
    return cache_folder
tempfile.mkdtemp = mock_mkdtemp

def check_cache_folder(expected_exists, expected_mkdtemp_counter, comment):
    if os.path.exists(cache_folder) != expected_exists:
        if expected_exists:
            message = "does not exist when expected"
        else:
            message = "exists when not expected"
        print("Cache folder %%s (%%s)." %% (message, comment))
        sys.exit(-2)
    if mock_mkdtemp_counter != expected_mkdtemp_counter:
        if mock_mkdtemp_counter < expected_mkdtemp_counter:
            message = "less"
        else:
            message = "more"
        print("tempfile.mkdtemp() called %%s times then expected (%%s)" %%
            (message, comment,))

cache_folder = %(cache_folder)r
fake_cache_folder = %(fake_cache_folder)r
def fake_cache(n):
    return fake_cache_folder + str(n)

from suds.cache import DocumentCache, FileCache, ObjectCache
check_cache_folder(False, 0, "import")

assert DocumentCache(fake_cache(1)).location == fake_cache(1)
assert FileCache(fake_cache(2)).location == fake_cache(2)
assert ObjectCache(fake_cache(3)).location == fake_cache(3)
check_cache_folder(False, 0, "initial caches with non-default location")

assert %(cache_class_name)s().location == cache_folder
check_cache_folder(True, 1, "initial cache with default location")

assert DocumentCache().location == cache_folder
assert FileCache().location == cache_folder
assert ObjectCache().location == cache_folder
check_cache_folder(True, 1, "non-initial caches with default location")

assert DocumentCache(fake_cache(4)).location == fake_cache(4)
assert FileCache(fake_cache(5)).location == fake_cache(5)
assert ObjectCache(fake_cache(6)).location == fake_cache(6)
check_cache_folder(True, 1, "non-initial caches with non-default location")

assert DocumentCache().location == cache_folder
assert FileCache().location == cache_folder
assert ObjectCache().location == cache_folder
check_cache_folder(True, 1, "final caches with default location")
""" % {"cache_class_name": cache_class.__name__,
    "cache_folder": cache_folder,
    "fake_cache_folder": fake_cache_folder})

        assert not os.path.exists(cache_folder)
        testutils.run_test_process(test_file)

    @pytest.mark.parametrize("removal_enabled", (True, False))
    def test_remove_on_exit(self, tmpdir, removal_enabled):
        """
        Test removing the default cache folder on process exit.

        The folder should be removed by default on process exit, but this
        behaviour may be disabled by the user.

        """
        cache_folder_name = "my test cache-%s" % (removal_enabled,)
        cache_folder = tmpdir.join(cache_folder_name).strpath
        test_file = tmpdir.join("test_file.py")
        test_file.write("""\
import os.path

import tempfile
original_mkdtemp = tempfile.mkdtemp
mock_mkdtemp_counter = 0
def mock_mkdtemp(*args, **kwargs):
    global mock_mkdtemp_counter
    mock_mkdtemp_counter += 1
    return cache_folder
tempfile.mkdtemp = mock_mkdtemp

import suds.cache
if not suds.cache.FileCache.remove_default_location_on_exit:
    print("Default FileCache folder removal not enabled by default.")
    sys.exit(-2)
suds.cache.FileCache.remove_default_location_on_exit = %(removal_enabled)s

cache_folder = %(cache_folder)r
if os.path.exists(cache_folder):
    print("Cache folder exists too early.")
    sys.exit(-2)

suds.cache.FileCache()

if not mock_mkdtemp_counter == 1:
    print("tempfile.mkdtemp() not called as expected (%%d)." %%
        (mock_mkdtemp_counter,))
    sys.exit(-2)

if not os.path.isdir(cache_folder):
    print("Cache folder not created when expected.")
    sys.exit(-2)
""" % {"cache_folder": cache_folder, "removal_enabled": removal_enabled})

        assert not os.path.exists(cache_folder)
        testutils.run_test_process(test_file)
        if removal_enabled:
            assert not os.path.exists(cache_folder)
        else:
            assert os.path.isdir(cache_folder)


class TestDocumentCache:

    def compare_document_to_content(self, document, content):
        """Assert that the given XML document and content match."""
        assert document.__class__ is suds.sax.document.Document
        elements = document.getChildren()
        assert len(elements) == 1
        element = elements[0]
        assert element.__class__ is suds.sax.element.Element
        assert suds.byte_str(str(element)) == content

    @staticmethod
    def construct_XML(element_name="Elemento"):
        """
        Construct XML content and a Document wrapping it.

        The XML contains a single Element (may be parametrized with the given
        element name) and possibly additional sub-elements under it.

        """
        #TODO: Update the tests in this group to no longer depend on the exact
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
        assert xml.__class__ is suds.sax.document.Document
        return content, xml

    def test_cache_document(self, tmpdir):
        cache_item_id = "unga1"
        cache = suds.cache.DocumentCache(tmpdir.strpath)
        assert isinstance(cache, suds.cache.FileCache)
        assert cache.get(cache_item_id) is None
        content, document = self.construct_XML()
        cache.put(cache_item_id, document)
        self.compare_document_to_content(cache.get(cache_item_id), content)

    def test_cache_element(self, tmpdir):
        cache_item_id = "unga1"
        cache = suds.cache.DocumentCache(tmpdir.strpath)
        assert isinstance(cache, suds.cache.FileCache)
        assert cache.get(cache_item_id) is None
        content, document = self.construct_XML()
        cache.put(cache_item_id, document.root())
        self.compare_document_to_content(cache.get(cache_item_id), content)

    def test_file_open_failure(self, tmpdir, monkeypatch):
        """
        File open failure should cause no cached object to be found, but any
        existing underlying cache file should be kept around.

        """
        mock_open = MockFileOpener(fail_open=True)

        cache_folder = tmpdir.strpath
        cache = suds.cache.DocumentCache(cache_folder)
        content1, document1 = self.construct_XML("One")
        content2, document2 = self.construct_XML("Two")
        assert content1 != content2
        cache.put("unga1", document1)

        mock_open.apply(monkeypatch)
        assert cache.get("unga1") is None
        monkeypatch.undo()
        assert mock_open.counter == 1
        _assert_empty_cache_folder(cache_folder, expected=False)
        self.compare_document_to_content(cache.get("unga1"), content1)

        mock_open.apply(monkeypatch)
        assert cache.get("unga2") is None
        monkeypatch.undo()
        assert mock_open.counter == 2
        _assert_empty_cache_folder(cache_folder, expected=False)
        self.compare_document_to_content(cache.get("unga1"), content1)
        assert cache.get("unga2") is None

        cache.put("unga2", document2)
        assert mock_open.counter == 2

        mock_open.apply(monkeypatch)
        assert cache.get("unga1") is None
        monkeypatch.undo()
        assert mock_open.counter == 3
        _assert_empty_cache_folder(cache_folder, expected=False)

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
        content1, document1 = self.construct_XML("Eins")
        content2, document2 = self.construct_XML("Zwei")
        cache.put("unga1", document1)

        mock.apply(monkeypatch)
        assert cache.get("unga1") is None
        monkeypatch.undo()
        assert mock.counter == 1
        assert extra_checks[0](mock)
        _assert_empty_cache_folder(cache_folder)

        mock.reset()
        assert cache.get("unga1") is None
        cache.put("unga1", document1)
        cache.put("unga2", document2)
        assert mock.counter == 0
        assert extra_checks[1](mock)

        mock.reset()
        mock.apply(monkeypatch)
        assert cache.get("unga1") is None
        monkeypatch.undo()
        assert mock.counter == 1
        assert extra_checks[2](mock)
        _assert_empty_cache_folder(cache_folder, expected=False)

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
        content, document = self.construct_XML()
        cache.put("willy", document)
        TestFileCache.item_expiration_test_worker(cache, "willy", monkeypatch,
            current_time, expect_remove)

    def test_repeated_reads(self, tmpdir):
        cache = suds.cache.DocumentCache(tmpdir.strpath)
        content, document = self.construct_XML()
        cache.put("unga1", document)
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

        MockDateTime.mock_counter = 0
        if isinstance(current_time, datetime.timedelta):
            expire_time = file_time + cache.duration
            MockDateTime.mock_value = expire_time + current_time
        else:
            MockDateTime.mock_value = current_time
        monkeypatch.setattr(datetime, "datetime", MockDateTime)
        fp = cache._getf(id)
        assert (fp is None) == expect_remove
        if fp:
            fp.close()
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
        _assert_empty_cache_folder(cache_folder, expected=False)

    def test_cached_content_unicode(self, tmpdir):
        cache_folder = tmpdir.strpath
        cache = suds.cache.FileCache(cache_folder)
        cache.put("unga1", value_unicode)
        assert cache.get("unga1") == value_unicode
        _assert_empty_cache_folder(cache_folder, expected=False)

    def test_clear(self, tmpdir):
        cache_folder1 = tmpdir.join("fungus").strpath
        cache1 = suds.cache.FileCache(cache_folder1)
        cache1.put("unga1", value_p1)
        _assert_empty_cache_folder(cache_folder1, expected=False)
        cache1.put("unga2", value_p2)
        _assert_empty_cache_folder(cache_folder1, expected=False)
        assert cache1.get("unga1") == value_p1
        assert cache1.get("unga2") == value_p2
        _assert_empty_cache_folder(cache_folder1, expected=False)
        cache1.clear()
        _assert_empty_cache_folder(cache_folder1)
        assert cache1.get("unga1") is None
        assert cache1.get("unga2") is None
        _assert_empty_cache_folder(cache_folder1)
        cache1.put("unga1", value_p11)
        cache1.put("unga2", value_p2)
        _assert_empty_cache_folder(cache_folder1, expected=False)
        assert cache1.get("unga1") == value_p11
        assert cache1.get("unga2") == value_p2
        _assert_empty_cache_folder(cache_folder1, expected=False)

        cache_folder2 = tmpdir.join("broccoli").strpath
        cache2 = suds.cache.FileCache(cache_folder2)
        cache2.put("unga2", value_f2)
        assert cache2.get("unga2") == value_f2
        assert cache1.get("unga2") == value_p2
        cache2.clear()
        _assert_empty_cache_folder(cache_folder1, expected=False)
        _assert_empty_cache_folder(cache_folder2)
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
        _assert_empty_cache_folder(cache_folder1)
        assert cache1.get("unga1") is None
        cache1.put("unga1", value_p1)
        _assert_empty_cache_folder(cache_folder1, expected=False)
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
        _assert_empty_cache_folder(cache_folder2)
        assert cache2.get("unga2") is None
        cache2.put("unga2", value_f2)
        _assert_empty_cache_folder(cache_folder2, expected=False)
        assert cache2.get("unga2") == value_f2
        assert cache2.get("unga3") is None
        cache2.put("unga2", value_f22)
        assert cache2.get("unga2") == value_f22
        assert cache2.get("unga3") is None
        cache2.put("unga3", value_f3)
        assert cache2.get("unga2") == value_f22
        assert cache2.get("unga3") == value_f3

        _assert_empty_cache_folder(cache_folder1, expected=False)
        _assert_empty_cache_folder(cache_folder2, expected=False)
        assert cache1.get("unga1") == value_p11
        assert cache1.get("unga2") == value_p2
        assert cache1.get("unga3") is None
        assert cache2.get("unga1") is None
        assert cache2.get("unga2") == value_f22
        assert cache2.get("unga3") == value_f3

    def test_independent_item_expirations(self, tmpdir, monkeypatch):
        cache = suds.cache.FileCache(tmpdir.strpath, days=1)
        cache.put("unga1", value_p1)
        cache.put("unga2", value_p2)
        cache.put("unga3", value_f2)
        filepath1 = cache._FileCache__filename("unga1")
        filepath2 = cache._FileCache__filename("unga2")
        filepath3 = cache._FileCache__filename("unga3")
        file_timestamp1 = os.path.getctime(filepath1)
        file_timestamp2 = file_timestamp1 + 10 * 60  # in seconds
        file_timestamp3 = file_timestamp1 + 20 * 60  # in seconds
        file_time1 = datetime.datetime.fromtimestamp(file_timestamp1)
        file_time1_expiration = file_time1 + cache.duration

        original_getctime = os.path.getctime
        def mock_getctime(path):
            if path == filepath2:
                return file_timestamp2
            if path == filepath3:
                return file_timestamp3
            return original_getctime(path)

        timedelta = datetime.timedelta

        monkeypatch.setattr(os.path, "getctime", mock_getctime)
        monkeypatch.setattr(datetime, "datetime", MockDateTime)

        MockDateTime.mock_value = file_time1_expiration + timedelta(minutes=15)
        assert cache._getf("unga2") is None
        assert os.path.isfile(filepath1)
        assert not os.path.isfile(filepath2)
        assert os.path.isfile(filepath3)

        cache._getf("unga3").close()
        assert os.path.isfile(filepath1)
        assert not os.path.isfile(filepath2)
        assert os.path.isfile(filepath3)

        MockDateTime.mock_value = file_time1_expiration + timedelta(minutes=25)
        assert cache._getf("unga1") is None
        assert not os.path.isfile(filepath1)
        assert not os.path.isfile(filepath2)
        assert os.path.isfile(filepath3)

        assert cache._getf("unga3") is None
        assert not os.path.isfile(filepath1)
        assert not os.path.isfile(filepath2)
        assert not os.path.isfile(filepath3)

    @pytest.mark.parametrize(("duration", "current_time", "expect_remove"),
        file_cache_item_expiration_test_data)
    def test_item_expiration(self, tmpdir, monkeypatch, duration, current_time,
            expect_remove):
        """See TestFileCache.item_expiration_test_worker() for more info."""
        cache = suds.cache.FileCache(tmpdir.strpath, **duration)
        cache.put("unga1", value_p1)
        TestFileCache.item_expiration_test_worker(cache, "unga1", monkeypatch,
            current_time, expect_remove)

    def test_non_default_location(self, tmpdir):
        FileCache = suds.cache.FileCache

        cache_folder1 = tmpdir.join("flip-flop1").strpath
        assert not os.path.isdir(cache_folder1)
        assert FileCache(location=cache_folder1).location == cache_folder1
        _assert_empty_cache_folder(cache_folder1)

        cache_folder2 = tmpdir.join("flip-flop2").strpath
        assert not os.path.isdir(cache_folder2)
        assert FileCache(cache_folder2).location == cache_folder2
        _assert_empty_cache_folder(cache_folder2)

    def test_purge(self, tmpdir):
        cache_folder1 = tmpdir.join("flamenco").strpath
        cache1 = suds.cache.FileCache(cache_folder1)
        cache1.put("unga1", value_p1)
        assert cache1.get("unga1") == value_p1
        cache1.purge("unga1")
        _assert_empty_cache_folder(cache_folder1)
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
        _assert_empty_cache_folder(cache_folder2)
        assert cache1.get("unga1") == value_p111
        assert cache1.get("unga2") == value_p2
        assert cache2.get("unga2") is None

    def test_reused_cache_folder(self, tmpdir):
        cache_folder = tmpdir.strpath
        cache1 = suds.cache.FileCache(cache_folder)
        _assert_empty_cache_folder(cache_folder)
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
        _assert_empty_cache_folder(cache_folder)
        assert cache.get("unga1") is None
        assert cache2.get("unga1") is None
        assert version_file.read() == suds.__version__
        cache.put("unga1", value_p11)
        cache.put("unga2", value_p22)

        version_file.remove()
        assert cache.get("unga1") == value_p11
        assert cache.get("unga2") == value_p22

        cache3 = suds.cache.FileCache(cache_folder)
        _assert_empty_cache_folder(cache_folder)
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

    #TODO: It should not be an error to call clear() or purge() on a NoCache
    # instance.
    monkeypatch.delitem(locals(), "e", False)
    e = pytest.raises(Exception, cache.purge, "id").value
    try:
        assert str(e) == "not-implemented"
    finally:
        del e  # explicitly break circular reference chain in Python 3
    e = pytest.raises(Exception, cache.clear).value
    try:
        assert str(e) == "not-implemented"
    finally:
        del e  # explicitly break circular reference chain in Python 3


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
        _assert_empty_cache_folder(cache_folder, expected=False)
        assert cache.get("unga1").x == 1

        mock_open.apply(monkeypatch)
        assert cache.get("unga2") is None
        monkeypatch.undo()
        assert mock_open.counter == 2
        _assert_empty_cache_folder(cache_folder, expected=False)
        assert cache.get("unga1").x == 1
        assert cache.get("unga2") is None

        cache.put("unga2", InvisibleMan(2))
        assert mock_open.counter == 2

        mock_open.apply(monkeypatch)
        assert cache.get("unga1") is None
        monkeypatch.undo()
        assert mock_open.counter == 3
        _assert_empty_cache_folder(cache_folder, expected=False)

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
        _assert_empty_cache_folder(cache_folder)

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
        _assert_empty_cache_folder(cache_folder, expected=False)

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


def _assert_empty_cache_folder(folder, expected=True):
    """Test utility asserting that a cache folder is or is not empty."""
    if not _is_assert_enabled():
        return
    assert os.path.isdir(folder)
    def walk_error(error):
        pytest.fail("Error walking through cache folder content.")
    root, folders, files = next(os.walk(folder, onerror=walk_error))
    assert root == folder
    empty = len(folders) == 0 and len(files) == 1 and files[0] == 'version'
    if expected:
        assert len(folders) == 0
        assert len(files) == 1
        assert files[0] == 'version'
        assert empty, "bad test code"
    else:
        assert not empty, "unexpected empty cache folder"


def _is_assert_enabled():
    """Return whether Python assertions have been enabled in this module."""
    try:
        assert False
    except AssertionError:
        return True
    return False
