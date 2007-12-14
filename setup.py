import sys
from setuptools import setup, find_packages

requires = ['python >= 2.4']

if sys.version_info < (2,5):
    requires.append('lxml.etree >= 1.3.3')
else:
    requires.append('xml.etree >= 1.3.3')
    
setup(
    name="suds",
    version="0.1",
    description="Lightweight SOAP client",
    author="Jeff Ortel",
    author_email="jortel@redhat.com",
    maintainer="Jeff Ortel",
    maintainer_email="jortel@redhat.com",
    packages=find_packages(),
    url="https://fedorahosted.org/suds",
    install_requires=requires
)
