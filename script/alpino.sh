#!/usr/bin/env bash

set -e
set -x

# This script installs a local copy of Alpino for Travis. This is done in a
# separate script to keep the Travis configuration clean. We can't use Rake as
# this script is executed _before_ installing the Ruby dependencies.

wget --quiet https://s3-eu-west-1.amazonaws.com/opener/alpino/Alpino-x86_64-linux-glibc2.5-20522-sicstus.tar.gz

tar -xvf Alpino-x86_64-linux-glibc2.5-20522-sicstus.tar.gz
