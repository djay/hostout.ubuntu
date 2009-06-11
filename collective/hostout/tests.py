##############################################################################
#
# Copyright (c) 2006 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

import os, re, StringIO, sys, tarfile
import zc.buildout.testing

import unittest
import doctest
import zope.testing
from zope.testing import renormalizing
from zc.buildout.tests import easy_install_SetUp
from zc.buildout.tests import normalize_bang
import os

current_dir = os.path.abspath(os.path.dirname(__file__))
recipe_location = current_dir

for i in range(2):
    recipe_location = os.path.split(recipe_location)[0]


def setUp(test):
    #zc.buildout.tests.easy_install_SetUp(test)
    zc.buildout.testing.buildoutSetUp(test)
    zc.buildout.testing.install_develop('collective.hostout', test)
    zc.buildout.testing.install('functools', test)
    zc.buildout.testing.install('Fabric<0.1.0', test)
    zc.buildout.testing.install('paramiko==1.7.4', test)
    zc.buildout.testing.install('pycrypto==2.0.1', test)
    zc.buildout.testing.install('zc.recipe.egg', test)



def add(tar, name, src, mode=None):
    info.size = len(src)
    if mode is not None:
        info.mode = mode
    tar.addfile(info, StringIO.StringIO(src))



def test_suite():

    globs = globals()


    return unittest.TestSuite((
        #doctest.DocTestSuite(),
        doctest.DocFileSuite(
            'README.txt',
             package='collective.hostout',
            setUp=setUp, tearDown=zc.buildout.testing.buildoutTearDown,
            optionflags = doctest.ELLIPSIS | doctest.REPORT_ONLY_FIRST_FAILURE |
                        doctest.NORMALIZE_WHITESPACE,
                        globs=globs,
            checker=renormalizing.RENormalizing([
               zc.buildout.testing.normalize_path,
               #zc.buildout.testing.normalize_script,
               #zc.buildout.testing.normalize_egg_py,
               #zc.buildout.tests.normalize_bang,
               ]),
            ),


        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
