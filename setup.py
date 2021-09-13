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

Attempts to use setuptools if available, and even attempts to install it
automatically if it is not, downloading it from PyPI if needed. However, its
main functionality will function just fine without setuptools as well. Having
setuptools available provides us with the following benefits:
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
if sys.version_info < (2, 4):
    print("ERROR: Python 2.4+ required")
    sys.exit(-2)
if (3,) <= sys.version_info < (3, 1):
    print("ERROR: Python 3.0 not supported - please use Python 3.1+ instead")
    sys.exit(-2)

import os
import os.path
import re

# Workaround for a Python issue detected with Python 3.1.3 when running our
# pytest based 'setup.py test' command. At the end of the test run, Python
# would report an error:
#
#   > Error in atexit._run_exitfuncs:
#   > TypeError: print_exception(): Exception expected for value, str found
#
# Workaround found suggested by Richard Oudkerk in Python's issue tracker at:
#   http://bugs.python.org/issue15881#msg170215
#
# The error is caused by two chained Python bugs:
#  1. The multiprocessing module seems to call its global cleanup function only
#     after all of its globals have already been released, thus raising an
#     exception.
#  2. atexit exception handling implementation is not prepared to handle and
#     correctly report the exception as raised by the multiprocessing module
#     cleanup.
if (3,) <= sys.version_info < (3, 2):
    import multiprocessing
    del multiprocessing


# -----------------------------------------------------------------------------
# Global variables.
# -----------------------------------------------------------------------------

distutils_cmdclass = {}
extra_setup_params = {}

# Hardcoded configuration.
attempt_to_use_setuptools = True
attempt_to_install_setuptools = True


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

from suds_devel.requirements import (check_Python24_pytest_requirements,
    pytest_requirements, six_requirements)


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
#       - chosen design
#       - see below for notes on using different setuptools versions
#       - automated setuptools installations, and especially in-place upgrades,
#         can fail for various reasons (see below)
#       - reduces the risk of a stalled download stalling the whole setup
#         operation, e.g. because of an unavailable or unresponsive DNS server
#   * always install setuptools
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
    if not attempt_to_use_setuptools:
        return

    def import_setuptools_setup():
        try:
            from setuptools import setup
        except ImportError:
            return
        return setup

    setup = import_setuptools_setup()
    if setup or not attempt_to_install_setuptools:
        return setup
    if (3,) <= sys.version_info[:2] < (3, 2):
        # Setuptools contains a test module with an explicitly specified UTF-8
        # BOM, which is not supported by Python's py2to3 tool prior to Python
        # 3.2 (see Python issue #7313). Setuptools can still be installed
        # manually using its ez_setup.py installer script (it will report and
        # ignore the error), but if we use the ez_setup.use_setuptools()
        # programmatic setup invocation from here - it will fail.
        #
        # There are several things that could be done here - patches welcome if
        # anyone actually needs them:
        #  - the issue could be worked around by running the setuptools
        #    installation as a separate process in this case
        #  - warning display could be more cleanly integrated into distutils
        #    command execution process so the warning does not get displayed
        #    if setuptools would not actually be useful, e.g. if user just ran
        #    our setup script with no command or with the --help option
        print("---")
        print("WARNING: can not install setuptools automatically using Python "
            "3.0 & 3.1")
        print("WARNING: if needed, install setuptools manually before running "
            "this installation using Python prior to version 3.2")
        print("---")
        return
    import suds_devel.ez_setup_versioned
    ez_setup = suds_devel.ez_setup_versioned.import_module()
    try:
        # Since we know there is no setuptools package in the current
        # environment, this will:
        # 1. download a setuptools source distribution to the current folder
        # 2. prepare an installable setuptools egg distribution in the current
        #    folder
        # 3. schedule for the prepared setuptools distribution to be installed
        #    together with our package (if our package is getting installed at
        #    all and setup has not been called for some other purpose, e.g.
        #    displaying its help information or running a non-install related
        #    setup command)
        ez_setup.use_setuptools()
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception:
        return
    return import_setuptools_setup()

