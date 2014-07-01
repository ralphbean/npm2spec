{% if test_command %}%global enable_tests {{enable_tests}}{% endif %}
%global barename {{barename}}

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
{% if test_command %}
%if 0%{?enable_tests}{% for depname, version in dev_deps.items() %}
BuildRequires:      nodejs-{{depname}}{% endfor %}
%endif
{% endif %}

%description
{{description}}

%prep
%setup -q -n package

# Remove bundled node_modules if there are any..
rm -rf node_modules/
{% for depname, version in deps.items() %}
%nodejs_fixdep {{depname}}{% endfor %}
{% if test_command %}
%if 0%{?enable_tests}{% for depname, version in dev_deps.items() %}
%nodejs_fixdep --dev {{depname}}{% endfor %}
%endif
{% else %}
{% for depname, version in deps.items() %}
%nodejs_fixdep --dev -r {{depname}}{% endfor %}
{% endif %}

%build
%nodejs_symlink_deps --build

%install
mkdir -p %{buildroot}%{nodejs_sitelib}/{{barename}}
cp -pr {{ " ".join(package_files) }} \
    %{buildroot}%{nodejs_sitelib}/{{barename}}

%nodejs_symlink_deps

{% if test_command %}
%check
%if 0%{?enable_tests}
%nodejs_symlink_deps --check
{{test_command}}
%endif
{% endif %}

%files
%doc{% for filename in doc_files %} {{filename}}{% endfor %}
%{nodejs_sitelib}/{{barename}}/

%changelog
* {{date}} {{packager}} <{{email}}> - {{version}}-1
- Initial packaging for Fedora.
