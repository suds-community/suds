# -*- coding: utf-8 -*-

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

import os
import tempfile


class InvisibleMan:
    """Dummy class used for pickling related tests."""
    def __init__(self, x):
        self.x = x


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


def test_Cache():
    cache = suds.cache.Cache()
    pytest.raises(Exception, cache.get, "id")
    pytest.raises(Exception, cache.put, "id", "object")
    pytest.raises(Exception, cache.purge, "id")
    pytest.raises(Exception, cache.clear)


def test_DocumentCache(tmpdir):
    cacheFolder = tmpdir.join("puffy").strpath
    cache = suds.cache.DocumentCache(cacheFolder)
    assert isinstance(cache, suds.cache.FileCache)
    assert cache.get("unga1") is None

    # TODO: DocumentCache class interface seems silly. Its get() operation
    # returns an XML document while its put() operation takes an XML element.
    # The put() operation also silently ignores passed data of incorrect type.
    # TODO: Update this test to no longer depend on the exact input XML data
    # formatting. We currently expect it to be formatted exactly as what gets
    # read back from the DocumentCache.
    content = suds.byte_str("""\
<xsd:element name="Elemento">
   <xsd:simpleType>
      <xsd:restriction base="xsd:string">
         <xsd:enumeration value="alfa"/>
         <xsd:enumeration value="beta"/>
         <xsd:enumeration value="gamma"/>
      </xsd:restriction>
   </xsd:simpleType>
</xsd:element>""")
    xml = suds.sax.parser.Parser().parse(suds.BytesIO(content))
    cache.put("unga1", xml.getChildren()[0])
    readXML = cache.get("unga1")
    assert isinstance(readXML, suds.sax.document.Document)
    readXMLElements = readXML.getChildren()
    assert len(readXMLElements) == 1
    readXMLElement = readXMLElements[0]
    assert isinstance(readXMLElement, suds.sax.element.Element)
    assert suds.byte_str(str(readXMLElement)) == content


def test_FileCache():
    cache = suds.cache.FileCache()
    assert isinstance(cache, suds.cache.Cache)


def test_FileCache_clear(tmpdir):
    cacheFolder1 = tmpdir.join("fungus").strpath
    cache1 = suds.cache.FileCache(cacheFolder1)
    cache1.put("unga1", value_p1)
    cache1.put("unga2", value_p2)
    assert cache1.get("unga1") == value_p1
    assert cache1.get("unga2") == value_p2
    cache1.clear()
    assert _isEmptyCacheFolder(cacheFolder1)
    assert cache1.get("unga1") is None
    assert cache1.get("unga2") is None
    cache1.put("unga1", value_p11)
    cache1.put("unga2", value_p2)
    assert cache1.get("unga1") == value_p11
    assert cache1.get("unga2") == value_p2

    cacheFolder2 = tmpdir.join("broccoli").strpath
    cache2 = suds.cache.FileCache(cacheFolder2)
    cache2.put("unga2", value_f2)
    assert cache2.get("unga2") == value_f2
    cache2.clear()
    assert not _isEmptyCacheFolder(cacheFolder1)
    assert _isEmptyCacheFolder(cacheFolder2)
    assert cache2.get("unga2") is None
    assert cache1.get("unga1") == value_p11
    assert cache1.get("unga2") == value_p2
    cache2.put("unga2", value_p22)
    assert cache2.get("unga2") == value_p22


def test_FileCache_location(tmpdir):
    defaultLocation = os.path.join(tempfile.gettempdir(), "suds")
    cache = suds.cache.FileCache()
    assert os.path.isdir(cache.location)
    assert cache.location == defaultLocation
    assert suds.cache.FileCache().location == defaultLocation
    assert cache.location == defaultLocation

    cacheFolder1 = tmpdir.join("flip-flop1").strpath
    assert not os.path.isdir(cacheFolder1)
    assert suds.cache.FileCache(location=cacheFolder1).location == cacheFolder1
    assert _isEmptyCacheFolder(cacheFolder1)

    cacheFolder2 = tmpdir.join("flip-flop2").strpath
    assert not os.path.isdir(cacheFolder2)
    assert suds.cache.FileCache(cacheFolder2).location == cacheFolder2
    assert _isEmptyCacheFolder(cacheFolder2)


def test_FileCache_close_leaves_cached_files_behind(tmpdir):
    cacheFolder1 = tmpdir.join("ana").strpath
    cache1 = suds.cache.FileCache(cacheFolder1)
    cache1.put("unga1", value_p1)
    cache1.put("unga2", value_p2)

    cacheFolder2 = tmpdir.join("nan").strpath
    cache2 = suds.cache.FileCache(cacheFolder2)
    cache2.put("unga2", value_f2)
    cache2.put("unga3", value_f3)

    del cache1

    cache11 = suds.cache.FileCache(cacheFolder1)
    assert cache11.get("unga1") == value_p1
    assert cache11.get("unga2") == value_p2
    assert cache2.get("unga2") == value_f2
    assert cache2.get("unga3") == value_f3


