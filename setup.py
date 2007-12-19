#!/usr/bin/python
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
# written by: Jeff Ortel ( jortel@redhat.com )

import sys
from setuptools import setup, find_packages
from suds import VERSION

requires = ['python >= 2.4']

if sys.version_info < (2,5):
    requires.append('lxml.etree >= 1.3.3')
else:
    requires.append('xml.etree >= 1.3.3')
    
setup(
    name="suds",
    version=VERSION,
    description="Lightweight SOAP client",
    author="Jeff Ortel",
    author_email="jortel@redhat.com",
    maintainer="Jeff Ortel",
    maintainer_email="jortel@redhat.com",
    packages=find_packages(),
    url="https://fedorahosted.org/suds",
    install_requires=requires
)
