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

"""
Integration test for bareon allocation system.

Checks that high level abstraction works together
including the solver.
"""

import glob
import os

import six
import yaml

from bareon_dynamic_allocator.allocators import DynamicAllocator
from bareon_dynamic_allocator.tests import base

fixtures_path = os.path.join(os.path.dirname(__file__), 'fixtures', '*.yaml')


class TestGeneratorMeta(type):
    """Autogenerate tests from fixtures."""

    def __new__(mcs, name, bases, cls_dict):

        def gen_test(hw_info, dynamic_schema, expected, doc):
            def test(self):
                result = DynamicAllocator(
                    hw_info,
                    dynamic_schema).generate_static()
                self.assertEqual(expected, result)

            test.__doc__ = doc
            return test

        for f in glob.glob(fixtures_path):
            file_name = os.path.splitext(os.path.basename(f))[0]
            with open(f, 'r') as fd:
                data = yaml.load(fd)

                test_name = 'test_{0}'.format(file_name)
                cls_dict[test_name] = gen_test(
                    data['hw_info'],
                    data['dynamic_schema'],
                    data['expected'],
                    data['name'])

        return type.__new__(mcs, name, bases, cls_dict)


@six.add_metaclass(TestGeneratorMeta)
class TestAllocatorIntegration(base.TestCase):
    pass
