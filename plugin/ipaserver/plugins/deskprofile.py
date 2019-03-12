# Authors:
#   Alexander Bokovoy <abokovoy@redhat.com>
#
# Copyright (C) 2016  Red Hat
# see file 'COPYING' for use and warranty information

import re

from ipalib import api, errors
from ipalib import Str, StrEnum, Bool, Bytes, Int
from ipalib.plugable import Registry
from .baseldap import (
    pkey_to_value,
    LDAPObject,
    LDAPCreate,
    LDAPDelete,
    LDAPUpdate,
    LDAPSearch,
    LDAPRetrieve,
    LDAPQuery,
    LDAPAddMember,
    LDAPRemoveMember)
from ipalib import _, ngettext
from ipalib import output
from .hbacrule import is_all
from ipapython.dn import DN

__doc__ = _("""
Desktop profile mapping

Maintain desktop profiles for FleetCommander

FleetCommander delivers desktop profiles to the clients.

A desktop profile is a set of configuration settings enforced by
FleetCommander.  The profiles are stored by IPA and can be associated with
hosts, hostgroups, users, and groups by creating a mapping rule.

Hosts, hostgroups, users and groups can be either defined within
the rule or it may point to an existing HBAC rule. When using
--hbacrule option to deskprofilerule-find an exact match is made on the
HBAC rule name, so only one or zero entries will be returned.

EXAMPLES:

 Create a desktop profile, "finance", by providing a FleetCommander's JSON file:
   ipa deskprofile-add finance --data=finance.json --desc="Finance Department Desktop"

 Create a desktop profile mapping rule, "finance", to apply "finance" desktop
 profile to "finance" group on hosts "a1" and "a2" at priority 100:
   ipa deskprofilerule-add finance --groups=finance --profile=finance --prio=100 --hosts={a1,a2}
 
 Create a desktop profile mapping rule, "design", to apply "Visual Design" desktop
 profile to all users/groups and hosts that match HBAC rule "design department access":
   ipa deskprofilerule-add design --hbacrule="design department access" --profile="Visual Design"

 Create a desktop profile mapping rule, "engineering", to apply "Engineer" desktop
 profile to a specific user on any host:
   ipa deskprofilerule-add engineer --user=bob --profile="Engineer" --hostcat=all
 
Display the properties of a desktop profile:
   ipa deskprofile-show finance

 Display the properties of a desktop profile rule:
   ipa deskprofilerule-show design

 Disable a rule:
   ipa deskprofilerule-disable engineering

 Enable a rule:
   ipa deskprofilerule-enable engineering

 Find desktop profiles that apply to a specific host:
   ipa deskprofile-find --hosts={a1,a2}

 Find a rule referencing a specific HBAC rule:
   ipa deskprofilerule-find --hbacrule="design department access"

 Remove a rule:
   ipa deskprofilerule-del "finance"

 Remove a profile:
   ipa deskprofile-del "Visual Design"

 To define global policy on how profile apply:
   ipa deskprofileconfig-mod --priority=NUMBER

 Where NUMBER is 1..24 according to the following table:
  1 = user, group, host, hostgroup
  2 = user, group, hostgroup, host
  3 = user, host, group, hostgroup
  4 = user, host, hostgroup, group
  5 = user, hostgroup, group, host
  6 = user, hostgroup, host, group
  7 = group, user, host, hostgroup
  8 = group, user, hostgroup, host
  9 = group, host, user, hostgroup
 10 = group, host, hostgroup, user
 11 = group, hostgroup, user, host
 12 = group, hostgroup, host, user
 13 = host, user, group, hostgroup
 14 = host, user, hostgroup, group
 15 = host, group, user, hostgroup
 16 = host, group, hostgroup, user
 17 = host, hostgroup, user, group
 18 = host, hostgroup, group, user
 19 = hostgroup, user, group, host
 20 = hostgroup, user, host, group
 21 = hostgroup, group, user, host
 22 = hostgroup, group, host, user
 23 = hostgroup, host, user, group
 24 = hostgroup, host, group, user

""")

register = Registry()

notboth_err = _('HBAC rule and local members cannot both be set')

PLUGIN_CONFIG = (
    ('container_deskprofile', DN(('cn', 'desktop-profile'))),
    ('container_deskprofilerule', DN(('cn', 'rules'), ('cn', 'desktop-profile'))),
)


