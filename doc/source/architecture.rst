============
Architecture
============
Problem description
-------------------
User may have a variety of bare-metal node configuration, with different amount of disks, types of disks and their sizes, there should be a way to store best practises on what is the best way to do partitioning, so they can be applied for the most configuration cases without asking the end user to manually adjust the configuration of partitioning, with posibility to do that, if user wants to.

History
-------
First (and second) attempts to solve the problem has begun during development of `Fuel <https://wiki.openstack.org/wiki/Fuel>`_ project, special module `VolumeManager <https://github.com/openstack/fuel-web/blob/7.0/nailgun/nailgun/extensions/volume_manager/manager.py>`_ was created to solve the problem, it consumes `hardware information <https://github.com/openstack/fuel-web/blob/7.0/nailgun/nailgun/fixtures/sample_environment.json#L195-L232>`_ and `partitioning schema <https://github.com/openstack/fuel-web/blob/7.0/nailgun/nailgun/fixtures/openstack.yaml#L444-L577>`_, as result it generates sizes of spaces which should be allocated on the disks.

Current solution has `plenty of problems <https://blueprints.launchpad.net/bareon/+spec/dynamic-allocation>`_, it's hard and expensive to solve this problem in terms of old VolumeManager, because trivial algorithms and schema format don't allow us to extend it easily, handle all of the cases combined is not a trivial task to do if we try to solve the problem using brute-force.

List of terms
-------------
* **Disk** - a place where space can be allocated
* **Space** - an entity which can be allocated on several disks at once, a good example of a space is a `logical volume <https://en.wikipedia.org/wiki/Logical_Volume_Manager_(Linux)>`_ for lvm, another one is partition
* **Dynamic schema** - a schema without specific sizes, it's a schema which is used by user to specify partitioning schema without details
* **Static schema** - a schema for `Bareon <https://wiki.openstack.org/wiki/Bareon>`_ which requires exact space <-> disk mapping with exact size of each space

High level architecture
-----------------------

::

    +-------------------------+
    |                         |
    |  Dynamic schema parser  |
    |                         |
    +------------+------------+
                 |
                 |
    +------------v------------+
    |                         |
    |    Allocation solver    |
    |                         |
    +------------+------------+
                 |
                 |
    +------------v-------------+
    |                          |
    |    Solution convertor    |
    |                          |
    +--------------------------+

* **Dynamic schema parser** - parses an input from the user and prepares the data which can be consumed by Allocation solver
* **Allocation solver** - an algorithm which takes dynamic schema and produces a static schema
* **Solution convertor** - a result which is produced by solver, should be parsed and converted into `Bareon <https://wiki.openstack.org/wiki/Bareon>`_ consumable format, for example for `Logical Volume <https://en.wikipedia.org/wiki/Logical_Volume_Manager_(Linux)>`_ Solution convertor should generate a physical volume for each disk, where it's allocated

Dynamic schema parser
---------------------

In the current version we user flat schema, it's a list which consists dictionaries.

Basic syntax
~~~~~~~~~~~~

* **id** - id of a space
* **type** - type of a space, for example Volume Group or Logical Volume
* **max_size** - maximum size which is allowed for the space
* **min_size** - minimal size which is allowed for the space
* **size** - a static size, it's similar as to set for **min_size** and **max_size** the same value
* **contains** - is required for hierarchical spaces such as Volume Group

Also there are couple of different attributes, such as **mount**, **fs_type**, which are self-explanatory. A list of such attributes is not complete and may be easily extended in the future.

.. code-block:: yaml

    - id: os
      type: vg
      contains:
        - id: swap
        - id: root

    - id: root
      type: lv
      max_size: 10000
      min_size: 5000
      mount: /
      fs_type: ext4

    - id: swap
      type: lv
      size: 2000
      fs_type: swap


Dynamic parameters
~~~~~~~~~~~~~~~~~~

What if user wants to allocate a size of space based on some different parameter?
As an example lets consider a size of swap which has to be based on amount of RAM the node has.

.. code-block:: yaml

    ram: 4096
    disks:
      - id: /dev/disk/by-id/id-for-sda
        path: /dev/disk/by-path/path-for-sda
        dev: /dev/sda
        type: hdd
        vendor: Hitachi
        size: 5000

