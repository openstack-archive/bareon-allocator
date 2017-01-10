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

from oslo_log import log

from bareon_allocator.parsers import DynamicSchemaParser
from bareon_allocator.solvers import LinearProgramCreator
from bareon_allocator.solvers import LinearProgrammingScipySolver
from bareon_allocator import utils

LOG = log.getLogger(__name__)


class DynamicAllocator(object):

    def __init__(self, hw_info, schema):
        LOG.debug('Hardware information: %s', hw_info)
        LOG.debug('Spaces schema: %s', schema)
        self.dynamic_schema = DynamicSchemaParser(hw_info, schema)
        LOG.debug('Spaces objects: %s', self.dynamic_schema.spaces)
        LOG.debug('Disks objects: %s', self.dynamic_schema.disks)

        linear_program = LinearProgramCreator(
            self.dynamic_schema).linear_program()
        self.solver = LinearProgrammingScipySolver(linear_program)

    def generate_static(self):
        solution = self.solver.solve()
        LOG.debug('Static allocation schema: \n%s', solution)
        return self._convert_solution(solution)

    def _convert_solution(self, solution_vector):
        # TODO(eli): convertation logic should be moved to solvers,
        # as result Solver object should be returned and used
        result = []

        spaces_grouped_by_disk = list(utils.grouper(
            solution_vector,
            len(self.dynamic_schema.spaces)))
        for disk_i in range(len(self.dynamic_schema.disks)):
            disk_id = self.dynamic_schema.disks[disk_i].id
            disk = {'disk_id': disk_id,
                    'size': self.dynamic_schema.disks[disk_i].size,
                    'spaces': []}
            spaces_for_disk = spaces_grouped_by_disk[disk_i]

            for space_i, space_size in enumerate(spaces_for_disk):
                disk['spaces'].append({
                    'space_id': self.dynamic_schema.spaces[space_i].id,
                    'size': space_size})

            result.append(disk)

        return result
