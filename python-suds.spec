%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Summary: A python SOAP client
Name:  python-suds
Version: 0.3.5
Release: 1%{?dist}
Source0: https://fedorahosted.org/releases/s/u/%{name}/%{name}-%{version}.tar.gz
License: LGPLv3+
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
BuildArch: noarch
Requires: python >= 2.3
BuildRequires: python-setuptools-devel
Url: https://fedorahosted.org/suds

%description
The suds project is a python soap web services client lib.  Suds leverages
python meta programming to provide an intuative API for consuming web
services.  Objectification of types defined in the WSDL is provided
without class generation.  Programmers rarely need to read the WSDL since
services and WSDL based objects can be easily inspected.  Supports
pluggable soap bindings.

%prep
%setup -q

%build
python setup.py sdist

%install
rm -rf $RPM_BUILD_ROOT
python setup.py install --optimize=1 --root=$RPM_BUILD_ROOT

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%{python_sitelib}/suds*.egg-info
%dir %{python_sitelib}/suds
%dir %{python_sitelib}/suds/bindings
%dir %{python_sitelib}/suds/sax
%dir %{python_sitelib}/suds/xsd
%dir %{python_sitelib}/suds/transport
%{python_sitelib}/suds/*.py*
%{python_sitelib}/suds/bindings/*.py*
%{python_sitelib}/suds/sax/*.py*
%{python_sitelib}/suds/xsd/*.py*
%{python_sitelib}/suds/transport/*.py*

%doc README LICENSE

%changelog
* Wed Feb 25 2009 jortel <jortel@redhat.com> - 0.3.5-1
- 0.3.5

* Mon Dec 08 2008 jortel <jortel@redhat.com> - 0.3.4-1
- Static (automatic) Import.bind('http://schemas.xmlsoap.org/soap/encoding/')
- Basic ws-security with {{{UsernameToken}}} and clear-text password only.
- Add support for ''sparse'' soap headers via passing dictionary
- Add support for arbitrary user defined soap headers
- Fixes service operations with multiple soap header entries.
- Schema loading and dereferencing algorithm enhancements.
- Nested soap multirefs fixed.
- Better (true) support for elementFormDefault="unqualified" provides more accurate namespaing.
- WSDL part types no longer default to WSDL targetNamespace.
- Fixed Tickets: #4, #6, #21, #32, #62, #66, #71, #72, #114, #155, #201.

* Wed Dec 04 2008 jortel <jortel@redhat.com> - 0.3.3-2
- Rebuild for Python 2.6

* Wed Dec 04 2008 jortel <jortel@redhat.com> - 0.3.3-1
- No longer installs (tests) package.
- Implements API-3 proposal
    Pluggable transport
    Keyword method arguments
    Baisc http authentication in default transport
- Add namespace prefix normalization in soap message.
- Better soap message pruning of empty nodes.
- Fixed Tickets: #51 - #60.

* Sat Nov 29 2008 Ignacio Vazquez-Abrams <ivazqueznet+rpm@gmail.com> - 0.3.2-2
- Rebuild for Python 2.6

* Fri Nov 06 2008 jortel <jortel@redhat.com> - 0.3.2-1
- Add SOAP MultiRef support
- Add support for new schema tags:
    <xs:include/>
    <xs:simpleContent/>
    <xs:group/>
    <xs:attributeGroup/>
- Added support for new xs <--> python type conversions:
    xs:int
    xs:long
    xs:float
    xs:double
- Revise marshaller and binding to further sharpen the namespacing of nodes produced.
- Infinite recursion fixed in ''xsd'' package dereference() during schema loading.
- Add support for <wsdl:import/> of schema files into the wsdl root <definitions/>.
- Fix double encoding of (&)
- Add Client API:
    setheaders()  - Same as keyword but works for all invocations.
    addprefix()   - Mapping of namespace prefixes.
    setlocation() - Override the location in the wsdl.
    setproxy()    - Same as proxy keyword but for all invocations.
- Add proper namespace prefix for soap headers.
- Fixed Tickets: #5, #12, #34, #37, #40, #44, #45, #46, #48, #49, #50, #51

* Fri Nov 03 2008 jortel <jortel@redhat.com> - 0.3.1-5
- Add LICENSE to %%doc.

* Fri Oct 28 2008 jortel <jortel@redhat.com> - 0.3.1-4
- Changes acc. #466496 Comment #8

* Fri Oct 27 2008 jortel <jortel@redhat.com> - 0.3.1-3
- Add "rm -rf $RPM_BUILD_ROOT" to install

* Fri Oct 16 2008 jortel <jortel@redhat.com> - 0.3.1-2
- Changes acc. #466496 Comment #1

* Fri Oct 10 2008 jortel <jortel@redhat.com> - 0.3.1-1
- Extends the support for multi-port services introduced earlier. This addition, 
  provides for multiple services to define the *same* method and suds will
  handle it properly.  See section 'SERVICES WITH MULTIPLE PORTS:'
- Add support for multi-document document/literal soap binding style.
  See section 'MULTI-DOCUMENT Docuemnt/Literal:'
- Add support for (xs:group, xs:attributeGroup) tags.
- Add Client.last_sent() and Client.last_received().