From Hardware Information example we can see that the node has 4096 megabytes of RAM, according to `best practises <https://access.redhat.com/documentation/en-US/Red_Hat_Enterprise_Linux/6/html/Installation_Guide/s2-diskpartrecommend-ppc.html>`_ on swap size allocation swap size has to be twice bigger than current RAM.

.. code-block:: yaml

    - id: swap
      type: lv
      size: 2000
      fs_type: swap
      size: |
        yaql=let(ram => $.get(ram, 1024)) ->
        selectCase(
          $ram <= 2048,
          $ram > 2048 and $ram < 8192,
          $ram > 8192 and $ram < 65536).
        switchCase(
          $ram * 2,
          $ram,
          $ram / 2,
          4096)

In order to implement an algorithm of swap size calculation we use `YAQL <https://github.com/openstack/yaql>`_, which is small but powerful enough query language. Any value of the parameter which matches to **yaql=yaql expression** will be evaluated using YAQL, execution result will be passed as is to the Solver.

Allocation solver
-----------------

By the name of the chapter it can be seen that we are going to solve something.

Lets try to generalize a problem of spaces allocation:

* there are constraints, for example size of a space cannot be bigger than size of all disks, or size of swap space cannot be bigger or smaller than **size** of the space
* there exists "the best allocation static schema", it's almost impossible to find what "the best" is, what we can do is to parse all constraint and find such an allocation which fits all the constraints, and at the same time uses given resources (disks) by maximum

Lets consider an example with two spaces and a single disk, parameters which don't affect allocation problem were removed to reduce the amount of unnecessary information.

Two space **root** and **swap**, for **swap** there is static size which is 10, for **root** the size should be at least 50.

.. code-block:: yaml

    - id: root
      min_size: 50

    - id: swap
      size: 10

A single ~10G disk.

.. code-block:: yaml

    disks:
      - id: sda
        size: 100

Also we can describe the same problem as:

.. math::

    \begin{cases}
    root + swap \le 100 \\
    root \ge 50 \\
    swap = 10
    \end{cases}

On disks with bigger sizes we can get a lot of solutions.

Lets consider two corner case solutions

.. math::

    root = 50, \quad swap = 10

and

.. math::

    root = 90, \quad swap = 10

Second one is better since it uses more disks resources and doesn't leave unallocated space.
So we should find a way to describe that second one is better.

It can be described with the next function.

.. math::

   Maximize: root + swap


Solver description
~~~~~~~~~~~~~~~~~~

The problem is described in terms of `Linear programming <https://en.wikipedia.org/wiki/Linear_programming>`_ (note that "programming" is being used in not computer-programming sense). The method is being widely used to solve optimal resources allocation problem which is exactly what we are trying to achieve during the allocation.

.. math::

    max\left\{cx : Ax \ge b\right\}

* **cx** - is an objective function for maximization
* **c** - a vector of coefficients for the values to be found
* **x** - a vector of result values
* **A** - coefficients matrix
* **b** - a vector, when combined with a row from matrix **A** gives as a constraint

Description of previous example in terms of Linear programming, is going to be pretty similar to what we did.

.. math::

   x_1 = root\\
   x_2 = swap\\[2ex]

Coefficients for objective function.

.. math::

   c = \begin{bmatrix}
   1 & 1
   \end{bmatrix}^{T}\\[2ex]

A vector of values to be found, i.e. sizes of spaces.

.. math::

   x = \begin{bmatrix}
   x_1 \\
   x_2
   \end{bmatrix}\\[2ex]

System of linear inequalities. Inequalities which are "less or equal" multiplied by -1 to make them "greater or equal".

.. math::

   Ax \ge b = \begin{cases}
    - x_1  - x_2 \ge -100 \\
    x_1 \ge 50 \\
    -x_2 \ge -10 \\
    x_2 \ge 10 \\
    x_1 \ge 0 \\
    x_2 \ge 0
   \end{cases}\\[2ex]

**A** and **b** written in matrix and vector form respectively.

.. math::

   A =  \begin{bmatrix}
   -1 & -1 \\
   1 & 0 \\
   0 & -1 \\
   0 & 1 \\
   1 & 0 \\
   0 & 1 \\
   \end{bmatrix}\\[2ex]

   b = \begin{bmatrix}
   -100 \\
   50 \\
   -10 \\
   10 \\
   0 \\
   0
   \end{bmatrix}\\[2ex]

In order to solve the problem `Scipy linprog <http://docs.scipy.org/doc/scipy-0.16.0/reference/generated/scipy.optimize.linprog.html>`_ module is being used. It uses `Simplex algorithm <https://en.wikipedia.org/wiki/Simplex_algorithm>`_ to find the most feasible solution.

