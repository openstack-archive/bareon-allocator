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


import yaml
import yaql

data = yaml.load(open('/Users/eli/job/bareon-dynamic-allocator/etc/bareon-dynamic-allocator/example_2_disks.yaml').read())


engine_options = {
    'yaql.limitIterators': 100,
    'yaql.treatSetsAsLists': True,
    'yaql.memoryQuota': 10000
}


factory = yaql.YaqlFactory()
parser = factory.create(options=engine_options)

from pprint import pprint
pprint(parser('$.disks.where($.type = "hdd" or ($.type = "ssd" and $.dev = "/dev/sda")) ').evaluate(data))
pprint(parser('$.disks.where(($.type = "ssd" and $.dev = "/dev/sda") or $.type = "hdd") ').evaluate(data))
print parser('$.get(ram1, 1000) + 2').evaluate(data)
