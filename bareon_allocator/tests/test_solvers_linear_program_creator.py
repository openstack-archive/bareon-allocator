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

import mock

from bareon_allocator.solvers import LinearProgramCreator
from bareon_allocator.tests import base


class TestSolversLinearProgramCreator(base.TestCase):

    def create_lp(self, spaces_info=[], disks_info=[]):
        dynamic_schema_mock = mock.MagicMock(spaces=[], disks=[])
        for s in spaces_info:
            dynamic_schema_mock.spaces.append(mock.MagicMock(**s))

        for d in disks_info:
            dynamic_schema_mock.disks.append(mock.MagicMock(**d))

        return LinearProgramCreator(dynamic_schema_mock).linear_program()

    def assert_lower_eq_exists(self, lp, eq, value):
        self.assert_eq_and_value(
            lp.lower_constraint_matrix,
            lp.lower_constraint_vector,
            eq,
            value)

    def assert_upper_eq_exists(self, lp, eq, value):
        self.assert_eq_and_value(
            lp.upper_constraint_matrix,
            lp.upper_constraint_vector,
            eq,
            value)

    def assert_eq_exists(self, lp, eq, value):
        self.assert_eq_and_value(
            lp.equality_constraint_matrix,
            lp.equality_constraint_vector,
            eq,
            value)

    def assert_eq_and_value(self, eq_list, eq_vector, expected_eq, value):
        eq = None
        i_eq = None
        for i, _eq in enumerate(eq_list):
            if _eq == expected_eq:
                eq = _eq
                i_eq = i
                break

        self.assertIsNotNone(eq, 'Cannot find equation')
        self.assertEqual(eq_vector[i_eq], value,
                         'Value of equation does not match to expected')

    def test_min_size_equations(self):
        lp = self.create_lp(
            spaces_info=[
                {'min_size': 10},
                {'min_size': 20},
                {'min_size': 0}],
            disks_info=[
                {'id': 'sda', 'size': 50},
                {'id': 'sda', 'size': 60}])
        self.assert_lower_eq_exists(lp, [1, 0, 0, 1, 0, 0], 10)
        self.assert_lower_eq_exists(lp, [0, 1, 0, 0, 1, 0], 20)
        self.assert_lower_eq_exists(lp, [0, 0, 1, 0, 0, 1], 0)

    def test_max_size_equations(self):
        lp = self.create_lp(
            spaces_info=[
                {'max_size': 10},
                {'max_size': 20},
                {'min_size': 0}],
            disks_info=[
                {'id': 'sda', 'size': 50},
                {'id': 'sda', 'size': 60}])
        self.assert_upper_eq_exists(lp, [1, 0, 0, 1, 0, 0], 10)
        self.assert_upper_eq_exists(lp, [0, 1, 0, 0, 1, 0], 20)

    def test_disk_size_equations(self):
        lp = self.create_lp(
            spaces_info=[
                {'max_size': 10},
                {'max_size': 20},
                {'min_size': 0}],
            disks_info=[
                {'id': 'sda', 'size': 50},
                {'id': 'sda', 'size': 60}])
        self.assert_upper_eq_exists(lp, [1, 1, 1, 0, 0, 0], 50)
        self.assert_upper_eq_exists(lp, [0, 0, 0, 1, 1, 1], 60)

    def test_weight_eq(self):
        lp = self.create_lp(
            spaces_info=[
                {'id': 'v1', 'min_size': 20, 'max_size': None,
                 'best_with_disks': [], 'weight': 10},
                {'id': 'v2', 'min_size': 20, 'max_size': None,
                 'best_with_disks': [], 'weight': 5},
                {'id': 'v3', 'min_size': 30, 'max_size': None,
                 'best_with_disks': ['sda'], 'weight': 1},
                {'id': 'v4', 'min_size': 30, 'max_size': None,
                 'best_with_disks': ['sda'], 'weight': 1}],
            disks_info=[
                {'id': 'sda', 'size': 100},
                {'id': 'sdb', 'size': 200},
                {'id': 'sdc', 'size': 300}])

        self.assert_eq_exists(
            lp,
            [0.1, -0.2, 0, 0,
             0.1, -0.2, 0, 0,
             0.1, -0.2, 0, 0],
            0)

        self.assert_eq_exists(
            lp,
            [0, 0, 1.0, -1.0,
             0, 0, 1.0, -1.0,
             0, 0, 1.0, -1.0],
            0)

    def test_objective_function_equation(self):
        lp = self.create_lp(
            spaces_info=[
                {'id': 'v0', 'min_size': 20, 'max_size': None,
                 'best_with_disks': [],
                 'weight': 10, 'none_order': False},
                {'id': 'v1', 'min_size': 20, 'max_size': None,
                 'best_with_disks': [],
                 'weight': 5, 'none_order': False},
                {'id': 'v2', 'min_size': 30, 'max_size': None,
                 'best_with_disks': ['sda'],
                 'weight': 1, 'none_order': False},
                {'id': 'v3', 'min_size': 30, 'max_size': None,
                 'best_with_disks': ['sda'],
                 'weight': 1, 'none_order': False}],
            disks_info=[
                {'id': 'sda', 'size': 100},
                {'id': 'sdb', 'size': 200},
                {'id': 'sdc', 'size': 300}])

        seq = [2, 4, 6, 9, 12, 16, 20, 25, 30, 36, 42, 49]
        reverse_seq = [-1.0 / s for s in seq]

        weight_indexes = [
            2,  # v2, sda
            3,  # v3, sda
            4,  # v0, sdb
            5,  # v1, sdb
            8,  # v0, sdc
            9]  # v1, sdc

        for idx in weight_indexes:
            # Substitute "set" coefficient
            reverse_seq[idx] -= 2

        self.assertEqual(
            lp.objective_function_coefficients,
            reverse_seq)
