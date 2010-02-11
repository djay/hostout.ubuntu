#!/bin/sh

# Now make and install a local python that is well tested with Repoze
PYBASE=/opt
VERSION=2.6.2
cd
mkdir -p tmp
mkdir -p $PYBASE
cd tmp
wget -nv http://python.org/ftp/python/$VERSION/Python-$VERSION.tgz
tar xzf Python-$VERSION.tgz
cd Python-$VERSION
make clean
./configure   --prefix=$PYBASE/Python-$VERSION
make
make install
PP=$PYBASE/Python-$VERSION/bin/python
PB=$PYBASE/Python-$VERSION/bin
