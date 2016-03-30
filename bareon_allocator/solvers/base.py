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

import abc

import six


@six.add_metaclass(abc.ABCMeta)
class BaseSolver(object):
    """Base class for Bareon Allocator Objects."""

    def __init__(self, linear_program):
        """Initialize object.

        :param linear_program: `class`:LinearProgram object
        """
        self.linear_program = linear_program

    @abc.abstractmethod
    def solve(self):
        """Returns solution hash.

        :raises: errors.NoSolutionFound
        """
