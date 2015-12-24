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

import sys

from oslo_config import cfg
from oslo_log import log

from bareon_dynamic_allocator import utils
from bareon_dynamic_allocator.allocators import DynamicAllocator
from bareon_dynamic_allocator import viewer


cli_opts = [
    cfg.StrOpt(
        'schema',
        required=True,
        help='Input file, path to a file with dynamic partitioning schema'
    ),
    cfg.StrOpt(
        'file',
        required=True,
        help='Output path to a file with static partitioning schema'
    ),
    cfg.StrOpt(
        'hw-info',
        required=True,
        help='Hardware information'
    )
]


def make_config():
    conf = cfg.ConfigOpts()

    conf.register_cli_opts(cli_opts)
    log.register_options(conf)

    return conf


def parse_args(conf, args=None):
    project = 'bareon_dynamic_allocator'
    version = '1.0.0'
    conf(args=args if args else sys.argv[1:],
         project=project,
         version=version)
    log.setup(conf,
              project,
              version=version)


CONF = make_config()
parse_args(CONF)
LOG = log.getLogger(__name__)


def parse_configs(conf):
    hw_info = utils.parse_yaml(conf.hw_info)
    schema = utils.parse_yaml(conf.schema)

    return (hw_info, schema)


def save_result(data, output_file):
    viewer.StdoutViewer(data).show_me()
    viewer.SVGViewer(data).show_me()


def validate_schema(schema):
    # TODO should be implemented
    return schema


def validate_hw_info(hw_info):
    # TODO should be implemented
    return hw_info


def allocator():
    LOG.debug('hi')
    conf = parse_configs(CONF)
    validate_schema(conf[0])
    validate_hw_info(conf[1])

    schema = DynamicAllocator(*conf).generate_static()

    save_result(schema, CONF.file)


if __name__ == '__main__':
    allocator()
