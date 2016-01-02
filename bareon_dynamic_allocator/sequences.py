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
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See then
#    License for the specific language governing permissions and limitations
#    under the License.

import math


class BaseSequence(object):

    def __init__(self, n):
        self.n = n
        self.n_current = 0
        self.current = 1
        self.previous = 0

    def __iter__(self):
        return self

    def next(self):
        self.previous = self.current
        self.current += 1
        return self.current
        

class CrossSumInequalitySequence(BaseSequence):
    """An implementaion of a sequence from 1 to n

    http://math.stackexchange.com/a/1596812/301008
    """

    def next(self):
        if self.n_current >= self.n:
            raise StopIteration
        else:
            self.previous = int(math.floor((self.current + 1) / 2.0) *
                            math.floor((self.current + 2) / 2.0))
            self.n_current += 1
            self.current += 1

            return self.previous


class FibonacciSequence(BaseSequence):
    """Iterator over a sequence of Fibonacci numbers with n elements from 1 to n
    """
    def __init__(self, n):
        super(FibonacciSequence, self).__init__(n)
        self.previous = 0
        self.current = 1

    def next(self):
        if self.n_current > self.n:
            raise StopIteration
        else:
            self.n_current += 1
            self.previous, self.current = self.current, self.current + self.previous
            return self.current
