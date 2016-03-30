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

from bareon_allocator import errors
from bareon_allocator.objects import Space
from bareon_allocator.tests import base


class TestObjectsSpace(base.TestCase):

    def test_object_creation(self):
        space = Space(id=10,
                      min_size=1,
                      max_size=2,
                      type='lv',
                      best_with_disks=[1, 2, 3])
        self.assertEqual(space.id, 10)
        self.assertEqual(space.min_size, 1)
        self.assertEqual(space.max_size, 2)
        self.assertEqual(space.type, 'lv')
        self.assertEqual(space.best_with_disks, [1, 2, 3])
        self.assertEqual(space.weight, 1)
        self.assertEqual(space.none_order, False)

    def test_size_sets_min_and_max(self):
        space = Space(id=10, type='lv', size=15)
        self.assertEqual(space.min_size, 15)
        self.assertEqual(space.max_size, 15)

    def test_fail_if_no_type(self):
        self.assertRaises(errors.InvalidData, Space, id=11)
