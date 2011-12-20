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

setup(
    name="suds",
    version=__version__,
    description="Lightweight SOAP client",
    author="Jeff Ortel",
    author_email="jortel@redhat.com",
    maintainer="Jeff Ortel",
    maintainer_email="jortel@redhat.com",
    packages=find_packages(exclude=["tests"]),
    url="https://fedorahosted.org/suds",
)
