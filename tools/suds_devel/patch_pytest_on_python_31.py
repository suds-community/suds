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
Support for patching an existing pytest installation to make it work correctly
in a Python 3.1 environment.

pytest versions prior to its 2.6 release do not support Python 3.1 out of the
box, but can be patched to do so. Basic gist of this patch is to replace a
single call to the builtin function 'callable()' in pytest's _pytest/runner.py
module with a call to 'py.builtin.callable()'. The patch has been tested to
make pytest 2.5.2 work correctly with Python 3.1 and is based on code found in
pytest pull request #168 & commit 04c4997da865344f2ebb8569c73c51c57cd4ba05.

"""

import os
import os.path
import re
import sys

from suds_devel.environment import EnvironmentScanner
from suds_devel.exception import EnvironmentSetupError
from suds_devel.parse_version import parse_version


def patch(env):
    assert env.sys_version_info[:2] == (3, 1)
    pytest_location, pytest_version = _scan(env)
    if parse_version(pytest_version) >= parse_version("2.6.0"):
        return
    print("Patching installed pytest package...")
    file_path = os.path.join(pytest_location, "_pytest", "runner.py")
    file_temp_path = _file_temp_path(file_path)
    try:
        try:
            prepatched_count, patched_count = _patch(file_path, file_temp_path,
                unpatched_regex="(.*\s)callable([(].*)$",
                patched_regex="(.*\s)py[.]builtin[.]callable([(].*)",
                patch_pattern="%spy.builtin.callable%s")
            if (prepatched_count, patched_count) not in ((1, 0), (0, 1)):
                _error(file_path, "file content not recognized")
            if prepatched_count:
                print("WARNING: pytest already patched")
            else:
                os.remove(file_path)
                os.rename(file_temp_path, file_path)
        finally:
            _try_remove_file(file_temp_path)
    except (EnvironmentSetupError, KeyboardInterrupt, SystemExit):
        raise
    except Exception:
        _error(file_path, str(sys.exc_info()[1]))


def _error(file_path, message):
    raise EnvironmentSetupError("can not patch pytest module '%s' - %s" % (
        file_path, message))


def _file_temp_path(file_path):
    for i in range(100):
        temp_path = "%s.patching.%d.tmp" % (file_path, i)
        if not os.path.exists(temp_path):
            return temp_path
    _error(file_path, "can not find available temp file name")


def _patch(source, dest, unpatched_regex, patched_regex, patch_pattern):
    """
    Patch given source file into the given destination file.

    Patching is done line by line. Given un-patched and patched line detection
    regular expressions are expected never to match the same line.

    Does not modify the source file in any way.

    Returns the number of detected pre-patched lines, and a number of newly
    patched lines.

    """
    prepatched_count = 0
    patched_count = 0
    unpatched_matcher = re.compile(unpatched_regex, re.DOTALL)
    patched_matcher = re.compile(patched_regex)
    f_in = None
    f_out = None
    try:
        f_in = open(source, "r")
        f_out = open(dest, mode="w")
        for line in f_in:
            match = unpatched_matcher.match(line)
            if match:
                assert not patched_matcher.match(line)
                patched_count += 1
                line = patch_pattern % match.groups()
                assert patched_matcher.match(line)
            elif patched_matcher.match(line):
                prepatched_count += 1
            f_out.write(line)
    finally:
        if f_in:
            f_in.close()
        if f_out:
            f_out.close()
    return prepatched_count, patched_count


def _scan(env):
    """Scan the given Python environment's pytest installation."""
    s = EnvironmentScanner()
    s.add_function("""\
def get_pytest_location():
    from pkg_resources import get_distribution
    return get_distribution("pytest").location
""")
    s.add_field("pytest location", "get_pytest_location()")
    s.add_package_version_field("pytest", default="")
    scan_results = s.scan(env)
    return scan_results["pytest location"], scan_results["pytest version"]


def _try_remove_file(path):
    try:
        os.remove(path)
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception:
        pass