@register()
class deskprofile(LDAPObject):
    """
    Desktop profile object.
    """
    container_dn = None
    object_name = _('FleetCommander Desktop Profile')
    object_name_plural = _('FleetCommander Desktop Profiles')
    object_class = ['ipaassociation', 'ipadeskprofile']
    permission_filter_objectclasses = ['ipadeskprofile']
    default_attributes = [
        'cn', 'ipadeskdata',
        'description', 
    ]
    search_display_attributes = [
        'cn', 'description',
    ]
    uuid_attribute = 'ipauniqueid'
    rdn_is_primary_key = True

    managed_permissions = {
        'System: Read FleetCommander Desktop Profile': {
            'ipapermbindruletype': 'all',
            'ipapermright': {'read', 'search', 'compare'},
            'ipapermdefaultattr': {
                'cn', 'description',
                'ipauniqueid',
                'objectclass',
            },
        },
        'System: Read FleetCommander Desktop Profile': {
            'ipapermbindruletype': 'permission',
            'ipapermright': {'read'},
            'ipapermdefaultattr': {
                'ipadeskdata'
            },
            'default_privileges': {'FleetCommander Desktop Profile Administrators'},
        },
        'System: Add FleetCommander Desktop Profile': {
            'ipapermbindruletype': 'permission',
            'ipapermright': {'add'},
            'default_privileges': {'FleetCommander Desktop Profile Administrators'},
        },
        'System: Modify FleetCommander Desktop Profile': {
            'ipapermbindruletype': 'permission',
            'ipapermright': {'write'},
            'ipapermdefaultattr': {
                'cn', 'ipadeskdata', 'description',
            },
            'default_privileges': {'FleetCommander Desktop Profile Administrators'},
        },
        'System: Remove FleetCommander Desktop Profile': {
            'ipapermbindruletype': 'permission',
            'ipapermright': {'delete'},
            'default_privileges': {'FleetCommander Desktop Profile Administrators'},
        },
    }

    label = _('FleetCommander Desktop Profile')
    label_singular = _('FleetCommander Desktop Profile')

    takes_params = (
        Str('cn',
            cli_name='name',
            label=_('Profile name'),
            primary_key=True,
        ),
        Str('description?',
            cli_name='desc',
            label=_('Description'),
        ),
        Bytes('ipadeskdata',
            cli_name='data',
            label=_('JSON data for profile'),
        ),
    )

    # Inject constants into the api.env before it is locked down
    def _on_finalize(self):
        self.env._merge(**dict(PLUGIN_CONFIG))
        self.container_dn = self.env.container_deskprofile
        super(deskprofile, self)._on_finalize()

@register()
class deskprofile_add(LDAPCreate):
    __doc__ = _('Create a new Desktop Profile.')

    msg_summary = _('Added Desktop Profile "%(value)s"')



@register()
class deskprofile_del(LDAPDelete):
    __doc__ = _('Delete a Desktop Profile.')

    msg_summary = _('Deleted Desktop Profile "%(value)s"')



@register()
class deskprofile_mod(LDAPUpdate):
    __doc__ = _('Modify a Desktop Profile.')

    msg_summary = _('Modified Desktop Profile "%(value)s"')



@register()
class deskprofile_find(LDAPSearch):
    __doc__ = _('Search for Desktop Profiles.')

    msg_summary = ngettext(
        '%(count)d Desktop Profile matched', '%(count)d Desktop Profiles matched', 0
    )



@register()
class deskprofile_show(LDAPRetrieve):
    __doc__ = _('Display the properties of a Desktop Profile.')



