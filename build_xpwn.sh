#!/bin/sh

cd "$(dirname "$0")"

git submodule init

cd xpwn

mkdir build

cd build

cmake ..
make
