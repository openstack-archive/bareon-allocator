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

Future Improvments
------------------

* create special types, like lv_mirror with special policy to allocate volume of the same size over several disks
* implement less or equal instead of equal for disk size constraint in this case artificial Unallocated space is not going to be required