@register()
class deskprofilerule(LDAPObject):
    """
    Desktop profile object.
    """
    container_dn = None
    object_name = _('FleetCommander Desktop Profile Rule Map')
    object_name_plural = _('FleetCommander Desktop Profile Rule Maps')
    object_class = ['ipaassociation', 'ipadeskprofilerule']
    permission_filter_objectclasses = ['ipadeskprofilerule']
    default_attributes = [
        'cn', 'ipaenabledflag', 'ipadeskprofiletarget'
        'description', 'usercategory', 'hostcategory',
        'memberuser', 'memberhost', 'ipadeskprofilepriority',
        'seealso',
    ]
    uuid_attribute = 'ipauniqueid'
    rdn_is_primary_key = True
    attribute_members = {
        'memberuser': ['user', 'group'],
        'memberhost': ['host', 'hostgroup'],
    }
    managed_permissions = {
        'System: Read FleetCommander Desktop Profile Rule Map': {
            'ipapermbindruletype': 'all',
            'ipapermright': {'read', 'search', 'compare'},
            'ipapermdefaultattr': {
                'cn', 'description', 'hostcategory',
                'ipaenabledflag', 'ipauniqueid',
                'memberhost', 'memberuser', 'seealso', 'usercategory',
                'objectclass', 'member', 'ipadeskprofilepriority',
                'ipadeskprofiletarget',
            },
        },
        'System: Add FleetCommander Desktop Profile Rule Map': {
            'ipapermbindruletype': 'permission',
            'ipapermright': {'add'},
            'default_privileges': {'FleetCommander Desktop Profile Administrators'},
        },
        'System: Modify FleetCommander Desktop Profile Rule Map': {
            'ipapermbindruletype': 'permission',
            'ipapermright': {'write'},
            'ipapermdefaultattr': {
                'cn', 'ipaenabledflag', 'memberhost',
                'memberuser', 'seealso', 'ipadeskprofilepriority',
                'ipadeskprofiletarget',
            },
            'default_privileges': {'FleetCommander Desktop Profile Administrators'},
        },
        'System: Remove FleetCommander Desktop Profile Rule Map': {
            'ipapermbindruletype': 'permission',
            'ipapermright': {'delete'},
            'default_privileges': {'FleetCommander Desktop Profile Administrators'},
        },
    }

    label = _('FleetCommander Desktop Profile Rule Map')
    label_singular = _('FleetCommander Desktop Profile Rule Map')

    takes_params = (
        Str('cn',
            cli_name='name',
            label=_('Rule name'),
            primary_key=True,
        ),
        Str('ipadeskprofiletarget',
            cli_name='profile',
            label=_('Desktop profile'),
            doc=_('Desktop profile associated with the rule'),
        ),
        Int('ipadeskprofilepriority',
            cli_name='prio',
            label=_('Desktop profile priority'),
            minvalue=1,
            maxvalue=100000,
            doc=_('Priority for desktop profile associated with the rule'),
        ),
        Str('seealso?',
            cli_name='hbacrule',
            label=_('HBAC Rule'),
            doc=_('HBAC Rule that defines the users, groups and hostgroups'),
        ),
        StrEnum('usercategory?',
            cli_name='usercat',
            label=_('User category'),
            doc=_('User category the rule applies to'),
            values=(u'all', ),
        ),
        StrEnum('hostcategory?',
            cli_name='hostcat',
            label=_('Host category'),
            doc=_('Host category the rule applies to'),
            values=(u'all', ),
        ),
        Str('description?',
            cli_name='desc',
            label=_('Description'),
        ),
        Bool('ipaenabledflag?',
             label=_('Enabled'),
             flags=['no_option'],
        ),
        Str('memberuser_user?',
            label=_('Users'),
            flags=['no_create', 'no_update', 'no_search'],
        ),
        Str('memberuser_group?',
            label=_('User Groups'),
            flags=['no_create', 'no_update', 'no_search'],
        ),
        Str('memberhost_host?',
            label=_('Hosts'),
            flags=['no_create', 'no_update', 'no_search'],
        ),
        Str('memberhost_hostgroup?',
            label=_('Host Groups'),
            flags=['no_create', 'no_update', 'no_search'],
        ),
    )

    # Inject constants into the api.env before it is locked down
    def _on_finalize(self):
        self.env._merge(**dict(PLUGIN_CONFIG))
        self.container_dn = self.env.container_deskprofilerule
        super(deskprofilerule, self)._on_finalize()

    def _normalize_seealso(self, seealso):
        """
        Given a HBAC rule name verify its existence and return the dn.
        """
        if not seealso:
            return None

        try:
            dn = DN(seealso)
            return str(dn)
        except ValueError:
            try:
                entry_attrs = self.backend.find_entry_by_attr(
                    self.api.Object['hbacrule'].primary_key.name,
                    seealso,
                    self.api.Object['hbacrule'].object_class,
                    [''],
                    DN(self.api.Object['hbacrule'].container_dn, api.env.basedn))
                seealso = entry_attrs.dn
            except errors.NotFound:
                raise errors.NotFound(reason=_('HBAC rule %(rule)s not found') % dict(rule=seealso))

        return seealso

    def _convert_seealso(self, ldap, entry_attrs, **options):
        """
        Convert an HBAC rule dn into a name
        """
        if options.get('raw', False):
            return

        if 'seealso' in entry_attrs:
            hbac_attrs = ldap.get_entry(entry_attrs['seealso'][0], ['cn'])
            entry_attrs['seealso'] = hbac_attrs['cn'][0]

    def _normalize_profile(self, profile):
        """
        Given a Desktop Profile name verify its existence and return the dn.
        """
        if not profile:
            return None

        try:
            dn = DN(profile)
            return str(dn)
        except ValueError:
            try:
                entry_attrs = self.backend.find_entry_by_attr(
                    self.api.Object['deskprofile'].primary_key.name,
                    profile,
                    self.api.Object['deskprofile'].object_class,
                    [''],
                    DN(self.api.Object['deskprofile'].container_dn, api.env.basedn))
                return entry_attrs.dn
            except errors.NotFound:
                raise errors.NotFound(reason=_('Desktop profile %(rule)s not found') % dict(rule=profile))

    def _convert_profile(self, ldap, entry_attrs, **options):
        """
        Convert an Desktop Profile dn into a name
        """
        if options.get('raw', False):
            return

        if 'ipadeskprofiletarget' in entry_attrs:
            profile_attrs = ldap.get_entry(entry_attrs['ipadeskprofiletarget'][0], ['cn'])
            entry_attrs['ipadeskprofiletarget'] = profile_attrs['cn'][0]


