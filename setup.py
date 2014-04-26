#!/usr/bin/python
# -*- coding: utf-8 -*-
#
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
Main installation and project management script for this project.

Requires setuptools, and even attempts to install it automatically if it is
not available, downloading it from PyPI if needed. Having setuptools available
provides us with the following benefits:
  - py2to3/distutils integration
  - setup.py 'egg_info' command constructing the project's metadata
  - setup.py 'develop' command deploying the project in 'development mode',
    thus making it available on sys.path, yet still editable directly in its
    source checkout - equivalent to running a pip based installation using
    'easy_install -e' or 'pip install -e'
  - setup.py 'test' command as a standard way to run the project's test suite
  - when running the installation directly from the source tree setup.py
    'install' command:
      - automatically installs the project's metadata so package management
        tools like pip recognize the installation correctly, e.g. this allows
        using 'pip uninstall' to undo the installation
      - package installed as a zipped egg by default

"""

import os
import os.path
import sys


# -----------------------------------------------------------------------------
# Global variables.
# -----------------------------------------------------------------------------

distutils_cmdclass = {}
extra_setup_params = {}


# -----------------------------------------------------------------------------
# Use setuptools for this installation.
# -----------------------------------------------------------------------------

def use_compatible_setuptools():
    """
    Makes sure a compatible setuptools version is used for this installation.

    As a general rule, uses the most recent setuptools distribution tested to
    work with our project and the current platform, and will accept as
    compatible only that setuptools version or newer.

    If a compatible setuptools version is detected, automatically imports its
    modules into sys.modules.

    If a compatible setuptools package is not already installed, downloads a
    compatible one from PyPI, imports it and configures it to install itself as
    a part of our project's setup procedure. This includes automatically
    upgrading an already installed incompatible setuptools version.

    """
    # We considered reusing an existing setuptools installation even if it is
    # older than the one downloaded by our setuptools installation scripts, as
    # that could help simplify the installation in some cases and certain older
    # versions have been seen to install our project without problems. However,
    # such older setuptools releases have known usability issues we really do
    # not want to waste time dealing with in some more esoteric usage
    # scenarios. Also, not all older setuptools versions have been tested and
    # some of them have documented regressions that would most likely break our
    # project installation as well, e.g. upgrading to setuptools 3.0 is
    # documented to fail on Python 2.6 due to an accidental backward
    # incompatibility corrected in the setuptools 3.1 release.

    if sys.version_info < (2, 6):
        # setuptools 1.4.2 - the final release supporting Python 2.4 & 2.5.
        import ez_setup_1_4_2 as ez_setup
    else:
        import ez_setup
    ez_setup.use_setuptools()


use_compatible_setuptools()
import pkg_resources
from setuptools import setup, find_packages


# -----------------------------------------------------------------------------
# Support functions.
# -----------------------------------------------------------------------------

def read_python_code(filename):
    "Returns the given Python source file's compiled content."
    file = open(filename, "rt")
    try:
        source = file.read()
    finally:
        file.close()
    # Python 2.6 and below did not support passing strings to exec() &
    # compile() functions containing line separators other than '\n'. To
    # support them we need to manually make sure such line endings get
    # converted even on platforms where this is not handled by native text file
    # read operations.
    source = source.replace("\r\n", "\n").replace("\r", "\n")
    return compile(source, filename, "exec")


# -----------------------------------------------------------------------------
# Detect the setup.py environment - current & script folder.
# -----------------------------------------------------------------------------

# Setup documentation incorrectly states that it will search for packages
# relative to the setup script folder by default when in fact it will search
# for them relative to the current working folder. It seems avoiding this
# problem cleanly and making the setup script runnable with any current working
# folder would require better distutils and/or setuptools support.
# Attempted alternatives:
#   * Changing the current working folder internally makes any passed path
#     parameters be interpreted relative to the setup script folder when they
#     should be interpreted relative to the initial current working folder.
#   * Passing the script folder as setup() & find_packages() function
#     parameters makes the final installed distribution contain the absolute
#     package source location information and not include some other meta-data
#     package information as well.
script_folder = os.path.realpath(os.path.dirname(__file__))
current_folder = os.path.realpath(os.getcwd())
if script_folder != current_folder:
    print("ERROR: Suds library setup script needs to be run from the folder "
        "containing it.")
    print()
    print("Current folder: %s" % current_folder)
    print("Script folder: %s" % script_folder)
    sys.exit(-2)


# -----------------------------------------------------------------------------
# Load the suds library version information.
# -----------------------------------------------------------------------------

# Load the suds library version information directly into this module without
# having to import the whole suds library itself. Importing the suds package
# would have caused problems like the following:
#   * Forcing the imported package module to be Python 3 compatible without any
#     lib2to3 fixers first being run on it (since such fixers get run only
#     later as a part of the setup procedure).
#   * Making the setup module depend on the package module's dependencies, thus
#     forcing the user to install them manually (since the setup procedure that
#     is supposed to install them automatically will not be able to run unless
#     they are already installed).
# We execute explicitly compiled source code instead of having the exec()
# function compile it to get a better error messages. If we used exec() on the
# source code directly, the source file would have been listed as just
# '<string>'.
exec(read_python_code(os.path.join(script_folder, "suds", "version.py")))


# -----------------------------------------------------------------------------
# Custom setup.py 'test' command for running the project test suite.
# -----------------------------------------------------------------------------
# Support for integrating running the project' pytest based test suite directly
# into this setup script so the test suite can be run by 'setup.py test'. Since
# Python's distutils framework does not allow passing all received command-line
# arguments to its commands, it does not seem easy to customize how pytest runs
# its tests this way. To have better control over this, user should run the
# pytest on the target source tree directly, possibly after first building a
# temporary one to work around problems like Python 2/3 compatibility.

import setuptools.command.test

class TestCommand(setuptools.command.test.test):

    def finalize_options(self):
        setuptools.command.test.test.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # Make sure the tests are run on the correct test sources. E.g. when
        # using Python 3, the tests need to be run in the temporary build
        # folder where they have been previously processed using py2to3.
        # Running them directly on the original source tree would fail due to
        # Python 2/3 source code incompatibility.
        ei_cmd = self.get_finalized_command("egg_info")
        build_path = setuptools.command.test.normalize_path(ei_cmd.egg_base)
        import pytest
        sys.exit(pytest.main(["--pyargs", build_path]))

extra_setup_params["tests_require"] = ["pytest"]
distutils_cmdclass["test"] = TestCommand


# -----------------------------------------------------------------------------
# Mark the original suds project as obsolete.
# -----------------------------------------------------------------------------

if sys.version_info >= (2, 5):
    # distutils.setup() 'obsoletes' parameter not introduced until Python 2.5.
    extra_setup_params["obsoletes"] = ["suds"]


# -----------------------------------------------------------------------------
# Integrate py2to3 into our build operation.
# -----------------------------------------------------------------------------

if sys.version_info >= (3, 0):
    # Integrate the py2to3 step into our build.
    extra_setup_params["use_2to3"] = True

    # Teach Python's urllib lib2to3 fixer that the old urllib2.__version__ data
    # member is now stored in the urllib.request module.
    import lib2to3.fixes.fix_urllib
    for x in lib2to3.fixes.fix_urllib.MAPPING["urllib2"]:
        if x[0] == "urllib.request":
            x[1].append("__version__")
            break;


# -----------------------------------------------------------------------------
# Set up project metadata and run the actual setup.
# -----------------------------------------------------------------------------

# Wrap long_description at 72 characters since the PKG-INFO package
# distribution metadata file stores this text with an 8 space indentation.
long_description = """
---------------------------------------
Lightweight SOAP client (Jurko's fork).
---------------------------------------

  Based on the original 'suds' project by Jeff Ortel (jortel at redhat
dot com) hosted at 'http://fedorahosted.org/suds'.

  'Suds' is a lightweight SOAP-based web service client for Python
licensed under LGPL (see the LICENSE.txt file included in the
distribution).

  This is hopefully just a temporary fork of the original suds Python
library project created because the original project development seems
to have stalled. Should be reintegrated back into the original project
if it ever gets revived again.

"""

package_name = "suds-jurko"
version_tag = pkg_resources.safe_version(__version__)
project_url = "http://bitbucket.org/jurko/suds"
base_download_url = project_url + "/downloads"
download_distribution_name = "%s-%s.tar.bz2" % (package_name, version_tag)
download_url = "%s/%s" % (base_download_url, download_distribution_name)

setup(
    name=package_name,
    version=__version__,
    description="Lightweight SOAP client (Jurko's fork)",
    long_description=long_description,
    keywords=["SOAP", "web", "service", "client"],
    url=project_url,
    download_url=download_url,
    packages=find_packages(),

    # 'maintainer' will be listed as the distribution package author.
    # Warning: Due to a 'distribute' package defect when used with Python 3
    # (verified using 'distribute' package version 0.6.25), given strings must
    # be given using ASCII characters only. This is needed because 'distribute'
    # stores the strings by doing a simple write to a PKG-INFO file opened as a
    # 'default text file' thus attempting to encode the given characters using
    # the user's default system code-page, e.g. typically CP1250 on eastern
    # European Windows, CP1252 on western European Windows, UTF-8 on Linux or
    # any other.
    #
    # 'distribute' package merged back with the 'setuptools' package in the
    # setuptools 0.7 release but we have not yet checked whether this bug has
    # been corrected there or not.
    author="Jeff Ortel",
    author_email="jortel@redhat.com",
    maintainer="Jurko Gospodnetic",
    maintainer_email="jurko.gospodnetic@pke.hr",

    # See PEP-301 for the classifier specification. For a complete list of
    # available classifiers see
    # 'http://pypi.python.org/pypi?%3Aaction=list_classifiers'.
    classifiers=["Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: "
            "GNU Library or Lesser General Public License (LGPL)",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.4",
        "Programming Language :: Python :: 2.5",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.0",
        "Programming Language :: Python :: 3.1",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Topic :: Internet"],

    # PEP-314 states that, if possible, license & platform should be specified
    # using 'classifiers'.
    license="(specified using classifiers)",
    platforms=["(specified using classifiers)"],

    # Register distutils command customizations.
    cmdclass=distutils_cmdclass,

    **extra_setup_params)
