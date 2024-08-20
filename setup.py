#!/usr/bin/python
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
Main installation and project management script for this project.

Requires setuptools. Having setuptools available provides us with the following
benefits:
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

import sys
import os
import os.path
import re

# -----------------------------------------------------------------------------
# Global variables.
# -----------------------------------------------------------------------------

distutils_cmdclass = {}

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
#   * Passing the script folder to setup() using the parameter
#       package_dir={"": script_folder}
#     makes the setup 'build' command work from any folder but 'egg-info'
#     (together with any related commands) still fails.
script_folder = os.path.realpath(os.path.dirname(__file__))
current_folder = os.path.realpath(os.getcwd())
if script_folder != current_folder:
    print("ERROR: Suds library setup script needs to be run from the folder "
        "containing it.")
    print("")
    print("Current folder: %s" % current_folder)
    print("Script folder: %s" % script_folder)
    sys.exit(-2)


# -----------------------------------------------------------------------------
# Import suds_devel module shared between setup & development scripts.
# -----------------------------------------------------------------------------

tools_folder = os.path.join(script_folder, "tools")
sys.path.insert(0, tools_folder)
import suds_devel
sys.path.pop(0)

# -----------------------------------------------------------------------------
# Attempt to use setuptools for this installation.
# -----------------------------------------------------------------------------
# setuptools brings us several useful features (see the main setup script
# docstring) but if it causes problems for our users or even only
# inconveniences them, they tend to complain about why we are using setuptools
# at all. Therefore we try to use setuptools as silently as possible, with a
# clear error message displayed to the user, but only in cases when we
# absolutely need setuptools.
#
# Setuptools usage logic:
# 1. attempt to use a preinstalled setuptools version
# 2. if a preinstalled setuptools version is not available, attempt to install
#    and use the most recent tested compatible setuptools release, possibly
#    downloading the installation from PyPI into the current folder
# 3. if we still do not have setuptools available, fall back to using distutils
#
# Note that we have made a slight trade-off here and chose to reuse an existing
# setuptools installation if available instead of always downloading and
# installing the most recent compatible setuptools release.
#
# Alternative designs and rationale for selecting the current design:
#
# distutils/setuptools usage:
#   * always use distutils
#       - misses out on all the setuptools features
#   * use setuptools if available, or fall back to using distutils
#       - chosen design
#       - gets us setuptools features if available, with clear end-user error
#         messages in case an operation is triggered that absolutely requires
#         setuptools to be available
#       - see below for notes on different setuptools installation alternatives
#   * always use setuptools
#       - see below for notes on different setuptools installation alternatives
#
# setuptools installation:
#   * expect setuptools to be preinstalled
#       - if not available, burden the user with installing setuptools manually
#       - see below for notes on using different setuptools versions
#   * use preinstalled setuptools if possible, or fall back to installing it
#     on-demand
#       - see below for notes on using different setuptools versions
#       - automated setuptools installations, and especially in-place upgrades,
#         can fail for various reasons (see below)
#       - reduces the risk of a stalled download stalling the whole setup
#         operation, e.g. because of an unavailable or unresponsive DNS server
#   * always install setuptools
#       - chosen design
#       - automated setuptools installations, and especially in-place upgrades,
#         can fail for various reasons (see below)
#       - user has no way to avoid setuptools installation issues by installing
#         setuptools himself, which would force us to make our setuptools
#         installation support universally applicable and that is just not
#         possible, e.g. users might be wanting to use customized package
#         management or their own package index instead of PyPI.
#
# setuptools version usage:
#   - basic problem here is that our project can be and has been tested only
#     with certain setuptools versions
#   - using a different version may have issues causing our setup procedures to
#     fail outside our control, either due to a setuptools bug or due to an
#     incompatibility between our implementation and the used setuptools
#     version
#   - some setuptools releases have known regressions, e.g. setuptools 3.0
#     which is documented to fail on Python 2.6 due to an accidental backward
#     incompatibility corrected in the setuptools 3.1 release
#   * allow using any setuptools version
#       - chosen design
#       - problems caused by incompatible setuptools version usage are
#         considered highly unlikely and can therefore be patched up as needed
#         when and if they appear
#       - users will most likely not have a setuptools version preinstalled
#         into their Python environment that is incompatible with that
#         environment
#       - if there is no setuptools version installed, our setup will attempt
#         to install the most recent tested setuptools release
#   * allow using only tested setuptools versions or possibly more recent ones
#       - unless we can automatically install a suitable setuptools version, we
#         will need to burden the user with installing it manually or fall back
#         to using distutils
#       - automated setuptools installations, and especially in-place upgrades,
#         can fail for various reasons (see below)
#       - extra implementation effort required compared to the chosen design,
#         with no significant benefit
#
# Some known scenarios causing automated setuptools installation failures:
#   * Download failures, e.g. because user has no access to PyPI.
#   * In-place setuptool upgrades can fail due to a known setuptools issue (see
#     'https://bitbucket.org/pypa/setuptools/issue/168') when both the original
#     and the new setuptools version is installed as a zipped egg distribution.
#     Last seen using setuptools 3.4.4.
#   * If the Python environment running our setup has already loaded setuptools
#     packages, then upgrading that installation in-place will fail with an
#     error message instructing the user to do the upgrade manually.
#   * When installing our project using pip, pip will load setuptools
#     internally, and it typically uses an older setuptools version which can
#     trigger the in-place upgrade failure as described above. What is worse,
#     we ignore this failure, we run into the following combination problem:
#       * pip calls our setup twice - once to collect the package requirement
#         information and once to perform the actual installation, and we do
#         not want to display multiple potentially complex error messages to
#         user for what is effectively the same error.
#       * Since we can not affect how external installers call our setup, to
#         avoid this we would need to either:
#           * Somehow cache the information that we already attempted and
#             failed to upgrade setuptools (complicated + possibly not robust).
#           * Patch the setuptools installation script to not display those
#             error messages (we would prefer to not be forced to maintain our
#             own patches for this script and use it as is).
#           * Avoid the issue by never upgrading an existing setuptools
#             installation (chosen design).

