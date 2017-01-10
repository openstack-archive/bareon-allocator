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

from copy import deepcopy

from bareon_allocator import errors

import six


@six.add_metaclass(abc.ABCMeta)
class BaseObject(object):
    """Base class for Bareon Allocator Objects."""

    def __init__(self, **kwargs):
        self.init_data = deepcopy(kwargs)
        self.additional_parameters = {}

        # Fail if required property is not specified
        if not set(self.required) <= set(kwargs.keys()):
            required_properties = set(self.required) - set(kwargs.keys())
            raise errors.InvalidData(
                'Cannot create object with parameters "{0}", because '
                'required parameters are not provided {1}'.format(
                    self.init_data,
                    required_properties))

        # Set default properties for the object
        for k, v in six.iteritems(self.properties):
            setattr(self, k, v)

        # Override properties with data from parameters
        for k, v in six.iteritems(self.init_data):
            if k in self.properties.keys():
                setattr(self, k, v)
            else:
                self.additional_parameters[k] = v

    def __repr__(self):
        return str(self.init_data)

    @abc.abstractproperty
    def properties(self):
        """Set object properties.

        Should be dictionary, example

        {
          'property': default_value
        }
        """

    @property
    def required(self):
        """A list of required properties."""
        return []
