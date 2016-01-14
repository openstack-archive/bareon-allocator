#!/bin/bash

set -eux

export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8

rm -rf build/doc || true
python doc_generate_static.py
python setup.py build_sphinx
