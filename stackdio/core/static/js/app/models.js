/*
*  ==================================================================================
*  D A T A   M O D E L S
*  ==================================================================================
*/
var Stack = function (title, description, status, created, host_count, id, slug, user, url) {
    var self = this;
    self.id = id;
    self.title = ko.observable(title);
    self.description = ko.observable(description);
    self.slug = slug;
    self.url = url;
    self.created = created;
    self.status = ko.observable(status);
    self.host_count = host_count;
    self.user = user;
};

var ProviderType = function (id, url, type_name, title) {
    var self = this;
    self.id = id;
    self.title = title;
    self.url = url;
    self.type_name = type_name;
};


var Account = function (id, title, description, slug, provider_type, provider_type_name, yaml) {
    var self = this;
    self.id = id;
    self.title = title;
    self.description = description;
    self.slug = slug;
    self.provider_type = provider_type;
    self.provider_type_name = provider_type_name;
    self.yaml = yaml;
};

var AccountProfile = function (id, url, title, description, slug, cloud_provider, default_instance_size, image_id, ssh_user) {
    var self = this;
    self.cloud_provider = cloud_provider;
    self.title = title;
    self.description = description;
    self.default_instance_size = default_instance_size;
    self.image_id = image_id;
    self.ssh_user = ssh_user;
    self.id = id;
    self.slug = slug;
    self.url = url;
};

var NewHost = function (id, stack, count, cloud_profile, instance_size, roles, hostname, security_groups) {
    var self = this;
    self.id = id;
    self.stack = stack;
    self.count = count;
    self.cloud_profile = cloud_profile;
    self.instance_size = instance_size;
    self.instance_size_name = null;
    self.roles = ko.observable(roles);
    self.hostname = hostname;
    self.security_groups = security_groups;
    
    self.flat_roles = ko.computed(function () {
        return _.map(self.roles(), function (r) { 
            return '<div style="line-height:15px !important;">' + r.text + '</div>'; 
        }).join('');
    });

};

var NewHostVolume = function (id, snapshot, device, mount_point) {
    var self = this;
    self.id = id;
    self.snapshot = snapshot;
    self.device = device;
    self.mount_point = mount_point;
};

var InstanceSize = function (id, url, title, description, slug, provider_type, instance_id) {
    var self = this;
    self.id = id;
    self.url = url;
    self.title = title;
    self.description = description;
    self.slug = slug;
    self.provider_type = provider_type;
    self.instance_id = instance_id;
};

var Role = function (id, url, title, role_name) {
    var self = this;
    self.id = id;
    self.url = url;
    self.title = title;
    self.role_name = role_name;
};

var Snapshot = function (id, url, title, description, cloud_provider, size_in_gb, snapshot_id) {
    var self = this;
    self.id = id;
    self.url = url;
    self.title = title;
    self.description = description;
    self.cloud_provider = cloud_provider;
    self.account_name = null;
    self.size_in_gb = size_in_gb;
    self.snapshot_id = snapshot_id;
};
