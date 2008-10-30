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

SPEC = python-suds.spec
SETUP = setup.py
pythonSETUP = .python-suds
DOCTAR = suds-docs.tar.gz
FEDORAPEOPLE = jortel@fedorapeople.org

all: rpm docs

egg: clean
	python $(SETUP) bdist_egg
	rm -rf *.egg-info

dist: clean
	sed -e "s/name=\"suds\"/name=\"python-suds\"/" $(SETUP) > $(pythonSETUP)
	python $(SETUP) sdist bdist_egg
	python $(pythonSETUP) sdist bdist_egg
	scp dist/python* fedorahosted.org:suds
	rm -rf *.egg-info
	rm -f $(pythonSETUP)

rpm: dist
	cp dist/python-suds*.gz /usr/src/redhat/SOURCES
	rpmbuild -ba $(SPEC)
	cp /usr/src/redhat/RPMS/noarch/python-suds*.rpm dist
	cp /usr/src/redhat/SRPMS/python-suds*.rpm dist
	scp dist/python*.rpm fedorahosted.org:suds

register: FORCE
	python setup.py sdist bdist_egg register upload

docs: FORCE
	rm -rf doc
	rm -f /tmp/$(DOCTAR)
	epydoc -o doc `find suds -name "*.py"`
	tar czvf /tmp/$(DOCTAR) doc
	scp /tmp/$(DOCTAR) $(FEDORAPEOPLE):
	ssh $(FEDORAPEOPLE) 'cd public_html/suds; rm -rf doc; tar xzvf ~/$(DOCTAR)'

clean: FORCE
	rm -rf dist
	rm -rf build
	rm -rf doc
	rm -rf *.egg-info
	rm -rf /usr/src/redhat/BUILD/python-suds*
	rm -rf /usr/src/redhat/RPMS/noarch/python-suds*
	rm -rf /usr/src/redhat/SOURCES/python-suds*
	rm -rf /usr/src/redhat/SRPMS/python-suds*
	find . -name "*.pyc" -exec rm -f {} \;
	find . -name "*~" -exec rm -f {} \;

FORCE:
