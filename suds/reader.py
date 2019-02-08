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
# written by: Jeff Ortel ( jortel@redhat.com )

"""
XML document reader classes providing integration with the suds library's
caching system.

"""

import suds.cache
import suds.plugin
import suds.sax.parser
import suds.transport

import time
import sys

try:
    from hashlib import md5
except ImportError:
    # 'hashlib' package added in Python 2.5 so use the now deprecated/removed
    # 'md5' package in older Python versions.
    from md5 import md5


class Reader(object):
    """
    Provides integration with the cache.

    @ivar options: An options object.
    @type options: I{Options}

    """

    def __init__(self, options):
        """
        @param options: An options object.
        @type options: I{Options}

        """
        self.options = options
        self.plugins = suds.plugin.PluginContainer(options.plugins)

    def mangle(self, name, x):
        """
        Mangle the name by hashing the I{name} and appending I{x}.

        @return: The mangled name.
        @rtype: str

        """
        h = md5(name.encode()).hexdigest()
        return '%s-%s' % (h, x)

import gc
class DefinitionsReader(Reader):
    """
    Integrates between the WSDL Definitions object and the object cache.

    @ivar fn: A factory function used to create objects not found in the cache.
    @type fn: I{Constructor}

    """

    def __init__(self, options, fn):
        """
        @param options: An options object.
        @type options: I{Options}
        @param fn: A factory function used to create objects not found in the
            cache.
        @type fn: I{Constructor}

        """
        super(DefinitionsReader, self).__init__(options)
        self.fn = fn

    def open(self, url):
        """
        Open a WSDL schema at the specified I{URL}.

        First, the WSDL schema is looked up in the I{object cache}. If not
        found, a new one constructed using the I{fn} factory function and the
        result is cached for the next open().

        @param url: A WSDL URL.
        @type url: str.
        @return: The WSDL object.
        @rtype: I{Definitions}

        """
        cache = self.__cache()
        id = self.mangle(url, "wsdl")
        start = time.time()
        # disable garbage collector
        gc.disable()
        wsdl = cache.get(id)
        # enable garbage collector again
        gc.enable()
        end = time.time()
        cache_get = end - start
        if wsdl is None:
            start = time.time()
            wsdl = self.fn(url, self.options)
            end = time.time()
            sys.stdout.write('self.fn '+str(end-start)+'\n')
            cache.put(id, wsdl)
        else:
            # Cached WSDL Definitions objects may have been created with
            # different options so we update them here with our current ones.
            wsdl.options = self.options
            for imp in wsdl.imports:
                imp.imported.options = self.options
            sys.stdout.write('cache.get '+str(cache_get)+'\n')
        return wsdl

    def __cache(self):
        """
        Get the I{object cache}.

        @return: The I{cache} when I{cachingpolicy} = B{1}.
        @rtype: L{Cache}

        """
        if self.options.cachingpolicy == 1:
            return self.options.cache
        return suds.cache.NoCache()


class DocumentReader(Reader):
    """Integrates between the SAX L{Parser} and the document cache."""

    def open(self, url):
        """
        Open an XML document at the specified I{URL}.

        First, a preparsed document is looked up in the I{object cache}. If not
        found, its content is fetched from an external source and parsed using
        the SAX parser. The result is cached for the next open().

        @param url: A document URL.
        @type url: str.
        @return: The specified XML document.
        @rtype: I{Document}

        """
        cache = self.__cache()
        id = self.mangle(url, "document")
        xml = cache.get(id)
        if xml is None:
            xml = self.__fetch(url)
            cache.put(id, xml)
        start = time.time()
        self.plugins.document.parsed(url=url, document=xml.root())
        end = time.time()
        sys.stdout.write('documents.parsed '+str(end-start)+'\n')
        return xml

    def __cache(self):
        """
        Get the I{object cache}.

        @return: The I{cache} when I{cachingpolicy} = B{0}.
        @rtype: L{Cache}

        """
        if self.options.cachingpolicy == 0:
            return self.options.cache
        return suds.cache.NoCache()

    def __fetch(self, url):
        """
        Fetch document content from an external source.

        The document content will first be looked up in the registered document
        store, and if not found there, downloaded using the registered
        transport system.

        Before being returned, the fetched document content first gets
        processed by all the registered 'loaded' plugins.

        @param url: A document URL.
        @type url: str.
        @return: A file pointer to the fetched document content.
        @rtype: file-like

        """
        content = None
        store = self.options.documentStore
        if store is not None:
            content = store.open(url)
        if content is None:
            request = suds.transport.Request(url)
            fp = self.options.transport.open(request)
            try:
                content = fp.read()
            finally:
                fp.close()
        start = time.time()
        ctx = self.plugins.document.loaded(url=url, document=content)
        end = time.time()
        sys.stdout.write('document.loaded '+str(end-start)+'\n')
        content = ctx.document
        sax = suds.sax.parser.Parser()
        start = time.time()
        result = sax.parse(string=content)
        end = time.time()
        sys.stdout.write('sax.parse '+str(end-start)+'\n')
        return result
