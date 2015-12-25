===============================
bareon-dynamic-allocator
===============================

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

* user weight if max is not specified
* if min and max for several spaces are the same, consider using weight
* create special types, like lv_mirror with special policy to allocate volume
  of the same size over several disks
* research on YAQL in order to filter the disks by some criteria
