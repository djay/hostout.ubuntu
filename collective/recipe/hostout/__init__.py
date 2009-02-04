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
import sha
import shutil
import zc.buildout
from os.path import join
import os

def system(c):
    if os.system(c):
        raise SystemError("Failed", c)

class Recipe:

    def __init__(self, buildout, name, options):
        self.egg = zc.recipe.egg.Egg(buildout, options['recipe'], options)
        self.name, self.options = name, options
        directory = buildout['buildout']['directory']
        self.download_cache = buildout['buildout'].get('download-cache')
        self.install_from_cache = buildout['buildout'].get('install-from-cache')
        self.buildout = buildout

        if self.download_cache:
            # cache keys are hashes of url, to ensure repeatability if the
            # downloads do not have a version number in the filename
            # cache key is a directory which contains the downloaded file
            # download details stored with each key as cache.ini
            self.download_cache = os.path.join(
                directory, self.download_cache, 'cmmi')

        # we assume that install_from_cache and download_cache values
        # are correctly set, and that the download_cache directory has
        # been created: this is done by the main zc.buildout anyway

        options['location'] = os.path.join(
            buildout['buildout']['parts-directory'],
            self.name,
            )
        options['bin-directory'] = buildout['buildout']['bin-directory']
        self.dist_dir = options['dist_dir'] = dist_dir = self.options.get('dist_dir','dist')
        self.buildout_dir = self.buildout.get('buildout').get('directory')
        self.buildout_cfg = options['buildout'] = options.get('buildout','buildout.cfg')

    def install(self):
        logger = logging.getLogger(self.name)
        user = self.options.get('user','plone')
        remote_dir = self.options.get('buildout_dir','~%s/buildout'%user)
        host = self.options['host']
        #import pdb; pdb.set_trace()
        
        requirements, ws = self.egg.working_set()
        options = self.options
        location = options['location']
        from os.path import dirname, abspath
        here = abspath(dirname(__file__))
        base = join(here,'fabfile.py')
        if not os.path.exists(location):
            os.mkdir(location)
        fabfile = template % (self.name, [host], base)
        fname = join(location,'fabfile.py')
        open(fname, 'w+').write(fabfile)
        extra_paths=[]
        packages = [p.strip() for p in self.buildout.get('buildout').get('develop').split()]
        #for package in self.options['buildout']['develop']:
        #    extra_paths+=[package]
        #extra_paths.append(os.path.join('c:\\python25'))
        #options['executable'] = 'c:\\Python25\\python.exe'

#        buildoutroot = os.getcwd()
        
        hostout = self.genhostout()
        
        args = 'fabfile=r"%s",user=r"%s",remote_dir=r"%s",dist_dir=r"%s",packages=%s,buildout_location="%s",config_file="%s"'%\
                (fname,user,remote_dir,self.dist_dir, str(packages), self.buildout_dir, hostout)
                
        
        zc.buildout.easy_install.scripts(
                [(self.name, 'collective.recipe.hostout.hostout', 'main')],
                ws, options['executable'], options['bin-directory'],
                arguments=args,
                extra_paths=extra_paths
#                initialization=address_info,
#                arguments='host, port, socket_path', extra_paths=extra_paths
                )


        # now unpack and work as normal
        tmp = tempfile.mkdtemp('buildout-'+self.name)
#        logger.info('Unpacking and configuring')
#        setuptools.archive_util.unpack_archive(fname, tmp)

#        here = os.getcwd()
#        if not os.path.exists(dest):
#            os.mkdir(dest)


        return location

    def update(self):
        return self.install()


    def genhostout(self):
        """ generate a new buildout file which pins versions and uses our deployment distributions"""

    
        base = self.buildout_dir
        buildoutfile = relpath(self.buildout_cfg, base)
        dist_dir = relpath(self.dist_dir, base)
        versions = ''
        hostout = HOSTOUT_TEMPLATE % dict(buildoutfile=buildoutfile,
                                          eggdir=dist_dir,
                                          versions=versions)
        path = os.path.join(base,'hostout.cfg')     
        hostoutf = open(path,'w')
        hostoutf.write(hostout)
        hostoutf.close()
        return path
                        
        

HOSTOUT_TEMPLATE = """
[buildout]
extends=%(buildoutfile)s
#versions=versions
find-links+=%(eggdir)s

[versions]
%(versions)s
"""



    


template = """
set(
        project = '%s',
        fab_hosts = %s,
)
load(r'%s')
"""    


# relpath.py
# R.Barran 30/08/2004

import os

def relpath(target, base=os.curdir):
    """
    Return a relative path to the target from either the current dir or an optional base dir.
    Base can be a directory specified either as absolute or relative to current dir.
    """

    if not os.path.exists(target):
        raise OSError, 'Target does not exist: '+target

    if not os.path.isdir(base):
        raise OSError, 'Base is not a directory or does not exist: '+base

    base_list = (os.path.abspath(base)).split(os.sep)
    target_list = (os.path.abspath(target)).split(os.sep)

    # On the windows platform the target may be on a completely different drive from the base.
    if os.name in ['nt','dos','os2'] and base_list[0] <> target_list[0]:
        raise OSError, 'Target is on a different drive to base. Target: '+target_list[0].upper()+', base: '+base_list[0].upper()

    # Starting from the filepath root, work out how much of the filepath is
    # shared by base and target.
    for i in range(min(len(base_list), len(target_list))):
        if base_list[i] <> target_list[i]: break
    else:
        # If we broke out of the loop, i is pointing to the first differing path elements.
        # If we didn't break out of the loop, i is pointing to identical path elements.
        # Increment i so that in all cases it points to the first differing path elements.
        i+=1

    rel_list = [os.pardir] * (len(base_list)-i) + target_list[i:]
    return os.path.join(*rel_list)

    