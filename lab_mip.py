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
z = []

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

for i in range(6 / 2):
    name = 'z{0}'.format(i + 1)
    var = LpVariable(name, 0, 1, 'Binary')
    setattr(thismodule, name, var)
    z.append(var)


# defines the problem
prob = LpProblem("problem", LpMaximize)

# defines the objective function to maximize
prob += x1 + x2 + x3 + x4 + x5 + x6, 'Sum of spaces'

# defines the constraints
prob += x1 + x2 <= 100, 'First disk'
prob += x3 + x4 <= 100, 'Second disk'
prob += x5 + x6 <= 100, 'Third disk'

prob += y1 + y3 + y5 == 2, 'Replication factor'

prob += x2 + x4 + x6 >= 10, 'Second min size'

# Specify min and max sizes for RAIDs using allocation size
# of each space, not sum of all spaces
prob += x1 >= y1 * 10
prob += x1 <= y1 * 30

prob += x3 >= y3 * 10
prob += x3 <= y3 * 30

prob += x5 >= y5 * 10
prob += x5 <= y5 * 30

# z1, z2 and z3 are going to store info about available pairs
prob += z1 >= y1 + y3 - 1
prob += z1 <= y1
prob += z1 <= y3

prob += z2 >= y1 + y5 - 1
prob += z2 <= y1
prob += z2 <= y5

prob += z3 >= y3 + y5 - 1
prob += z3 <= y3
prob += z3 <= y5

# Make sizes equal if they are set
M = 10000000

prob += x1 - x3 + M * z1 <= M
prob += -x1 + x3 + M * z1 <= M

prob += x1 - x5 + M * z2 <= M
prob += -x1 + x5 + M * z2 <= M

prob += x3 - x5 + M * z3 <= M
prob += -x3 + x5 + M * z3 <= M

# Convert from Float to Integer
for i, x_ in enumerate(x):
    y_ = y[i]

    prob += y_ - x_ <= 0
    prob += x_ - 100 * y_ <= 0

# solve the problem
status = prob.solve(GLPK(msg=1))

def print_vector(vector, prefix, n=2):

    for i, v in enumerate(vector):
        sys.stdout.write('{0}{1} = {2}'.format(prefix, i + 1, value(v)))
        if (i + 1) % n:
            sys.stdout.write('\t')
        else:
            sys.stdout.write('\n')

print
print_vector(x, 'x')
print
print_vector(y, 'y')
print
print_vector(z, 'z', n=3)
print
