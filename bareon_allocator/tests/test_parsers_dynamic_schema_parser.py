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


from bareon_allocator.parsers import DynamicSchemaParser
from bareon_allocator.tests import base


class TestParsersDynamicSchemaParser(base.TestCase):

    def setUp(self):
        super(TestParsersDynamicSchemaParser, self).setUp()
        hw_info = {
            'disks': [
                {'id': 'sda', 'size': 100},
                {'id': 'sdb', 'size': 42},
                {'id': 'sdc', 'size': 42}]}
        schema = [
            {'id': 'lv1',
             'type': 'lv',
             'max_size': 1},
            {'id': 'lv2',
             'type': 'lv',
             'max_size': 1,
             'best_with_disks': 'yaql=$.disks.where($.size=42)'},
            {'id': 'vg1',
             'type': 'vg'}]
        self.dynamic_schema_parser = DynamicSchemaParser(hw_info, schema)

    def test_unallocated_is_added(self):
        unallocated = filter(lambda s: s.id == 'unallocated',
                             self.dynamic_schema_parser.spaces)

        self.assertEqual(len(unallocated), 1)
        self.assertEqual(unallocated[0].type, 'unallocated')
        self.assertEqual(unallocated[0].none_order, True)
        self.assertEqual(unallocated[0].weight, 0)

    def test_aggregation_spaces_are_not_in_the_list(self):
        spaces = filter(lambda d: d.type == 'vg',
                        self.dynamic_schema_parser.spaces)
        self.assertEqual(len(spaces), 0)

    def test_sets_best_with_disks_ids(self):
        spaces = filter(lambda s: s.id == 'lv2',
                        self.dynamic_schema_parser.spaces)

        self.assertEqual(len(spaces), 1)
        self.assertEqual(spaces[0].best_with_disks, {'sdb', 'sdc'})
