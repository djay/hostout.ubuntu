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
import socket
from paramiko import Transport, ServerInterface, AUTH_SUCCESSFUL, OPEN_SUCCEEDED
import paramiko
import paramiko as ssh
from threading import Event, Thread
import fabric
from collective.hostout.tests import LocalSSH


current_dir = os.path.abspath(os.path.dirname(__file__))
recipe_location = current_dir

for i in range(2):
    recipe_location = os.path.split(recipe_location)[0]


def setUp(test):
    #zc.buildout.tests.easy_install_SetUp(test)
    zc.buildout.testing.buildoutSetUp(test)
    zc.buildout.testing.install('collective.hostout', test)
    zc.buildout.testing.install('hostout.ubuntu', test)
    
    zc.buildout.testing.install('Fabric', test)
    zc.buildout.testing.install('paramiko', test)
    zc.buildout.testing.install('pycrypto', test)
    zc.buildout.testing.install('zc.recipe.egg', test)
    
    test.localssh = LocalSSH(9022)
    
    test.localssh.start()
#    client  = ssh.SSHClient()
#    client.connect('127.0.0.1', 10022, 'root', None)


def tearDown(test):
    test.localssh.socket.close()





def add(tar, name, src, mode=None):
    info.size = len(src)
    if mode is not None:
        info.mode = mode
    tar.addfile(info, StringIO.StringIO(src))



def test_suite():

    globs = globals()
    flags = optionflags = doctest.ELLIPSIS | doctest.REPORT_ONLY_FIRST_FAILURE | \
                        doctest.NORMALIZE_WHITESPACE | doctest.REPORT_UDIFF


    return unittest.TestSuite((
        #doctest.DocTestSuite(),
        doctest.DocFileSuite(
            'README.txt',
             package='hostout.ubuntu',
            setUp=setUp, tearDown=tearDown,
            optionflags = flags,
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
