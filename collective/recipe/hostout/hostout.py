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
from zc.buildout.buildout import Buildout
from paramiko import DSSKey, PKey


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

class HostOut:
    def __init__(self,
                 buildout_location,
                 dist_dir,
                 buildout_file,
                 config_file,
                 packages):
    
        self.buildout_location = buildout_location
        self.dist_dir = dist_dir
        self.buildout_file = buildout_file
        self.config_file = config_file
        self.packages = packages
        dist_dir = os.path.abspath(os.path.join(self.buildout_location,self.dist_dir))
        if not os.path.exists(dist_dir):
            os.makedirs(dist_dir)
        self.tar = None
        
    def getDeployTar(self):
        dist_dir = os.path.abspath(os.path.join(self.buildout_location,self.dist_dir))
        name = '%s/%s_1.tgz'%(dist_dir,'deploy')
        if self.tar is None:
            if os.path.exists(name):
                os.remove(name)
            self.tar = tarfile.open(name,"w:gz")
        return self.tar,name #TODO: need to give it a version

    
    def package_buildout(self):
        "determine all the buildout files that make up this configuration and package them"
        folder = self.dist_dir
        
        dist_dir = os.path.abspath(os.path.join(self.buildout_location,self.dist_dir))
        config_file = os.path.abspath(os.path.join(self.buildout_location,self.config_file))
        base = os.path.dirname(config_file)
        if not os.path.exists(config_file):
            raise "Invalid config file"
    
        files = get_all_extends(config_file)
        
        tar,tarname = self.getDeployTar()
        
        for file in files:
            relative = file[len(self.buildout_location)+1:] #TODO
            tar.add(file,arcname=relative)
        
        #tarball = '%s/%s_1.tgz'%(folder,filename+'re')
        #project.project_eggs(cfg=config_file, tarball=tarball)
        
        
        #get all files and put them in a tar
        
    def pin_versions(self,fname):
        "create a .hostoutVersions.cfg which contains the pinned versions"
    
    
    
    
    def release_eggs(self):
        "developer eggs->if changed, increment versions, build and get ready to upload"
        # first get list of deveelop packages we got from recipe
        # for each package
        #   
        
        #python setup.py sdist bdist_egg
        tmpdir = tempfile.mkdtemp()
        localdist_dir = os.path.abspath(os.path.join(self.buildout_location,self.dist_dir))
        import pdb; pdb.set_trace()
        
        buildout = Buildout(self.buildout_file,[])
        for path in self.packages:
            
            # use buildout to run setup for us
            if os.path.isdir(path):
                buildout.setup(args=[path,'clean','egg_info', '-RD','sdist','--dist-dir', '%s'%tmpdir ])
            else:
                shutil.copy(path,tmpdir)
        tar,tarname = self.getDeployTar()

        for dist in os.listdir(tmpdir):
            src = os.path.join(tmpdir,dist)
            tar.add(src, arcname=os.path.join(self.dist_dir,dist))
            tgt = os.path.join(localdist_dir,dist)
            if os.path.exists(tgt):
                os.remove(tgt)
            os.rename(src, tgt)
        os.removedirs(tmpdir)
        
    def getDSAKey(self):
        keyfile = os.path.abspath(os.path.join(self.buildout_location,'hostout_dsa'))
        if not os.path.exists(keyfile):
            key = DSSKey.generate()
            key.write_private_key_file(keyfile)
        else:
            key = PKey.from_private_key_file(DSSKey, keyfile)
        return keyfile, str(key)
            
        

def runfabric(fabfile, args):            
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
        return False
#    except:
#        sys.excepthook(*sys.exc_info())
#        # we might leave stale threads if we don't explicitly exit()
#        return False
    return True


def main(fabfile='fabfile.py',
         user='root',
         password=None,
         effectiveuser='plone',
         remote_dir='buildout',
         buildout_file='buildout.cfg',
         dist_dir='dist', 
         packages=[],
         buildout_location='',
         config_file='hostout.cfg'):
    "execute the fabfile we generated"
    
#    from os.path import dirname, abspath
#    here = abspath(dirname(__file__))
    
    hostout = HostOut(buildout_location,
                      dist_dir,
                      buildout_file,
                      config_file,
                      packages)

    hostout.release_eggs()
    hostout.package_buildout()
    tar,package = hostout.getDeployTar()
    tar.close()
    dir,package = os.path.split(package)
    
    if remote_dir[0] not in ['/','~']:
        remote_dir = '~%s/%s' %(remote_dir,effective_user)
    
    args = ['deploy:user=%s,remote_dir=%s,dist_dir=%s,package=%s'%(user,remote_dir,dist_dir,package)]
    runfabric(fabfile, args)
 
     
        
        