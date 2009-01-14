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

    def install(self):
        logger = logging.getLogger(self.name)
        user = self.options.get('user','plone')
        remote_dir = self.options.get('buildout_dir','~%s/buildout'%user)
        dist_dir = self.options.get('dist_dir','dist')
        host = self.options['host']
        
        requirements, ws = self.egg.working_set()
        options = self.options
        location = options['location']
        here = os.getcwd()
        from os.path import dirname, abspath
        here = abspath(dirname(__file__))
        base = join(here,'fabfile.py')
        if not os.path.exists(location):
            os.mkdir(location)
        fabfile = template % (self.name, [host], base)
        fname = join(location,'fabfile.py')
        open(fname, 'w+').write(fabfile)
        extra_paths=[]
        extra_paths.append(os.path.join('c:\\python25'))
        options['executable'] = 'c:\\Python25\\python.exe'
        zc.buildout.easy_install.scripts(
                [(self.name, 'collective.recipe.hostout.hostout', 'main')],
                ws, options['executable'], options['bin-directory'],
                arguments='fabfile=r"%s",user=r"%s",remote_dir=r"%s",dist_dir=r"%s"'%\
                (fname,user,remote_dir,dist_dir),
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



template = """
let(
        project = '%s',
        fab_hosts = %s,
)
load(r'%s')
"""        