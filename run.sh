#!/bin/bash

export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8

python bareon_allocator/cmd.py --svg-file /tmp/bareon.svg --debug --schema etc/bareon-allocator/simple_schema.yaml --file o.txt --hw-info etc/bareon-allocator/example_2_disks.yaml
