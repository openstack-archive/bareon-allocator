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


import re
import six
import yaql


def seq_iter(obj):
    if isinstance(obj, dict):
        for k, v in six.iteritems(obj):
            yield k, v
    elif isinstance(obj, list):
        for i in xrange(len(obj)):
            yield i, obj[i]


class YAQLParser(object):
    engine_options = {
        'yaql.limitIterators': 100,
        'yaql.treatSetsAsLists': True,
        'yaql.memoryQuota': 10000
    }

    def __init__(self, data, context):
        self.factory = yaql.YaqlFactory()
        self.parser = self.factory.create(options=self.engine_options)
        self.context = context
        self.data = data

    def parse(self):
        return self.parser(self.data).evaluate(self.context)


class NoopParser(object):

    def __init__(self, data, _):
        self.data = data

    def parse(self):
        return self.data


class Parser(object):

    yaql_re = re.compile(r'^\s*yaql\s*=\s*')

    def __init__(self, template, context):
        self.template = template
        self.context = context

    def parse(self):
        return self._walk(self.template)

    def _walk(self, node):
        if isinstance(node, six.string_types):
            return self.get_parser(node).parse()

        for key, item in seq_iter(node):
            node[key] = self._walk(item)

        return node

    def get_parser(self, node):
        if self.yaql_re.match(node):
            wo_prefix = self.yaql_re.sub('', node)
            return YAQLParser(wo_prefix, self.context)

        return NoopParser(node, self.context)