setup = acquire_setuptools_setup()
using_setuptools = bool(setup)
if not using_setuptools:
    # Fall back to using distutils.
    from distutils.core import setup


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
# Custom setup.py 'test' command for running the project test suite.
# -----------------------------------------------------------------------------
# pytest and any of its requirements not already installed in the target Python
# environment will be automatically downloaded from PyPI and installed into the
# current folder as zipped egg distributions.
#
# Requirements:
#   - setup must be using setuptools
#   - if running Python version prior to 2.5, a suitable pytest version must
#     already be installed and will not be installed on demand (see the related
#     embedded code comment below for more detailed information)
#
# If the requirements are not met, the command simply reports an end-user error
# message explaining why the test functionality is unavailable.
#
# Since Python's distutils framework does not allow passing all received
# command-line arguments to its commands, it does not seem easy to customize
# how pytest runs its tests this way. To have better control over this, user
# should run the pytest on the target source tree directly, possibly after
# first building a temporary one to work around problems like Python 2/3
# compatibility.

def test_requirements():
    """
    Return test requirements for the 'test' command or an error string.

    An error is reported if the requirements can not be satisfied for some
    reason.

    Exact required packages and their versions vary depending on our target
    Python environment version as pytest dropped backward compatibility support
    for some of the Python versions we still support in this project.

    """
    if not using_setuptools:
        return "test command not available without setuptools"

    include_pytest_requirements = True

    if sys.version_info < (2, 5):
        # pytest requirements can not be installed automatically by this setup
        # script under Python 2.4.x environment. Specific pytest & py library
        # package version combination that we found working in Python 2.4.x
        # environments does not formally satisfy pytest requirements, and we
        # found no way to make setuptools' test command succeed when this
        # script installs packages that do not have all their formal
        # requirements satisfied.
        have_pytest, have_py = check_Python24_pytest_requirements()
        if not have_pytest:
            return "compatible preinstalled pytest needed prior to Python 2.5"
        if not have_py:
            return "compatible preinstalled py needed prior to Python 2.5"

        # We must not explicitly specify pytest requirements when running the
        # tests using a Python 2.4.x environment as the only way we found we
        # can run our tests there is to use formally incompatible pytest & py
        # packages. Explicitly specifying pytest requirements here would then
        # cause setuptols to verify those requirements prior to running our
        # test suite.
        include_pytest_requirements = False

    if ((3,) <= sys.version_info < (3, 2, 3)):
        # Python 3.x versions prior to Python 3.2.3 have a bug in their inspect
        # module causing inspect.getmodule() calls to fail if some module lazy
        # loads other modules when some of its attributes are accessed. For
        # more detailed information see Python development issue #13487
        # (http://bugs.python.org/issue13487).
        #
        # This occurs when using setuptools to install our project into a
        # Python 3.1 environment. There the py.error module seems to do such
        # lazy loading. Forcing that module to be loaded here, before the
        # setuptools installation procedure, avoids the issue.
        try:
            import py.error
            py.error.__attribute_access_to_force_this_module_to_lazy_load__
        except (AttributeError, ImportError):
            pass

    # When using Python 2.5 on Windows, if setuptools chooses to install the
    # colorama package (pytest requirement on Windows) older than version
    # 0.1.11, running our 'setup.py test' command may show benign error
    # messages caused by some colorama atexit handlers getting triggered
    # multiple times. There are no adverse effects to this and the issue only
    # occurs if the package is not already installed and it is the 'setup.py
    # test' command that is installing it. The issue has been fixed by the next
    # Python 2.5 compatible colorama 0.3.2 release.
    result = []
    if include_pytest_requirements:
        result.extend(pytest_requirements())
    result.extend(six_requirements())
    return result

test_error = None
tests_require = test_requirements()
if isinstance(tests_require, str):
    test_error = tests_require
else:
    extra_setup_params["tests_require"] = tests_require

if test_error:
    import distutils.cmd
    import distutils.errors

    class TestCommand(distutils.cmd.Command):
        description = test_error
        user_options = []
        def initialize_options(self):
            pass
        def finalize_options(self):
            pass
        def run(self):
            raise distutils.errors.DistutilsPlatformError(self.description)
