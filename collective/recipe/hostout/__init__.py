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
        self.versions_part = buildout['buildout'].get('versions_part','versions')
        self.buildout = buildout

        #get all recipes here to make sure we're the last called
        self.getAllRecipes()

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
        self.user = self.options.get('user','')
        self.identityfile = self.options.get('identityfile','')
        self.effectiveuser = self.options.get('effective-user','plone')
        self.host = self.options['host']
        self.password = options.get('password','')
        self.start_cmd = options.get('start_cmd','')
        self.stop_cmd = options.get('stop_cmd', '')
        #replace any references to the localbuildout dir with the remote buildout dir
        self.remote_dir = self.options.get('remote_path','~%s/buildout'%self.user)
        self.stop_cmd = self.stop_cmd.replace(buildout['buildout']['directory'],self.remote_dir)
        self.start_cmd = self.start_cmd.replace(buildout['buildout']['directory'],self.remote_dir)
        self.extra_config = self.options.get('extra_config','')


    def install(self):
        logger = logging.getLogger(self.name)

        requirements, ws = self.egg.working_set()
        options = self.options
        location = options['location']
        from os.path import dirname, abspath
        if not os.path.exists(location):
            os.mkdir(location)
        #fabfile = template % (self.name, [host], base)
        #fname = join(location,'fabfile.py')
        #open(fname, 'w+').write(fabfile)
        extra_paths=[]
        self.develop = [p.strip() for p in self.buildout.get('buildout').get('develop').split()]
        packages = self.develop + self.options.get('packages','').split()
        config_file = self.buildout_cfg


        hostout = self.genhostout()

        args = 'effectiveuser="%s",\
        remote_dir=r"%s",\
        dist_dir=r"%s",\
        packages=%s,\
        buildout_location="%s",\
        host="%s",\
        user=r"%s",\
        password=r"%s",\
        identityfile="%s",\
        config_file="%s",\
        extra_config="%s",\
        start_cmd="%s",\
        stop_cmd="%s"'%\
                (
                 self.effectiveuser,
                 self.remote_dir,
                 self.dist_dir,
                 str(packages),
                 self.buildout_dir,
                 self.host,
                 self.user,
                 self.password,
                 self.identityfile,
                 hostout,
                 self.extra_config,
                 self.start_cmd,
                 self.stop_cmd
                 )


        zc.buildout.easy_install.scripts(
                [(self.name, 'collective.recipe.hostout.hostout', 'main')],
                ws, options['executable'], options['bin-directory'],
                arguments=args,
                extra_paths=extra_paths
#                initialization=address_info,
#                arguments='host, port, socket_path', extra_paths=extra_paths
                )



        return location

    def update(self):
        return self.install()


    def genhostout(self):
        """ generate a new buildout file which pins versions and uses our deployment distributions"""


        base = self.buildout_dir
        dist_dir = os.path.abspath(os.path.join(self.buildout_dir,self.dist_dir))
        if not os.path.exists(dist_dir):
            os.makedirs(dist_dir)

        buildoutfile = relpath(self.buildout_cfg, base)
        dist_dir = relpath(self.dist_dir, base)
        versions = self.getversions()
        #versions = ""
        install_base = os.path.dirname(self.remote_dir)
        buildout_cache = os.path.join(install_base,'buildout-cache')
        hostout = HOSTOUT_TEMPLATE % dict(buildoutfile=buildoutfile,
                                          eggdir=dist_dir,
                                          versions=versions,
                                          buildout_cache=buildout_cache,
                                          versions_part = self.versions_part)
        path = os.path.join(base,'hostout.cfg')
        hostoutf = open(path,'w')
        hostoutf.write(hostout)
        hostoutf.close()
        return path

    def getAllRecipes(self):
        recipes = []
        for part in [p.strip() for p in self.buildout['buildout']['parts'].split()]:
            options = self.buildout.get(part)
            if not options.get('recipe'):
                continue
            try:
                recipe,subrecipe = options['recipe'].split(':')
            except:
                recipe=options['recipe']
            recipes.append((recipe,options))
        return recipes

    def getversions(self):
        versions = {}
        for recipe, options in self.getAllRecipes():
            egg = zc.recipe.egg.Egg(self.buildout, recipe, options)
            #TODO: need to put in recipe versions too
            requirements, ws = egg.working_set()
            for dist in ws.by_key.values():
                project_name =  dist.project_name
                version = dist.version
                old_version,dep = versions.get(project_name,('',[]))
                if recipe not in dep:
                    dep.append(recipe)
                versions[project_name] = (version,dep)
        spec = ""
        for project_name,info in versions.items():
            version,deps = info
            spec+='\n'
            for dep in deps:
                spec+='# Required by %s==%s\n' % (dep, 'Not Implemented') #versions[dep][0])
            if version != '0.0':
                spec+='%s = %s' % (project_name,version)+'\n'
            else:
                spec+='#%s = %s' % (project_name,version)+'\n'
        return spec



HOSTOUT_TEMPLATE = """
[buildout]
extends = %(buildoutfile)s

#Our own packaged eggs
find-links +=
    %(eggdir)s

#prevent us looking for them as developer eggs
develop=

#Match to unifiedinstaller
eggs-directory = %(buildout_cache)s/eggs
download-cache = %(buildout_cache)s/downloads

versions=%(versions_part)s
#non-newest set because we know exact versions we want
#newest=false
[%(versions_part)s]
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

