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
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import itertools

import numpy as np
import yaml

from termcolor import colored


def shift(arr, steps, val=0):
    res_arr = np.roll(arr, steps)
    np.put(res_arr, range(steps), val)

    return res_arr


def grouper(iterable, n, fillvalue=None):
    """Collect data into fixed-length chunks or blocks.

    Source: https://docs.python.org/2/library/itertools.html#recipes
    """
    args = [iter(iterable)] * n
    return itertools.izip_longest(fillvalue=fillvalue, *args)


def format_x_vector(coefficients, num=0):
    return '\n{0}\n'.format('\n'.join(
        [' + '.join(group)
         for group in grouper(['({0:+.5f} * x{1})'.format(c, i)
                               for i, c in enumerate(coefficients)], num)]))


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


def parse_yaml(path):
    """Parses yaml file.

    :param str path: path to the file
    :returns: dict or list
    """
    return yaml.load(open(path))