else:
    from setuptools.command.test import (normalize_path as _normalize_path,
        test as _test)

    class TestCommand(_test):
        # Derived from setuptools.command.test.test for its
        # with_project_on_sys_path() method.

        # The test build can not be done in-place with Python 3+ as it requires
        # py2to3 conversion which we do not want modifying our original project
        # sources.
        if sys.version_info < (3,):
            description = "run pytest based unit tests after an in-place build"
        else:
            description = "run pytest based unit tests after a build"

        # Override base class's command-line options.
        #TODO: pytest argument passing support could be improved if we could
        # get distutils/setuptools to pass all unrecognized command-line
        # parameters to us instead of complaining about them.
        user_options = [("pytest-args=", "a", "arguments to pass to pytest "
            "(whitespace separated, whitespaces in arguments not supported)")]

        def initialize_options(self):
            self.pytest_args = None

        def finalize_options(self):
            self.test_args = []
            if self.pytest_args is not None:
                self.test_args = self.pytest_args.split()

        def run(self):
            # shamelessly lifted from setuptools.command.test.test.run()
            dist = self.distribution
            if dist.install_requires:
                dist.fetch_build_eggs(dist.install_requires)
            if dist.tests_require:
                dist.fetch_build_eggs(dist.tests_require)

            cmd = self._test_cmd_string()
            if self.dry_run:
                self.announce("skipping '%s' (dry run)" % (cmd,))
            else:
                self.announce("running '%s'" % (cmd,))
                self.with_project_on_sys_path(self.run_tests)

        def run_tests(self):
            import pytest
            sys.exit(pytest.main(self.test_args))

        def _test_cmd_string(self):
            parts = ["pytest"]
            if self.pytest_args:
                parts.append(self.pytest_args)
            return " ".join(parts)

distutils_cmdclass["test"] = TestCommand


# -----------------------------------------------------------------------------
# Mark the original suds project as obsolete.
# -----------------------------------------------------------------------------

if sys.version_info >= (2, 5):
    # distutils.setup() 'obsoletes' parameter not introduced until Python 2.5.
    extra_setup_params["obsoletes"] = ["suds"]


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
#  * Python 2.x - UTF-8 encoded bytes
#  * Python [2.6, 3.0> - unicode string
#      - unicode strings containing non-ASCII characters supported since Python
#        commit 4c683ec4415b3c4bfbc7fe7a836b949cb7beea03
#  * Python [3.0, 3.2.2>
#      - may only contain ASCII characters due to a distutils bug (given input
#        can only be a unicode string and is encoded using the user's default
#        system code-page, e.g. typically CP1250 on eastern European Windows,
#        CP1252 on western European Windows, UTF-8 on Linux or any other)
#      - setuptools 3.5 works around the issue by overriding relevant distutils
#        functionality, allowing the use of non-ASCII characters, but only for
#        Python 3.1
#  * Python 3.2.2+ - unicode string
#      - unicode strings containing non-ASCII characters supported since Python
#        commit fb4d2e6d393e96baac13c4efc216e361bf12c293

can_not_use_non_ASCII_meta_data = (3,) <= sys.version_info < (3, 2, 2)
if (can_not_use_non_ASCII_meta_data and using_setuptools and
        sys.version_info[:2] == (3, 1)):
    from setuptools import __version__ as setuptools_version
    from pkg_resources import parse_version as pv
    can_not_use_non_ASCII_meta_data = pv(setuptools_version) < pv("3.5")

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

package_name = "suds-community"
version_tag = safe_version(__version__)
project_url = "https://github.com/suds-community/suds"
base_download_url = project_url + "/archive"
download_distribution_name = "release-%s.tar.gz" % (version_tag)
download_url = "%s/%s" % (base_download_url, download_distribution_name)

maintainer="Jurko Gospodnetić"
if can_not_use_non_ASCII_meta_data:
    maintainer = unicode2ascii(maintainer)

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
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Internet"],

    # PEP-314 states that, if possible, license & platform should be specified
    # using 'classifiers'.
    license="(specified using classifiers)",
    platforms=["(specified using classifiers)"],

    # Register distutils command customizations.
    cmdclass=distutils_cmdclass,
    python_requires=">=3.5",

    **extra_setup_params)
