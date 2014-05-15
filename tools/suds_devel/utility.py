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
Generic functionality shared in different development utility modules.

"""

import os
import os.path
import sys
if sys.version_info < (3, 0):
    from urllib import quote as url_quote
else:
    from urllib.parse import quote as url_quote


def any_contains_any(strings, candidates):
    """Whether any of the strings contains any of the candidates."""
    for string in strings:
        for c in candidates:
            if c in string:
                return True


class FileJanitor:
    """Janitor class for removing a specific file."""

    def __init__(self, path):
        self.__path = path

    def clean(self):
        try:
            os.remove(self.__path)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            pass


def path_to_URL(path, escape=True):
    """Convert a local file path to a absolute path file protocol URL."""
    # We do not use urllib's builtin pathname2url() function since:
    #  - it has been commented with 'not recommended for general use'
    #  - it does not seem to work the same on Windows and non-Windows platforms
    #    (result starts with /// on Windows but does not on others)
    #  - urllib implementation prior to Python 2.5 used to quote ':' characters
    #    as '|' which would confuse pip on Windows.
    url = os.path.abspath(path)
    for sep in (os.sep, os.altsep):
        if sep and sep != "/":
            url = url.replace(sep, "/")
    if escape:
        # Must not escape ':' or '/' or Python will not recognize those URLs
        # correctly. Detected on Windows 7 SP1 x64 with Python 3.4.0, but doing
        # this always does not hurt since both are valid ASCII characters.
        no_protocol_URL = url_quote(url, safe=":/")
    else:
        no_protocol_URL = url
    return "file:///%s" % (no_protocol_URL,)


def report_error(message):
    print("ERROR: %s" % (message,))


def requirement_spec(package_name, *args):
    """Identifier used when specifying a requirement to pip or setuptools."""
    if not args or args == (None,):
        return package_name
    version_specs = []
    for version_spec in args:
        if isinstance(version_spec, (list, tuple)):
            operator, version = version_spec
        else:
            assert isinstance(version_spec, str)
            operator = "=="
            version = version_spec
        version_specs.append("%s%s" % (operator, version))
    return "%s%s" % (package_name, ",".join(version_specs))


def path_iter(path):
    """Returns an iterator over all the file & folder names in the path."""
    parts = []
    while path:
        path, item = os.path.split(path)
        if item:
            parts.append(item)
    return reversed(parts)