def acquire_setuptools_setup():
    try:
        from setuptools import setup
    except ImportError:
        print("WARNING: setuptools is not detected. It is required, install via: "
            "python -m pip install --upgrade pip setuptools wheel")
        return
    return setup

setup = acquire_setuptools_setup()
using_setuptools = bool(setup)


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

def recursive_package_list(*packages):
    """
    Returns a list of all the given packages and all their subpackages.

    Given packages are expected to be found relative to this script's location.

    Subpackages are detected by scanning the given packages' subfolder
    hierarchy for any folders containing the '__init__.py' module. As a
    consequence, namespace packages are not supported.

    This is our own specialized setuptools.find_packages() replacement so we
    can avoid the setuptools dependency.

    """
    result = set()
    todo = []
    for package in packages:
        folder = os.path.join(script_folder, *package.split("."))
        if not os.path.isdir(folder):
            raise Exception("Folder not found for package '%s'." % (package,))
        todo.append((package, folder))
    while todo:
        package, folder = todo.pop()
        if package in result:
            continue
        result.add(package)
        for subitem in os.listdir(folder):
            subpackage = ".".join((package, subitem))
            subfolder = os.path.join(folder, subitem)
            if not os.path.isfile(os.path.join(subfolder, "__init__.py")):
                continue
            todo.append((subpackage, subfolder))
    return list(result)

# Shamelessly stolen from setuptools project's pkg_resources module.
def safe_version(version_string):
    """
    Convert an arbitrary string to a standard version string

    Spaces become dots, and all other non-alphanumeric characters become
    dashes, with runs of multiple dashes condensed to a single dash.

    """
    version_string = version_string.replace(" ", ".")
    return re.sub("[^A-Za-z0-9.]+", "-", version_string)

def unicode2ascii(unicode):
    """Convert a unicode string to its approximate ASCII equivalent."""
    return unicode.encode("ascii", 'xmlcharrefreplace').decode("ascii")


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
# Avoid setup warnings when constructing a list of all project sources.
# -----------------------------------------------------------------------------
# Part of this workaround implemented and part in the project's MANIFEST.in
# template. See a related comment in MANIFEST.in for more detailed information.

dummy_tools_folder = os.path.join(tools_folder, "__dummy__")
dummy_tools_file = os.path.join(dummy_tools_folder, "readme.txt")
try:
    if not os.path.isdir(dummy_tools_folder):
        os.mkdir(dummy_tools_folder)
    if not os.path.isfile(dummy_tools_file):
        f = open(dummy_tools_file, "w")
        try:
            f.write("""\
Dummy empty folder added as a part of a patch to silence setup.py warnings when
determining which files belong to the project. See a related comment in the
project's MANIFEST.in template for more detailed information.

Both the folder and this file have been generated by the project's setup.py
script and should not be placed under version control.
""")
        finally:
            f.close()
except EnvironmentError:
    # Something went wrong attempting to construct the dummy file. Ah well, we
    # gave it our best. Continue on with possible spurious warnings.
    pass


# -----------------------------------------------------------------------------
# Set up project metadata and run the actual setup.
# -----------------------------------------------------------------------------
# Package meta-data needs may be specified as:
#  * Python 3.2.2+ - unicode string
#      - unicode strings containing non-ASCII characters supported since Python
#        commit fb4d2e6d393e96baac13c4efc216e361bf12c293

# Wrap long_description at 72 characters since the PKG-INFO package
# distribution metadata file stores this text with an 8 space indentation.
long_description = """
---------------------------------------
Lightweight SOAP client (Community fork).
---------------------------------------

  Based on the original 'suds' project by Jeff Ortel (jortel at redhat
dot com) hosted at 'http://fedorahosted.org/suds'.

  'Suds' is a lightweight SOAP-based web service client for Python
licensed under LGPL (see the LICENSE.txt file included in the
distribution).
"""

forked_package_name = 'suds-community'
package_name = os.environ.get('SUDS_PACKAGE', forked_package_name)
version_tag = safe_version(__version__)
project_url = "https://github.com/suds-community/suds"
base_download_url = project_url + "/archive"
download_distribution_name = "release-%s.tar.gz" % (version_tag)
download_url = "%s/%s" % (base_download_url, download_distribution_name)

maintainer="Jurko Gospodnetić"

setup(
    name=package_name,
    version=__version__,
    description="Lightweight SOAP client (community fork)",
    long_description=long_description,
    long_description_content_type='text/markdown',
    keywords=["SOAP", "web", "service", "client"],
    url=project_url,
    download_url=download_url,
    packages=recursive_package_list("suds"),

    author="Jeff Ortel",
    author_email="jortel@redhat.com",
    maintainer=maintainer,
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
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Internet"],

    # PEP-314 states that, if possible, license & platform should be specified
    # using 'classifiers'.
    license="(specified using classifiers)",
    platforms=["(specified using classifiers)"],

    python_requires=">=3.7",
    obsoletes=["suds"] if package_name == forked_package_name else [],
)