@register()
class deskprofilerule_add(LDAPCreate):
    __doc__ = _('Create a new Desktop Profile Rule Map.')

    msg_summary = _('Added Desktop Profile Rule Map "%(value)s"')

    def pre_callback(self, ldap, dn, entry_attrs, attrs_list, *keys, **options):
        assert isinstance(dn, DN)
        # rules are enabled by default
        entry_attrs['ipaenabledflag'] = 'TRUE'

        # hbacrule is not allowed when usercat or hostcat is set
        is_to_be_set = lambda x: x in entry_attrs and entry_attrs[x] != None

        are_local_members_to_be_set = any(is_to_be_set(attr)
                                          for attr in ('usercategory',
                                                       'hostcategory'))

        is_hbacrule_to_be_set = is_to_be_set('seealso')

        if is_hbacrule_to_be_set and are_local_members_to_be_set:
            raise errors.MutuallyExclusiveError(reason=notboth_err)

        if is_hbacrule_to_be_set:
            entry_attrs['seealso'] = self.obj._normalize_seealso(entry_attrs['seealso'])

        entry_attrs['ipadeskprofiletarget'] = \
            self.obj._normalize_profile(entry_attrs['ipadeskprofiletarget'])

        return dn

    def post_callback(self, ldap, dn, entry_attrs, *keys, **options):
        assert isinstance(dn, DN)
        self.obj._convert_seealso(ldap, entry_attrs, **options)
        self.obj._convert_profile(ldap, entry_attrs, **options)

        return dn



@register()
class deskprofilerule_del(LDAPDelete):
    __doc__ = _('Delete a Desktop Profile Rule Map.')

    msg_summary = _('Deleted Desktop Profile Rule Map "%(value)s"')



