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

from bareon_allocator.objects import Disk
from bareon_allocator.objects import Space
from bareon_allocator.parser import Parser


LOG = log.getLogger(__name__)


class DynamicSchemaParser(object):

    def __init__(self, hw_info, schema):
        self.hw_info = hw_info
        self.schema = schema
        self.raw_disks = self.hw_info['disks']
        self.rendered_spaces = []
        self.disks = []
        self.spaces = []

        self.parse()
        self.post_parse()

    def parse(self):
        self.render_expressions()

        self.disks = [
            Disk(**disk)
            for disk in self.raw_disks]

        self.spaces = [
            Space(**space)
            for space in self.rendered_spaces if space['type'] != 'vg']

    def post_parse(self):
        # Add fake volume Unallocated, in order to be able
        # to have only volumes with minimal size, without
        # additional space allocation
        self.spaces.append(Space(
            id='unallocated',
            type='unallocated',
            none_order=True,
            weight=0))

    def render_expressions(self):
        self.rendered_spaces = self._convert_disks_to_indexes(
            Parser(self.schema, self.hw_info).parse(),
            self.hw_info)

    def _convert_disks_to_indexes(self, spaces, hw_info):
        """Convert disks to indexes.

        Convert disks which are specified in `best_with_disks`
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
