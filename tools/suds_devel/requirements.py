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
Package requirements for this project.

Extracted here so they can be reused between the project's setup and different
development utility scripts.

Python 2.4 pytest compatibility notes:
--------------------------------------

pytest versions prior to 2.4.0 may be installed but will fail at runtime when
running our test suite, as they can not parse all of the pytest constructs used
in this project, e.g. skipif expressions not given as strings. Versions 2.4.2
and later can not be installed at all.

pytest 2.4.0 release formally broke compatibility with Python releases prior to
2.5 and the last officially supported pytest version on Python 2.4 platforms is
2.3.5.

Our tests can still be run using a Python 2.4.x environment if the following
package versions are installed into it:
 - pytest - not older than 2.4.0 nor equal to or newer than 2.4.2
 - py - older than 1.4.16 (version 1.4.16 may be installed but will cause
   pytest to fail when running our test suite).

Listed package versions can be installed together using a pip command like:
  install pytest>=2.4.0,<2.4.2 py<1.4.16

Listed pytest versions specify py version 1.4.16+ as their requirement but work
well enough for us with this older py release. Note though that due to pytest
not having its requirements formally satisfied, some operations related to it
may fail unexpectedly. For example, running setuptools installed 'py.test'
startup scripts will fail, as they explicitly check that all the formally
specified pytest requirements have been met, but pytest can still be started
using 'py24 -m pytest'.

See the project's Python compatibility related hacking docs for more detailed
information.

Python 2.5 pytest compatibility notes:
--------------------------------------

pytest 2.6.1 release started using the 'with' statement and so broke
compatibility with Python 2.5.

py 1.4.24 release started using the 'with' statement and so broke compatibility
with Python 2.5.

"""

import sys

from suds_devel.parse_version import parse_version
from suds_devel.utility import (lowest_version_string_with_prefix,
    requirement_spec)


class _Unspecified:
    pass


def virtualenv_requirements(version_info=sys.version_info):
    """
    Generate Python version specific virtualenv package requirements.

    The requirements are returned as setuptools/pip compatible requirement
    specification strings.

    """
    if version_info < (2, 5):
        # 'virtualenv' release 1.8 dropped Python 2.4.x compatibility.
        yield requirement_spec("virtualenv",
            ("<", lowest_version_string_with_prefix("1.8")))
    elif version_info < (2, 6):
        # 'virtualenv' release 1.10 dropped Python 2.5.x compatibility.
        yield requirement_spec("virtualenv",
            ("<", lowest_version_string_with_prefix("1.10")))
    else:
        yield requirement_spec("virtualenv")
