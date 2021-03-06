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


import logging

from django.db.models import URLField
from rest_framework import serializers
from six.moves.urllib_parse import urlsplit, urlunsplit  # pylint: disable=import-error

from stackdio.core.fields import PasswordField
from stackdio.core.mixins import CreateOnlyFieldsMixin
from stackdio.core.serializers import StackdioHyperlinkedModelSerializer
from stackdio.core.utils import recursively_sort_dict
from . import models, tasks, validators

logger = logging.getLogger(__name__)


class FormulaSerializer(CreateOnlyFieldsMixin, StackdioHyperlinkedModelSerializer):
    # Non-model fields
    git_password = PasswordField(write_only=True, required=False,
                                 allow_blank=True, label='Git Password')

    default_version = serializers.ReadOnlyField()

    # Link fields
    properties = serializers.HyperlinkedIdentityField(
        view_name='api:formulas:formula-properties')
    components = serializers.HyperlinkedIdentityField(
        view_name='api:formulas:formula-component-list')
    valid_versions = serializers.HyperlinkedIdentityField(
        view_name='api:formulas:formula-valid-version-list')
    action = serializers.HyperlinkedIdentityField(
        view_name='api:formulas:formula-action')
    user_permissions = serializers.HyperlinkedIdentityField(
        view_name='api:formulas:formula-object-user-permissions-list')
    group_permissions = serializers.HyperlinkedIdentityField(
        view_name='api:formulas:formula-object-group-permissions-list')

    class Meta:
        model = models.Formula
        fields = (
            'id',
            'url',
            'title',
            'description',
            'uri',
            'private_git_repo',
            'git_username',
            'git_password',
            'access_token',
            'default_version',
            'root_path',
            'created',
            'modified',
            'status',
            'status_detail',
            'properties',
            'components',
            'valid_versions',
            'action',
            'user_permissions',
            'group_permissions',
        )

        read_only_fields = (
            'title',
            'description',
            'private_git_repo',
            'root_path',
            'status',
            'status_detail',
        )

        create_only_fields = (
            'uri',
            'git_password',
        )

        extra_kwargs = {
            'access_token': {'default': serializers.CreateOnlyDefault(False)},
        }

    # Add in our custom URL field
    serializer_field_mapping = serializers.ModelSerializer.serializer_field_mapping
    serializer_field_mapping[URLField] = validators.FormulaURLField

    def validate(self, attrs):
        git_username = attrs.get('git_username')

        errors = {}

        if git_username and not self.instance:
            # We only need validation if a non-empty username is provided
            # We only care about this if we're importing
            access_token = attrs.get('access_token')
            git_password = attrs.get('git_password')

            if not access_token and not git_password:
                err_msg = 'Your git password is required if you\'re not using an access token.'
                errors.setdefault('access_token', []).append(err_msg)
                errors.setdefault('git_password', []).append(err_msg)

            if access_token and git_password:
                err_msg = 'If you are using an access_token, you may not provide a password.'
                errors.setdefault('access_token', []).append(err_msg)
                errors.setdefault('git_password', []).append(err_msg)

        if self.instance:
            uri = attrs.get('uri') if 'uri' in attrs else self.instance.uri
        else:
            uri = attrs['uri']

        # Remove the git username from the uri if it's a private formula
        if git_username:
            parse_res = urlsplit(uri)
            if '@' in parse_res.netloc:
                new_netloc = parse_res.netloc.split('@')[-1]
                attrs['uri'] = urlunsplit((
                    parse_res.scheme,
                    new_netloc,
                    parse_res.path,
                    parse_res.query,
                    parse_res.fragment,
                ))

        if errors:
            raise serializers.ValidationError(errors)

        return attrs


class FormulaPropertiesSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    def to_representation(self, obj):
        ret = {}
        if obj is not None:
            # Make it work two different ways.. ooooh
            if isinstance(obj, models.Formula):
                ret = obj.properties
            else:
                ret = obj
        return recursively_sort_dict(ret)

    def to_internal_value(self, data):
        return data


class FormulaActionSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    available_actions = ('update',)

    action = serializers.ChoiceField(available_actions, write_only=True)
    git_password = PasswordField(write_only=True, required=False,
                                 allow_blank=True, label='Git Password')

    def validate(self, attrs):
        formula = self.instance

        git_password = attrs.get('git_password')
        if formula.private_git_repo and not formula.access_token:
            if not git_password:
                raise serializers.ValidationError({
                    'git_password': ['This is a required field on private formulas.']
                })

        return attrs

    def to_representation(self, instance):
        """
        We just want to return a serialized formula object here.  Returning an object with
        the action in it just doesn't make much sense.
        """
        return FormulaSerializer(
            instance,
            context=self.context
        ).to_representation(instance)

    def do_update(self):
        formula = self.instance
        git_password = self.validated_data.get('git_password', '')
        logger.debug(type(git_password))
        formula.set_status(
            models.Formula.IMPORTING,
            'Importing formula...this could take a while.'
        )
        tasks.update_formula.si(formula.id, git_password, formula.default_version).apply_async()

    def save(self, **kwargs):
        action = self.validated_data['action']

        formula_actions = {
            'update': self.do_update
        }

        formula_actions[action]()

        return self.instance


class FormulaVersionSerializer(serializers.ModelSerializer):
    formula = serializers.SlugRelatedField(slug_field='uri', queryset=models.Formula.objects.all())

    class Meta:
        model = models.FormulaVersion
        fields = (
            'formula',
            'version',
        )

        extra_kwargs = {
            'version': {'allow_null': True},
        }

    def validate(self, attrs):
        formula = attrs['formula']
        version = attrs.get('version')

        if version is None:
            # If it's None, this version should be deleted, so no need to do any further checks
            return attrs

        # Verify that the version is either a branch, tag, or commit hash
        if version not in formula.get_valid_versions():
            err_msg = '{0} cannot be found to be a branch, tag, or commit hash'.format(version)
            raise serializers.ValidationError({
                'version': [err_msg]
            })

        return attrs

    def create(self, validated_data):
        # Somewhat of a hack, but if the object already exists, we want to update the current one
        content_obj = validated_data['content_object']
        formula = validated_data['formula']
        try:
            version = content_obj.formula_versions.get(formula=formula)
            # Provide a way to remove a formula version (set it to none)
            if validated_data['version'] is None:
                version.delete()
                return version

            # Otherwise update it
            return self.update(version, validated_data)
        except models.FormulaVersion.DoesNotExist:
            pass

        if validated_data['version'] is None:
            raise serializers.ValidationError({
                'version': ['This field may not be null or blank.']
            })

        return super(FormulaVersionSerializer, self).create(validated_data)


class FormulaComponentSerializer(serializers.HyperlinkedModelSerializer):
    # Possibly required
    formula = serializers.SlugRelatedField(slug_field='uri',
                                           queryset=models.Formula.objects.all(), required=False)

    class Meta:
        model = models.FormulaComponent
        fields = (
            'formula',
            'title',
            'description',
            'sls_path',
            'order',
        )

        extra_kwargs = {
            'order': {'min_value': 0, 'default': serializers.CreateOnlyDefault(0)}
        }

    def validate(self, attrs):
        formula = attrs.get('formula', None)
        sls_path = attrs['sls_path']
        attrs['validated'] = False

        # Grab the formula versions out of the content object
        content_object = self.context.get('content_object')
        formula_versions = content_object.formula_versions.all() if content_object else ()

        if formula is None:
            # Do some validation if the formula is done
            all_components = models.Formula.all_components(formula_versions)

            if sls_path not in all_components:
                raise serializers.ValidationError({
                    'sls_path': ['sls_path `{0}` does not exist.'.format(sls_path)]
                })

            # This means the component exists.  We'll check to make sure it doesn't
            # span multiple formulas.
            sls_formulas = all_components[sls_path]
            if len(sls_formulas) > 1:
                err_msg = 'sls_path `{0}` is contained in multiple formulas.  Please specify one.'
                raise serializers.ValidationError({
                    'sls_path': [err_msg.format(sls_path)]
                })

            # Be sure to throw the formula in!
            attrs['formula'] = sls_formulas[0]
            attrs['validated'] = True
        else:
            # If they provided a formula, validate the sls_path is in that formula
            validators.validate_formula_component(attrs, formula_versions)
            attrs['validated'] = True

        return attrs

    def save(self, **kwargs):
        # Be sure that validated doesn't end up in the final validated data
        self.validated_data.pop('validated', None)
        return super(FormulaComponentSerializer, self).save(**kwargs)