@register()
class deskprofilerule_mod(LDAPUpdate):
    __doc__ = _('Modify a Desktop Profile Rule Map.')

    msg_summary = _('Modified Desktop Profile Rule Map "%(value)s"')

    def pre_callback(self, ldap, dn, entry_attrs, attrs_list, *keys, **options):
        assert isinstance(dn, DN)
        try:
            _entry_attrs = ldap.get_entry(dn, attrs_list)
        except errors.NotFound:
            self.obj.handle_not_found(*keys)

        is_to_be_deleted = lambda x: (x in _entry_attrs and x in entry_attrs) and \
                                     entry_attrs[x] == None

        # makes sure the local members and hbacrule is not set at the same time
        # memberuser or memberhost could have been set using --setattr
        is_to_be_set = lambda x: ((x in _entry_attrs and _entry_attrs[x] != None) or \
                                 (x in entry_attrs and entry_attrs[x] != None)) and \
                                 not is_to_be_deleted(x)

        are_local_members_to_be_set = any(is_to_be_set(attr)
                                          for attr in ('usercategory',
                                                       'hostcategory',
                                                       'memberuser',
                                                       'memberhost'))

        is_hbacrule_to_be_set = is_to_be_set('seealso')

        # this can disable all modifications if hbacrule and local members were
        # set at the same time bypassing this commad, e.g. using ldapmodify
        if are_local_members_to_be_set and is_hbacrule_to_be_set:
            raise errors.MutuallyExclusiveError(reason=notboth_err)

        if is_all(entry_attrs, 'usercategory') and 'memberuser' in entry_attrs:
            raise errors.MutuallyExclusiveError(reason="user category "
                 "cannot be set to 'all' while there are allowed users")
        if is_all(entry_attrs, 'hostcategory') and 'memberhost' in entry_attrs:
            raise errors.MutuallyExclusiveError(reason="host category "
                 "cannot be set to 'all' while there are allowed hosts")

        if 'seealso' in entry_attrs:
            entry_attrs['seealso'] = self.obj._normalize_seealso(entry_attrs['seealso'])

        entry_attrs['ipadeskprofiletarget'] = \
            self.obj._normalize_profile(entry_attrs['ipadeskprofiletarget'])

        return dn

    def post_callback(self, ldap, dn, entry_attrs, *keys, **options):
        assert isinstance(dn, DN)
        self.obj._convert_seealso(ldap, entry_attrs, **options)
        self.obj._convert_profile(ldap, entry_attrs, **options)
        return dn



@register()
class deskprofilerule_find(LDAPSearch):
    __doc__ = _('Search for Desktop Profile Rule Maps.')

    msg_summary = ngettext(
        '%(count)d Desktop Profile Rule Map matched', '%(count)d Desktop Profile Rule Maps matched', 0
    )

    def execute(self, *args, **options):
        # If searching on hbacrule we need to find the uuid to search on
        if options.get('seealso'):
            hbacrule = options['seealso']

            try:
                hbac = api.Command['hbacrule_show'](hbacrule,
                                                    all=True)['result']
                dn = hbac['dn']
            except errors.NotFound:
                return dict(count=0, result=[], truncated=False)
            options['seealso'] = dn

        return super(deskprofilerule_find, self).execute(*args, **options)

    def post_callback(self, ldap, entries, truncated, *args, **options):
        if options.get('pkey_only', False):
            return truncated
        for attrs in entries:
            self.obj._convert_seealso(ldap, attrs, **options)
            self.obj._convert_profile(ldap, attrs, **options)
        return truncated



@register()
class deskprofilerule_show(LDAPRetrieve):
    __doc__ = _('Display the properties of a Desktop Profile Rule Map.')

    def post_callback(self, ldap, dn, entry_attrs, *keys, **options):
        assert isinstance(dn, DN)
        self.obj._convert_seealso(ldap, entry_attrs, **options)
        self.obj._convert_profile(ldap, entry_attrs, **options)
        return dn



@register()
class deskprofilerule_enable(LDAPQuery):
    __doc__ = _('Enable a Desktop Profile Rule Map.')

    msg_summary = _('Enabled Desktop Profile Rule Map "%(value)s"')
    has_output = output.standard_value

    def execute(self, cn, **options):
        ldap = self.obj.backend

        dn = self.obj.get_dn(cn)
        try:
            entry_attrs = ldap.get_entry(dn, ['ipaenabledflag'])
        except errors.NotFound:
            self.obj.handle_not_found(cn)

        entry_attrs['ipaenabledflag'] = ['TRUE']

        try:
            ldap.update_entry(entry_attrs)
        except errors.EmptyModlist:
            raise errors.AlreadyActive()

        return dict(
            result=True,
            value=pkey_to_value(cn, options),
        )



@register()
class deskprofilerule_disable(LDAPQuery):
    __doc__ = _('Disable a Desktop Profile Rule Map.')

    msg_summary = _('Disabled Desktop Profile Rule Map "%(value)s"')
    has_output = output.standard_value

    def execute(self, cn, **options):
        ldap = self.obj.backend

        dn = self.obj.get_dn(cn)
        try:
            entry_attrs = ldap.get_entry(dn, ['ipaenabledflag'])
        except errors.NotFound:
            self.obj.handle_not_found(cn)

        entry_attrs['ipaenabledflag'] = ['FALSE']

        try:
            ldap.update_entry(entry_attrs)
        except errors.EmptyModlist:
            raise errors.AlreadyInactive()

        return dict(
            result=True,
            value=pkey_to_value(cn, options),
        )



