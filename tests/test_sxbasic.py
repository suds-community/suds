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
sxbasic module unit tests.

Implemented using the 'pytest' testing framework.

"""

import testutils
if __name__ == "__main__":
    testutils.run_using_pytest(globals())

import suds.xsd.sxbasic


class TestImport:

    def test_bind(self):
        ns = "http://www.w3.org/2001/XMLSchema"
        location = "http://www.w3.org/2001/XMLSchema.xsd"
        suds.xsd.sxbasic.Import.bind(ns, location)
        assert(suds.xsd.sxbasic.Import.locations[ns], location)

        new_location = "file://home/me/XMLSchema.xsd"
        suds.xsd.sxbasic.Import.bind(ns, new_location)
        assert(suds.xsd.sxbasic.Import.locations[ns], location)

    def test_replace(self):
        ns = "http://www.w3.org/2001/XMLSchema"
        new_location = "file://home/me/XMLSchema.xsd"
        suds.xsd.sxbasic.Import.replace(ns, new_location)
        assert(suds.xsd.sxbasic.Import.locations[ns], new_location)
