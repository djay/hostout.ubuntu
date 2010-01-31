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


current_dir = os.path.abspath(os.path.dirname(__file__))
recipe_location = current_dir

for i in range(2):
    recipe_location = os.path.split(recipe_location)[0]


def run(host, client, env, cmd, **kvargs):
    return 'run'

def _connect():
    print "Connected"
    
    

class LocalSSH(ServerInterface, Thread):
    def __init__(self):
        Thread.__init__(self)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('127.0.0.1', 10022))
        self.key = ssh.RSAKey.generate(1024)

    def run(self):

        self.socket.listen(100)
        while True:
            self.socket.settimeout(15)
            s,addr = self.socket.accept()
            transport = Transport(s)
            transport.add_server_key(self.key)
            event = Event()
            #transport.set_subsystem_handler('', ShellHandler)
            transport.start_server(event, server=self)

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
#        f = channel.makefile('rU')
#        cmd = f.readline().strip('\r\n')
        channel.send("CMD RECIEVED\n")
        channel.send_exit_status(0)
        return True
    def check_channel_shell_request(self, channel):
            self.channel = channel
            self.fs = channel.makefile()
            return True
    def read(self):
        return self.fs.read()

localssh = LocalSSH()


def setUp(test):
    #zc.buildout.tests.easy_install_SetUp(test)
    zc.buildout.testing.buildoutSetUp(test)
    zc.buildout.testing.install_develop('collective.hostout', test)
    zc.buildout.testing.install('functools', test)
    zc.buildout.testing.install('Fabric', test)
    zc.buildout.testing.install('paramiko', test)
    zc.buildout.testing.install('pycrypto', test)
    zc.buildout.testing.install('zc.recipe.egg', test)
    zc.buildout.testing.install('mr.developer', test)
    
    localssh.start()
#    client  = ssh.SSHClient()
#    client.connect('127.0.0.1', 10022, 'root', None)


def tearDown(test):
    localssh.socket.close()





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
             package='collective.hostout',
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