@register()
class deskprofilerule_add_user(LDAPAddMember):
    __doc__ = _('Add users and groups to a Desktop Profile Rule Map.')

    member_attributes = ['memberuser']
    member_count_out = ('%i object added.', '%i objects added.')

    def pre_callback(self, ldap, dn, found, not_found, *keys, **options):
        assert isinstance(dn, DN)
        try:
            entry_attrs = ldap.get_entry(dn, self.obj.default_attributes)
            dn = entry_attrs.dn
        except errors.NotFound:
            self.obj.handle_not_found(*keys)
        if 'usercategory' in entry_attrs and \
            entry_attrs['usercategory'][0].lower() == 'all':
            raise errors.MutuallyExclusiveError(
                reason=_("users cannot be added when user category='all'"))
        if 'seealso' in entry_attrs:
            raise errors.MutuallyExclusiveError(reason=notboth_err)
        return dn



@register()
class deskprofilerule_remove_user(LDAPRemoveMember):
    __doc__ = _('Remove users and groups from a Desktop Profile Rule Map.')

    member_attributes = ['memberuser']
    member_count_out = ('%i object removed.', '%i objects removed.')



@register()
class deskprofilerule_add_host(LDAPAddMember):
    __doc__ = _('Add target hosts and hostgroups to a Desktop Profile Rule Map.')

    member_attributes = ['memberhost']
    member_count_out = ('%i object added.', '%i objects added.')

    def pre_callback(self, ldap, dn, found, not_found, *keys, **options):
        assert isinstance(dn, DN)
        try:
            entry_attrs = ldap.get_entry(dn, self.obj.default_attributes)
            dn = entry_attrs.dn
        except errors.NotFound:
            self.obj.handle_not_found(*keys)
        if 'hostcategory' in entry_attrs and \
            entry_attrs['hostcategory'][0].lower() == 'all':
            raise errors.MutuallyExclusiveError(
                reason=_("hosts cannot be added when host category='all'"))
        if 'seealso' in entry_attrs:
            raise errors.MutuallyExclusiveError(reason=notboth_err)
        return dn



@register()
class deskprofilerule_remove_host(LDAPRemoveMember):
    __doc__ = _('Remove target hosts and hostgroups from a Desktop Profile Rule Map.')

    member_attributes = ['memberhost']
    member_count_out = ('%i object removed.', '%i objects removed.')

@register()
class deskprofileconfig(LDAPObject):
    """
    Global configuration for desktop profiles
    """
    object_name = _('configuration options')
    default_attributes = [
        'ipadeskprofilepriority',
    ]
    permission_filter_objectclasses = ['ipadeskprofileconfig']
    managed_permissions = {
        'System: Read FleetCommander Desktop Profile Configuration': {
            'ipapermbindruletype': 'all',
            'ipapermright': {'read', 'search', 'compare'},
            'ipapermdefaultattr': {
                'cn', 'ipadeskprofilepriority',
                'objectclass',
            },
        },
        'System: Modify FleetCommander Desktop Profile Configuration': {
            'ipapermbindruletype': 'permission',
            'ipapermright': {'write'},
            'ipapermdefaultattr': {
                'ipadeskprofilepriority',
            },
            'default_privileges': {'FleetCommander Desktop Profile Administrators'},
        },
    }

    label = _('Desktop Profile Global Configuration')
    label_singular = _('Desktop Profile Global Configuration')

    takes_params = (
        Int('ipadeskprofilepriority',
            cli_name='priority',
            label=_('Priority of profile application'),
            minvalue=1,
            maxvalue=24,
        ),
    )

    # Inject constants into the api.env before it is locked down
    def _on_finalize(self):
        self.env._merge(**dict(PLUGIN_CONFIG))
        self.container_dn = self.env.container_deskprofile
        super(deskprofileconfig, self)._on_finalize()

    def get_dn(self, *keys, **kwargs):
        return DN(self.container_dn, api.env.basedn)


@register()
class deskprofileconfig_mod(LDAPUpdate):
    __doc__ = _('Modify Desktop Profile configuration options.')


@register()
class deskprofileconfig_show(LDAPRetrieve):
    __doc__ = _('Show Desktop Profile configuration options.')

