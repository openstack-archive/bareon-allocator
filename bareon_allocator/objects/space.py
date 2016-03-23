# -*- coding: utf-8 -*-

#    Copyright 2016 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from bareon_allocator.objects import BaseObject


class Space(BaseObject):

    properties = {
        'id': None,
        'min_size': 0,
        'max_size': None,
        'best_with_disks': set([]),
        'weight': 1
    }
    required = ['id', 'type']

    def __init__(self, **kwargs):
        super(Space, self).__init__(**kwargs)

        # Exact size should be repreneted as min_size and max_size
        if kwargs.get('size'):
            self.min_size = kwargs.get('size')
            self.max_size = kwargs.get('size')
