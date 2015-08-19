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


import logging

from django.shortcuts import resolve_url
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import TemplateView

from stackdio.server import __version__

logger = logging.getLogger(__name__)


class StackdioView(TemplateView):

    def get_context_data(self, **kwargs):
        context = super(StackdioView, self).get_context_data(**kwargs)
        context['version'] = __version__
        return context

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            return super(StackdioView, self).get(request, *args, **kwargs)
        else:
            redirect_url = resolve_url('ui:login')
            if request.path != '/':
                redirect_url = '{0}?next={1}'.format(redirect_url, request.path)
            return HttpResponseRedirect(redirect_url)


class RootView(StackdioView):
    template_name = 'stackdio/home.html'


class AppMainView(TemplateView):
    template_name = 'stackdio/js/main.js'

    def __init__(self, **kwargs):
        super(AppMainView, self).__init__(**kwargs)
        self.viewmodel = None

    def get_context_data(self, **kwargs):
        context = super(AppMainView, self).get_context_data(**kwargs)
        context['viewmodel'] = self.viewmodel
        return context

    def get(self, request, *args, **kwargs):
        self.viewmodel = kwargs.get('vm')
        if self.viewmodel is None:
            return HttpResponse()
        return super(AppMainView, self).get(request, *args, **kwargs)


class PageView(StackdioView):
    viewmodel = None

    def __init__(self, **kwargs):
        super(PageView, self).__init__(**kwargs)
        assert self.viewmodel is not None, ('You must specify a viewmodel via the `viewmodel` '
                                            'attribute of your class.')

    def get_context_data(self, **kwargs):
        context = super(PageView, self).get_context_data(**kwargs)
        context['viewmodel'] = self.viewmodel
        return context


class UserProfileView(StackdioView):
    template_name = 'stackdio/user-profile.html'


class StackCreateView(PageView):
    template_name = 'stacks/stack-create.html'
    viewmodel = 'viewmodels/stack-create'


class StackListView(PageView):
    template_name = 'stacks/stack-list.html'
    viewmodel = 'viewmodels/stack-list'


class StackDetailView(PageView):
    template_name = 'stacks/stack-detail.html'
    viewmodel = 'viewmodels/stack-detail'

    def get_context_data(self, **kwargs):
        context = super(StackDetailView, self).get_context_data(**kwargs)
        context['stack_id'] = kwargs['pk']
        return context
