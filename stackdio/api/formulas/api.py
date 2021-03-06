# -*- coding: utf-8 -*-

# Copyright 2016,  Digital Reasoning
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


import logging
from collections import OrderedDict

from guardian.shortcuts import assign_perm
from rest_framework import generics
from rest_framework.filters import DjangoFilterBackend, DjangoObjectPermissionsFilter
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from stackdio.core.permissions import StackdioModelPermissions, StackdioObjectPermissions
from stackdio.core.viewsets import (
    StackdioModelUserPermissionsViewSet,
    StackdioModelGroupPermissionsViewSet,
    StackdioObjectUserPermissionsViewSet,
    StackdioObjectGroupPermissionsViewSet,
)
from stackdio.api.blueprints.models import Blueprint
from . import permissions, mixins, models, filters, serializers

logger = logging.getLogger(__name__)


class FormulaListAPIView(generics.ListCreateAPIView):
    """
    Displays a list of all formulas visible to you.
    You may import a formula here also by providing a URI to a git repository containing a valid
    SPECFILE at the root of the repo.  You may optionally provide a git_username and git_password
    if your repository requires authentication.
    """
    queryset = models.Formula.objects.all()
    serializer_class = serializers.FormulaSerializer
    permission_classes = (StackdioModelPermissions,)
    filter_backends = (DjangoObjectPermissionsFilter, DjangoFilterBackend)
    filter_class = filters.FormulaFilter

    def perform_create(self, serializer):
        formula = serializer.save()

        # Assign permissions so the user that just created the formula can operate on it
        for perm in models.Formula.object_permissions:
            assign_perm('formulas.%s_formula' % perm, self.request.user, formula)


class FormulaDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Formula.objects.all()
    serializer_class = serializers.FormulaSerializer
    permission_classes = (StackdioObjectPermissions,)

    def perform_destroy(self, instance):
        # Check for Blueprints depending on this formula
        # This should catch MOST errors
        blueprints = Blueprint.objects.filter(
            host_definitions__formula_components__formula=instance
        ).distinct()

        if blueprints:
            raise ValidationError({
                'detail': ['One or more blueprints are making use of this formula.'],
                'blueprints': [b.title for b in blueprints],
            })

        instance.delete()


class FormulaPropertiesAPIView(mixins.FormulaRelatedMixin, generics.RetrieveAPIView):
    queryset = models.Formula.objects.all()
    serializer_class = serializers.FormulaPropertiesSerializer


class FormulaComponentListAPIView(mixins.FormulaRelatedMixin, generics.ListAPIView):
    """
    Returns a list of formula components available for this formula.  If the `version`
    query parameter is specified, it will show a list for that version.
    """
    def list(self, request, *args, **kwargs):
        formula = self.get_formula()

        # determine if a version was specified
        version = request.query_params.get('version')

        if version in formula.get_valid_versions():
            components = formula.components_for_version(version)
        else:
            version = formula.default_version
            if formula.repo is None:
                components = {}
            else:
                formula.repo.git.checkout(version)
                components = formula.components

        components = components.values()

        data = OrderedDict((
            ('count', len(components)),
            ('version', version),
            ('results', components),
        ))

        return Response(data)


class FormulaValidVersionListAPIView(mixins.FormulaRelatedMixin, generics.ListAPIView):
    """
    Returns a list of valid versions for this formula.
    """
    def list(self, request, *args, **kwargs):
        formula = self.get_formula()

        versions = formula.get_valid_versions()

        data = OrderedDict((
            ('count', len(versions)),
            ('results', versions),
        ))

        return Response(data)


class FormulaActionAPIView(mixins.FormulaRelatedMixin, generics.GenericAPIView):
    serializer_class = serializers.FormulaActionSerializer

    def get(self, request, *args, **kwargs):
        ret = {
            'available_actions': self.serializer_class.available_actions
        }
        return Response(ret)

    def post(self, request, *args, **kwargs):
        formula = self.get_formula()

        serializer = self.get_serializer(formula, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class FormulaModelUserPermissionsViewSet(StackdioModelUserPermissionsViewSet):
    permission_classes = (permissions.FormulaPermissionsModelPermissions,)
    model_cls = models.Formula


class FormulaModelGroupPermissionsViewSet(StackdioModelGroupPermissionsViewSet):
    permission_classes = (permissions.FormulaPermissionsModelPermissions,)
    model_cls = models.Formula


class FormulaObjectUserPermissionsViewSet(mixins.FormulaRelatedMixin,
                                          StackdioObjectUserPermissionsViewSet):
    permission_classes = (permissions.FormulaPermissionsObjectPermissions,)


class FormulaObjectGroupPermissionsViewSet(mixins.FormulaRelatedMixin,
                                           StackdioObjectGroupPermissionsViewSet):
    permission_classes = (permissions.FormulaPermissionsObjectPermissions,)
