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

from scipy.optimize import linprog

from bareon_allocator import errors
from bareon_allocator.solvers import BaseSolver
from bareon_allocator.solvers import utils


class LinearProgrammingScipySolver(BaseSolver):
    """Linear programming allocator.

    Use Linear Programming method [0] (the method itself has nothing to do
    with computer-programming) in order to formulate and solve the problem
    of spaces allocation on disks, with the best outcome.

    In this implementation scipy is being used since it already implements
    simplex algorithm to find the best feasible solution.

    [0] https://en.wikipedia.org/wiki/Linear_programming
    [1] http://docs.scipy.org/doc/scipy-0.16.0/reference/generated
                             /scipy.optimize.linprog.html
    [2] https://en.wikipedia.org/wiki/Simplex_algorithm
    """

    def solve(self):
        """Solves linear program.

        :return: solution vector
        """
        lp_solution = linprog(
            self.linear_program.objective_function_coefficients,
            A_eq=self.linear_program.equality_constraint_matrix or None,
            b_eq=self.linear_program.equality_constraint_vector or None,
            A_ub=self._make_upper_constraint_matrix() or None,
            b_ub=self._make_upper_constraint_vector() or None,
            bounds=self.linear_program.bounds,
            options={"disp": False})

        self._check_errors(lp_solution)

        # Naive implementation of getting integer result
        # from a linear programming algorithm, MIP
        # (mixed integer programming) should be considered
        # instead, but it may have a lot of problems (solution
        # of such equations is NP-hard in some cases),
        # for our practical purposes it's enough to round
        # the number down, in this case we may get `n` megabytes
        # unallocated, where n is len(spaces) * len(disks)
        solution_vector = utils.round_vector_down(lp_solution.x)

        return solution_vector

    def _check_errors(self, solution):
        """Checks if solution is not found.

        :param solution: solution object from scipy
        :raises: errors.NoSolutionFound if solution is not found
        """
        if not solution.success:
            raise errors.NoSolutionFound(
                'Allocation is not possible '
                'with specified constraints: {0}'.format(solution.message))

    def _make_upper_constraint_matrix(self):
        """Merges lower constraint matrix into upper."""
        upper_constraint_matrix = []
        upper_constraint_matrix.extend(
            self.linear_program.upper_constraint_matrix)
        if self.linear_program.lower_constraint_matrix:
            # Swap sign for lower constraint matrix in order to make it
            # upper bound instead of lower bound
            upper_constraint_matrix.extend(
                [[-i for i in row] for row in
                 self.linear_program.lower_constraint_matrix])

        return upper_constraint_matrix

    def _make_upper_constraint_vector(self):
        """Merges lower constraint vector into upper."""
        upper_constraint_vector = []
        upper_constraint_vector.extend(
            self.linear_program.upper_constraint_vector)

        if self.linear_program.lower_constraint_vector:
            # Swap sign for items in the vector to make it upper bound
            # instead of lower bound
            upper_constraint_vector.extend(
                [-i for i in self.linear_program.lower_constraint_vector])

        return upper_constraint_vector
