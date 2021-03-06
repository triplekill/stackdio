# -*- coding: utf-8 -*-

# Copyright 2016,  Digital Reasoning
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


import json
import logging

from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.db import models
from django_extensions.db.models import TimeStampedModel, TitleSlugDescriptionModel

from stackdio.core.fields import DeletingFileField

PROTOCOL_CHOICES = [
    ('tcp', 'TCP'),
    ('udp', 'UDP'),
    ('icmp', 'ICMP'),
    ('-1', 'all'),
]

DEVICE_ID_CHOICES = [
    ('/dev/sdb', '/dev/sdb'),
    ('/dev/sdc', '/dev/sdc'),
    ('/dev/sdd', '/dev/sdd'),
    ('/dev/sde', '/dev/sde'),
    ('/dev/sdf', '/dev/sdf'),
    ('/dev/sdg', '/dev/sdg'),
    ('/dev/sdh', '/dev/sdh'),
    ('/dev/sdi', '/dev/sdi'),
    ('/dev/sdj', '/dev/sdj'),
    ('/dev/sdk', '/dev/sdk'),
    ('/dev/sdl', '/dev/sdl'),
]

logger = logging.getLogger(__name__)


def get_props_file_path(obj, filename):
    return 'blueprints/{0}-{1}.props'.format(obj.pk, obj.slug)


_blueprint_model_permissions = (
    'create',
    'admin',
)

_blueprint_object_permissions = (
    'view',
    'update',
    'delete',
    'admin',
)


class Blueprint(TimeStampedModel, TitleSlugDescriptionModel):
    """
    Blueprints are a template of reusable configuration used to launch
    Stacks. The purpose to create a blueprint that encapsulates the
    functionality, software, etc you want in your infrastructure once
    and use it to repeatably create your infrastructure when needed.

    TODO: @params
    """
    model_permissions = _blueprint_model_permissions
    object_permissions = _blueprint_object_permissions
    searchable_fields = ('title', 'description')

    class Meta:
        ordering = ('title',)
        default_permissions = tuple(set(_blueprint_model_permissions +
                                        _blueprint_object_permissions))

    labels = GenericRelation('core.Label')

    formula_versions = GenericRelation('formulas.FormulaVersion')

    create_users = models.BooleanField('Create SSH Users')

    # storage for properties file
    props_file = DeletingFileField(
        max_length=255,
        upload_to=get_props_file_path,
        null=True,
        blank=True,
        default=None,
        storage=FileSystemStorage(location=settings.FILE_STORAGE_DIRECTORY))

    def __unicode__(self):
        return u'{0} (id={1})'.format(self.title, self.id)

    @property
    def host_definition_count(self):
        return self.host_definitions.count()

    @property
    def properties(self):
        if not self.props_file:
            return {}
        with open(self.props_file.path) as f:
            return json.loads(f.read())

    @properties.setter
    def properties(self, props):
        props_json = json.dumps(props, indent=4)
        if not self.props_file:
            self.props_file.save(self.slug + '.props', ContentFile(props_json))
        else:
            with open(self.props_file.path, 'w') as f:
                f.write(props_json)

    def get_formulas(self):
        formulas = set()
        for host_definition in self.host_definitions.all():
            for component in host_definition.formula_components.all():
                formulas.add(component.formula)

        return list(formulas)


class BlueprintHostDefinition(TitleSlugDescriptionModel, TimeStampedModel):

    class Meta:
        verbose_name_plural = 'host definitions'

        default_permissions = ()

        unique_together = (('title', 'blueprint'), ('hostname_template', 'blueprint'))

    # The blueprint object this host is owned by
    blueprint = models.ForeignKey('blueprints.Blueprint',
                                  related_name='host_definitions')

    # The cloud image object this host should use when being
    # launched
    cloud_image = models.ForeignKey('cloud.CloudImage',
                                    related_name='host_definitions')

    # The default number of instances to launch for this host definition
    count = models.PositiveIntegerField('Count')

    # The hostname template that will be used to generate the actual
    # hostname at launch time. Several template variables will be provided
    # when the template is rendered down to its final form
    hostname_template = models.CharField('Hostname Template', max_length=64)

    # The default instance size for the host
    size = models.ForeignKey('cloud.CloudInstanceSize')

    # The default availability zone for the host
    # Only for EC2 classic
    zone = models.ForeignKey('cloud.CloudZone', null=True, blank=True)

    # The subnet id for VPC enabled accounts
    # Only for EC2 VPC
    subnet_id = models.CharField('Subnet ID', max_length=32, blank=True, default='')

    # The spot instance price for this host. If null, spot
    # instances will not be used for this host.
    spot_price = models.DecimalField(max_digits=5,
                                     decimal_places=2,
                                     blank=True,
                                     null=True)

    # Grab the list of formula components
    formula_components = GenericRelation('formulas.FormulaComponent')

    @property
    def formula_components_count(self):
        return self.formula_components.count()

    def __unicode__(self):
        return self.title


class BlueprintAccessRule(TitleSlugDescriptionModel, TimeStampedModel):
    """
    Access rules are a white list of rules for a host that defines
    what protocols and ports are available for the corresponding
    machines at launch time. In other words, they define the
    firefall rules for the machine.
    """

    class Meta:
        verbose_name_plural = 'access rules'

        default_permissions = ()

    # The host definition this access rule applies to
    host = models.ForeignKey('blueprints.BlueprintHostDefinition',
                             related_name='access_rules')

    # The protocol for the access rule. One of tcp, udp, or icmp
    protocol = models.CharField('Protocol', max_length=4, choices=PROTOCOL_CHOICES)

    # The from and to ports define the range of ports to open for the
    # given protocol and rule string. To open a single port, the
    # from and to ports should be the same integer.
    from_port = models.IntegerField('Start Port')
    to_port = models.IntegerField('End Port')

    # Rule is a string specifying the CIDR for what network has access
    # to the given protocl and ports. For AWS, you may also specify
    # a rule of the form "owner_id:security_group", that will authorize
    # access to the given security group owned by the owner_id's account
    rule = models.CharField('Rule', max_length=255)

    def __unicode__(self):
        return u'{0} {1}-{2} {3}'.format(
            self.protocol,
            self.from_port,
            self.to_port,
            self.rule
        )


class BlueprintVolume(TitleSlugDescriptionModel, TimeStampedModel):

    class Meta:
        verbose_name_plural = 'volumes'

        default_permissions = ()

    # The host definition this access rule applies to
    host = models.ForeignKey('blueprints.BlueprintHostDefinition',
                             related_name='volumes')

    # The device that the volume should be attached to when a stack is created
    device = models.CharField('Device Name', max_length=32, choices=DEVICE_ID_CHOICES)

    # Where the volume will be mounted after created and attached
    mount_point = models.CharField('Mount Point', max_length=64)

    # The snapshot ID to create the volume from
    snapshot = models.ForeignKey('cloud.Snapshot',
                                 related_name='host_definitions')

    def __unicode__(self):
        return u'BlueprintVolume: {0}'.format(self.pk)
