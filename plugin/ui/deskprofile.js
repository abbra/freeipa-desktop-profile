/*  Authors:
 *    Petr Vobornik <pvoborni@redhat.com>
 *    Alexander Bokovoy <abokovoy@redhat.com>
 *
 * Copyright (C) 2012-2016 Red Hat
 * see file 'COPYING' for use and warranty information
 */

define([
        './ipa',
        './jquery',
        './phases',
        './reg',
        './association',
        './entity',
        './details',
        './rule',
        './search'
        ],
            function(IPA, $, phases, reg) {

var exp_deskprofile = IPA.deskprofile = {
    remove_method_priority: IPA.config.default_priority - 1
};

var make_deskprofile_spec = function() {
var spec = {
    name: 'deskprofile',
    facets: [
        {
            $type: 'search',
            columns: [
                'cn',
                'description'
            ],
        },
        {
            $type: 'details',
            $factory: IPA.deskprofile_details_facet,
            command_mode: 'info',
            actions: [
                'select',
                'delete'
            ],
            header_actions: ['delete'],
        }
    ],
    adder_dialog: {
        fields: [
            'cn',
            'description',
            'ipadeskdata'
        ]
    }
};

    add_deskprofile_details_facet_widgets(spec.facets[1]);
    return spec;
};


/**
 * @ignore
 * @param {Object} facet spec
 */
var add_deskprofile_details_facet_widgets = function (spec) {

    //
    // General
    //

    spec.fields = [
        {
            name: 'cn',
            read_only: true,
            widget: 'general.cn'
        },
        {
            $type: 'textarea',
            name: 'description',
            widget: 'general.description'
        },
        {
            $type: 'textarea',
            name: 'ipadeskdata',
            widget: 'general.description'
        },
    ];

    spec.widgets = [
        {
            $type: 'details_section',
            name: 'general',
            label: '@i18n:details.general',
            widgets: [
                {
                    name: 'cn'
                },
                {
                    $type: 'textarea',
                    name: 'description'
                },
                {
                    $type: 'textarea',
                    name: 'ipadeskdata',
                },
            ]
        }
    ];

};

IPA.deskprofile_details_facet = function(spec) {

    var that = IPA.details_facet(spec);

    that.update_on_success = function(data, text_status, xhr) {
        that.refresh();
        that.on_update.notify();
        that.nofify_update_success();
    };

    that.update_on_error = function(xhr, text_status, error_thrown) {
        that.refresh();
    };

    return that;
};

exp_deskprofile.entity_spec = make_deskprofile_spec();
exp_deskprofile.register = function() {
    var e = reg.entity;
    e.register({type: 'deskprofile', spec: exp_deskprofile.entity_spec});
};
phases.on('registration', exp_deskprofile.register);

return exp_deskprofile;
});

