#!/bin/bash

export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8

python bareon_dynamic_allocator/cmd.py --debug --schema etc/bareon-dynamic-allocator/simple_schema.yaml --file o.txt --hw-info etc/bareon-dynamic-allocator/example_2_disks.yaml
