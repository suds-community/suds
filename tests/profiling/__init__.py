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
Package containing different suds profiling scripts used for comparing
different suds detail implementations or running them under different Python
interpreter versions.

"""

import sys
import timeit


class ProfilerBase(object):
    """Base class for profilers implemented in this project."""

    def __init__(self, show_each_timing=False, show_minimum=True):
        self.show_each_timing = show_each_timing
        self.show_minimum = show_minimum

    def timeit(self, method_name, number, repeat=5):
        print("Timing '%s' (looping %d times, %d timings)" % (method_name,
            number, repeat))
        # We want to pass 'self' as input to the timing functionality
        # implemented in the timeit module, but its interface only allows
        # sharing data via global storage.
        timit_input_storage = "__temporary_timeit_input_data_storage__12345"
        assert not hasattr(sys, timit_input_storage)
        try:
            code = "p.%s()" % (method_name,)
            setup_code = "import sys;p = sys.%s" % (timit_input_storage,)
            setattr(sys, timit_input_storage, self)
            timer = timeit.Timer(code, setup=setup_code)
            times = []
            try:
                for i in range(repeat):
                    time = timer.timeit(number)
                    times.append(time)
                    if self.show_each_timing:
                        print("%d. %s" % (time,))
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception:
                timer.print_exc()
            else:
                if self.show_minimum:
                    print(min(times))
            return times
        finally:
            try:
                delattr(sys, timit_input_storage)
            except AttributeError:
                pass
