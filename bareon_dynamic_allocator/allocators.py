#    Copyright 2015 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See then
#    License for the specific language governing permissions and limitations
#    under the License.

import six

from scipy.optimize import linprog
from scipy.ndimage.interpolation import shift

import numpy as np


def shift(arr, steps, val=0):
    res_arr = np.roll(arr, steps)
    np.put(res_arr, range(steps), val)

    return res_arr


class Disk(object):

    def __init__(self, **kwargs):
        for k, v in six.iteritems(kwargs):
            setattr(self, k, v)


class Space(object):

    def __init__(self, **kwargs):
        for k, v in six.iteritems(kwargs):
            setattr(self, k, v)


class DynamicAllocator(object):

    def __init__(self, hw_info, schema):
        self.disks = [Disk(**disk) for disk in  hw_info['disks']]
        self.spaces = [Space(**space) for space in schema]

        # Add fake volume Unallocated, in order to be able
        # to have only volumes with minimal size, without
        # additional space allocation
        self.lp = DynamicAllocationLinearProgram(self.disks, self.spaces)

    def generate_static(self):
        sizes = self.lp.solve()

        return sizes


class DynamicAllocationLinearProgram(object):
    """Use Linear Programming method [0] (the method itself has nothing to do
    with computer-programming) in order to formulate and solve the problem
    of spaces allocation on disks, with the best outcome.

    In this implementation scipy is being used since it already implements
    simplex algorithm to find the best feasible solution.

    [0] https://en.wikipedia.org/wiki/Linear_programming
    [1] http://docs.scipy.org/doc/scipy-0.16.0/reference/generated
                             /scipy.optimize.linprog.html
    [2] https://en.wikipedia.org/wiki/Simplex_algorithm
    """

    def __init__(self, disks, spaces):
        # Coefficients of the linear objective minimization function.
        # During iteration over vertexes the function is used to identify
        # if current solution (vertex) satisfies the equation more, than
        # previous one.
        # Example of equation: c[0]*x1 + c[1]*x2
        self.objective_function_coefficients = []

        # A matrix which, gives the values of the equality constraints at x,
        # when multipled by x.
        self.equality_constraint_matrix = []

        # An array of values representing right side of equation,
        # left side is represented by row of `equality_constraint_matrix`
        # matrix
        self.equality_constraint_vector = np.array([])

        # Specify boundaries of each x in the next format (min, max). Use
        # None for one of min or max when there is no bound.
        self.bounds = np.array([])

        self._initialize_equation(disks, spaces)

    def solve(self):
        solution = linprog(
            self.objective_function_coefficients,
            A_eq=self.equality_constraint_matrix,
            b_eq=self.equality_constraint_vector,
            bounds=self.bounds,
            options={"disp": True})

        return solution.x

    def _initialize_equation(self, disks, spaces):
        for d in disks:
            # Initialize constraints, each row in the matrix should
            # be equal to size of the disk
            self.equality_constraint_vector = np.append(self.equality_constraint_vector, d.size)

        # Initialize the matrix
        # In case of 2 spaces and 3 disks the result should be:
        # [[1, 1, 0, 0, 0, 0],
        #  [0, 0, 1, 1, 0, 0],
        #  [0, 0, 0, 0, 1, 1]]
        #
        # Explanation of the first row
        # [1, - x1 multiplier, size of space 1 on the first disk
        #  1, - x2 multiplier, size of space 2 on the first disk
        #  0, - x3 multiplier, size of space 1 on 2nd disk, 0 for the first
        #  0, - x4 multiplier, size of space 2 on 2nd disk, 0 for the first
        #  0, - x5 multiplier, size of space 1 on 3rd disk, 0 for the first
        #  0] - x6 multiplier, size of space 2 on 3rd disk, 0 for the first

        # For each space x (size of the space) is represented
        # for each disk as separate variable, so for each
        # disk we have len(spaces) * len(disks) sizes
        equality_matrix_row = np.zeros(len(spaces) * len(disks))
        self._init_objective_function_coefficient(len(spaces) * len(disks))

        # Set first len(spaces) elements to 1
        equality_matrix_row = shift(equality_matrix_row, len(spaces), val=1)

        for _ in range(len(disks)):
            self.equality_constraint_matrix.append(equality_matrix_row)
            equality_matrix_row = shift(equality_matrix_row, len(spaces), val=0)

    def _add_disk(self):
        pass

    def _add_space(self):
        pass

    def _add_objective_function_coefficient(self):
        # By default the algorithm tries to minimize the solution
        # we should invert sign, in order to make it as a maximization
        # function, we want disks to be maximally allocated.
        # Coefficient for space per disk is 1, because all spaces
        # are equal and should not be adjusted.
        self.objective_function_coefficients.append(-1)

    def _init_objective_function_coefficient(self, size):
        self.objective_function_coefficients = [-1] * size

    def _add_bound(self, min_, max_):
        np.append(self.bounds, (min_, max_))
