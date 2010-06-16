import os
import os.path
from fabric import api


def bootstrap():
    """Update ubuntu with build tools, python and bootstrap buildout"""
    hostout = api.env.get('hostout')
    path = api.env.path
 
    # Add the plone user:
    hostout.setupusers()
    api.sudo('mkdir -p %(path)s' % locals())
    hostout.setowners()

    #http://wiki.linuxquestions.org/wiki/Find_out_which_linux_distribution_a_system_belongs_to
    d = api.run(
    #    "[ -e /etc/SuSE-release ] && echo SuSE "
    #            "[ -e /etc/redhat-release ] && echo redhat"
    #            "[ -e /etc/fedora-release ] && echo fedora || "
                "lsb_release -rd "
    #            "[ -e /etc/debian-version ] && echo debian or ubuntu || "
    #            "[ -e /etc/slackware-version ] && echo slackware"
               )
    print d
    api.run('uname -r')

#    api.sudo('apt-get -y update')
#    api.sudo('apt-get -y upgrade ')
    
    
    version = api.env['python-version']
    major = '.'.join(version.split('.')[:2])
    
    #Install and Update Dependencies
    api.sudo('apt-get -y install '
             'build-essential '
             'python%(major)s python%(major)s-dev '
#             'python-libxml2 '
#             'python-elementtree '
#             'python-celementtree '
             'ncurses-dev '
             'libreadline5-dev '
             % locals())
    # python-profiler?
    
    #install buildout
    api.env.cwd = api.env.path
    api.sudo('wget -r http://python-distribute.org/bootstrap.py')
    api.sudo('echo "[buildout]" > buildout.cfg')
    api.sudo('python%(major)s bootstrap.py' % locals())


def predeploy():
    path = api.env.path
    api.env.cwd = ''

    if api.sudo("ls  %(path)s/bin/buildout || echo 'bootstrap' " % locals()) == 'bootstrap':
        bootstrap()
    #bootstrap()

def installPIL():
    """ Install dependecies for PIL on ubuntu """
    hostout = api.env.get('hostout')

    version = api.env['python-version']
    major = '.'.join(version.split('.')[:2])
    
    api.sudo('apt-get -ym install '
             'python-imaging '
             'libjpeg-dev '
             'libfreetype6-dev '
             'zlib1g-dev '
             'libjpeg62-dev ')

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



