import logging

from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework import serializers

from . import models

logger = logging.getLogger(__name__)


class BlueprintPropertySerializer(serializers.ModelSerializer):

    class Meta:
        model = models.BlueprintProperty
        fields = (
            'name',
            'value',
        )


class BlueprintAccessRuleSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.BlueprintAccessRule
        fields = (
            'protocol',
            'from_port',
            'to_port',
            'rule',
        )


class BlueprintVolumeSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.BlueprintVolume
        fields = (
            'device',
            'mount_point',
            'snapshot',
        )


class BlueprintHostFormulaComponentSerializer(serializers.HyperlinkedModelSerializer):
    title = serializers.Field(source='component.title')
    description = serializers.Field(source='component.description')
    formula = serializers.Field(source='component.formula')
    sls_path = serializers.Field(source='component.sls_path')

    class Meta:
        model = models.BlueprintHostFormulaComponent
        fields = (
            'title',
            'description',
            'formula',
            'sls_path',
            'order',
        )


class BlueprintHostDefinitionSerializer(serializers.HyperlinkedModelSerializer):

    formula_components = BlueprintHostFormulaComponentSerializer(many=True)
    access_rules = BlueprintAccessRuleSerializer(many=True, required=False)
    volumes = BlueprintVolumeSerializer(many=True)

    class Meta:
        model = models.BlueprintHostDefinition
        fields = (
            'title',
            'description',
            'cloud_profile',
            'count',
            'prefix',
            'size',
            'zone',
            'formula_components',
            'access_rules',
            'volumes',
            'spot_price',
        )


class BlueprintSerializer(serializers.HyperlinkedModelSerializer):
    
    properties = BlueprintPropertySerializer(many=True, required=False)
    host_definitions = BlueprintHostDefinitionSerializer(many=True, required=False)

    class Meta:
        model = models.Blueprint
        fields = (
            'title',
            'description',
            'url',
            'properties',
            'host_definitions',
        )

    def validate(self, attrs):
        # if the user failed to supply a properties list, then
        # we'll default to the empty list
        if attrs.get('properties', None) is None:
            attrs['properties'] = []

        # property names must be unique
        properties = attrs['properties']
        if properties:
            names = set([p.name for p in properties])
            if len(names) != len(properties):
                raise serializers.ValidationError({
                    'properties': ['Property names must be unique.']
                })
        return super(BlueprintSerializer, self).validate(attrs)
