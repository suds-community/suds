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


_first_unsupported_py_version_on_Python_24 = (
    lowest_version_string_with_prefix("1.4.16"))
_first_unsupported_py_version_on_Python_25 = (
    lowest_version_string_with_prefix("1.4.24"))

# pytest versions prior to 2.4.0 do not support non-string 'skipif'
# expressions.
_first_supported_pytest_version = "2.4.0"
_first_unsupported_pytest_version_on_Python_24 = (
    lowest_version_string_with_prefix("2.4.2"))
# pytest version 2.6.0 actually supports Python 2.5 but has some internal
# issues causing it to break our our tests, while version 2.6.1 fails to
# install on Python 2.5 all together.
_first_unsupported_pytest_version_on_Python_25 = (
    lowest_version_string_with_prefix("2.6.0"))


def check_Python24_pytest_requirements():
    """
    Check pytest requirements in the current Python 2.4.x environment.

    Installing pytest into a Python 2.4.x environment requires specific py &
    pytest package versions. This function checks whether the environment has
    such compatible Python environments installed.

    Returns a 2-tuple (have_pytest, have_py) indicating whether valid pytest &
    py library packages have been detected in the current Python 2.4.x
    environment. If the pytest package has not been detected, the py library
    package will not be checked and the have_py value will be set to None.

    See the module docstring for more detailed information.

    """
    assert sys.version_info[:2] == (2, 4)
    try:
        from pytest import __version__ as pytest_version
    except ImportError:
        return False, None  # no pytest
    pv_from = parse_version(_first_supported_pytest_version)
    pv_to = parse_version(_first_unsupported_pytest_version_on_Python_24)
    if not (pv_from <= parse_version(pytest_version) < pv_to):
        return False, None  # incompatible pytest version
    try:
        from py import __version__ as py_version
    except ImportError:
        return True, False  # no py library package
    pv_unsupported = parse_version(_first_unsupported_py_version_on_Python_24)
    if parse_version(py_version) >= pv_unsupported:
        return True, False  # incompatible py library package version
    return True, True


def pytest_requirements(version_info=None, ctypes_version=_Unspecified):
    """
    Generate Python version specific pytest package requirements.

    The requirements are returned as setuptools/pip compatible requirement
    specification strings.

    As a slight optimization, specify no Python version information to indicate
    that the requirements are being listed for the current Python environment.

    Missing ctypes installation should be indicated by setting ctypes_version
    parameter to None, while not specifying it indicates that no ctypes version
    information is provided.

    """
    current_environment = version_info is None
    if current_environment:
        version_info = sys.version_info

    pytest_version = None
    if version_info < (2, 5):
        pytest_version = (
            (">=", _first_supported_pytest_version),
            ("<", _first_unsupported_pytest_version_on_Python_24))
        yield requirement_spec("py",
            ("<", _first_unsupported_py_version_on_Python_24))
        #IDEA: In this case we could run the pytest installation separately
        # from all the other pip based installations and have it not install
        # pytest scripts. Since in general there is no 'setup.py install' or
        # 'pip' command-line argument that can say 'do not install scripts',
        # this would most likely need to use a pip command-line option like
        # '--install-option="--install-scripts=..."' to make the scripts be
        # installed into a temporary folder and then remove that folder after
        # the installation. An alternative would be to use easy_install which
        # does support the --exclude-scripts command-line option. N.B. This
        # could work for the project's Python environment setup scripts but not
        # when installing the the project's using its setup script as that
        # script expects to set up all the required packages itself.

    # pytest on Windows depends on the colorama package, and that package has
    # several accidental backward compatibility issues we have to work around
    # when using Python 2.5.
    elif version_info < (2, 6):
        if sys.platform == "win32":
            # colorama releases [0.1.11 - 0.3.2> do not work unless the ctypes
            # module is available, but that module is not included in 64-bit
            # CPython distributions (tested using Python 2.5.4). Some of those
            # versions fail to install, while others only fail at run-time.
            # Pull request https://github.com/tartley/colorama/pull/4 resolves
            # this issue for colorama release 0.3.2.
            if ctypes_version is _Unspecified:
                assert current_environment
                try:
                    from ctypes import __version__ as ctypes_version
                except ImportError:
                    ctypes_version = None
            if ctypes_version is None:
                # We could try to install an external 'ctypes' package from
                # PyPI here, but that would require an old C++ compiler and so
                # would not be highly likely to work in any concurrent
                # development environment.
                #
                #TODO: When using colorama releases older than 0.1.11, you
                # might get atexit() errors on process shutdown after running
                # the project's 'setup.py test' command and having it
                # automatically install the colorama package in the process.
                # The error itself is benign and there are no other effects to
                # it other than the error message getting displayed. The whole
                # issue is caused by colorama's atexit handler getting called
                # multiple times due to some internal setuptools module loading
                # and unloading. We found no easy workaround to this so update
                # this code to use the colorama package version 0.3.2+ as soon
                # as it gets released. When this is done, also remove a related
                # setup.py comment.
                v_bad_low = lowest_version_string_with_prefix("0.1.11")
                v_bad_high = "0.3.2"
                version_spec = ("<", v_bad_low), (">=", v_bad_high)
            else:
                # colorama 0.3.1 release accidentally uses the 'with' keyword
                # without a corresponding __future__ import in its setup.py
                # script.
                version_spec = ("!=", "0.3.1"),
            yield requirement_spec("colorama", *version_spec)

        yield requirement_spec("py",
            ("<", _first_unsupported_py_version_on_Python_25))

        pytest_version = (
            (">=", _first_supported_pytest_version),
            ("<", _first_unsupported_pytest_version_on_Python_25))

    # Python 3.0 & 3.1 stdlib does not include the argparse module which pytest
    # requires, even though it does not list it explicitly among its
    # requirements. Python 3.x series introduced the argparse module in its 3.2
    # release so it needs to be installed manually in 3.0.x & 3.1.x releases.
    # Tested that pytest 2.5.2+ requires py 1.4.20+ which in turn requires the
    # argparse module but does not specify this dependency explicitly.
    elif (3,) <= version_info < (3, 2):
        # pytest versions prior to 2.6.0 are not compatible with Python 3.1,
        # mostly due to accidental incompatibilities introduced because that is
        # not one of the officially supported platforms for pytest and so does
        # not get regular testing. Development version 2.6.0 has been tested
        # with this project and found to work correctly.
        #TODO: Once pytest 2.6.0 has been officially released change the pytest
        # requirement to ("==", "2.6.0").
        pytest_version = (">=", lowest_version_string_with_prefix("2.6.0")),
        missing_argparse = True
        if current_environment:
            try:
                import argparse
                missing_argparse = False
            except ImportError:
                pass
        if missing_argparse:
            yield requirement_spec("argparse")

    if not pytest_version:
        pytest_version = (">=", _first_supported_pytest_version),
    yield requirement_spec("pytest", *pytest_version)


def six_requirements(version_info=sys.version_info):
    """
    Generate Python version specific six package requirements.

    The requirements are returned as setuptools/pip compatible requirement
    specification strings.

    """
    if version_info < (2, 5):
        # 'six' release 1.5 dropped Python 2.4.x compatibility.
        yield requirement_spec("six",
            ("<", lowest_version_string_with_prefix("1.5")))
    else:
        yield requirement_spec("six")


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
