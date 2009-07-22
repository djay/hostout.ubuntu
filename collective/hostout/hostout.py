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
from itertools import chain
import re
from zc.buildout.buildout import Buildout
from paramiko import DSSKey, PKey
from paramiko import SSHConfig

import time, random, md5
from collective.hostout import relpath



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
    def __init__(self, name, opt, packages):

        self.buildout_dir = packages.buildout_location
        self.dist_dir = packages.dist_dir
        self.packages = packages

        self.name = name
        self.effective_user = opt['effective-user']
        self.remote_dir = opt['remote_path']
        self.host = opt['host']
        self.user = opt['user']
        self.password = opt['password']
        self.identityfile = opt['identity_file']
        #create new buildout so we can analyse the working set.
        self.start_cmd = opt['start_cmd']
        self.stop_cmd = opt['stop_cmd']
        self.extra_config = opt['extra_config']
        self.buildout_cfg = opt['buildout']
        self.versions_section = opt['versions']

        #self.packages = opt['packages']
        #dist_dir = os.path.abspath(os.path.join(self.buildout_location,self.dist_dir))
        #if not os.path.exists(dist_dir):
        #    os.makedirs(dist_dir)
        #self.tar = None


    def getDeployTar(self):
        return self.packages.getDeployTar()


    def package_buildout(self):
        "determine all the buildout files that make up this configuration and package them"
        folder = self.dist_dir

        dist_dir = self.packages.dist_dir
        #config_file = os.path.abspath(os.path.join(self.buildout_location,self.config_file))
        config_file = self.genhostout()
        base = os.path.dirname(config_file)
        if not os.path.exists(config_file):
            raise "Invalid config file"

        files = get_all_extends(config_file)
        files += self.extra_config

        tar,tarname = self.packages.release_eggs()

        self.packages.writeVersions(config_file)


        for file in files:
            relative = file[len(self.buildout_dir)+1:] #TODO
            tar.add(file,arcname=relative)


    def pin_versions(self,fname):
        "create a .hostoutVersions.cfg which contains the pinned versions"



    def getDSAKey(self):
        keyfile = os.path.abspath(os.path.join(self.buildout_location,'hostout_dsa'))
        if not os.path.exists(keyfile):
            key = DSSKey.generate()
            key.write_private_key_file(keyfile)
        else:
            key = PKey.from_private_key_file(DSSKey, keyfile)
        return keyfile, str(key)

    def readsshconfig(self):
        config = os.path.expanduser('~/.ssh/config')
        if not os.path.exists(config):
            return
        f = open(config,'r')
        sshconfig = SSHConfig()
        sshconfig.parse(f)
        f.close()
        host = self.host
        try:
            host,port = host.split(':')
        except:
            port = None
        opt = sshconfig.lookup(host)

        if port is None:
            port = opt.get('port')

        host = opt.get('hostname', host)
        if port:
            host = "%s:%s" % (host,port)
        self.host=host
        if not self.identityfile:
            self.identityfile = opt.get('identityfile',None)
            if self.identityfile:
                self.identityfile = os.path.expanduser(self.identityfile).strip()
        if not self.user:
            self.user=opt.get('user','root')



    def runfabric(self):
        if self.remote_dir[0] not in ['/','~']:
            remote_dir = '~%s/%s' %(self.remote_dir,self.effective_user)

 #       args = (self.user,self.password,self.identityfile,self.remote_dir,self.dist_dir,self.packages)
 #       args = ['deploy:user=%s,password=%s,identityfile=%s,remote_dir=%s,dist_dir=%s,package=%s'%args]
        tar,package = self.getDeployTar()
        tar.close()
        dir,package = os.path.split(package)

        from pkg_resources import resource_string, resource_filename
        fabfile = resource_filename(__name__, 'fabfile.py')

        #here = os.path.abspath(os.path.dirname(__file__))
        #fabfile = os.path.join(here,'fabfile.py')

        try:
            try:

                fabric._load_default_settings()
                fabric.load(fabfile, fail='warn')
                cmd = fabric.COMMANDS['deploy']
                cmd(self, package)
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

    def genhostout(self):
        """ generate a new buildout file which pins versions and uses our deployment distributions"""


        base = self.buildout_dir

        buildoutfile = relpath(self.buildout_cfg, base)
        dist_dir = relpath(self.dist_dir, base)
        versions = self.packages.versions
        #versions = ""
        install_base = os.path.dirname(self.remote_dir)
        buildout_cache = os.path.join(install_base,'buildout-cache')
        hostout = HOSTOUT_TEMPLATE % dict(buildoutfile=buildoutfile,
                                          eggdir=dist_dir,
                                          versions=versions,
                                          buildout_cache=buildout_cache,
                                          versions_part = self.versions_section)
        path = os.path.join(base,'%s.cfg'%self.name)
        hostoutf = open(path,'w')
        hostoutf.write(hostout)
        hostoutf.close()
        return path


HOSTOUT_TEMPLATE = """
[buildout]
extends = %(buildoutfile)s

#Our own packaged eggs
find-links += %(eggdir)s

#prevent us looking for them as developer eggs
develop=

#Match to unifiedinstaller
#eggs-directory = %(buildout_cache)s/eggs
#download-cache = %(buildout_cache)s/downloads

versions=%(versions_part)s
#non-newest set because we know exact versions we want
#newest=false
[%(versions_part)s]
%(versions)s
"""



import zc.buildout.easy_install
from zc.buildout.buildout import pkg_resources_loc