define([
        './ipa',
        './jquery',
        './phases',
        './reg',
        './association',
        './entity',
        './details',
        './rule',
        './search'
        ],
            function(IPA, $, phases, reg) {


var exp_deskprofilerule = IPA.deskprofilerule = {
    remove_method_priority: IPA.config.default_priority - 1
};

var make_deskprofilerule_spec = function() {
var spec = {
    name: 'deskprofilerule',
    facets: [
        {
            $type: 'search',
            row_enabled_attribute: 'ipaenabledflag',
            columns: [
                'cn',
                'ipadeskprofiletarget',
                {
                    name: 'ipaenabledflag',
                    label: '@i18n:status.label',
                    formatter: 'boolean_status'
                },
                'description',
                'ipadeskprofilepriority'
            ],
            actions: [
                'batch_disable',
                'batch_enable'
            ],
            control_buttons: [
                {
                    name: 'disable',
                    label: '@i18n:buttons.disable',
                    icon: 'fa-minus'
                },
                {
                    name: 'enable',
                    label: '@i18n:buttons.enable',
                    icon: 'fa-check'
                }
            ]
        },
        {
            $type: 'details',
            $factory: IPA.deskprofilerule_details_facet,
            command_mode: 'info',
            actions: [
                'select',
                'enable',
                'disable',
                'delete'
            ],
            header_actions: ['enable', 'disable', 'delete'],
            state: {
                evaluators: [
                    {
                        $factory: IPA.enable_state_evaluator,
                        field: 'ipaenabledflag'
                    }
                ],
                summary_conditions: [
                    IPA.enabled_summary_cond,
                    IPA.disabled_summary_cond
                ]
            }
        }
    ],
    adder_dialog: {
        fields: [
            'cn',
            'ipadeskprofilerule',
            'ipadeskprofilepriority'
        ]
    }
};

    add_deskprofilerule_details_facet_widgets(spec.facets[1]);
    return spec;
};


/**
 * @ignore
 * @param {Object} facet spec
 */
var add_deskprofilerule_details_facet_widgets = function (spec) {

    //
    // General
    //

    spec.fields = [
        {
            name: 'cn',
            read_only: true,
            widget: 'general.cn'
        },
        {
            name: 'ipadeskprofilepriority',
            widget: 'general.prio'
        },
        {
            $type: 'textarea',
            name: 'description',
            widget: 'general.description'
        },
        {
            name: 'ipadeskprofiletarget',
            widget: 'general.ipadeskprofiletarget'
        },
        {
            $type: 'entity_select',
            name: 'seealso',
            widget: 'general.seealso'
        }
    ];

    spec.widgets = [
        {
            $type: 'details_section',
            name: 'general',
            label: '@i18n:details.general',
            widgets: [
                {
                    name: 'cn'
                },
                {
                    name: 'ipadeskprofilepriority'
                },
                {
                    $type: 'textarea',
                    name: 'description'
                },
                {
                    name: 'ipadeskprofiletarget',
                    widget: 'general.ipadeskprofiletarget'
                },
                {
                    $type: 'entity_select',
                    name: 'seealso',
                    other_entity: 'hbacrule',
                    other_field: 'cn'
                }
            ]
        }
    ];

    //
    // Users
    //

    spec.fields.push(
        {
            $type: 'radio',
            name: 'usercategory',
            widget: 'user.rule.usercategory'
        },
        {
            $type: 'rule_association_table',
            name: 'memberuser_user',
            widget: 'user.rule.memberuser_user',
            priority: IPA.deskprofilerule.remove_method_priority
        },
        {
            $type: 'rule_association_table',
            name: 'memberuser_group',
            widget: 'user.rule.memberuser_group',
            priority: IPA.deskprofilerule.remove_method_priority
        }
    );

    spec.widgets.push(
        {
            $factory: IPA.section,
            name: 'user',
            label: '@i18n:objects.deskprofilerule.user',
            widgets: [
                {
                    $factory: IPA.rule_details_widget,
                    name: 'rule',
                    radio_name: 'usercategory',
                    options: [
                        { value: 'all',
                        label: '@i18n:objects.deskprofilerule.anyone' },
                        { value: '',
                        label: '@i18n:objects.deskprofilerule.specified_users' }
                    ],
                    tables: [
                        { name: 'memberuser_user' },
                        { name: 'memberuser_group' }
                    ],
                    widgets: [
                        {
                            $type: 'rule_association_table',
                            id: 'deskprofilerule-memberuser_user',
                            name: 'memberuser_user',
                            add_method: 'add_user',
                            remove_method: 'remove_user',
                            add_title: '@i18n:association.add.member',
                            remove_title: '@i18n:association.remove.member'
                        },
                        {
                            $type: 'rule_association_table',
                            id: 'deskprofilerule-memberuser_group',
                            name: 'memberuser_group',
                            add_method: 'add_user',
                            remove_method: 'remove_user',
                            add_title: '@i18n:association.add.member',
                            remove_title: '@i18n:association.remove.member'
                        }
                    ]
                }
            ]
        }
    );

    //
    // Hosts
    //

    spec.fields.push(
        {
            $type: 'radio',
            name: 'hostcategory',
            widget: 'host.rule.hostcategory'
        },
        {
            $type: 'rule_association_table',
            name: 'memberhost_host',
            widget: 'host.rule.memberhost_host',
            priority: IPA.deskprofilerule.remove_method_priority
        },
        {
            $type: 'rule_association_table',
            name: 'memberhost_hostgroup',
            widget: 'host.rule.memberhost_hostgroup',
            priority: IPA.deskprofilerule.remove_method_priority
        }
    );

    spec.widgets.push(
        {
            $factory: IPA.section,
            name: 'host',
            label: '@i18n:objects.deskprofilerule.host',
            widgets: [
                {
                    $factory: IPA.rule_details_widget,
                    name: 'rule',
                    radio_name: 'hostcategory',
                    options: [
                        {
                            'value': 'all',
                            label: '@i18n:objects.deskprofilerule.any_host'
                        },
                        {
                            'value': '',
                            label: '@i18n:objects.deskprofilerule.specified_hosts'
                        }
                    ],
                    tables: [
                        { 'name': 'memberhost_host' },
                        { 'name': 'memberhost_hostgroup' }
                    ],
                    widgets: [
                        {
                            $type: 'rule_association_table',
                            id: 'deskprofilerule-memberuser_user',
                            name: 'memberhost_host',
                            add_method: 'add_host',
                            remove_method: 'remove_host',
                            add_title: '@i18n:association.add.member',
                            remove_title: '@i18n:association.remove.member'
                        },
                        {
                            $type: 'rule_association_table',
                            id: 'deskprofilerule-memberuser_group',
                            name: 'memberhost_hostgroup',
                            add_method: 'add_host',
                            remove_method: 'remove_host',
                            add_title: '@i18n:association.add.member',
                            remove_title: '@i18n:association.remove.member'
                        }
                    ]
                }
            ]
        }
    );
};

IPA.deskprofilerule_details_facet = function(spec) {

    var that = IPA.details_facet(spec);

    that.update_on_success = function(data, text_status, xhr) {
        that.refresh();
        that.on_update.notify();
        that.nofify_update_success();
    };

    that.update_on_error = function(xhr, text_status, error_thrown) {
        that.refresh();
    };

    return that;
};

exp_deskprofilerule.entity_spec = make_deskprofilerule_spec();
exp_deskprofilerule.register = function() {
    var e = reg.entity;
    e.register({type: 'deskprofilerule', spec: exp_deskprofilerule.entity_spec});
};
phases.on('registration', exp_deskprofilerule.register);

return exp_deskprofilerule;
});
