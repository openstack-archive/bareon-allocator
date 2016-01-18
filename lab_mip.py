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


from pulp import *
import sys

x = []
y = []

thismodule = sys.modules[__name__]

for i in range(6):
    name = 'x{0}'.format(i + 1)
    var = LpVariable(name, 0, None)
    setattr(thismodule, name, var)
    x.append(var)

for i in range(6):
    name = 'y{0}'.format(i + 1)
    var = LpVariable(name, 0, 1, 'Binary')
    setattr(thismodule, name, var)
    y.append(var)


# defines the problem
prob = LpProblem("problem", LpMaximize)

# defines the objective function to maximize
prob += x1 + x2 + x3 + x4 + x5 + x6, 'Sum of spaces'


# defines the constraints
prob += x1 + x2 <= 100, 'First disk'
prob += x3 + x4 <= 100, 'Second disk'
prob += x5 + x6 <= 100, 'Third disk'

prob += y1 + y3 + y5 == 2, 'Replication factor'

prob += x1 + x3 + x5 >= 20, 'First min size'
prob += x2 + x4 + x6 >= 101, 'Second min size'

prob += x1 - x5 == 0, 'Sizes equality for raid'

# Convert from Float to Integer
for i, x_ in enumerate(x):
    y_ = y[i]

    prob += y_ - x_ <= 0
    prob += x_ - 100 * y_ <= 0

# solve the problem
status = prob.solve(GLPK(msg=1))

def print_vector(vector, prefix, n=2):

    for i, v in enumerate(vector):
        sys.stdout.write('{0}_{1} = {2}'.format(prefix, i + 1, value(v)))
        if (i + 1) % n:
            sys.stdout.write('\t')
        else:
            sys.stdout.write('\n')

print_vector(x, 'x')
print_vector(y, 'y')
