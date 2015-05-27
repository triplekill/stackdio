# -*- coding: utf-8 -*-

# Copyright 2014,  Digital Reasoning
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

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from guardian.shortcuts import assign_perm
from rest_framework import status
from rest_framework.test import APIClient

from api_v1.urls import urlpatterns
from .utils import get_urls


logger = logging.getLogger(__name__)


class StackdioTestCase(TestCase):
    """
    Base test case class for stackd.io.  Will add a client object, and create an admin and a
    regular user.  Will also create an 'everybody' group with permissions to view most of the
    endpoints.
    """
    GLOBAL_PERM_MODELS = (
        'cloud.%s_cloudprovidertype',
        'cloud.%s_cloudprovider',
        'cloud.%s_cloudprofile',
        'cloud.%s_snapshot',
        'cloud.%s_cloudregion',
        'cloud.%s_cloudzone',
        'cloud.%s_cloudinstancesize',
        'cloud.%s_securitygroup',
        'cloud.%s_globalorchestrationformulacomponent',
        'stacks.%s_stack',
        'stacks.%s_host',
        'volumes.%s_volume',
        'blueprints.%s_blueprint',
        'formulas.%s_formula',
    )

    def setUp(self):
        self.client = APIClient()
        user_model = get_user_model()
        self.admin = user_model.objects.create_superuser('test.admin',
                                                         'test.admin@digitalreasoning.com', '1234')
        self.user = user_model.objects.create_user('test.user', 'test.user@digitalreasoning.com',
                                                   '1234')

        # Create an everybody group
        everybody = Group.objects.create(name='everybody')
        # Give the necessary global permissions
        for perm in self.GLOBAL_PERM_MODELS:
            assign_perm(perm % 'view', everybody)

        # Put the users in the group
        self.admin.groups.add(everybody)
        self.user.groups.add(everybody)


class AuthenticationTestCase(StackdioTestCase):
    """
    Test all list endpoints to ensure they throw a permission denied when a user isn't logged in
    """

    # These don't allow get requests
    EXEMPT_ENDPOINTS = (
        '/api/settings/change_password/',
    )

    # These should be only visible by admins
    ADMIN_ONLY = (
        '/api/users/',
    )

    def setUp(self):
        super(AuthenticationTestCase, self).setUp()

        # Build up a list of all list endpoints

        # Start out with just the root endpoint
        self.list_endpoints = ['/api/']

        for url in list(get_urls(urlpatterns)):
            # Filter out the urls with format things in them
            if not url:
                continue
            if 'format' in url:
                continue
            if '(?P<' in url:
                continue

            self.list_endpoints.append('/api/' + url)

    def test_permission_denied(self):
        for url in self.list_endpoints:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_success_admin(self):
        self.client.login(username='test.admin', password='1234')

        for url in self.list_endpoints:
            response = self.client.get(url)
            expected = status.HTTP_200_OK
            if url in self.EXEMPT_ENDPOINTS:
                expected = status.HTTP_405_METHOD_NOT_ALLOWED

            self.assertEqual(response.status_code, expected, 'URL {0} failed'.format(url))

    def test_success_non_admin(self):
        self.client.login(username='test.user', password='1234')

        for url in self.list_endpoints:
            response = self.client.get(url)
            expected = status.HTTP_200_OK
            if url in self.EXEMPT_ENDPOINTS:
                expected = status.HTTP_405_METHOD_NOT_ALLOWED
            elif url in self.ADMIN_ONLY:
                expected = status.HTTP_403_FORBIDDEN

            self.assertEqual(response.status_code, expected,
                             'URL {0} failed.  Expected {1}, was {2}.'.format(url,
                                                                              expected,
                                                                              response.status_code))
