%global debug_package %{nil}

Name:           freeipa-desktop-profile
Version:        0.0.1 
Release:        1%{?dist}
Summary:        FleetCommander integration with FreeIPA

License:        GPL
URL:            https://github.com/abbra/freeipa-desktop-profile
Source0:        freeipa-desktop-profile-%{version}.tar.gz

BuildRequires:  python2-devel
Requires:       freeipa-server-common >= 4.4.1
Requires:       python2-ipaserver >= 4.4.1

%description
A module for FreeIPA to allow managing desktop profiles defined
by the FleetCommander.

%prep
%autosetup

%build
touch debugfiles.list

%install
rm -rf $RPM_BUILD_ROOT
%__mkdir_p %buildroot/%{python2_sitelib}/ipaclient/plugins
%__mkdir_p %buildroot/%{python2_sitelib}/ipaserver/plugins
%__mkdir_p %buildroot/%_datadir/ipa/schema.d
%__mkdir_p %buildroot/%_datadir/ipa/updates
#%__mkdir_p %buildroot/%_datadir/ipa/ui/js/plugins/deskprofile

%__cp plugin/ipaclient/plugins/deskprofile.py %buildroot/%{python2_sitelib}/ipaclient/plugins
%__cp plugin/ipaserver/plugins/deskprofile.py %buildroot/%{python2_sitelib}/ipaserver/plugins
%__cp plugin/schema.d/75-deskprofile.ldif %buildroot/%_datadir/ipa/schema.d 
%__cp plugin/updates/75-deskprofile.update %buildroot/%_datadir/ipa/updates 
#%__cp plugin/ui/deskprofile.js %buildroot/%_datadir/ipa/ui/js/plugins/deskprofile

%files
%license COPYING
%doc plugin/Feature.mediawiki
%python2_sitelib/ipaclient/plugins/*
%python2_sitelib/ipaserver/plugins/*
%_datadir/ipa/schema.d/*
%_datadir/ipa/updates/*
#%_datadir/ipa/ui/js/plugins/deskprofile/*

%changelog
* Mon Sep  5 2016 Alexander Bokovoy <abokovoy@redhat.com> 0.0.1-1
- Initial release
