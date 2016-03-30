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

from bareon_allocator.solvers import LinearProgram
from bareon_allocator.tests import base


class TestSolversLinearProgram(base.TestCase):

    def setUp(self):
        super(TestSolversLinearProgram, self).setUp()
        self.lp = LinearProgram(
            x_amount=3,
            objective_function_coefficients=[1, 0, 0],

            equality_constraint_matrix=[[1, 2, 3], [4, 5, 6]],
            lower_constraint_matrix=[[7, 8, 9], [10, 11, 12]],
            upper_constraint_matrix=[[13, 14, 15], [16, 17, 18]],

            equality_constraint_vector=[1, 2, 3],
            lower_constraint_vector=[3, 4, 5],
            upper_constraint_vector=[6, 7, 8])

    def test_values_are_set(self):
        self.assertEqual(self.lp.x_amount, 3)
        self.assertEqual(
            self.lp.objective_function_coefficients,
            [1, 0, 0])

        self.assertEqual(
            self.lp.equality_constraint_matrix,
            [[1, 2, 3], [4, 5, 6]])
        self.assertEqual(
            self.lp.lower_constraint_matrix,
            [[7, 8, 9], [10, 11, 12]])
        self.assertEqual(
            self.lp.upper_constraint_matrix,
            [[13, 14, 15], [16, 17, 18]])

        self.assertEqual(
            self.lp.equality_constraint_vector,
            [1, 2, 3])
        self.assertEqual(
            self.lp.lower_constraint_vector,
            [3, 4, 5])
        self.assertEqual(
            self.lp.upper_constraint_vector,
            [6, 7, 8])

    def test_default_values_are_set(self):
        self.assertEqual(self.lp.lp_type, self.lp.LP_TYPE_LP)
        self.assertEqual(self.lp.objective_function_optimization_type,
                         self.lp.MAXIMIZE)
        self.assertEqual(self.lp.bounds, [(0, None), (0, None), (0, None)])
