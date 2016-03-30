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

import itertools

from bareon_allocator.sequences import CrossSumInequalitySequence
from bareon_allocator.solvers.linear_program import LinearProgram


class LinearProgramCreator(object):
    """Creates LinearProgram based on DynamicSchema object."""
    NONE_ORDER_COEFFICIENT = 1
    SET_COEFFICIENT = 2

    def __init__(self,
                 dynamic_schema,
                 weight_sets_criteria=[
                     'min_size',
                     'max_size',
                     'best_with_disks']):
        """Initializes the object.

        :param dynamic_schema: :class:`DynamicSchema` object
        :param weight_sets_criteria: a list of strings, which represents
               attributes of spaces based on which sets will be created to
               make equations.
        """
        self.weight_sets_criteria = weight_sets_criteria
        self.disks = dynamic_schema.disks
        self.spaces = dynamic_schema.spaces

        self.spaces_len = len(self.spaces)
        self.disks_len = len(self.disks)

        # For each space, x (size of the space) is represented
        # for each disk as separate variable, so for each
        # disk we have len(spaces) * len(disks) sizes
        self.x_amount = self.disks_len * self.spaces_len

    def linear_program(self):
        """Returns linear program object

        :return: :class:`LinearProgram` linear program object
        """
        space_size_equation = self._make_space_size_constraints()
        disk_size_equation = self._make_disk_size_constraints()
        equality_weight_equation = self._make_weight_constraints()

        # Merge both equality and constraint vectors into a single dictionary
        equations = self._merge_equations(space_size_equation,
                                          disk_size_equation)
        equations = self._merge_equations(equations,
                                          equality_weight_equation)

        objective_coefficients = self._make_objective_function_coefficient()
        return LinearProgram(
            x_amount=self.x_amount,
            optimization_type=LinearProgram.MAXIMIZE,
            objective_function_coefficients=objective_coefficients,
            **equations)

    def _make_space_size_constraints(self):
        """Create min and max constraints for each space.

        In case of 2 disks and 2 spaces

        For first space min_size >= 10 and max_size <= 20
        1 * x1 + 0 * x2 + 1 * x3 + 0 * x4 >= 10
        1 * x1 + 0 * x2 + 1 * x3 + 0 * x4 <= 20

        For second space min_size >= 15 and max_size <= 30
        0 * x1 + 1 * x2 + 0 * x3 + 1 * x4 >= 15
        0 * x1 + 1 * x2 + 0 * x3 + 1 * x4 <= 30
        """
        constraint_equation = {
            'lower_constraint_matrix': [],
            'lower_constraint_vector': [],
            'upper_constraint_matrix': [],
            'upper_constraint_vector': []}

        for space_idx, space in enumerate(self.spaces):
            row = self._make_matrix_row()

            for disk_idx in range(self.disks_len):
                row[disk_idx * self.spaces_len + space_idx] = 1

            if space.min_size is not None:
                constraint_equation['lower_constraint_matrix'].append(
                    row)
                constraint_equation['lower_constraint_vector'].append(
                    space.min_size)

            if space.max_size is not None:
                constraint_equation['upper_constraint_matrix'].append(
                    row)
                constraint_equation['upper_constraint_vector'].append(
                    space.max_size)

        return constraint_equation

    def _merge_equations(self, eq1, eq2):
        """Merges two equations into a single dictionary of equations.

        :param eq1: equation dictionary, where key is a name of equation and
                    value is a vector or matrix
        :param eq2: same as eq1
        :return: merged equation
        """
        result = {}
        all_keys = set(eq1.keys() + eq2.keys())
        for key in all_keys:
            if eq2.get(key) and eq1.get(key):
                # Merge if both have values
                result[key] = eq1[key] + eq2[key]
            elif eq2.get(key):
                result[key] = eq2[key]
            elif eq1.get(key):
                result[key] = eq1[key]

        return result

    def _make_disk_size_constraints(self):
        """Creates equations based on disk sizes.

        So solver will not allocate more then "disk size" space for each disk.

        :return: equations, where key is a name of equation, value is a list
                 or vector
        """
        constraint_equation = {
            'upper_constraint_matrix': [],
            'upper_constraint_vector': []}

        for disk_idx in range(self.disks_len):
            row = self._make_matrix_row()

            for space_idx, space in enumerate(self.spaces):
                row[disk_idx * self.spaces_len + space_idx] = 1

            constraint_equation['upper_constraint_matrix'].append(row)
            constraint_equation['upper_constraint_vector'].append(
                self.disks[disk_idx].size)

        return constraint_equation

    def _make_weight_constraints(self):
        """Refresh weight.

        Create weight constraints for spaces which have same
        max constraint or for those which don't have it at all.

        Lets say, second's space is equal to max of the third and fourth,
        we will have next equation:
        0 * x1 + (1 / weight) * x2 + (-1 / weight) * x3 +
        0 * x4 + (1 / weight) * x5 + (-1 / weight) * x6 = 0

        TODO(eli): it should be not equality, but inequality with some
        range, so we will not get fails every time exact constraint cannot be
        satisfied.

        See "Weight" section in the documentation for details:
        http://bareon-allocator.readthedocs.org/en
              /latest/architecture.html#weight
        """
        weight_equations = {
            'equality_constraint_matrix': [],
            'equality_constraint_vector': []}

        weight_spaces_sets = self._get_spaces_sets_by(
            self.weight_sets_criteria)

        for spaces_set in weight_spaces_sets:
            # Don't set weight if there is less than one space in the set
            if len(spaces_set) < 2:
                continue

            first_weight = spaces_set[0].weight
            first_space_idx = self.spaces.index(spaces_set[0])
            for space in spaces_set[1:]:
                row = self._make_matrix_row()

                # If weight is 0, it doesn't make sense to set for such
                # space a weight
                if space.weight == 0:
                    continue

                space_idx = self.spaces.index(space)

                for disk_idx in range(len(self.disks)):
                    row_i = disk_idx * len(self.spaces)
                    row[row_i + first_space_idx] = 1 / first_weight
                    row[row_i + space_idx] = -1 / space.weight

                weight_equations['equality_constraint_matrix'].append(row)
                weight_equations['equality_constraint_vector'].append(0)

        return weight_equations

    def _make_objective_function_coefficient(self):
        # Amount of coefficients is equal to amount of x
        c_amount = self.x_amount

        # We want spaces to be allocated on disks in order which user
        # specified them in the schema. In order to do that, we set
        # coefficients higher for those spaces which defined earlier in the
        # list.
        # Instead of just Integer seuqence special type of sequence is being
        # used, see documentation [1] for details.
        #
        # [1] http://bareon-allocator.readthedocs.org/en
        #          /latest/architecture.html#ordering
        coefficients = [1.0 / i for i in CrossSumInequalitySequence(c_amount)]

        space_sets = self._get_spaces_sets_by(['best_with_disks'])
        no_best_disks = self._get_empty_sets_disks_idx(['best_with_disks'])

        for i_set, space_set in enumerate(space_sets):
            for space in space_set:
                s_i = self.spaces.index(space)

                for d_i in range(self.disks_len):
                    c_i = self.spaces_len * d_i + s_i

                    # Set constant for none_order spaces
                    if space.none_order:
                        coefficients[c_i] = self.NONE_ORDER_COEFFICIENT
                        continue

                    # If space does not belong to any set, order coefficient
                    # will be left without any additional coefficients.
                    if space.best_with_disks and d_i in space.best_with_disks:
                        # If the space has "best disks" and current disk is
                        # in best disks list, add coefficient.
                        coefficients[c_i] += self.SET_COEFFICIENT
                    elif not space.best_with_disks and d_i in no_best_disks:
                        # If the space does *not* have "best disks" and
                        # current disk is not in the list of "best disks" of
                        # any space, add set coefficient.
                        coefficients[c_i] += self.SET_COEFFICIENT

        # By default the algorithm tries to minimize the solution
        # we should invert sign, in order to make it a maximization
        # function, because we want disks to be maximally allocated.
        return [-c for c in coefficients]

    def _get_empty_sets_disks_idx(self, criteria):
        """Get disks indexes which do not belong to set of any spaces.

        :param criteria: a list of strings, with criteria by which sets has
                         to be created
        :return: a list of disks indexes
        """
        all_disks_idx = [i for i in range(self.disks_len)]
        used_disks_idx = []

        for k, space in self._get_sets_by(criteria):
            if k[0]:
                used_disks_idx.extend(list(k[0]))

        return list(set(all_disks_idx) - set(used_disks_idx))

    def _get_spaces_sets_by(self, criteria):
        """Get all spaces which are used for sets.

        :param criteria: a list of strings with attributes by which sets has
                         to be created
        :return: a list of spaces lists, where each list item is represents
                 a set
        """
        return [i[1] for i in self._get_sets_by(criteria)]

    def _get_sets_by(self, criteria):
        """Makes sets based on criteria from space attributes.

        :param criteria: a list of strings with attributes by which sets has
                         to be created
        :return: a list of tuples, where first item are criteria, second
                item is a list of spaces
        """
        def get_values(space):
            return [getattr(space, c, None) for c in criteria]

        grouped_spaces = itertools.groupby(
            sorted(self.spaces, key=get_values),
            key=get_values)

        return [(k, list(v)) for k, v in grouped_spaces]

    def _make_matrix_row(self):
        """Make a matrix row

        :return: a vector where all the items are 0
        """
        return [0] * self.x_amount
