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


from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.dispatch import receiver

import model_utils.models

import logging
logger = logging.getLogger(__name__)


class UserSettings(models.Model):

    class Meta:
        verbose_name_plural = 'User settings'

    # which user the settings below
    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                related_name='settings')

    # public RSA key for the user
    public_key = models.TextField(blank=True)

    def __unicode__(self):
        return self.user.username

@receiver(models.signals.post_save, sender=get_user_model())
def user_post_save(sender, instance, **kwargs):
    '''
    Catch the post_save signal for all User objects and create a
    UserSettings objects if needed
    '''
    if 'created' in kwargs and kwargs['created'] == True:
        logger.debug('Creating UserSettings object for {0!r}'.format(instance))
        UserSettings.objects.create(user=instance)

