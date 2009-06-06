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
                 extra_config,
                 remote_dir,
                 packages,
                 effective_user,
                 host,user,password,identityfile,
                 start_cmd, stop_cmd):

        self.buildout_location = buildout_location
        self.dist_dir = dist_dir
        self.effective_user = effective_user
        self.buildout_file = buildout_file
        self.config_file = config_file
        self.remote_dir = remote_dir
        self.packages = packages
        dist_dir = os.path.abspath(os.path.join(self.buildout_location,self.dist_dir))
        if not os.path.exists(dist_dir):
            os.makedirs(dist_dir)
        self.tar = None
        self.host = host
        self.user = user
        self.password = password
        self.identityfile = identityfile
        #create new buildout so we can analyse the working set.
        self.buildout = Buildout(self.buildout_file,[])
        self.start_cmd = start_cmd
        self.stop_cmd = stop_cmd
        self.extra_config = extra_config

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
        files += self.extra_config

        tar,tarname = self.getDeployTar()

        for file in files:
            relative = file[len(self.buildout_location)+1:] #TODO
            tar.add(file,arcname=relative)


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

        releaseid = '%s_%s'%(time.time(),uuid())

        donepackages = []
        for path in self.packages:

            # use buildout to run setup for us
            if os.path.isdir(path):
                res = self.buildout.setup(args=[path,
                                     'clean',
                                     'egg_info',
                                     '--tag-svn-revision',
                                     '--tag-build','dev_'+releaseid,
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
            version = tail[:tail.find(releaseid)+len(releaseid)]
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

        assert len(specs) == len(self.packages)
        config = ConfigParser.ConfigParser()
        config.read([self.config_file])
        for name,version in specs:
            config.set('versions',name,version)
        fp = open(self.config_file,'w')
        config.write(fp)
        fp.close()



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



def main(
         effectiveuser='plone',
         remote_dir='buildout',
         buildout_file='buildout.cfg',
         dist_dir='dist',
         packages=[],
         buildout_location='',
         host=None,
         user=None,
         password=None,
         identityfile=None,
         config_file=None,
         extra_config='',
         start_cmd='',
         stop_cmd=''):
    "execute the fabfile we generated"

#    from os.path import dirname, abspath
#    here = abspath(dirname(__file__))

    hostout = HostOut(buildout_location,
                      dist_dir,
                      buildout_file,
                      config_file,
                      extra_config,
                      remote_dir,
                      packages,
                      effectiveuser,
                      host,user,password,identityfile,
                      start_cmd,stop_cmd)

    hostout.readsshconfig()
    hostout.release_eggs()
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

