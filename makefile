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
#

SPEC = suds.spec
PUBSPEC = .pubsuds.spec
SETUP = setup.py
PUBSETUP = .pubsetup.py

all: rpm tar egg

egg: clean
	sed -e "s/python-suds/suds/g" $(SETUP) > $(PUBSETUP)
	python $(PUBSETUP) bdist_egg
	rm -rf *.egg-info
	rm -f $(PUBSETUP)

pdist: clean
	sed -e "s/python-suds/suds/g" $(SETUP) > $(PUBSETUP)
	python $(PUBSETUP) sdist
	rm -rf *.egg-info
	rm -f $(PUBSETUP)

dist: clean
	python $(SETUP) sdist
	rm -rf *.egg-info

rpm: dist
	cp dist/python-suds*.gz /usr/src/redhat/SOURCES
	rpmbuild -ba $(SPEC)
	cp /usr/src/redhat/RPMS/noarch/python-suds*.rpm dist
	cp /usr/src/redhat/SRPMS/python-suds*.rpm dist

prpm: pdist
	cp dist/suds*.gz /usr/src/redhat/SOURCES
	sed -e "s/python-suds/suds/g;s/$(SETUP)/$(PUBSETUP)/g" $(SPEC) > $(PUBSPEC)
	rpmbuild -ba $(PUBSPEC)
	cp /usr/src/redhat/RPMS/noarch/suds*.rpm dist
	cp /usr/src/redhat/SRPMS/suds*.rpm dist
	rm -f $(PUBSPEC)

register: FORCE
	sed -e "s/python-suds/suds/g" $(SETUP) > $(PUBSETUP)
	python $(PUBSETUP) register
	rm -f $(PUBSETUP)

clean: FORCE
	rm -rf dist
	rm -rf *.egg-info
	find . -name "*.pyc" -exec rm -f {} \;
	rm -f $(PUBSETUP) $(PUBSPEC)

FORCE:
