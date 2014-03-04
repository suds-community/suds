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
Suds SAX module's special character encoder profiler.

"""

import suds.sax.enc
import tests.profiling

import sys


"""Profiler parameter constants."""
NONE = 0
SOME = 1
MANY = 2
QUANTITY = {NONE: "NONE", SOME: "SOME", MANY: "MANY"}


class Profiler(tests.profiling.ProfilerBase):

    def __init__(self, long_input, replacements, cdata,
            show_each_timing=False, show_minimum=True):
        assert long_input in (True, False)
        assert replacements in QUANTITY
        assert cdata in QUANTITY

        super(Profiler, self).__init__(show_each_timing, show_minimum)

        self.encode_input = self.__construct_input(long_input, replacements,
            cdata, encoded=False)
        self.decode_input = self.__construct_input(long_input, replacements,
            cdata, encoded=True)

        print("long_input=%s; replacements=%s; cdata=%s" % (long_input,
            QUANTITY[replacements], QUANTITY[cdata]))
        print("  encode input data length: %d" % (len(self.encode_input),))
        print("  decode input data length: %d" % (len(self.decode_input),))

    def decode(self):
        suds.sax.enc.Encoder().decode(self.decode_input)

    def encode(self):
        suds.sax.enc.Encoder().encode(self.encode_input)

    def __construct_input(self, long_input, replacements, cdata, encoded):
        """Construct profiling input data matching the given parameters."""
        basic_input = "All that glitters is not gold."
        replacements_input = "<>&'"
        if encoded:
            replacements_input = "&gt;&lt;&amp;&apos"
        cdata_input = "<![CDATA[yaba-daba-duba]]>"

        # Approximate constructed input data size in bytes.
        size = 500
        if long_input:
            size = 1000000

        border_input = basic_input
        if replacements != NONE:
            border_input += replacements_input
        if cdata != NONE:
            border_input += cdata_input
        if replacements == MANY:
            basic_input += replacements_input
        if cdata == MANY:
            basic_input += cdata_input

        border_size = 2 * len(border_input)
        middle_size = max(size - border_size, 0)
        middle_count = middle_size // len(basic_input) + 1
        input = [border_input, basic_input * middle_count, border_input]
        return "".join(input)


if __name__ == "__main__":
    print("Python %s" % (sys.version,))
    print("")
    p = Profiler(long_input=True, replacements=MANY, cdata=MANY)
    p.timeit('encode', 18)
    p.timeit('decode', 170)
    print("")
    p = Profiler(long_input=False, replacements=MANY, cdata=MANY)
    p.timeit('encode', 24000)
    p.timeit('decode', 140000)
    print("")
    p = Profiler(long_input=True, replacements=MANY, cdata=NONE)
    p.timeit('encode', 16)
    p.timeit('decode', 150)
    print("")
    p = Profiler(long_input=False, replacements=MANY, cdata=NONE)
    p.timeit('encode', 21000)
    p.timeit('decode', 140000)
    print("")
    p = Profiler(long_input=True, replacements=NONE, cdata=NONE)
    p.timeit('encode', 250)
    p.timeit('decode', 450)
    print("")
    p = Profiler(long_input=False, replacements=NONE, cdata=NONE)
    p.timeit('encode', 240000)
    p.timeit('decode', 200000)
    print("")
    p = Profiler(long_input=True, replacements=NONE, cdata=MANY)
    p.timeit('encode', 45)
    p.timeit('decode', 400)
    print("")
    p = Profiler(long_input=False, replacements=NONE, cdata=MANY)
    p.timeit('encode', 35000)
    p.timeit('decode', 190000)
