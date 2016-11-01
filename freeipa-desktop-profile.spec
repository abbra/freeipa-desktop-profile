%global debug_package %{nil}

Name:           freeipa-desktop-profile
Version:        0.0.1 
Release:        2%{?dist}
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

%posttrans
python2 -c "import sys; from ipaserver.install import installutils; sys.exit(0 if installutils.is_ipa_configured() else 1);" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    # This must be run in posttrans so that updates from previous
    # execution that may no longer be shipped are not applied.
    /usr/sbin/ipa-server-upgrade --quiet >/dev/null || :

    # Restart IPA processes. This must be also run in postrans so that plugins
    # and software is in consistent state
    # NOTE: systemd specific section

    /bin/systemctl is-enabled ipa.service >/dev/null 2>&1
    if [  $? -eq 0 ]; then
        /bin/systemctl restart ipa.service >/dev/null 2>&1 || :
    fi
fi

%files
%license COPYING
%doc plugin/Feature.mediawiki
%python2_sitelib/ipaclient/plugins/*
%python2_sitelib/ipaserver/plugins/*
%_datadir/ipa/schema.d/*
%_datadir/ipa/updates/*
#%_datadir/ipa/ui/js/plugins/deskprofile/*

%changelog
* Tue Nov  1 2016 Fabiano Fidêncio <fidencio@redhat.com> 0.0.1-2
- Use the same posttrans method used by FreeIPA

* Mon Sep  5 2016 Alexander Bokovoy <abokovoy@redhat.com> 0.0.1-1
- Initial release
