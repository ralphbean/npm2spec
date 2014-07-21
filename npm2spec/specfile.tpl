# This macro is needed at the start for building on EL6
%{?nodejs_find_provides_and_requires}

{% if test_command %}%global enable_tests {{enable_tests}}{% endif %}
{% if prerelease %}%global prerelease {{prerelease}}{% endif %}
%global barename {{barename}}

Name:               nodejs-{{fixname}}
Version:            {{version}}
{% if prerelease %}Release:            0.1.%{prerelease}%{?dist}{% else %}Release:            1%{?dist}{% endif %}
Summary:            {{summary}}

Group:              Development/Libraries
License:            {{license}}
URL:                {{URL}}
Source0:            {{_source0}}
BuildArch:          noarch
%if 0%{?fedora} >= 19
ExclusiveArch:      %{nodejs_arches} noarch
%else
ExclusiveArch:      %{ix86} x86_64 %{arm} noarch
%endif

BuildRequires:      nodejs-packaging >= 6
{% for depname, version in deps.items() %}
BuildRequires:      npm({{depname}}){% endfor %}
{% for depname, version in deps.items() %}
Requires:           npm({{depname}}){% endfor %}
{% if test_command %}
%if 0%{?enable_tests}{% for depname, version in dev_deps.items() %}
BuildRequires:      npm({{depname}}){% endfor %}
%endif
{% endif %}

%description
{{description}}

%prep
%setup -q -n package

# Remove bundled node_modules if there are any..
rm -rf node_modules/

%nodejs_fixdep --caret

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
{% if prerelease %}* {{date}} {{packager}} <{{email}}> - {{version}}-0.1.{{prerelease}}{% else %}* {{date}} {{packager}} <{{email}}> - {{version}}-1{% endif %}
- Initial packaging for Fedora.
