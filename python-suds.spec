%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Summary: A python SOAP client
Name:  python-suds
Version: 0.3.9
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
%dir %{python_sitelib}/suds/mx
%dir %{python_sitelib}/suds/umx
%dir %{python_sitelib}/suds/transport
%{python_sitelib}/suds/*.py*
%{python_sitelib}/suds/bindings/*.py*
%{python_sitelib}/suds/sax/*.py*
%{python_sitelib}/suds/xsd/*.py*
%{python_sitelib}/suds/mx/*.py*
%{python_sitelib}/suds/umx/*.py*
%{python_sitelib}/suds/transport/*.py*

%doc README LICENSE

%changelog
* Thu Dec 17 2009 jortel <jortel@redhat.com> - 0.3.9-1
 - 0.3.9
* Wed Dec 9 2009 jortel <jortel@redhat.com> - 0.3.8-1
- Includeds Windows NTLM Transport.
- Add missing self.messages in Client.clone().
- Changed default behavior for WSDL PartElement to be optional.
- Add support for services/ports defined without <address/> element in WSDL.
- Fix sax.attribute.Element.attrib() to find by name only when ns is not specified; renamed to Element.getAttribute().
- Update HttpTransport to pass timeout parameter to urllib2 open() methods when supported by urllib2.
- Add null class to pass explicit NULL values for parameters and optional elements.
- Soap encoded array (soap-enc:Array) enhancement for rpc/encoded.
  Arrays passed as python arrays - works like document/literal now.
  No more using the factory to create the Array.
  Automatically includes arrayType attribute.  Eg: soap-enc:arrayType="Array[2]".
  Reintroduced ability to pass complex (objects) using python dict instead of suds object via factory.
- Fixed tickets: #84, #261, #262, #263, #265, #266, #278, #280, #282.

* Thu Oct 16 2009 jortel <jortel@redhat.com> - 0.3.7-1
- Better soap header support
- Added new transport HttpAuthenticated for active (not passive) basic authentication.
- New options (prefixes, timeout, retxml)
- WSDL processing enhancements.
- Expanded builtin XSD type support.
- Fixed <xs:iniclude/>
- Better XML date/datetime conversion.
- Client.clone() method added for lightweight copy of client object.
- XSD processing fixes/enhancements.
- Better <simpleType/> by <xs:restriction/> support.
- Performance enhancements. 
- Fixed tickets: #65, #232, #233, #235, #241, #242, #244, #247, #254, #254, #256, #257, #258

* Sun Jul 26 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.3.6-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Wed May 1 2009 jortel <jortel@redhat.com> - 0.3.6-1
- Change hard coded /tmp/suds to tempfile.gettempdir() and create suds/ on demand.
- Fix return type for Any.get_attribute().
- Update http caching to ignore file:// urls.
- Better logging of messages when only the reply is injected.
- Fix XInteger and XFloat types to translate returned arrays properly.
- Fix xs:import schema with same namespace.
- Update parser to not load external references and add Import.bind() for XMLSchema.xsd location.
- Add schema doctor - used to patch XSDs at runtime.  (See Options.doctor)
- Fix deprecation warnings in python 2.6.
- Add behavior for @default defined on <element/>.
- Change @xsi:type value to always be qualified for doc/literal.
- Add Option.xstq option to control when @xsi:type is qualified.
- Fixed Tickets: #64, #129, #205, #206, #217, #221, #222, #224, #225, #228, #229, #230

* Wed Feb 25 2009 jortel <jortel@redhat.com> - 0.3.5-1
- Adds http caching.  Default is (1) day.
- Removed checking fc version in spec since no longer building < fc9.
- Updated makefile to roll tarball with tar.sh.
- Moved bare/wrapped determination to wsdl for document/literal.
- Refactored Transport to provide better visibility into http headers.
- Fixed Tickets: #207, #207, #209, #210, #212, #214, #215

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
