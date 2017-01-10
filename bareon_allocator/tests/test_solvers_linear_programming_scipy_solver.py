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
from bareon_allocator.solvers.linear_program import LinearProgram
from bareon_allocator.solvers.linear_programming_scipy_solver \
    import LinearProgrammingScipySolver
from bareon_allocator.tests import base


class TestSolversLinearProgrammingScipySolver(base.TestCase):

    def test_solves_lp(self):
        # x = 1
        # y = 1
        # z + j >= 2
        # x + y + z + j <= 4
        lp = LinearProgram(
            equality_constraint_matrix=[[1, 0, 0, 0], [0, 1, 0, 0]],
            equality_constraint_vector=[1, 1],
            lower_constraint_matrix=[[0, 0, 1, 1]],
            lower_constraint_vector=[2],
            upper_constraint_matrix=[[1, 1, 1, 1]],
            upper_constraint_vector=[4],
            objective_function_coefficients=[0, 0, 0, 0],
            x_amount=4)

        solver = LinearProgrammingScipySolver(lp)
        self.assertEqual(
            solver.solve(),
            [1, 1, 2, 0])

    def test_raises_error(self):
        # 0 + 0 = 2
        lp = LinearProgram(
            equality_constraint_matrix=[[0, 0]],
            equality_constraint_vector=[1],
            objective_function_coefficients=[0, 0],
            x_amount=2)

        solver = LinearProgrammingScipySolver(lp)
        self.assertRaises(errors.NoSolutionFound, solver.solve)
