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

import sys
import logging


def client_from_wsdl(wsdl_content, *args, **kwargs):
    """
    Constructs a non-caching suds Client based on the given WSDL content.

      Stores the content directly inside the suds library internal document
    store under a hard-coded id to avoid having to load the data from a
    temporary file.

      Caveats:
        * All files stored under the same id so each new local file overwrites
          the previous one.
        * We need to explicitly disable caching here or otherwise, because we
          are using the same id for all our local WSDL documents, suds would
          always reuse the first such local document from its cache.

    """
    # Idea for an alternative implementation:
    #   Custom suds.cache.Cache subclass that would know how to access our
    # locally stored documents or at least not cache them if we are storing
    # them inside the suds library DocumentStore. Not difficult, allows us to
    # have per-client instead of global configuration & allows us to support
    # other cache types but certainly not as short as the current
    # implementation.
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
