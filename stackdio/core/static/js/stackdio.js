var stackdio = {};


$(document).ready(function () {


    $('#snapshots').dataTable({
        "bPaginate": false,
        "bLengthChange": false,
        "bFilter": true,
        "bSort": false,
        "bInfo": false,
        "bAutoWidth": true,
        "bFilter": false
    });

    $('#stacks').dataTable({
        "bPaginate": false,
        "bLengthChange": false,
        "bFilter": true,
        "bSort": false,
        "bInfo": false,
        "bAutoWidth": true,
        "bFilter": false
    });

    $('#accounts').dataTable({
        "bPaginate": false,
        "bLengthChange": false,
        "bFilter": true,
        "bSort": false,
        "bInfo": false,
        "bAutoWidth": true,
        "bFilter": false
    });

    $('#stack-hosts').dataTable({
        "bPaginate": false,
        "bLengthChange": false,
        "bFilter": true,
        "bSort": false,
        "bInfo": false,
        "bAutoWidth": true,
        "bFilter": false
    });

    $('#profiles').dataTable({
        "bPaginate": false,
        "bLengthChange": false,
        "bFilter": true,
        "bSort": false,
        "bInfo": false,
        "bAutoWidth": true,
        "bFilter": false
    });





    $( "#stack-form-container" ).dialog({
        autoOpen: false,
        width: 1200,
        position: [200,50],
        modal: false
    });

    $( "#snapshot-form-container" ).dialog({
        autoOpen: false,
        width: 650,
        modal: false
    });

    $( "#accounts-form-container" ).dialog({
        autoOpen: false,
        width: 650,
        modal: false
    });

    $( "#host-form-container" ).dialog({
        autoOpen: false,
        width: 800,
        modal: false
    });

    $( "#profile-form-container" ).dialog({
        autoOpen: false,
        width: 650,
        modal: false
    });




    /*
     *  ==================================================================================
     *  V I E W   M O D E L
     *  ==================================================================================
     */
    function stackdioModel() {
        var self = this;

        self.showVolumes = ko.observable(false);
        self.sections = ['Stacks', 'Accounts', 'Profiles', 'Snapshots'];
        self.currentSection = ko.observable();

        /*
         *  ==================================================================================
         *  C O L L E C T I O N S
         *  ==================================================================================
         */
        self.stacks = ko.observableArray([]);
        self.roles = ko.observableArray([]);
        self.launchedHosts = ko.observableArray([]);
        self.instanceSizes = ko.observableArray([]);

        self.providerTypes = ko.observableArray([]);
        self.selectedProviderType = null;

        self.profiles = ko.observableArray([]);
        self.selectedProfile = null;
        self.addProfile = function (model, evt) {
            var record = self.collectFormFields(evt.target.form);

            $.ajax({
                url: '/api/profiles/',
                method: 'POST',
                data: {
                    title: record.profile_title.value,
                    description: record.profile_description.value,
                    cloud_provider: self.selectedAccount.id,
                    image_id: record.image_id.value,
                    default_instance_size: record.default_instance_size.value,
                    ssh_user: record.ssh_user.value
                },
                headers: {
                    "Authorization": "Basic " + Base64.encode('testuser:password'),
                    "Accept": "application/json"
                },
                success: function (response) {
                    var i, item = response;

                    if (item.hasOwnProperty('id')) {
                        self.profiles.push(item);
                        $( "#profile-form-container" ).dialog("close");
                    }
                }
            });
        };
        self.removeProfile = function (profile) {
            self.profiles.remove(profile);
        };


        self.accounts = ko.observableArray([]);
        self.selectedAccount = null;
        self.addAccount = function (model, evt) {
            var record = self.collectFormFields(evt.target.form);
            var files, formData = new FormData(), xhr = new XMLHttpRequest();

            // A reference to the files selected
            // files = me.accountForm.down('filefield').fileInputEl.dom.files;
            console.log(record);

            // Append private key file to the FormData() object
            formData.append('private_key_file', record.private_key_file[0]);

            // Add the provider type that the user chose from the account split button
            formData.append('provider_type', self.selectedProviderType.id);

            // Append all other required fields to the form data
            for (r in record) {
                rec = record[r];
                formData.append(r, rec);
            }

            // Open the connection to the provider URI and set authorization header
            xhr.open('POST', '/api/providers/');
            xhr.setRequestHeader('Authorization', 'Basic ' + Base64.encode('testuser:password'));

            // Define any actions to take once the upload is complete
            xhr.onloadend = function (evt) {
                var record = JSON.parse(evt.target.response);

                // Show an animated message containing the result of the upload
                if (evt.target.status === 200 || evt.target.status === 201 || evt.target.status === 302) {
                    $( "#accounts-form-container" ).dialog( "close" );
                    self.accounts.push(new Account(record.id.text, 
                                                    record.title.text,
                                                    record.description.text,
                                                    record.provider_type.text,
                                                    record.provider_type_name.text
                                                  ));
                    console.log('accounts', self.accounts());
                } else {
                    // var html=[], response = JSON.parse(evt.target.response);

                    // for (key in response) {
                    //     failure = response[key];
                    //     html.push('<p>' + key + ': ' + failure + '</p>');
                    // }
                    // me.application.notification.scold('New account failed to save. Check your data and try again...'+html, 5000);
                }
            };

            // Start the upload process
            xhr.send(formData);
        };
        self.removeAccount = function (account) {
            self.accounts.remove(account);
        };


        self.snapshots = ko.observableArray([]);
        self.addSnapshot = function (model, evt) {
            var record = self.collectFormFields(evt.target.form);

            $.ajax({
                url: '/api/snapshots/',
                method: 'POST',
                data: {
                    title: record.snapshot_title.text,
                    description: record.snapshot_description.text,
                    cloud_provider: self.selectedAccount.id,
                    size_in_gb: record.snapshot_size.text,
                    snapshot_id: record.snapshot_id.text
                },
                headers: {
                    "Authorization": "Basic " + Base64.encode('testuser:password'),
                    "Accept": "application/json"
                },
                success: function (response) {
                    var i, item, items = response.results;

                    console.log(items);

                    // self.snapshots.removeAll();
                    // self.snapshots.push(snapshot);

                    // for (i in items) {
                    //     item = items[i];
                    //     self.snapshots.push(new Snapshot(item.id, item.url, item.title, item.description, item.cloud_provider, item.size_in_gb, item.snapshot_id));
                    // }
                }
            });
        };
        self.removeSnapshot = function (snapshot) {
            self.snapshots.remove(snapshot);
        };



        self.newHostVolumes = ko.observableArray([]);
        self.addHostVolume = function (model, evt) {
            var form = self.collectFormFields(evt.target.form);

            self.newHostVolumes.push(new NewHostVolume(0, form['volume-snapshot'].text, form['volume-device'].text, form['volume-mount-point'].text));
        };
        self.removeHostVolume = function (volume) {
            self.newHostVolumes.remove(volume);
        };



        // id, stack, count, cloud_profile, instance_size, roles, hostname, security_groups
        self.newHosts = ko.observableArray([
            // new NewHost(1, 'rwvf', 4, 'vfwvf', 'wvwgvfgw', 'vgr42hnntg', 'jikjimjunhjnb', 'rgbhrtbnhtg'),
            // new NewHost(1, 'rwvf', 4, 'vfwvf', 'wvwgvfgw', 'vgr42hnntg', 'jikjimjunhjnb', 'rgbhrtbnhtg'),
            // new NewHost(1, 'rwvf', 4, 'vfwvf', 'wvwgvfgw', 'vgr42hnntg', 'jikjimjunhjnb', 'rgbhrtbnhtg'),
            // new NewHost(1, 'rwvf', 4, 'vfwvf', 'wvwgvfgw', 'vgr42hnntg', 'jikjimjunhjnb', 'rgbhrtbnhtg'),
            // new NewHost(1, 'rwvf', 4, 'vfwvf', 'wvwgvfgw', 'vgr42hnntg', 'jikjimjunhjnb', 'rgbhrtbnhtg'),
            // new NewHost(1, 'rwvf', 4, 'vfwvf', 'wvwgvfgw', 'vgr42hnntg', 'jikjimjunhjnb', 'rgbhrtbnhtg'),
            // new NewHost(1, 'rwvf', 4, 'vfwvf', 'wvwgvfgw', 'vgr42hnntg', 'jikjimjunhjnb', 'rgbhrtbnhtg'),
            // new NewHost(1, 'rwvf', 4, 'vfwvf', 'wvwgvfgw', 'vgr42hnntg', 'jikjimjunhjnb', 'rgbhrtbnhtg'),
            // new NewHost(1, 'rwvf', 4, 'vfwvf', 'wvwgvfgw', 'vgr42hnntg', 'jikjimjunhjnb', 'rgbhrtbnhtg'),
            // new NewHost(1, 'rwvf', 4, 'vfwvf', 'wvwgvfgw', 'vgr42hnntg', 'jikjimjunhjnb', 'rgbhrtbnhtg')
        ]);

        self.addHost = function (model, evt) {
            var form = self.collectFormFields(evt.target.form);
            console.log(form);
            return;
            self.newHosts.push(new NewHost(0, 0, count, cloud_profile, instance_size, roles, hostname, security_groups));
        };
        self.removeHost = function (host) {
            self.newHosts.remove(host);
        };


        /*
         *  ==================================================================================
         *  M E T H O D S
         *  ==================================================================================
         */

        self.collectFormFields = function (obj) {
            var i, item, el, form = {}, id, idx;

            // Collect the fields from the form
            for (i in obj) {
                item = obj[i];
                if (item !== null && item.hasOwnProperty('localName') && ['select','input'].indexOf(item.localName) !== -1) {

                    id = item.id;
                    form[id] = {};

                    switch (item.localName) {
                        case 'input':
                            if (item.files === null) {
                                form[id].text = item.text;
                                form[id].value = item.value;
                            } else {
                                form[id].text = '';
                                form[id].value = '';
                                form[id].files = item.files;
                            }
                            break;
                        case 'select':
                            el = document.getElementById(id);
                            idx = el.selectedIndex;

                            if (idx !== -1) {
                                form[id].text = el[idx].text;
                                form[id].value = el[idx].value;
                                form[id].selectedIndex = idx;
                            }
                            break;
                    }
                }
            }

            return form;
        }

        self.showProfileForm = function (account) {
            console.log(account);
            self.selectedAccount = account;
            $( "#profile-form-container" ).dialog("open");
        }

        self.showSnapshotForm = function (account) {
            self.selectedAccount = account;
            $( "#snapshot-form-container" ).dialog("open");
        }

        self.showAccountForm = function (type) {
            self.selectedProviderType = type;
            $( "#accounts-form-container" ).dialog("open");
        }

        self.showStackForm = function () {
            $( "#stack-form-container" ).dialog("open");
        }

        self.showHostForm = function () {
            $( "#host-form-container" ).dialog("open");
        }

        self.gotoSection = function (section) { 
            location.hash = section;
            self.currentSection(section);
        };

        self.profileSelected = function (profile) { 
            console.log(profile);
        };

        self.toggleVolumeForm = function () { 
            self.showVolumes(!self.showVolumes());
        };


        /*
         *  ==================================================================================
         *  A P I   C A L L S
         *  ==================================================================================
         */

        $.ajax({
            url: '/api/provider_types/',
            headers: {
                "Authorization": "Basic " + Base64.encode('testuser:password'),
                "Accept": "application/json"
            },
            success: function (response) {
                var i, item, items = response.results;

                for (i in items) {
                    item = items[i];
                    self.providerTypes.push(new ProviderType(item.id, item.url, item.type_name, item.title));
                }

                console.log('providerTypes', self.providerTypes());
            }
        });

        self.loadStacks = function () {
            var deferred = Q.defer();

            console.log('loading stacks');

            $.ajax({
                url: '/api/stacks/',
                headers: {
                    "Authorization": "Basic " + Base64.encode('testuser:password'),
                    "Accept": "application/json"
                },
                success: function (response) {
                    var i, item, items = response.results;

                    deferred.resolve();
                    self.stacks.removeAll();

                    for (i in items) {
                        item = items[i];
                        self.stacks.push(new Stack(item.title, item.description, item.status, item.created, item.host_count, item.id, item.slug, item.user, item.url));
                    }

                    console.log('stacks', self.stacks());
                }
            });

            return deferred.promise
        };


        self.loadAccounts = function () {
            var deferred = Q.defer();

            console.log('loading accounts');

            $.ajax({
                url: '/api/providers/',
                headers: {
                    "Authorization": "Basic " + Base64.encode('testuser:password'),
                    "Accept": "application/json"
                },
                success: function (response) {
                    var i, item, items = response.results;

                    deferred.resolve();
                    self.accounts.removeAll();

                    for (i in items) {
                        item = items[i];
                        // id, title, description, slug, provider_type, provider_type_name, yaml
                        self.accounts.push(new Account(item.id, item.title, item.description, item.provider_type, item.provider_type_name));
                    }

                    console.log('accounts', self.accounts());
                }
            });

            return deferred.promise
        };

        self.loadSnapshots = function () {
            var deferred = Q.defer();

            console.log('loading snapshots');

            $.ajax({
                url: '/api/snapshots/',
                headers: {
                    "Authorization": "Basic " + Base64.encode('testuser:password'),
                    "Accept": "application/json"
                },
                success: function (response) {
                    var i, item, items = response.results, snapshot;

                    deferred.resolve(items);

                    self.snapshots.removeAll();

                    for (i in items) {
                        item = items[i];
                        snapshot = new Snapshot(
                                    item.id,
                                    item.url,
                                    item.title,
                                    item.description,
                                    item.cloud_provider,
                                    item.size_in_gb,
                                    item.snapshot_id
                                   );

                        // Inject the name of the provider account used to create the snapshot
                        snapshot.account_name = _.find(self.accounts(), function (account) {
                            return account.id = item.cloud_provider;
                        }).title;

                        self.snapshots.push(snapshot);
                    }

                    console.log('snapshots', self.snapshots());
                }
            });

            return deferred.promise
        };

        self.loadRoles = function () {
            $.ajax({
                url: '/api/roles/',
                headers: {
                    "Authorization": "Basic " + Base64.encode('testuser:password'),
                    "Accept": "application/json"
                },
                success: function (response) {
                    var i, item, items = response.results;

                    self.roles.removeAll();

                    for (i in items) {
                        item = items[i];
                        self.roles.push(new Role(item.id, item.url, item.title, item.role_name));
                    }
                }
            });
        };

        self.loadInstanceSizes = function () {
            var deferred = Q.defer();

            $.ajax({
                url: '/api/instance_sizes/',
                headers: {
                    "Authorization": "Basic " + Base64.encode('testuser:password'),
                    "Accept": "application/json"
                },
                success: function (response) {
                    var i, item, items = response.results;

                    deferred.resolve(items);
                    self.instanceSizes.removeAll();

                    for (i in items) {
                        item = items[i];
                        self.instanceSizes.push(new InstanceSize(item.id,
                                                                 item.url,
                                                                 item.title, 
                                                                 item.description,
                                                                 item.slug,
                                                                 item.provider_type,
                                                                 item.instance_id
                                                                )
                        );
                    }
                    console.log('instance sizes', self.instanceSizes());
                }
            });

            return deferred.promise
        };


        self.loadProfiles = function () {
            var deferred = Q.defer();
            var profile;

            console.log('loading profiles');

            $.ajax({
                url: '/api/profiles/',
                headers: {
                    "Authorization": "Basic " + Base64.encode('testuser:password'),
                    "Accept": "application/json"
                },
                success: function (response) {
                    var i, item, items = response.results;

                    deferred.resolve(items);

                    self.profiles.removeAll();

                    for (i in items) {
                        item = items[i];
                        profile = new AccountProfile(item.id,
                                        item.url,
                                        item.title, 
                                        item.description,
                                        item.slug,
                                        item.cloud_provider,
                                        item.default_instance_size,
                                        item.image_id,
                                        item.ssh_user
                                        );
                        console.log(profile);

                        // Inject the name of the provider account used to create the snapshot
                        profile.account_name = _.find(self.accounts(), function (account) {
                            return account.id = item.cloud_provider;
                        }).title;

                        self.profiles.push(profile);
                    }

                    console.log('profiles', self.profiles());
                }
            });

            return deferred.promise
        };




        /*
         *  ==================================================================================
         *  N A V I G A T I O N   H A N D L E R
         *  ==================================================================================
         */
        $.sammy(function() {
            this.get('#:section', function () {
                self.currentSection(this.params.section);

                switch (this.params.section) {
                    case 'Stacks':
                        self.loadInstanceSizes();
                        self.loadRoles();
                        self.loadStacks();

                        Q.fcall(self.loadAccounts)
                            .then(self.loadSnapshots)
                            .then(self.loadProfiles)
                            .catch(function (error) {
                                console.log(error);
                            })
                            .done();
                        break;
                    case 'Snapshots':
                        Q.fcall(self.loadAccounts)
                            .then(self.loadSnapshots)
                            .catch(function (error) {
                                console.log(error);
                            })
                            .done();
                        break;
                    case 'Profiles':
                        self.loadInstanceSizes();

                        Q.fcall(self.loadAccounts)
                            .then(self.loadProfiles)
                            .catch(function (error) {
                                console.log(error);
                            })
                            .done();
                        break;
                }
            });

            this.get('', function() { this.app.runRoute('get', '#Stacks') });
        }).run();
    };

    stackdio.mainModel = new stackdioModel();
    console.log(stackdio.mainModel);
    ko.applyBindings(stackdio.mainModel);

});