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

import itertools
import math

import six
import numpy as np
from termcolor import colored
from oslo_log import log
from scipy.optimize import linprog
from scipy.ndimage.interpolation import shift

from bareon_dynamic_allocator import errors
from bareon_dynamic_allocator.parser import Parser
from bareon_dynamic_allocator.sequences import CrossSumInequalitySequence


LOG = log.getLogger(__name__)


def shift(arr, steps, val=0):
    res_arr = np.roll(arr, steps)
    np.put(res_arr, range(steps), val)

    return res_arr


def grouper(iterable, n, fillvalue=None):
    """Collect data into fixed-length chunks or blocks
    Source: https://docs.python.org/2/library/itertools.html#recipes
    """
    args = [iter(iterable)] * n
    return itertools.izip_longest(fillvalue=fillvalue, *args)


def format_x_vector(coefficients, num=0):
    return '\n' + '\n'.join(
        [' + '.join(group)
         for group in grouper(
                 ['({0:+.5f} * x{1})'.format(c, i)
                  for i, c in enumerate(coefficients)], num)]) + '\n'


def format_equation(matrix, vector, row_len):
    equation = []

    for idx, m_row in enumerate(matrix):
        line = []

        for i, c in enumerate(m_row):
            x = '({0:+} * x{1})'.format(c, i)
            if c > 0:
                colored_x = colored(x, 'green')
            elif c < 0:
                colored_x = colored(x, 'red')
            else:
                colored_x = colored(x, 'white')

            line.append(colored_x)

        line = ' + '.join(line) + ' = {0}'.format(vector[idx])

        equation.append(line)

    return '\n'.join(equation)



class Disk(object):

    def __init__(self, **kwargs):
        for k, v in six.iteritems(kwargs):
            setattr(self, k, v)


class Space(object):

    def __init__(self, **kwargs):
        for k, v in six.iteritems(kwargs):
            setattr(self, k, v)

        # If no min_size specified set it to 0
        if not kwargs.get('min_size'):
            self.min_size = 0

        # Exact size can be repreneted as min_size and max_size
        if kwargs.get('size'):
            self.min_size = kwargs.get('size')
            self.max_size = kwargs.get('size')

        if not kwargs.get('best_with_disks'):
            self.best_with_disks = set([])

    def __repr__(self):
        return str(self.__dict__)


