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

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from stackdio.core.permissions import (
    StackdioObjectPermissions,
    StackdioPermissionsModelPermissions,
    StackdioPermissionsObjectPermissions,
)


class UserPermissionsModelPermissions(StackdioPermissionsModelPermissions):
    model_cls = get_user_model()


class GroupObjectPermissions(StackdioObjectPermissions):
    """
    Override the default permission namings
    """
    perms_map = {
        'GET': [],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['%(app_label)s.create_%(model_name)s'],
        'PUT': ['%(app_label)s.update_%(model_name)s'],
        'PATCH': ['%(app_label)s.update_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }


class GroupPermissionsModelPermissions(StackdioPermissionsModelPermissions):
    model_cls = Group


class GroupPermissionsObjectPermissions(StackdioPermissionsObjectPermissions):
    parent_model_cls = Group