def test_FileCache_get_put(tmpdir):
    cacheFolder1 = tmpdir.join("firefly").strpath
    cache1 = suds.cache.FileCache(cacheFolder1)
    assert _isEmptyCacheFolder(cacheFolder1)
    assert cache1.get("unga1") is None
    cache1.put("unga1", value_p1)
    assert not _isEmptyCacheFolder(cacheFolder1)
    assert cache1.get("unga1") == value_p1
    assert cache1.get("unga2") is None
    cache1.put("unga1", value_p11)
    assert cache1.get("unga1") == value_p11
    assert cache1.get("unga2") is None
    cache1.put("unga2", value_p2)
    assert cache1.get("unga1") == value_p11
    assert cache1.get("unga2") == value_p2

    cacheFolder2 = tmpdir.join("semper fi").strpath
    cache2 = suds.cache.FileCache(cacheFolder2)
    assert _isEmptyCacheFolder(cacheFolder2)
    assert cache2.get("unga2") is None
    cache2.put("unga2", value_f2)
    assert not _isEmptyCacheFolder(cacheFolder2)
    assert cache2.get("unga2") == value_f2
    assert cache2.get("unga3") is None
    cache2.put("unga2", value_f22)
    assert cache2.get("unga2") == value_f22
    assert cache2.get("unga3") is None
    cache2.put("unga3", value_f3)
    assert cache2.get("unga2") == value_f22
    assert cache2.get("unga3") == value_f3

    assert not _isEmptyCacheFolder(cacheFolder1)
    assert not _isEmptyCacheFolder(cacheFolder2)
    assert cache1.get("unga1") == value_p11
    assert cache1.get("unga2") == value_p2
    assert cache1.get("unga3") is None
    assert cache2.get("unga1") is None
    assert cache2.get("unga2") == value_f22
    assert cache2.get("unga3") == value_f3


def test_FileCache_purge(tmpdir):
    cacheFolder1 = tmpdir.join("flamenco").strpath
    cache1 = suds.cache.FileCache(cacheFolder1)
    cache1.put("unga1", value_p1)
    assert cache1.get("unga1") == value_p1
    cache1.purge("unga1")
    assert _isEmptyCacheFolder(cacheFolder1)
    assert cache1.get("unga1") is None
    cache1.put("unga1", value_p11)
    cache1.put("unga2", value_p2)
    assert cache1.get("unga1") == value_p11
    assert cache1.get("unga2") == value_p2
    cache1.purge("unga1")
    assert cache1.get("unga1") is None
    assert cache1.get("unga2") == value_p2
    cache1.put("unga1", value_p111)

    cacheFolder2 = tmpdir.join("shadow").strpath
    cache2 = suds.cache.FileCache(cacheFolder2)
    cache2.put("unga2", value_f2)
    cache2.purge("unga2")
    assert _isEmptyCacheFolder(cacheFolder2)
    assert cache1.get("unga1") == value_p111
    assert cache1.get("unga2") == value_p2
    assert cache2.get("unga2") is None


def test_FileCache_reused_cache_folder(tmpdir):
    cacheFolder = tmpdir.strpath
    cache1 = suds.cache.FileCache(cacheFolder)
    assert _isEmptyCacheFolder(cacheFolder)
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

    cache2 = suds.cache.FileCache(cacheFolder)
    assert cache2.get("unga1") == value_p11
    assert cache2.get("unga2") == value_p2
    cache2.put("unga3", value_f3)
    assert cache1.get("unga3") == value_f3


def test_FileCache_version(tmpdir):
    fakeVersionInfo = "--- fake version info ---"
    assert suds.__version__ != fakeVersionInfo

    cacheFolder = tmpdir.join("hitori")
    versionFile = cacheFolder.join("version")
    cache = suds.cache.FileCache(cacheFolder.strpath)
    assert versionFile.read() == suds.__version__
    cache.put("unga1", value_p1)

    versionFile.write(fakeVersionInfo)
    assert cache.get("unga1") == value_p1

    cache2 = suds.cache.FileCache(cacheFolder.strpath)
    assert _isEmptyCacheFolder(cacheFolder.strpath)
    assert cache.get("unga1") is None
    assert cache2.get("unga1") is None
    assert versionFile.read() == suds.__version__
    cache.put("unga1", value_p11)
    cache.put("unga2", value_p22)

    versionFile.remove()
    assert cache.get("unga1") == value_p11
    assert cache.get("unga2") == value_p22

    cache3 = suds.cache.FileCache(cacheFolder.strpath)
    assert _isEmptyCacheFolder(cacheFolder.strpath)
    assert cache.get("unga1") is None
    assert cache.get("unga2") is None
    assert cache2.get("unga1") is None
    assert versionFile.read() == suds.__version__


def test_FileCache_with_empty_cached_content(tmpdir):
    cacheFolder = tmpdir.strpath
    cache = suds.cache.FileCache(cacheFolder)
    cache.put("unga1", value_empty)
    assert cache.get("unga1") == value_empty
    assert not _isEmptyCacheFolder(cacheFolder)


def test_FileCache_with_random_utf_character_cached_content(tmpdir):
    cacheFolder = tmpdir.strpath
    cache = suds.cache.FileCache(cacheFolder)
    cache.put("unga1", value_unicode)
    assert cache.get("unga1") == value_unicode
    assert not _isEmptyCacheFolder(cacheFolder)


def test_NoCache():
    cache = suds.cache.NoCache()
    assert isinstance(cache, suds.cache.Cache)

    assert cache.get("id") == None
    cache.put("id", "something")
    assert cache.get("id") == None

    # TODO: It should not be an error to call purge() or clear() on a NoCache
    # instance.
    pytest.raises(Exception, cache.purge, "id")
    pytest.raises(Exception, cache.clear)


def test_ObjectCache(tmpdir):
    cacheFolder = tmpdir.join("george carlin").strpath
    cache = suds.cache.ObjectCache(cacheFolder)
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


def _isEmptyCacheFolder(folder):
    assert os.path.isdir(folder)
    def walkError(error):
        pytest.fail("Error attempting to walk through cache folder contents.")
    count = 0
    for root, folders, files in os.walk(folder, onerror=walkError):
        assert root == folder
        return len(folders) == 0 and len(files) == 1 and files[0] == 'version'
    return False
