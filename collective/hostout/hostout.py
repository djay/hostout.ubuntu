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
import md5
import os
from zc.buildout import buildout
from os.path import join, exists
from itertools import chain
import re
from zc.buildout.buildout import Buildout
from paramiko import DSSKey, PKey
from paramiko import SSHConfig

import time, random, md5
from collective.hostout import relpath
import pkg_resources


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
    if lines is None:
        return []
    return [l.strip() for l in lines.split('\n') if l.strip() != '']

_isurl = re.compile('([a-zA-Z0-9+.-]+)://').match

max_name_len = 18

def get_all_extends(cfgfile):
    if _isurl(cfgfile):
        return []

    config = ConfigParser.ConfigParser()
    config.optionxform = str
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
        self.hostout_package = None
        self.options = opt

        self.name = name
        self.effective_user = opt['effective-user']
        self.remote_dir = opt['path']
	try:
	    self.host, self.port = opt['host'].split(':')
	    self.port = int(self.port)
	except:
            self.host = opt['host']
	    self.port = 22
	    
        self.user = opt['user']
        self.password = opt['password']
        self.identityfile = opt['identity-file']
        self.start_cmd = opt.get('post-commands')
        self.stop_cmd = opt.get('pre-commands')
        self.extra_config = opt['include']
        self.buildout_cfg = [p.strip() for p in opt['buildout'].split() if p.strip()]
        self.versions_part = opt.get('versions','versions')
        self.parts = [p.strip() for p in opt['parts'].split() if p.strip()]
        self.buildout_cache = opt.get('buildout-cache','')
        if not self.buildout_cache:
            install_base = os.path.dirname(self.getRemoteBuildoutPath())
            self.buildout_cache = os.path.join(install_base,'buildout-cache')

        from pkg_resources import resource_string, resource_filename
        fabfile = resource_filename(__name__, 'fabfile.py')

        self.fabfiles = [p.strip() for p in opt.get('fabfiles','').split() if p.strip()] + [fabfile]

        #self.packages = opt['packages']
        #dist_dir = os.path.abspath(os.path.join(self.buildout_location,self.dist_dir))
        #if not os.path.exists(dist_dir):
        #    os.makedirs(dist_dir)
        #self.tar = None

    def getHostoutFile(self):
        #make sure package has generated
        self.getHostoutPackage()
        return self.config_file[len(self.packages.buildout_location)+1:]

    def getPreCommands(self):
        return self._subRemote(clean(self.stop_cmd))

    def getPostCommands(self):
        return self._subRemote(clean(self.start_cmd))

    def getBuildoutDependencies(self):
        abs = lambda p: os.path.abspath(os.path.join(self.getLocalBuildoutPath(),p))
        return [abs(p) for p in clean(self.extra_config)]

    def getLocalBuildoutPath(self):
        return os.path.abspath(self.packages.buildout_location)

    def getRemoteBuildoutPath(self):
        return self.remote_dir

    def splitPath(self):
        """return the two parts of the path needed by unified installer, the base install path
        and the instance sub directory of the install path. It does this by assuming the last
        part of the path is the instance sub directory"""

        install_dir=os.path.split(self.remote_dir)[0]
        instance=os.path.split(self.remote_dir)[1]
        return (install_Dir, instance)


    def localEggs(self):
        self.getHostoutPackage() #ensure eggs are generated
        return [e for p,v,e in self.packages.local_eggs.values()]

    def getParts(self):
        return self.parts

    def getDownloadCache(self):
        return "%s/%s" % (self.buildout_cache, 'downloads')
    def getEggCache(self):
        return "%s/%s" % (self.buildout_cache, 'eggs')

    def _subRemote(self, cmds):
        "replace abs localpaths to the buildout with absluote remate buildout paths"
        return [c.replace(self.getLocalBuildoutPath(), self.getRemoteBuildoutPath()) for c in cmds]

