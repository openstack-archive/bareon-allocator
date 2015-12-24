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

from pprint import pprint
import svgwrite
from svgwrite import cm, mm


class StdoutViewer(object):

    def __init__(self, disks_spaces_mapping):
        self.disks_spaces_mapping = disks_spaces_mapping

    def show_me(self):
        pprint(self.disks_spaces_mapping)


class SVGViewer(object):

    PALETTE = ['#666547', '#fb2e01', '#6fcb9f', '#ffe28a', '#fffeb3']
    DISK_HEIGHT = 3 * cm
    SPACE_HEIGHT = 3 * cm
    WIDTH_MULTIPLIER = 10
    DISKS_INTERVAL = 150
    SPACES_X_INTERVAL = 2
    STYLE = "fill:{color};stroke:black;stroke-width:5;"

    def __init__(self, disks_spaces_mapping, file_path='/tmp/bareon.svg'):
        self.disks_spaces_mapping = disks_spaces_mapping
        self.dwg = svgwrite.Drawing(filename=file_path, debug=True)

    def show_me(self):
        self._add_disk_with_spaces()
        self.dwg.save()

    def _add_disk_with_spaces(self):
        disk_g = self.dwg.add(self.dwg.g(id='disks-group', transform="translate({0}, {1})".format(30, 30)))

        for disk_idx, disk_w_spaces in enumerate(self.disks_spaces_mapping):
            disk_id = disk_w_spaces['disk_id']
            size = disk_w_spaces['size']

            disk = disk_g.add(self.dwg.g(id=disk_id, transform="translate(0, {0})".format(disk_idx * self.DISKS_INTERVAL)))
            disk.add(self.dwg.text(text='{0} size={1}'.format(disk_id, size), fill="black"))

            disk_rect = disk.add(self.dwg.g(transform="translate({0}, {1})".format(0, 10), id='in-{0}'.format(disk_id)))
            disk_rect.add(self.dwg.rect(
                style=self.STYLE.format(color='#f5f5f5'),
                ry=5,
                rx=5,
                size=(self.WIDTH_MULTIPLIER * disk_w_spaces['size'],
                      self.DISK_HEIGHT)))

            last_insert = [0, 0]
            for space_idx, space in enumerate(disk_w_spaces['spaces']):
                palette = self.PALETTE[space_idx % len(self.PALETTE)]
                disk_rect.add(self.dwg.rect(
                    style=self.STYLE.format(color=palette),
                    ry=5,
                    rx=5,
                    id=space['space_id'],
                    insert=last_insert,
                    size=(self.WIDTH_MULTIPLIER * space['size'], self.SPACE_HEIGHT)))

                last_insert[0] += self.WIDTH_MULTIPLIER * space['size']

            spaces_lines = ['{0} size={1}'.format(space['space_id'], space['size']) for space in disk_w_spaces['spaces']]

            last_insert[0] = self.WIDTH_MULTIPLIER * disk_w_spaces['size']
            last_insert[0] += 10
            last_insert[1] += 20
            for space_idx, space_line in enumerate(spaces_lines):
                palette = self.PALETTE[space_idx % len(self.PALETTE)]
                disk_rect.add(self.dwg.text(insert=last_insert, text=space_line, fill=palette))
                last_insert[1] += 20
