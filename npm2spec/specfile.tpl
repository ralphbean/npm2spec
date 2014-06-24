%global build_docs 0
%global enable_tests 0

Name:               nodejs-{{barename}}
Version:            {{version}}
Release:            1%{?dist}
Summary:            {{summary}}

Group:              Development/Libraries
License:            {{license}}
URL:                {{URL}}
Source0:            {{_source0}}

BuildRequires:      nodejs-packaging >= 6
{% for depname, version in deps.items() %}
BuildRequires:      nodejs-{{depname}}{% endfor %}

{% for depname, version in deps.items() %}
Requires:           nodejs-{{depname}}{% endfor %}

%description
{{description}}

%if 0%{?build_docs}
%package doc
Summary:    Documentation for nodejs-{{barename}}
Requires:   %{name} = %{version}-%{release}

%description doc
This package provides the documentation for nodejs-{{barename}}.
%endif

%prep
%setup -q

{% for depname, version in dev_deps.items() %}
%nodejs_fixdep --dev -r {{depname}}{% endfor %}

%build
%nodejs_symlink_deps --build

grunt dist

%if 0%{?build_docs}
grunt jekyll dist-docs
%endif

%install
mkdir -p %{buildroot}%{nodejs_sitelib}/{{barename}}
cp -pr package.json lib/ \
    %{buildroot}%{nodejs_sitelib}/{{barename}}

%nodejs_symlink_deps

%if 0%{?enable_tests}
%check
%nodejs_symlink_deps --check
grunt test
%endif

%files
%doc README.md LICENSE
%{nodejs_sitelib}/grunt

%changelog
* {{date}} {{packager}} <{{email}}> {{version}}-1
- initial package for Fedora
