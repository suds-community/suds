%define name python-suds
%define version 0.3.2
%define release 1

Summary: A python SOAP client
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}-%{version}.tar.gz
License: LGPLv3+
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
BuildArch: noarch
Requires: python >= 2.3
%if 0%{?fedora} >= 8
BuildRequires: python-setuptools-devel
%else
BuildRequires: python-setuptools
%endif
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
python setup.py install --optimize=1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES

%doc README

%changelog
 * Fri Oct 10 2008 jortel <jortel@redhat.com> - release 0.3.1-1
  - Extends the support for multi-port services introduced earlier.  This addition,
    provides for multiple services to define the *same* method and suds will
    handle it properly.  See section 'SERVICES WITH MULTIPLE PORTS:'
  - Add support for multi-document document/literal soap binding style.
    See section 'MULTI-DOCUMENT Docuemnt/Literal:'
  - Add support for (xs:group, xs:attributeGroup) tags.
  - Add Client.last_sent() and Client.last_received().
