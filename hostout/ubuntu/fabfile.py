import os
import os.path
from fabric import api


def bootstrap():
    hostout = api.env.get('hostout')
    #Install and Update Dependencies

    api.sudo('apt-get -y update')
    api.sudo('apt-get -y upgrade ')
    
    
    version = api.env['python-version']
    major = '.'.join(version.split('.')[:2])

    api.sudo('apt-get -y install '
             'build-essential '
             'python%(major)s python%(major)s-dev '
             'python-setuptools '
             'python-libxml2 '
             'python-elementtree '
             'python-celementtree '
             'ncurses-dev '
             'lynx '
             'python-imaging '
             'libjpeg-dev '
             'libfreetype6-dev '
             'zlib1g-dev '
             'libreadline5-dev '
             'zlib1g-dev '
             'libbz2-dev '
             'libssl-dev '
             'libjpeg62-dev '
             % locals())
    # python-profiler?

    #sudo apt-get install apache2

    #to install Python tools 2.4
    api.sudo('wget http://peak.telecommunity.com/dist/ez_setup.py')
    api.sudo('python%(major)s ez_setup.py' % locals())

    #to install PIL
    api.sudo('easy_install-%(major)s --find-links http://download.zope.org/distribution PILwoTK' % locals())
    api.sudo('easy_install-%(major)s --find-links http://dist.repoze.org/PIL-1.1.6.tar.gz PIL' % locals())

    #if its ok you will see something like this:
    #--------------------------------------------------------------------

    #*** TKINTER support not available

    #--- JPEG support ok

    #--- ZLIB (PNG/ZIP) support ok

    #--- FREETYPE2 support ok

    #--------------------------------------------------------------------

    # Add the plone user:

    owner = hostout.effective_user
    api.sudo('test -d ~%(owner)s || useradd -m %(owner)s' % locals())

    #Copy authorized keys to plone user:
    key_filename, key = api.env.hostout.getIdentityKey()
    api.sudo("rm -rf ~%(owner)s/.ssh" % locals())
    api.sudo("mkdir -p ~%(owner)s/.ssh" % locals())
    api.sudo("echo '%(key)s' > ~%(owner)s/.ssh/authorized_keys" % locals())
    api.sudo("chown -R %(owner)s:%(owner)s ~%(owner)s/.ssh" % locals() )

    path = api.env.path
    api.sudo('mkdir -p %(path)s' % locals())
    setowners()
    
    #install buildout
    api.sudo('easy_install-%(major)s zc.buildout' % locals())
    api.env.cwd = api.env.path
    api.run('buildout init')
#    api.run('cd /%(path)s && bin/buildout install lxml' % locals())
#    api.run('cd /%(path)s && bin/buildout' % locals())
    setowners()


def setowners():   
    hostout = api.env.get('hostout')
    owner = api.env['effective-user']
    path = api.env.path
    
    # cache and buildouts should be owned by the login user
    # var dir and db should be owned by effective-user

    api.sudo('chown -R %(owner)s:%(owner)s %(path)s' % locals())
    
    dl = hostout.getDownloadCache()
    dist = os.path.join(dl, 'dist')
    api.sudo('mkdir -p %(dist)s && chown -R %(owner)s:%(owner)s %(dl)s' % locals())
    bc = hostout.getEggCache()
    api.sudo('mkdir -p %(bc)s && chown -R %(owner)s:%(owner)s %(bc)s' % locals())


def predeploy():
    path = api.env.path

    if api.sudo("ls  %(path)s/bin/buildout || echo 'bootstrap' " % locals()) == 'bootstrap':
        bootstrap()
    #bootstrap()


