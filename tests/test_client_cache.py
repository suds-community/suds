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
Suds Python library client cache related unit tests.

Implemented using the 'pytest' testing framework.

"""

if __name__ == "__main__":
    import __init__
    __init__.runUsingPyTest(globals())


import suds
import suds.cache
import suds.store

import pytest


class MyException(Exception):
    """Local exception class used in this testing module."""
    pass


def test_default_cache_construction(monkeypatch):
    """
    Test when and how client creates its default cache object.

    We use a dummy store to get an expected exception rather than attempting to
    access the network, in case the test fails and the expected default cache
    object does not get created or gets created too late.

    """
    def constructDefaultCache(days):
        assert days == 1
        raise MyException
    class MockStore(suds.store.DocumentStore):
        def open(self, *args, **kwargs):
            pytest.fail("Default cache not created in time.")
    monkeypatch.setattr("suds.client.ObjectCache", constructDefaultCache)
    monkeypatch.setattr("suds.store.DocumentStore", MockStore)
    pytest.raises(MyException, suds.client.Client, "some_url",
        documentStore=MockStore())


@pytest.mark.parametrize("cache", (
    None,
    suds.cache.NoCache(),
    suds.cache.ObjectCache()))
def test_avoiding_default_cache(cache, monkeypatch):
    """Explicitly specified cache should avoid default cache construction."""
    def constructDefaultCache(*args, **kwargs):
        pytest.fail("Unexpected default cache instantiation.")
    class MockStore(suds.store.DocumentStore):
        def open(self, *args, **kwargs):
            raise MyException
    monkeypatch.setattr("suds.client.ObjectCache", constructDefaultCache)
    monkeypatch.setattr("suds.store.DocumentStore", MockStore)
    pytest.raises(MyException, suds.client.Client, "some_url",
        documentStore=MockStore(), cache=cache)
