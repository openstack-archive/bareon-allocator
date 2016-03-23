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

import os
import six

from glob import glob

from bareon_allocator.allocators import DynamicAllocator
from bareon_allocator import utils
from bareon_allocator import viewer


doc_schemas_path = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'doc',
    'source',
    'schemas')
doc_schemas_rst_path = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'doc',
    'source',
    'examples.rst')


def generate_svg_files():

    result = {}

    for dynamic_schema_path in sorted(
            glob(os.path.join(doc_schemas_path, '*_ds.yaml'))):
        print('Read file {0}'.format(dynamic_schema_path))
        dynamic_schema = utils.parse_yaml(dynamic_schema_path)
        dynamic_schema_file_name = os.path.basename(dynamic_schema_path)
        dynamic_schema_name = os.path.splitext(dynamic_schema_file_name)[0]
        for hw_info_path in sorted(
                glob(os.path.join(doc_schemas_path, '*_disk.yaml'))):
            print('Read file {0}'.format(hw_info_path))
            hw_info_file_name = os.path.basename(hw_info_path)
            hw_info_name = os.path.splitext(hw_info_file_name)[0]
            hw_info = utils.parse_yaml(hw_info_path)
            static_schema = DynamicAllocator(
                hw_info,
                dynamic_schema).generate_static()

            static_schema_name = '{0}_{1}.svg'.format(
                dynamic_schema_name,
                hw_info_name)
            result[static_schema_name[:-4]] = {
                'dynamic_schema': os.path.join('schemas',
                                               dynamic_schema_file_name),
                'hw_info': os.path.join('schemas', hw_info_file_name),
                'image': os.path.join('schemas', static_schema_name)}

            viewer.SVGViewer(static_schema,
                             file_path=os.path.join(doc_schemas_path,
                                                    static_schema_name),
                             fit=True).show_me()

    rst_doc = """
===================
Allocation Examples
===================

    """
    for name, value in sorted(six.iteritems(result)):
        rst_doc += """

{topic}
-----------------

Hardware information
~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: {hw_info}
    :language: yaml

Dynamic schema
~~~~~~~~~~~~~~
.. literalinclude:: {dynamic_schema}
    :language: yaml

Allocation result
~~~~~~~~~~~~~~~~~

.. image:: {image}
        :width: 100%

        """.format(
            topic=name,
            image=value['image'],
            hw_info=value['hw_info'],
            dynamic_schema=value['dynamic_schema'])

    with open(doc_schemas_rst_path, 'w') as f:
        f.write(rst_doc)


if __name__ == '__main__':
    generate_svg_files()
