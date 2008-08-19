
dist:
	python setup.py sdist

rpm: dist
	cp dist/*.gz /usr/src/redhat/SOURCES
	cp suds.spec /usr/src/redhat/SPECS
	rpmbuild -ba suds.spec

clean:
	rm -rf dist
	rm -rf *.egg-info
	find . -name "*.pyc" -exec rm -f {} \;