#    def getDeployTar(self):
#        return self.packages.getDeployTar()

    def getHostoutPackage(self):
        "determine all the buildout files that make up this configuration and package them"

        if self.hostout_package is not None:
            return self.hostout_package

        folder = self.dist_dir

        dist_dir = self.packages.dist_dir
        self.config_file = self.genhostout()
        config_file = os.path.abspath(os.path.join(self.packages.buildout_location,self.config_file))
        base = os.path.dirname(config_file)
        if not os.path.exists(config_file):
            raise "Invalid config file"

        files = get_all_extends(config_file)
        files += self.getBuildoutDependencies()

        self.packages.writeVersions(config_file, self.versions_part)

        dist_dir = self.dist_dir
        self.releaseid = '%s_%s'%(time.time(),uuid())
        self.releaseid = _dir_hash(files)

        name = '%s/%s_%s.tgz'%(dist_dir,'deploy', self.releaseid)
        self.hostout_package = name
        if os.path.exists(name):
            return name
        else:
            self.tar = tarfile.open(name,"w:gz")

        for file in files:
            relative = file[len(self.buildout_dir)+1:] #TODO
            self.tar.add(file,arcname=relative)
        self.tar.close()
        return self.hostout_package


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
            self.identityfile = opt.get('identityfile', None)
            if self.identityfile:
                self.identityfile = os.path.expanduser(self.identityfile).strip()
        if not self.user:
            self.user=opt.get('user','root')



    def runfabric(self, command=None, args=[]):
        "return all commands if none found to run"

        cmds = {}
        cmd = None
        res = True
        ran = False
        fabric.COMMANDS = {}
        fabric.USER_COMMANDS = {}
        sets = [(fabric.COMMANDS,"<DEFAULT>")]
        for fabfile in self.fabfiles:
            fabric.COMMANDS = {}
            fabric.USER_COMMANDS = {}

            fabric._load_default_settings()
            fabric.load(fabfile, fail='warn')
            sets.append((fabric.COMMANDS,fabfile))
        if command is None:
            allcmds = {}
            for commands,fabfile in sets:
                allcmds.update(commands)
            return allcmds
        

        try:
            try:
                for commands, fabfile in sets:
                    cmds.update(commands)
                    cmd = commands.get(command, None)
                    if cmd is None:
	                    continue
                    fabric.USER_COMMANDS = {}
                    fabric.COMMANDS = commands
                    fabric._load_default_settings()
                    print "Hostout: Running command '%s' from '%s'" % (command, fabfile)
                    fabric.set(hostout=self)
                    if self.password:
                        fabric.set(fab_password=self.password)
                    if self.identityfile:
                        fabric.set(fab_key_filename=self.identityfile)

                    fabric.set(
                               fab_user=self.user,
                               fab_hosts=[self.host],
			       fab_port=self.port,
                               )

                    if cmd is not None:
                        ran = True
                        res = cmd(*args)
                        if res not in [None,True]:
                            print >> sys.stderr, "Hostout aborted"
                            res = False
                            break
                        else:
                            res = True

            finally:
                fabric._disconnect()
            print("Done.")
        except SystemExit:
            # a number of internal functions might raise this one.
            raise
        except KeyboardInterrupt:
            print("Stopped.")
        #    except:
        #        sys.excepthook(*sys.exc_info())
        #        # we might leave stale threads if we don't explicitly exit()
        #        return False
        return res

#    def genhostout(self):
#        """ generate a new buildout file which pins versions and uses our deployment distributions"""
#

#        base = self.buildout_dir


#        files = [relpath(file, base) for file in self.buildout_cfg]
        #dist_dir = relpath(self.dist_dir, base)
        #versions = ""
#        hostout = HOSTOUT_TEMPLATE % dict(buildoutfile=' '.join(files),
                                          #eggdir=dist_dir,
 #                                         download_cache=self.getDownloadCache(),
 #                                         egg_cache=self.getEggCache(),
 #                                         )
 #       path = os.path.join(base,'%s.cfg'%self.name)
 #       hostoutf = open(path,'w')
 #       hostoutf.write(hostout)
 #       hostoutf.close()
 #       return path

    def genhostout(self):
        base = self.buildout_dir
        path = os.path.join(base,'%s.cfg'%self.name)
        config = ConfigParser.ConfigParser()
        config.optionxform = str
        config.read([path])
        if 'buildout' not in config.sections():
            config.add_section('buildout')
        files = [relpath(file, base) for file in self.buildout_cfg]

        config.set('buildout', 'extends', ' '.join(files))
        config.set('buildout', 'develop', '')
        config.set('buildout', 'eggs-directory', self.getEggCache())
        config.set('buildout', 'download-cache', self.getDownloadCache())
        config.set('buildout', 'newest', 'true')
        if self.getParts():
            config.set('buildout', 'parts', ' '.join(self.getParts()))

        fp = open(path,'w')
        config.write(fp)
        fp.close()
        return path



