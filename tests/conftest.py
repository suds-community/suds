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
pytest configuration file for the suds test suite.

"""

# Make pytest load custom plugins expected to be loaded in our test suite.
#TODO: pytest (tested up to version 2.5.1) will not display our plugin marker
# information in its --markers list if called from a folder other than the one
# containing the tests folder or if the tests folder is not on the current
# Python path, e.g. if using pytest in the Python 3 implementation 'build'
# folder constructed by 'setup.py build' using 'py.test build --markers'. The
# plugin will still get loaded correctly when actually running the tests. This
# has already been reported as a pytest issue.
pytest_plugins = "tests.indirect_parametrize"
