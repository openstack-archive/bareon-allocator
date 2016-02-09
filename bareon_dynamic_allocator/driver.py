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

from bareon.drivers.base import BaseDataDriver
from bareon.drivers.base import PartitioningDataDriverMixin
from bareon import objects
from bareon.openstack.common import log

from bareon_dynamic_allocator import allocators


# Logger for bareon-dynamic allocator should be configured
# to use Bareon's logger
LOG = log.getLogger(__name__)


class DynamicAllocator(BaseDataDriver, PartitioningDataDriverMixin):

    TABLE_TYPE = 'gpt'

    @property
    def partition_scheme(self):
        partition_objects = objects.PartitionScheme()

        hw_info = self.data.get('hw_info')
        dynamic_schema = self.data.get('dynamic_schema')

        static_scheme = allocators.DynamicAllocator(
            hw_info,
            dynamic_schema).generate_static()
        self._parse_partition_scheme(static_scheme, partition_objects)

        return partition_objects

    def _parse_partition_scheme(self, static_scheme, partition_objects):
        for disk in static_scheme:
            LOG.debug('Start allocation of spaces on disk %s', disk)
            disk_raw = filter(lambda d: d['id'] == disk['disk_id'],
                              self.data['hw_info']['disks'])[0]
            LOG.debug('Create parted object %s with label %s',
                      disk_raw['path'],
                      self.TABLE_TYPE)

            parted = partition_objects.add_parted(
                name=disk_raw['path'],
                label=self.TABLE_TYPE)

            for space in disk['spaces']:
                LOG.debug('Create partition name %s size %s',
                          space['space_id'], space['size'])

                partition = parted.add_partition(
                    size=space['size'],
                    name=space['space_id'])

                raw_space = filter(lambda s: s['id'] == space['space_id'],
                                   self.data['dynamic_schema'])

                if not raw_space:
                    raw_space = {}
                else:
                    raw_space = raw_space[0]

                if raw_space.get('type') == 'lv':
                    vg = filter(
                        lambda s: raw_space['id'] in map(
                            lambda v: v['id'], s.get('contains', []))
                        and s.get('type') == 'vg',
                        self.data['dynamic_schema'])[0]

                    LOG.debug(
                        'Add Phisical Volume to Volume '
                        'Group vgname %s pvname %s',
                        vg['id'],
                        raw_space['id'])

                    partition_objects.vg_attach_by_name(
                        pvname=partition.name,
                        vgname=vg['id'],
                        # TODO(eli): figure out how to calculate size
                        # of metadata properly
                        metadatasize=8,
                        metadatacopies=2)
