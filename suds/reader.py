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

"""
Contains xml document reader classes.
"""


from suds.sax.parser import Parser
from suds.transport import Request
from suds.store import DocumentStore
from logging import getLogger


log = getLogger(__name__)


class ObjectId(object):
    
    def __init__(self, name, suffix):
        self.name = name
        self.suffix = suffix


class DocumentReader:
    """
    The XML document reader provides an integration
    between the SAX L{Parser} and the document cache.
    @cvar suffix: The cache file suffix.
    @type suffix: str
    @ivar options: An options object.
    @type options: I{Options}
    """
    
    suffix = 'pxd'
    
    def __init__(self, options):
        """
        @param options: An options object.
        @type options: I{Options}
        """
        self.options = options
    
    def open(self, url):
        """
        Open an XML document at the specified I{url}.
        First, the document attempted to be retrieved from
        the I{object cache}.  If not found, it is downloaded and
        parsed using the SAX parser.  The result is added to the
        cache for the next open().
        @param url: A document url.
        @type url: str.
        @return: The specified XML document.
        @rtype: I{Document}
        """
        id = ObjectId(url, self.suffix)
        cache = self.options.cache
        d = cache.get(id)
        if d is None:
            d = self.download(url)
            cache.put(id, d)
        return d
    
    def download(self, url):
        store = DocumentStore()
        fp = store.open(url)
        if fp is None:
            fp = self.options.transport.open(Request(url))
        sax = Parser()
        return sax.parse(file=fp)


class DefinitionsReader:
    """
    The WSDL definitions reader provides an integration
    between the Definitions and the object cache.
    @cvar suffix: The cache file suffix.
    @type suffix: str
    @ivar options: An options object.
    @type options: I{Options}
    @ivar fn: A factory function (constructor) used to
        create the object not found in the cache.
    @type fn: I{Constructor}
    """
    
    suffix = 'pw'
    
    def __init__(self, options, fn):
        """
        @param options: An options object.
        @type options: I{Options}
        @param fn: A factory function (constructor) used to
            create the object not found in the cache.
        @type fn: I{Constructor}
        """
        self.options = options
        self.fn = fn
    
    def open(self, url):
        """
        Open a WSDL at the specified I{url}.
        First, the WSDL attempted to be retrieved from
        the I{object cache}.  After unpickled from the cache, the
        I{options} attribute is restored.
        If not found, it is downloaded and instantiated using the 
        I{fn} constructor and added to the cache for the next open().
        @param url: A WSDL url.
        @type url: str.
        @return: The WSDL object.
        @rtype: I{Definitions}
        """
        id = ObjectId(url, self.suffix)
        cache = self.options.cache
        d = cache.get(id)
        if d is None:
            d = self.fn(url, self.options)
            cache.put(id, d)
        else:
            d.options = self.options
            for imp in d.imports:
                imp.imported.options = self.options
        return d