class DynamicAllocator(object):

    def __init__(self, hw_info, schema):
        LOG.debug('Hardware information: \n%s', hw_info)
        LOG.debug('Spaces schema: \n%s', schema)
        self.hw_info = hw_info
        self.raw_disks = hw_info['disks']
        self.disks = [Disk(**disk) for disk in self.raw_disks]
        rendered_spaces = self.convert_disks_to_indexes(
            Parser(schema, hw_info).parse(),
            hw_info)
        LOG.debug('Rendered spaces schema: \n%s', rendered_spaces)
        self.spaces = [Space(**space) for space in rendered_spaces if space['type'] != 'vg']

        # Unallocated is required in order to be able to specify
        # spaces with only minimal
        self.spaces.append(Space(
            id='unallocated',
            type='unallocated',
            none_order=True,
            weight=0))

        # Add fake volume Unallocated, in order to be able
        # to have only volumes with minimal size, without
        # additional space allocation
        self.solver = DynamicAllocationLinearProgram(self.disks, self.spaces)

    def generate_static(self):
        sizes = self.solver.solve()

        return sizes

    def convert_disks_to_indexes(self, spaces, hw_info):
        """Convert disks which are specified in `best_with_disks`
        to a list of indexes in `disks` list.
        """
        for i, space in enumerate(spaces):

            if space.get('best_with_disks'):
                disks_idx = set()
                for disk in space['best_with_disks']:
                    try:
                        disks_idx.add(self.raw_disks.index(disk))
                    except ValueError as exc:
                        LOG.warn('Warning: %s', exc)

                spaces[i]['best_with_disks'] = disks_idx

        return spaces


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

    weight_set_mapping = [
        # Don't use minimal size, in this case
        # we will get a weight for the space which
        # in combination with space which has max_size
        # so there will be unallocated space
        # ['min_size', 'best_with_disks'],
        # ['max_size', 'best_with_disks'],
        ['min_size', 'max_size', 'best_with_disks']]

    def __init__(self, disks, spaces):
        self.disks = disks
        self.spaces = spaces
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

        self.upper_bound_constraint_matrix = []
        self.upper_bound_constraint_vector = []
        self.lower_bound_constraint_matrix = []
        self.lower_bound_constraint_vector = []

        # Specify boundaries of each x in the next format (min, max). Use
        # None for one of min or max when there is no bound.
        self.bounds = np.array([])

        # For each space, xn (size of the space) is represented
        # for each disk as separate variable, so for each
        # disk we have len(spaces) * len(disks) sizes
        self.x_amount = len(self.disks) * len(self.spaces)

        # TODO: has to be refactored
        # Here we store indexes for bounds and equation
        # matrix, in order to be able to change it on
        # refresh
        self.weight_equation_indexes = []

        self._set_spaces_sets_by(self.weight_set_mapping[0])
        self._init_equation(self.disks, self.spaces)
        self._init_objective_function_coefficient()
        self._init_min_max()
        self._refresh_weight()

    def solve(self):
        upper_bound_matrix = self._make_upper_bound_constraint_matrix() or None
        upper_bound_vector = self._make_upper_bound_constraint_vector() or None

        LOG.debug('Objective function coefficients human-readable:\n%s\n',
                  format_x_vector(self.objective_function_coefficients, len(self.spaces)))

        LOG.debug('Equality equation:\n%s\n',
                  format_equation(
                      self.equality_constraint_matrix,
                      self.equality_constraint_vector,
                      len(self.spaces)))
        LOG.debug('Inequality equation:\n%s\n',
                  format_equation(
                      upper_bound_matrix,
                      upper_bound_vector,
                      len(self.spaces)))

        for weight_for_sets in self.weight_set_mapping:
            LOG.debug('Parameters for spaces set formation: %s', weight_for_sets)
            self._set_spaces_sets_by(weight_for_sets)
            solution = linprog(
                self.objective_function_coefficients,
                A_eq=self.equality_constraint_matrix,
                b_eq=self.equality_constraint_vector,
                A_ub=upper_bound_matrix,
                b_ub=upper_bound_vector,
                bounds=self.bounds,
                options={"disp": False})

            # If solution is found we can finish attempts to find
            # the best solution
            if not solution.success:
                break

        LOG.debug("Solution: %s", solution)
        self._check_errors(solution)
        # Naive implementation of getting integer result
        # from a linear programming algorithm, MIP
        # (mixed integer programming) should be considered
        # instead, but it may have a lot of problems (solution
        # of such equations is NP-hard in some cases),
        # for our practical purposes it's enough to round
        # the number down, in this case we may get `n` megabytes
        # unallocated, where n is len(spaces) * len(disks)
        solution_vector = self._round_down(solution.x)

        return self._convert_solution(solution_vector)

    def _check_errors(self, solution):
        if not solution.success:
            raise errors.NoSolutionFound(
                'Allocation is not possible '
                'with specified constraints: {0}'.format(solution.message))

    def _round_down(self, vector):
        return [int(math.floor(f)) for f in vector]

    def _init_min_max(self):
        """Create min and max constraints for each space.

        In case of 2 disks and 2 spaces

        For first space min_size >= 10 and max_size <= 20
        1 * x1 + 0 * x2 + 1 * x3 + 0 * x4 >= 10
        1 * x1 + 0 * x2 + 1 * x3 + 0 * x4 <= 20

        For second space min_size >= 15 and max_size <= 30
        0 * x1 + 1 * x2 + 0 * x3 + 1 * x4 >= 15
        0 * x1 + 1 * x2 + 0 * x3 + 1 * x4 <= 30
        """
        for space_idx, space in enumerate(self.spaces):
            row = self._make_matrix_row()
            max_size = getattr(space, 'max_size', None)
            min_size = getattr(space, 'min_size', None)

            for disk_idx in range(len(self.disks)):
                row[disk_idx * len(self.spaces) + space_idx] = 1

            if min_size is not None:
                self.lower_bound_constraint_matrix.append(row)
                self.lower_bound_constraint_vector.append(min_size)

            if max_size is not None:
                self.upper_bound_constraint_matrix.append(row)
                self.upper_bound_constraint_vector.append(max_size)

    def _get_spaces_sets_by(self, criteria):
        return [i[1] for i in self._get_sets_by(criteria)]

    def _get_sets_by(self, criteria):
        def get_values(space):
            return [getattr(space, c, None) for c in criteria]

        grouped_spaces = itertools.groupby(
                sorted(self.spaces, key=get_values),
                key=get_values)

        return [(k, list(v)) for k, v in grouped_spaces]

    def _set_spaces_sets_by(self, criteria):
        self.weight_spaces_sets = self._get_spaces_sets_by(criteria)

    def _refresh_weight(self):
        """Create weight constraints for spaces which have same
        max constraint or for those which don't have it at all.

        Lets say, second's space is equal to max of the third and fourth,
        we will have next equation:
        0 * x1 + (1 / weight) * x2 + (-1 / weight) * x3 +
        0 * x4 + (1 / weight) * x5 + (-1 / weight) * x6 = 0
        """
        DEFAULT_WEIGHT = 1
        # Clean constraint matrix and vector from previous values
        for idx in sorted(self.weight_equation_indexes, reverse=True):
            del self.equality_constraint_matrix[idx]
            del self.equality_constraint_vector[idx]
        self.weight_equation_indexes = []

        for spaces_set in self.weight_spaces_sets:
            # Don't set weight if there is less than one space in the set
            if len(spaces_set) < 2:
                continue

            first_weight = getattr(spaces_set[0], 'weight', DEFAULT_WEIGHT)
            first_space_idx = self.spaces.index(spaces_set[0])
            for space in spaces_set[1:]:
                row = self._make_matrix_row()
                weight = getattr(space, 'weight', DEFAULT_WEIGHT)

                # If weight is 0, it doesn't make sense to set for such space a weight
                if weight == 0:
                    continue

                space_idx = self.spaces.index(space)

                for disk_idx in range(len(self.disks)):
                    row[disk_idx * len(self.spaces) + first_space_idx] = 1 / first_weight
                    row[disk_idx * len(self.spaces) + space_idx] = -1 / weight

                self.weight_equation_indexes.append(len(self.equality_constraint_matrix) - 1)

                self.equality_constraint_matrix.append(row)
                self.equality_constraint_vector = np.append(self.equality_constraint_vector, 0)

    def _make_matrix_row(self):
        return np.zeros(self.x_amount)

    def _make_upper_bound_constraint_matrix(self):
        """Upper bound constraint matrix consist of upper bound
        matrix and lower bound matrix witch changed sign
        """
        return (self.upper_bound_constraint_matrix +
                [[-i for i in row] for row in self.lower_bound_constraint_matrix])

    def _make_upper_bound_constraint_vector(self):
        """Upper bound constraint vector consist of upper bound
        and lower bound, with changed sign
        """
        return (self.upper_bound_constraint_vector +
                [-i for i in self.lower_bound_constraint_vector])

    def _convert_solution(self, solution_vector):
        result = []

        spaces_grouped_by_disk = list(grouper(solution_vector, len(self.spaces)))
        for disk_i in range(len(self.disks)):
            disk_id = self.disks[disk_i].id
            disk = {'disk_id': disk_id, 'size': self.disks[disk_i].size, 'spaces': []}
            spaces_for_disk = spaces_grouped_by_disk[disk_i]

            for space_i, space_size in enumerate(spaces_for_disk):
                disk['spaces'].append({
                    'space_id': self.spaces[space_i].id,
                    'size': space_size})

            result.append(disk)

        return result

    def _init_equation(self, disks, spaces):
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
        equality_matrix_row = self._make_matrix_row()

        # Set first len(spaces) elements to 1
        equality_matrix_row = shift(equality_matrix_row, len(spaces), val=1)

        for _ in range(len(disks)):
            self.equality_constraint_matrix.append(equality_matrix_row)
            equality_matrix_row = shift(equality_matrix_row, len(spaces), val=0)

        # Size of each space should be more or equal to 0
        for _ in range(self.x_amount):
            self._add_bound(0, None)

    def _init_objective_function_coefficient(self):
        # Amount of coefficients is equal to amount of x
        c_amount = self.x_amount

        # We want spaces to be allocated on disks
        # in order which user specified them in the schema.
        # In order to do that, we set coefficients
        # higher for those spaces which defined earlier
        # in the list

        # TODO describe why we should use special sequence
        # as order coefficients
        coefficients = [1.0/i for i in CrossSumInequalitySequence(c_amount)]

        NONE_ORDER_COEFF = 1
        SET_COEFF = 2

        space_sets = self._get_spaces_sets_by(['best_with_disks'])

        # A list of disks ids which are not selected for specific spaces
        all_disks_ids = [i for i in range(len(self.disks))]
        used_disks_ids = []

        for k, space in self._get_sets_by(['best_with_disks']):
            if k[0]:
                used_disks_ids.extend(list(k[0]))

        not_best_disks = list(set(all_disks_ids) - set(used_disks_ids))

        for i_set, space_set in enumerate(space_sets):
            for space in space_set:
                s_i = self.spaces.index(space)

                for d_i in range(len(self.disks)):
                    c_i = len(self.spaces) * d_i + s_i

                    # Set constant for none_order spaces
                    if getattr(space, 'none_order', False):
                        coefficients[c_i] = NONE_ORDER_COEFF
                        continue

                    if space.best_with_disks:
                        if d_i in space.best_with_disks:
                            coefficients[c_i] += SET_COEFF
                        else:
                            # If current disk is not in the set, set it to 0
                            # TODO isn't it better to leave there order coefficient?
                            # coefficients[c_i] = 0
                            pass
                    else:
                        # Don't allcoate coefficient for the spaces
                        # which have no best_with_disks, on best_with_disks
                        if d_i in not_best_disks:
                            coefficients[c_i] += SET_COEFF

        # By default the algorithm tries to minimize the solution
        # we should invert sign, in order to make it a maximization
        # function, because we want disks to be maximally allocated.
        self.objective_function_coefficients = [-c for c in coefficients]

    def _add_bound(self, min_, max_):
        np.append(self.bounds, (min_, max_))
