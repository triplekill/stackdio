/*!
  * Copyright 2016,  Digital Reasoning
  *
  * Licensed under the Apache License, Version 2.0 (the "License");
  * you may not use this file except in compliance with the License.
  * You may obtain a copy of the License at
  *
  *     http://www.apache.org/licenses/LICENSE-2.0
  *
  * Unless required by applicable law or agreed to in writing, software
  * distributed under the License is distributed on an "AS IS" BASIS,
  * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  * See the License for the specific language governing permissions and
  * limitations under the License.
  *
*/

define([
    'jquery',
    'knockout',
    'bootbox'
], function ($, ko, bootbox) {
    'use strict';

    return function() {
        var self = this;

        self.breadcrumbs = [
            {
                active: false,
                title: 'Profile',
                href: '/user/'
            },
            {
                active: true,
                title: 'Change Password'
            }
        ];

        // View variables
        self.currentPassword = ko.observable();
        self.newPassword1 = ko.observable();
        self.newPassword2 = ko.observable();

        // Necessary functions
        self.reset = function() {
            self.currentPassword('');
            self.newPassword1('');
            self.newPassword2('');
        };

        self.removeErrors = function(keys) {
            keys.forEach(function (key) {
                var el = $('#' + key);
                el.removeClass('has-error');
                var help = el.find('.help-block');
                help.remove();
            });
        };

        self.changePassword = function() {
            // First remove all the old error messages
            var keys = ['current_password', 'new_password1', 'new_password2'];

            self.removeErrors(keys);

            // Create the user!
            $.ajax({
                'method': 'POST',
                'url': '/api/user/password/',
                'data': JSON.stringify({
                    current_password: self.currentPassword(),
                    new_password1: self.newPassword1(),
                    new_password2: self.newPassword2()
                })
            }).done(function () {
                // Successful change, go back to the profile page
                window.location = '/user/';
            }).fail(function (jqxhr) {
                // Display any error messages
                var message = '';
                try {
                    var resp = JSON.parse(jqxhr.responseText);
                    for (var key in resp) {
                        if (resp.hasOwnProperty(key)) {
                            if (keys.indexOf(key) >= 0) {
                                var el = $('#' + key);
                                el.addClass('has-error');
                                resp[key].forEach(function (errMsg) {
                                    el.append('<span class="help-block">' + errMsg + '</span>');
                                });
                            } else {
                                var betterKey = key.replace('_', ' ');

                                resp[key].forEach(function (errMsg) {
                                    message += '<dt>' + betterKey + '</dt><dd>' + errMsg + '</dd>';
                                });
                            }
                        }
                    }
                    if (message) {
                        message = '<dl class="dl-horizontal">' + message + '</dl>';
                    }
                } catch (e) {
                    message = 'Oops... there was a server error.  This has been reported to ' +
                        'your administrators.';
                }
                if (message) {
                    bootbox.alert({
                        title: 'Error changing password',
                        message: message
                    });
                }
            });
        };

        self.reset();
    };
});