So what allocator does is builds a matrix and couple of vectors and using Simplex algorithm gets the result.

Two disks
~~~~~~~~~

If we have two spaces and two disks variable we will have 4 unkown variables:

#. 1st space, 1st disk size
#. 2st space, 1st disk size
#. 1st space, 2st disk size
#. 2st space, 2st disk size

Spaces definition which was used previously.

.. code-block:: yaml

    - id: root
      min_size: 50

    - id: swap
      size: 10

And two disks.

.. code-block:: yaml

    disks:
      - id: sda
        size: 100
      - id: sdb
        size: 200

Resulting system of linear inequalities.

.. math::

   \begin{cases}
   x_1 + x_2 \le 100 \\
   x_3 + x_4 \le 200 \\
   x_1 + x_3 \ge 50 \\
   x_2 + x_4 = 10
   \end{cases}

* :math:`x_1 + x_2 \le 100` inequality for root and swap on the 1st disk
* :math:`x_3 + x_4 \le 200` inequality for root and swap on the 2nd disk
* :math:`x_1 + x_3 \ge 50` inequality for root space
* :math:`x_2 + x_4 = 10` equality for swap space

Integer solution
~~~~~~~~~~~~~~~~

By default result vector provides us with rational number vector solution.
Very naive way is being used to get integer soluton, we round the number down,
this solution may have problems because some of the constraints may be vaiolated
with respect to one megabyte.
Another side effect is we may get **N** megabytes unallocated in the worst case, where
**N** is an amount of spaces.
For our application purposes all above drawbacks are not so big, considering
a complexity of proper solution.

`Mixed integer programming <https://en.wikipedia.org/wiki/Integer_programming>`_ can
be used to get integer result, but the problem is the problem described in terms of
Integer programming may be NP-hard. So it should be considered carefully if it's worth
to be used.

Ordering
~~~~~~~~

It would be really nice to have the volumes allocated on the disks in the order which
was specified by the user.

Lets consider two spaces example.

.. code-block:: yaml

    - id: root
      size: 100

    - id: var
      size: 100

With two disks.

.. code-block:: yaml

    disks:
      - id: sda
        size: 100
      - id: sdb
        size: 100

Which can be represented as next inequality.

.. math::

    \begin{cases}
    x_1 + x_2 \le 100 \\
    x_3 + x_4 \le 100 \\
    x_1 + x_3 = 100 \\
    x_2 + x_4 = 100
    \end{cases}

And objective function.

.. math::

   Maximize: x_1 + x_2


So we may have two obvious solutions here:

#. var for 1st disk, root for 2nd
#. root for 1st disk, var for 2nd

Objective function is being used by the algorithm to decide, which solution
is "better". Currently all elements in coefficients vector are equal to 1

.. math::
   c = \begin{bmatrix}
   1 &
   1 &
   1 &
   1
   \end{bmatrix}^{T}`.

We can change coefficients in a way that first volume has higher coefficient than the last one.

.. math::

   c = \begin{bmatrix}
   4 &
   3 &
   2 &
   1
   \end{bmatrix}^{T}\\[2ex]

Now Linear Programming solver will try to maximize the solution with respect to specified order of spaces.

But it's not so simple, if we take a closer look at the results we may get.

Lets consider two solutions and calculate the results of objective function.

.. math::

   cx = \begin{bmatrix}
   100 &
   0 &
   0 &
   100
   \end{bmatrix}

   \begin{bmatrix}
   4 \\
   3 \\
   2 \\
   1
   \end{bmatrix} =

   \begin{bmatrix}
   400 \\
   0 \\
   0 \\
   100
   \end{bmatrix}\\[2ex]

   sum\{cx\} = 500

The result that objective function provides is **500**, if **root** is allocated on the first disk and **var** on second one.

.. math::

   cx = \begin{bmatrix}
   50 &
   50 &
   50 &
   50
   \end{bmatrix}

   \begin{bmatrix}
   4 \\
   3 \\
   2 \\
   1
   \end{bmatrix} =

   \begin{bmatrix}
   200 \\
   150 \\
   100 \\
   50
   \end{bmatrix}\\[2ex]

   sum\{cx\} = 500


The result that objective function provides is **500**, if **root** and **var** are allocated equally on both disks.

So we need a different monolitically increasing sequence of integers, which is increasing as slow as possible.

Also sequence must not violate next requirements.

.. math::

    n_{i+1} \gt n_i \\[2ex]
    n_{i} + n_{j+1} \gt n_{i+1} + n_{j}$ where $i+1 < j

It means that sum of ranges taken on the "lower side" of a sequence has to be always smaller than sum of range on "higher side".

In our example this requirement is violated

.. math::

   i = 1\\
   j = 3\\
   1 + 4 = 2 + 3

Such sequence has been `found <http://math.stackexchange.com/questions/1596496/finding-a-monotonically-increasing-sequence-of-integers/1596812>`_

