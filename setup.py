#!/usr/bin/python
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the (LGPL) GNU Lesser General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library Lesser General Public License for more details at
# ( http://www.gnu.org/licenses/lgpl.html ).
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
# written by: Jeff Ortel ( jortel@redhat.com )

import os
import os.path
import sys

import pkg_resources
from setuptools import setup, find_packages

# Setup documentation incorrectly states that it will search for packages
# relative to the setup script folder by default when in fact it will search
# for them relative to the current working folder. It seems avoiding this
# problem cleanly and making the setup script runnable with any current working
# folder would require better setup() support.
# Attempted alternatives:
#   * Changing the current working folder internally makes any passed path
#     parameters be interpreted relative to the setup script folder when they
#     should be interpreted relative to the initial current working folder.
#   * Passing the script folder as setup() & find_packages() function
#     parameters makes the final installed distribution contain the absolute
#     package source location information and not include some other meta-data
#     package information as well.
script_folder = os.path.abspath(os.path.dirname(__file__))
current_folder = os.path.abspath(os.getcwd())
if script_folder != current_folder:
    print("ERROR: Suds library setup script needs to be run from the folder "
        "containing it.")
    print()
    print("Current folder: {}".format(current_folder))
    print("Script folder: {}".format(script_folder))
    sys.exit(-2)

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
exec(open(os.path.join("suds", "version.py"), "rt").read())

extra = {}
if sys.version_info >= (3,0):
    extra["use_2to3"] = True

    #   Teach Python's urllib lib2to3 fixer that the old urllib2.__version__
    # data member is now stored in the urllib.request module.
    import lib2to3.fixes.fix_urllib
    for x in lib2to3.fixes.fix_urllib.MAPPING["urllib2"]:
        if x[0] == "urllib.request":
            x[1].append("__version__")
            break;

#   Wrap long_description at 72 characters since PKG-INFO package distribution
# metadata file stores this text with an 8 space indentation.
long_description = """
----------------------------------------------------------
Lightweight SOAP client (Phillip's fork of Jurko's fork).
----------------------------------------------------------

  Based on the original 'suds' project by Jeff Ortel (jortel at redhat
dot com) hosted at 'https://fedorahosted.org/suds'.

  'Suds' is a lightweight SOAP-based web service client for Python licensed
under LGPL (see the LICENSE.txt file included in the distribution).

  This is hopefully just a temporary fork of the original suds Python library
project created because the original project development seems to have stalled.
Should be reintegrated back into the original project if it ever gets revived
again.

"""

package_name = "suds"
version_tag = pkg_resources.safe_version(__version__)
project_url = "https://bitbucket.org/palday/suds"
base_download_url = project_url + "/downloads"
download_distribution_name = "{}-{}.tar.bz2".format(package_name, version_tag)
download_url = "{}/{}".format(base_download_url, download_distribution_name)
packages_excluded_from_build = []

#   We generally do not want the tests package or any of its subpackages
# included in our non-source package builds (source distribution content gets
# specified separately via the MANIFEST.ini configuration file). Comment out
# the following line to include the test code anyway, e.g. if you want to run
# Python 3 based tests from the package build folder.
packages_excluded_from_build += ["tests", "tests.*"]

setup(
    name=package_name,
    version=__version__,
    description="Lightweight SOAP client (Phillip's fork of Jurko's fork)",
    long_description=long_description,
    keywords=["SOAP", "web", "service", "client"],
    url=project_url,
    download_url=download_url,
    obsoletes=["suds"],
    setup_requires=["distribute"],
    tests_require=["pytest"],
    packages=find_packages(exclude=packages_excluded_from_build),

    # 'maintainer' will be listed as the distribution package author.
    # Warning: Due to a 'distribute' package defect when used with Python 3
    # (verified using 'distribute' package version 0.6.25), given strings must
    # be given using ASCII characters only. This is needed because 'distribute'
    # stores the strings by doing a simple write to a PKG-INFO file opened as a
    # 'default text file' thus attempting to encode the given characters using
    # the user's default system code-page, e.g. typically CP1250 on eastern
    # European Windows, CP1252 on western European Windows, UTF-8 on Linux or
    # any other.
    author="Jeff Ortel",
    author_email="jortel@redhat.com",
    maintainer="Phillip Alday",
    maintainer_email="phillip.alday@staff.uni-marburg.de",

    #   See PEP-301 for the classifier specification. For a complete list of
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
        "Topic :: Internet"],

    #   PEP-314 states that if possible license & plaform should be specified
    # using 'classifiers'.
    license="(specified using classifiers)",
    platforms=["(specified using classifiers)"],

    **extra
)
