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
from socket import socket
from paramiko import Transport, ServerInterface, AUTH_SUCCESSFUL, OPEN_SUCCEEDED
import paramiko as ssh
from threading import Event, Thread


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
    zc.buildout.testing.install('paramiko', test)
    zc.buildout.testing.install('pycrypto', test)
    zc.buildout.testing.install('zc.recipe.egg', test)


class LocalSSH(ServerInterface, Thread):
    def __init__(self):
        Thread.__init__(self)
        self.socket = socket()
        self.socket.bind(('127.0.0.1', 10022))
        self.socket.listen(4)
        self.key = ssh.RSAKey.generate(160)

    def run(self):
        s,addr = self.socket.accept()
        t = Transport(s)
        t.add_server_key(self.key)
        e = Event()
        t.start_server(e, server=self)

    def get_allowed_auths(self, username):
        return "none,password,publickey"
    def check_auth_none(self, username):
        return AUTH_SUCCESSFUL
    def check_auth_password(self, username, password):
        return AUTH_SUCCESSFUL
    def check_auth_publickey(self, username, key):
        return AUTH_SUCCESSFUL
    def check_channel_request(self, kind, chanid):
        return OPEN_SUCCEEDED
    def check_channel_exec_request(self, channel, command):
        return True
    def check_channel_shell_request(self, channel):
            self.channel = channel
            self.fs = channel.makefile()
            return True
    def read(self):
        return self.fs.read()


localssh = LocalSSH()
localssh.start()
client  = ssh.SSHClient()
client.connect('localhost', 10022, 'root')


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
