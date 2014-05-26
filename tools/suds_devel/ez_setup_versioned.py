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
Managing Python version specific setuptools ez_setup setup modules used in this
project.

"""

import sys


def import_module(version_info=sys.version_info):
    return __import__(module_name(version_info))


def script_name(version_info=sys.version_info):
    return module_name(version_info) + ".py"


def module_name(version_info=sys.version_info):
    if version_info < (2, 6):
        # setuptools 1.4.2 - the final supported release on Python 2.4 & 2.5.
        return "ez_setup_1_4_2"
    return "ez_setup"