class Packages:
    """ responsible for packaging the development eggs ready to be released to each host"""

    def __init__(self, config):
        self.packages = packages = [p for p in config.get('buildout','packages').split()]

        self.buildout_location = config.get('buildout', 'location')
        self.dist_dir = config.get('buildout','dist_dir')
        self.versions = dict(config.items('versions'))
        self.tar = None
        dist_dir = os.path.abspath(os.path.join(self.buildout_location,self.dist_dir))
        if not os.path.exists(dist_dir):
            os.makedirs(dist_dir)
        self.dist_dir = dist_dir

    def getDeployTar(self):
        dist_dir = self.dist_dir
        name = '%s/%s_%s.tgz'%(dist_dir,'deploy', self.releaseid)
        if self.tar is None:
            if os.path.exists(name):
                os.remove(name)
            self.tar = tarfile.open(name,"w:gz")
        return self.tar,name #TODO: need to give it a version



    def release_eggs(self):
        "developer eggs->if changed, increment versions, build and get ready to upload"
        # first get list of deveelop packages we got from recipe
        # for each package
        #
        if self.tar is not None:
            return self.getDeployTar()

        #python setup.py sdist bdist_egg
        tmpdir = tempfile.mkdtemp()
        localdist_dir = self.dist_dir

        self.releaseid = '%s_%s'%(time.time(),uuid())

        donepackages = []
        for path in self.packages:

            # use buildout to run setup for us
            if os.path.isdir(path):
                res = self.setup(args=[path,
                                     'clean',
                                     'egg_info',
                                     '--tag-svn-revision',
                                     '--tag-build','dev_'+self.releaseid,
                                     #'sdist',
                                     #'--formats=zip', #fix bizzare gztar truncation on windows
                                      'bdist_egg',
                                     '--dist-dir',
                                     '%s'%tmpdir,
                                      ])
            else:
                shutil.copy(path,tmpdir)
            donepackages.append(path)
            assert len(donepackages) == len(os.listdir(tmpdir)), "Egg wasn't generated. See errors above"
        tar,tarname = self.getDeployTar()

        specs = []
        for dist in os.listdir(tmpdir):
            #work out version from name
            name,tail = dist.split('-', 1)
            #HACK: must be a better way to get full version spec
            version = tail[:tail.find(self.releaseid)+len(self.releaseid)]
            for end in ['.tar.gz','.zip','.egg','.tar','.tgz']:
                if version != tail:
                    specs.append((name,version))
                    break
                else:
                    version = tail[:tail.find(end)]

            src = os.path.join(tmpdir,dist)
            tar.add(src, arcname=os.path.join(self.dist_dir,dist))
            tgt = os.path.join(localdist_dir,dist)
            if os.path.exists(tgt):
                os.remove(tgt)
            shutil.move(src, tgt)
        os.removedirs(tmpdir)

        self.develop_versions = specs
        return self.getDeployTar()

    def writeVersions(self, versions_file):

#        assert len(specs) == len(self.packages)
        config = ConfigParser.ConfigParser()
        config.read([versions_file])
        for name,version in self.develop_versions + self.versions.items():
            config.set('versions',name,version)
        fp = open(versions_file,'w')
        config.write(fp)
        fp.close()


    def setup(self, args):
        setup = args.pop(0)
        if os.path.isdir(setup):
            setup = os.path.join(setup, 'setup.py')

        #self._logger.info("Running setup script %r.", setup)
        setup = os.path.abspath(setup)

        fd, tsetup = tempfile.mkstemp()
        try:
            os.write(fd, zc.buildout.easy_install.runsetup_template % dict(
                setuptools=pkg_resources_loc,
                setupdir=os.path.dirname(setup),
                setup=setup,
                __file__ = setup,
                ))
            os.spawnl(os.P_WAIT, sys.executable, zc.buildout.easy_install._safe_arg (sys.executable), tsetup,
                      *[zc.buildout.easy_install._safe_arg(a)
                        for a in args])
        finally:
            os.close(fd)
            os.remove(tsetup)


def main(cfgfile, args):
    "execute the fabfile we generated"

#    from os.path import dirname, abspath
#    here = abspath(dirname(__file__))

    config = ConfigParser.ConfigParser()
    config.read([cfgfile])
    files = [cfgfile]
    hosts = {}
#    buildout = Buildout(config.get('buildout','buildout'),[])
    packages = Packages(config)
    #eggs = packages.release_eggs()
    for section in [s for s in config.sections() if s not in ['buildout', 'versions']]:
        options = dict(config.items(section))

        hostout = HostOut(section, options, packages)
        hosts[section] = hostout
    if args:
        host,cmd = args[0],args[1]
        if host == 'all':
            torun = hosts.values()
        else:
            torun = hosts.has_key(host) and [hosts[host]]
        if cmd == 'deploy' and torun:
            for hostout in torun:
                hostout.readsshconfig()
                hostout.package_buildout()
                hostout.runfabric()


def uuid( *args ):
  """
    Generates a universally unique ID.
    Any arguments only create more randomness.
  """
  t = long( time.time() * 1000 )
  r = long( random.random()*100000000000000000L )
  try:
    a = socket.gethostbyname( socket.gethostname() )
  except:
    # if we can't get a network address, just imagine one
    a = random.random()*100000000000000000L
  data = str(t)+' '+str(r)+' '+str(a)+' '+str(args)
  data = md5.md5(data).hexdigest()
  return data

