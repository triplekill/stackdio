# -*- coding: utf-8 -*-

# Copyright 2014,  Digital Reasoning
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

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework import generics
from rest_framework.response import Response

from stackdio.core.permissions import StackdioModelPermissions
from stackdio.core.viewsets import (
    StackdioModelUserPermissionsViewSet,
    StackdioModelGroupPermissionsViewSet,
    StackdioObjectUserPermissionsViewSet,
    StackdioObjectGroupPermissionsViewSet,
)
from . import filters, mixins, permissions, serializers


class UserListAPIView(generics.ListAPIView):
    queryset = get_user_model().objects.exclude(id=settings.ANONYMOUS_USER_ID).order_by('username')
    serializer_class = serializers.PublicUserSerializer
    lookup_field = 'username'
    filter_class = filters.UserFilter


class UserDetailAPIView(generics.RetrieveAPIView):
    queryset = get_user_model().objects.exclude(id=settings.ANONYMOUS_USER_ID)
    serializer_class = serializers.PublicUserSerializer
    lookup_field = 'username'


class UserGroupListAPIView(mixins.UserRelatedMixin, generics.ListAPIView):
    serializer_class = serializers.UserGroupSerializer
    lookup_field = 'username'

    def get_queryset(self):
        return self.get_user().groups.all()


class GroupListAPIView(generics.ListCreateAPIView):
    queryset = Group.objects.all()
    serializer_class = serializers.GroupSerializer
    permission_classes = (StackdioModelPermissions,)
    lookup_field = 'name'
    filter_class = filters.GroupFilter


class GroupDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Group.objects.all()
    serializer_class = serializers.GroupSerializer
    permission_classes = (permissions.GroupObjectPermissions,)
    lookup_field = 'name'


class GroupUserListAPIView(mixins.GroupRelatedMixin, generics.ListAPIView):
    serializer_class = serializers.GroupUserSerializer
    lookup_field = 'name'

    def get_queryset(self):
        return self.get_group().user_set.all()


class GroupActionAPIView(mixins.GroupRelatedMixin, generics.GenericAPIView):
    serializer_class = serializers.GroupActionSerializer

    def get(self, request, *args, **kwargs):
        ret = {
            'available_actions': self.serializer_class.available_actions
        }
        return Response(ret)

    def post(self, request, *args, **kwargs):
        group = self.get_group()

        serializer = self.get_serializer(group, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class GroupModelUserPermissionsViewSet(StackdioModelUserPermissionsViewSet):
    permission_classes = (permissions.GroupPermissionsModelPermissions,)
    model_permissions = ('create', 'admin')
    parent_lookup_field = 'name'
    model_cls = Group


class GroupModelGroupPermissionsViewSet(StackdioModelGroupPermissionsViewSet):
    permission_classes = (permissions.GroupPermissionsModelPermissions,)
    model_permissions = ('create', 'admin')
    parent_lookup_field = 'name'
    model_cls = Group


class GroupObjectUserPermissionsViewSet(mixins.GroupRelatedMixin,
                                        StackdioObjectUserPermissionsViewSet):
    permission_classes = (permissions.GroupPermissionsObjectPermissions,)
    object_permissions = ('update', 'delete', 'admin')
    parent_lookup_field = 'name'


class GroupObjectGroupPermissionsViewSet(mixins.GroupRelatedMixin,
                                         StackdioObjectGroupPermissionsViewSet):
    permission_classes = (permissions.GroupPermissionsObjectPermissions,)
    object_permissions = ('update', 'delete', 'admin')
    parent_lookup_field = 'name'


class CurrentUserDetailAPIView(generics.RetrieveUpdateAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = serializers.UserSerializer

    def get_object(self):
        return self.request.user


class ChangePasswordAPIView(generics.GenericAPIView):
    """
    API that handles changing your account password. Note that
    only POST requests are available on this endpoint. Below
    are the required parameters of the JSON object you will PUT.

    @current_password: Your current password.
    @new_password: Your new password you want to change to.
    """

    serializer_class = serializers.ChangePasswordSerializer

    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = self.get_serializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
