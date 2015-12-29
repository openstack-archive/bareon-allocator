========================
bareon-dynamic-allocator
========================

A driver for Bareon for dynamic allocation of volumes

Please feel here a long description which must be at least 3 lines wrapped on
80 cols, so that distribution package maintainers can use it in their packages.
Note that this is a hard requirement.

* Free software: Apache license
* Documentation: http://docs.openstack.org/developer/bareon-dynamic-allocator
* Source: http://git.openstack.org/cgit/openstack/bareon-dynamic-allocator
* Bugs: http://bugs.launchpad.net/bareon

Features
--------

* TODO

Future Improvments
------------------

* user weight if max is not specified [DONE]
* if min and max for several spaces are the same, consider using weight (DONE, but only for max, better design for min is required)
* improve weight algorithm, use weights only if minimal size of one disk is not bigger than maximal size of another, otherwise we should notify user about the error
* research on YAQL in order to filter the disks by some criteria
* we should automatically add Unallocate volume with no constraints, so user can specify volumes with maximal sizes, and the rest of the space will be allocated for Unallocate
* create special types, like lv_mirror with special policy to allocate volume of the same size over several disks
* add integer constraints (the problem can be solved with integer programming, but it may lead to situation when there are no feasible solution, so for our practical purpose we are going to use naive implementation which is rounding of resulting vectos `x`)
* as a user I should be able to define a single disk partition (http://math.stackexchange.com/questions/1460350/formulation-of-mutually-exclusive-condition, http://people.brunel.ac.uk/~mastjjb/jeb/or/moreip.html)
