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

import logging, os, shutil, tempfile, urllib2, urlparse
import setuptools.archive_util
import datetime

import zc.buildout
import fabric
import tarfile
import sys
from zc.buildout import buildout
from os.path import join

def package_buildout(config_file):
    "determine all the buildout files that make up this configuration and package them"
    config_file = os.path.abspath(config_file)
    base = os.path.dirname(config_file)
    if not os.path.exists(config_file):
        raise "Invalid config file"

    files = []
    config = buildout._open(base,config_file, files)
    tar = tarfile.open('projectrelease.1',"w:gz")
    for file in files:
        tar.add(file)
    tar.close()
    
    
    #get all files and put them in a tar
    
def pin_versions(fname):
    "create a .hostoutVersions.cfg which contains the pinned versions"
    
def gen_hostout(fname):
    "create a main buildout file which pins versions"


def release_eggs(deveggs):
    "developer eggs->if changed, increment versions, build and get ready to upload"
    #python setup.py sdist bdist_egg

template = """
[buildout]
extends=%(buildoutfile)
versions=versions
find-links+=%(eggdir)

[versions]
%(versions)
"""

def main(fabfile='fabfile.py',user='plone',remote_dir='buildout',buildout_file='buildout.cfg',dist_dir='dist'):
    "execute the fabfile we generated"
    
    from os.path import dirname, abspath
    here = abspath(dirname(__file__))
    
    
    package_buildout(buildout_file)
    args = ['deploy:user=%s,remote_dir=%s'%(user,remote_dir)]
    try:
        try:
            fabric._load_default_settings()
            #fabfile = _pick_fabfile()
            fabric.load(fabfile, fail='warn')
            commands = fabric._parse_args(args)
            fabric._validate_commands(commands)
            fabric._execute_commands(commands)
        finally:
            fabric._disconnect()
        print("Done.")
    except SystemExit:
        # a number of internal functions might raise this one.
        raise
    except KeyboardInterrupt:
        print("Stopped.")
        sys.exit(1)
    except:
        sys.excepthook(*sys.exc_info())
        # we might leave stale threads if we don't explicitly exit()
        sys.exit(1)
    sys.exit(0)
 
     
        
        