.. math::

   1,2,4,6,9,12,16,20,25,30,36,42\cdots

there are `many ways <https://oeis.org/A002620>`_ to caculate such sequence, in our implementation next one is being used

.. math::

   a_n=\lfloor\frac {n+1}2\rfloor\lfloor\frac {n+2}2\rfloor

Lets use this sequence in our examples

.. math::

   cx = \begin{bmatrix}
   100 &
   0 &
   0 &
   100
   \end{bmatrix}

   \begin{bmatrix}
   6 \\
   4 \\
   2 \\
   1
   \end{bmatrix} =

   \begin{bmatrix}
   600 \\
   0 \\
   0 \\
   100
   \end{bmatrix}\\[2ex]

   sum\{cx\} = 700

And when **root** and **var** are allocated on both disks equally

.. math::

   cx = \begin{bmatrix}
   50 &
   50 &
   50 &
   50
   \end{bmatrix}

   \begin{bmatrix}
   6 \\
   4 \\
   2 \\
   1
   \end{bmatrix} =

   \begin{bmatrix}
   300 \\
   200 \\
   100 \\
   50
   \end{bmatrix}\\[2ex]

   sum\{cx\} = 650

Soo :math:`700 > 650` first function has greater maximization value, that is exactly what we need.

Weight
~~~~~~

Two spaces, no exact size specified.

.. code-block:: yaml

    - id: root
      size: 10

    - id: var
      size: 10

A single disk.

.. code-block:: yaml

    disks:
      - id: sda
        size: 100

According to coefficients of objective funciton with respect to ordering we will have the next allocation.

* **root** - 90
* **var** - 10

Which is not so obvious result for the user, the expected result would be to have the next allocation.

* **root** - 50
* **var** - 50

So for those spaces, which have the same **min_size**, **max_size** (and **best_with_disks** see next section),
allocator adds special equality to make sure that there is a fair allocation between spaces with same requirements.

Each space can have **weight** variable specified (**1** by default), which is used to make additional equality.

.. math::

    \begin{cases}
    x_1 + x_2 \le 100 \\
    x_3 + x_4 \le 200 \\
    x_1 + x_3 = 100 \\
    x_2 + x_4 = 100 \\
    x_2 * (1 / weight) + x_4 * (-1 / weight) = 0
    \end{cases}

To satisfy last equality, spaces have to be equal in size.
If it's required to have one space twice smaller than other one, it can be done by setting the weight variable.


.. code-block:: yaml

    - id: root
      size: 10
      weight: 1

    - id: var
      size: 10
      weight: 0.5

As result for **var** will be allocated twice smaller space on the disk.

Best with disks
~~~~~~~~~~~~~~~

User may want a space to be allocated on specific disk according to any attribute of a disk.

For example lets consider an example with **ceph-journal** which is better to allocate on **ssd** disks.

From user's perspective each space can have a new parameter **best_with_disks**, in order to fill in this parameter `YAQL <https://github.com/openstack/yaql>`_ can be used.

.. code-block:: yaml

    - id: ceph-journal
      best_with_disks: |
        yaql=$.disks.where($.type = "ssd")

    - id: root
      min_size: 10

.. code-block:: yaml

    disks:
      - id: sda
        size: 100
        type: hdd

      - id: sdb
        size: 10
        type: ssd


So in solver we get a list of **ssd** disks, if there are any.

Lets adjust coefficients to make ceph-journal to be allocated on ssd, as a second priority ordering should be respected.

In order to do that lets make order coefficient :math:`0 < order coefficient < 1`.

.. math::

   c = \begin{bmatrix}
   1 + (1/9) &
   0 + (1/6) &
   0 + (1/4) &
   1 + (1/2)
   \end{bmatrix}^{T}\\[2ex]
