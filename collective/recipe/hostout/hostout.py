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
import ConfigParser
import sys
from zc.buildout import buildout
from os.path import join, exists
from collective.releaser import project
from itertools import chain
import re



"""
1. ensure we are on trunk and up to date somehow.
1. Find any dependencies that need a new release and increment the version and create a distribution 
1. create a hostout.cfg which is a repeatable buildout which is pinned for deployment by listing all
of all the eggs.
2. version this + all dev dependencies with a tag so can recover this version.
4. bundle the cfg up + eggs (maybe just dev eggs)
5. send to host
6. setup host it need be
7. overwrite with bundle and build
"""

def clean(lines):
        return [l.strip() 
                for l in lines.split('\n') if l.strip() != '']
_isurl = re.compile('([a-zA-Z0-9+.-]+)://').match


def get_all_extends(cfgfile):
    if _isurl(cfgfile):
        return []
    
    config = ConfigParser.ConfigParser()
    config.read([cfgfile])
    files = [cfgfile]
    if not 'buildout' in config.sections():
        return files
    if not 'extends' in config.options('buildout'):
        return files
    extends = chain(*[el.split() for el in clean(config.get('buildout', 'extends'))])
    curdir = os.path.dirname(cfgfile)
    for extend in extends:
        if not _isurl(extend):
            extend = os.path.join(curdir, extend)
        files.extend(get_all_extends(extend))
    return files



def package_buildout(buildout_location, config_file, folder='dist', filename='buildout', dev_packages=[]):
    "determine all the buildout files that make up this configuration and package them"
    import pdb;pdb.set_trace()
    folder = os.path.abspath(os.path.join(buildout_location,folder))
    
    config_file = os.path.abspath(os.path.join(buildout_location,config_file))
    base = os.path.dirname(config_file)
    if not os.path.exists(config_file):
        raise "Invalid config file"

    files = get_all_extends(config_file)
    
    if not os.path.exists(folder):
        os.makedirs(folder)
    tar = tarfile.open('%s/%s_1.tgz'%(folder,filename),"w:gz")
    for file in files:
        relative = file[len(buildout_location)+1:] #TODO
        tar.add(file,arcname=relative)
    tar.close()
    
    #tarball = '%s/%s_1.tgz'%(folder,filename+'re')
    #project.project_eggs(cfg=config_file, tarball=tarball)
    
    
    #get all files and put them in a tar
    
def pin_versions(fname):
    "create a .hostoutVersions.cfg which contains the pinned versions"




def release_eggs(deveggs):
    "developer eggs->if changed, increment versions, build and get ready to upload"
    # first get list of deveelop packages we got from recipe
    # for each package
    #   
    
    #python setup.py sdist bdist_egg


def main(fabfile='fabfile.py',
         user='plone',
         remote_dir='buildout',
         buildout_file='buildout.cfg',
         dist_dir='dist', 
         packages=[],
         buildout_location='',
         config_file='hostout.cfg'):
    "execute the fabfile we generated"
    
    from os.path import dirname, abspath
    here = abspath(dirname(__file__))
    
    
    package_buildout(buildout_location, config_file, dist_dir, dev_packages=packages)
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
 
     
        
        