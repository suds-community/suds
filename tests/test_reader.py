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
suds.reader module unit tests.

Implemented using the 'pytest' testing framework.

"""

import testutils
if __name__ == "__main__":
    testutils.run_using_pytest(globals())

import suds
import suds.options
import suds.reader


class TestCacheItemNameMangling:
    """Tests suds.reader.Reader classes' cache item name mangling."""

    def test_different(self):
        test_item_name1 = "oh my god"
        test_item_name2 = "ha ha ha"
        test_item_suffix = "that's some funky sh*t"
        reader = suds.reader.Reader(suds.options.Options())
        mangled1 = reader.mangle(test_item_name1, test_item_suffix)
        mangled2 = reader.mangle(test_item_name2, test_item_suffix)
        assert mangled1 != mangled2

    def test_inter_processes_persistence(self, tmpdir):
        """
        Same cache item names must be mangled the same in different processes.

        This is a regression test against using a built-in Python hash()
        function internally since that function may be seeded by a process
        specific random seed. This Python interpreter behaviour has been
        enabled by default since Python 3.3 and may be explicitly enabled on
        earlier Python interpreter versions as well.

        """
        test_item_name = "test string"
        test_item_suffix = "test suffix"
        reader = suds.reader.Reader(suds.options.Options())
        expected = reader.mangle(test_item_name, test_item_suffix)
        test_file = tmpdir.join("test_mangle.py")
        test_file.write("""
import suds.options
import suds.reader
reader = suds.reader.Reader(suds.options.Options())
mangled = reader.mangle("%(test_item_name)s", "%(test_item_suffix)s")
assert mangled == '%(expected)s'
""" % {"expected": expected,
    "test_item_name": test_item_name,
    "test_item_suffix": test_item_suffix})
        testutils.run_test_process(test_file)

    def test_repeatable__different_readers(self):
        test_item_name = "R2D2"
        test_item_suffix = "C3P0"
        reader1 = suds.reader.Reader(suds.options.Options())
        reader2 = suds.reader.Reader(suds.options.Options())
        mangled1 = reader1.mangle(test_item_name, test_item_suffix)
        mangled2 = reader2.mangle(test_item_name, test_item_suffix)
        assert mangled1 == mangled2

    def test_repeatable__same_reader(self):
        test_item_name = "han solo"
        test_item_suffix = "chewbacca"
        reader = suds.reader.Reader(suds.options.Options())
        mangled1 = reader.mangle(test_item_name, test_item_suffix)
        mangled2 = reader.mangle(test_item_name, test_item_suffix)
        assert mangled1 == mangled2

    def test_suffix(self):
        test_item_name = "and a one! and a two! and a one - two - three!"
        test_item_suffix = "pimpl"
        reader = suds.reader.Reader(suds.options.Options())
        mangled = reader.mangle(test_item_name, test_item_suffix)
        assert mangled.endswith(test_item_suffix)