HOSTOUT_TEMPLATE = """
[buildout]
extends = %(buildoutfile)s

#prevent us looking for them as developer eggs
develop=

#install-from-cache = true

#Match to unifiedinstaller
eggs-directory = %(egg_cache)s
download-cache = %(download_cache)s

#non-newest set because we know exact versions we want
newest=true
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
        self.local_eggs = {}

    def getDistEggs(self):

        res = {}

        localdist_dir = self.dist_dir
        eggs = pkg_resources.find_distributions(localdist_dir)
        return dict([(( egg.project_name,egg.version),egg) for egg in eggs])


    def release_eggs(self):
        "developer eggs->if changed, increment versions, build and get ready to upload"
        # first get list of deveelop packages we got from recipe
        # for each package
        #
        if self.local_eggs:
            return self.local_eggs

        #python setup.py sdist bdist_egg
 #       tmpdir = tempfile.mkdtemp()
        localdist_dir = self.dist_dir
        eggs = self.getDistEggs()

        donepackages = []
        ids = {}
        self.local_eggs = {}
        released = {}
        if self.packages:
            print "Hostout: Preparing eggs for transport"
        for path in self.packages:

            # use buildout to run setup for us
            hash = _dir_hash([path])
            ids[hash]=path
            path = os.path.abspath(path)
            dist = self.find_distributions(path)
            if len(dist):
                dist = dist[0]
                egg = eggs.get( (dist.project_name, dist.version) )
            else:
                egg = None
            if egg is not None and hash in dist.version:
                self.local_eggs[dist.project_name] = (dist.project_name, dist.version, egg.location)
            elif os.path.isdir(path):
                print "Hostout: Develop egg %s changed. Releasing with hash %s" % (path,hash)
                args=[path,
                                     'clean',
                                     'egg_info',
                                     '--tag-build','dev_'+hash,
                                     #'sdist',
                                     #'--formats=zip', #fix bizzare gztar truncation on windows
                                      'bdist_egg',
                                     '--dist-dir',
                                     '%s'%localdist_dir,
                                      ]
                res = self.setup(args = args)
                dist = self.find_distributions(path)
                if len(dist):
                    dist = dist[0]
                    self.local_eggs[dist.project_name] = (dist.project_name, dist.version, None)
                    released[dist.project_name] = dist.version
                else:
                    raise "Error releasing egg at %s: No egg found after \n python setup.py %s" % (path, ' '.join(args))
            else:
#                shutil.copy(path,localdist_dir)
                self.local_eggs[path] = (None, None, path)
        if released:
            eggs = self.getDistEggs()
            for (name,version) in released.items():
                egg = eggs.get( (name, version) )
                if egg is not None:
                    self.local_eggs[name] = (name, version, egg.location)
                else:
                    raise "Egg wasn't generated. See errors above"


        if self.local_eggs:
            specs = ["\t%s = %s"% (p,v) for p,v,e in self.local_eggs.values()]
            print "Hostout: Eggs to transport:\n%s" % '\n'.join(specs)
        return self.local_eggs

    def find_distributions(self, path):
        #HACK: need to parse setup.py instead assuming src
        return [d for d in pkg_resources.find_distributions(path, only=True)] + \
            [d for d in pkg_resources.find_distributions(os.path.join(path,'src'), only=True)]

    def getVersion(self, path):
        "Test to see if we already have a release of this developer egg"
        dist = [d for d in pkg_resources.find_distributions(path, only=True)]
        dist = dist[0]

        return dist.version

    def writeVersions(self, versions_file, part):

        self.release_eggs() #ensure we've got self.develop_versions

#        assert len(specs) == len(self.packages)
        config = ConfigParser.RawConfigParser()
        config.optionxform = str
        config.read([versions_file])
        specs = {}
        specs.update(self.versions)
        #have to use lower since eggs are case insensitive
        specs.update(dict([(p,v) for p,v,e in self.local_eggs.values()]))
        config.set('buildout', 'versions', part)
        if part in config.sections():
            config.remove_section(part)
        config.add_section(part)

        for name, version in sorted(specs.items()):
            config.set(part,name,version)
        fp = open(versions_file,'w')
        config.write(fp)
        fp.close()
        print "Hostout: Wrote versions to %s"%versions_file


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

    config = ConfigParser.ConfigParser()
    config.optionxform = str
    config.read([cfgfile])
    files = [cfgfile]
    allhosts = {}
#    buildout = Buildout(config.get('buildout','buildout'),[])
    packages = Packages(config)
    #eggs = packages.release_eggs()
    # 
        
    for section in [s for s in config.sections() if s not in ['buildout', 'versions']]:
        options = dict(config.items(section))

        hostout = HostOut(section, options, packages)
        allhosts[section] = hostout

    # cmdline is bin/hostout host1 host2 ... cmd1 cmd2 ... arg1 arg2...
    cmds = []
    cmdargs = []
    hosts = []
    pos = 'hosts'
    for arg in args + [None]:
        if pos == 'hosts':
            if arg in allhosts:
                hosts += [(arg,allhosts[arg])]
                continue
            elif arg == 'all':
                hosts = allhosts.items()
	    else:
		pos = 'cmds'            
        	# get all cmds
		allcmds = {'deploy':None}
        	for host,hostout in hosts:
		    hostout.readsshconfig()
		    allcmds.update(hostout.runfabric())
        if pos == 'cmds':
            if arg == 'deploy':
                cmds += ['predeploy','uploadeggs','uploadbuildout','buildout','postdeploy']
                continue
            elif arg in allcmds:
                cmds += [arg]
                continue
            pos = 'args'
        if pos == 'args' and arg is not None:
            cmdargs += [arg]


    if not hosts or not cmds:
        print >> sys.stderr, "cmdline is: bin/hostout host1 [host2...] [all] cmd1 [cmd2...] [arg1 arg2...]"
    if not hosts:
        print >> sys.stderr, "Valid hosts are: %s"% ' '.join(allhosts.keys())
    elif not cmds:
        print >> sys.stderr, "Valid commands are:"
        max_name_len = reduce(lambda a,b: max(a, len(b)), allcmds.keys(), 0)
        cmds = allcmds.items()
        cmds.sort(lambda x,y: cmp(x[0], y[0]))
	for name, fn in cmds:
	    print >> sys.stderr, '  ', name.ljust(max_name_len),
	    if fn.__doc__:
		print >> sys.stderr, ':', fn.__doc__.splitlines()[0]
	    else:
	        print >> sys.stderr, ''
    else:
        for host, hostout in hosts:
            hostout.readsshconfig()
            for cmd in cmds:
                if cmd == cmds[-1]:
                    res = hostout.runfabric(cmd, cmdargs)
                else:
                    res = hostout.runfabric(cmd)
                if res == True:
                    continue
                elif res == False:
                    break
                else:
                    print >> sys.stderr, "'%s' is not a valid command for host '%s' - %s"%(cmd,host,res.keys())



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

ignore_directories = '.svn', 'CVS', 'build', '.git'
ignore_files = ['PKG-INFO']
def _dir_hash(paths):
    hash = md5.new()
    for path in paths:
        if os.path.isdir(path):
            walked = os.walk(path)
        else:
            walked = [(os.path.dirname(path), [], [os.path.basename(path)])]
        for (dirpath, dirnames, filenames) in walked:
            dirnames[:] = [n for n in dirnames if not (n in ignore_directories or n.endswith('.egg-info'))]
            filenames[:] = [f for f in filenames
                        if not (f in ignore_files or f.endswith('pyc') or f.endswith('pyo'))]
            hash.update(' '.join(dirnames))
            hash.update(' '.join(filenames))
            for name in filenames:
                hash.update(open(os.path.join(dirpath, name)).read())
    import base64
    hash = base64.urlsafe_b64encode(hash.digest()).strip()
    hash = hash.replace('_','-').replace('=','')
    return hash


