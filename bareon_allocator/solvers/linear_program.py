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


class LinearProgram(object):
    """LinearProgram object is abstract way to describe linear program."""
    MAXIMIZE = 'maximize'
    MINIMIZE = 'minimize'

    # Linear Program
    LP_TYPE_LP = 'lp'
    # Mixed Integer Program
    LP_TYPE_MIP = 'mip'

    def __init__(
            self,
            x_amount=0,
            optimization_type=MAXIMIZE,
            lp_type=LP_TYPE_LP,
            objective_function_coefficients=None,

            equality_constraint_matrix=None,
            lower_constraint_matrix=None,
            upper_constraint_matrix=None,

            equality_constraint_vector=None,
            lower_constraint_vector=None,
            upper_constraint_vector=None):

        self.lp_type = lp_type
        self.objective_function_optimization_type = optimization_type

        # Coefficients of the linear objective minimization function.
        # During iteration over vertexes the function is used to identify
        # if current solution (vertex) satisfies the equation more, than
        # previous one.
        # Example of equation: c[0]*x1 + c[1]*x2
        self.objective_function_coefficients = objective_function_coefficients

        # Matrices which, gives values of the equality/inequality
        # constraints, when multiplied by x.
        self.equality_constraint_matrix = equality_constraint_matrix
        self.lower_constraint_matrix = lower_constraint_matrix
        self.upper_constraint_matrix = upper_constraint_matrix

        # Vectors in combination with equality matrices give
        # equality/inequality system of linear equations.
        self.equality_constraint_vector = equality_constraint_vector
        self.lower_constraint_vector = lower_constraint_vector
        self.upper_constraint_vector = upper_constraint_vector

        # Amount unknown of variables.
        self.x_amount = x_amount

        # A list of tuples which represents min and max possible values for
        # each variable.
        self.bounds = [(0, None) for _ in xrange(self.x_amount)]

    def minimize_objective_function(self):
        """Minimize objective function."""
        self.objective_function_optimization_type = self.MINIMIZE

    def maximize_objective_function(self):
        """Maximize objective function."""
        self.objective_function_optimization_type = self.MAXIMIZE

    def set_type_lp(self):
        """Set type of linear program to Linear Program.

        Is default, produces real number result, without any integer
        constraints.
        """
        self.lp_type = self.LP_TYPE_LP

    def set_type_mip(self):
        """"Set type of linear program to Mixed Integer Program.

        This type may include integer constraints, as result wider range of
        operations may be available.

        Note: Not all linear programming solvers support this type.
        See: https://en.wikipedia.org/wiki/Integer_programming
        """
        self.lp_type = self.LP_TYPE_MIP
