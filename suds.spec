%define name python-suds
%define version 0.2.8
%define release 1

Summary: Lightweight SOAP client
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}-%{version}.tar.gz
License: LGPL
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
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
