import os
from os.path import join, basename, dirname


def predeploy():
    hostout = get('hostout')
    try:
        run('test -f %s/bin/buildout' % hostout.remote_dir)
    except:
        #Install and Update Dependencies

        sudo('apt-get update')
        sudo('apt-get upgrade')

        sudo('apt-get install python2.4 python2.4-dev python-profiler')

        sudo('apt-get install build-essential python2.4 python2.4-dev \
        python-setuptools python-imaging python-libxml2 ncurses-dev lynx')
        sudo('apt-get install libjpeg-dev libfreetype6-dev zlib1g-dev')

        #sudo apt-get install apache2

        #to install Python tools 2.4
        sudo('wget http://peak.telecommunity.com/dist/ez_setup.py')
        sudo('python2.4 ez_setup.py')

        #to install PIL
        sudo('easy_install-2.4 --find-links http://download.zope.org/distribution PILwoTK')

        #if its ok you will see something like this:
        #--------------------------------------------------------------------

        #*** TKINTER support not available

        #--- JPEG support ok

        #--- ZLIB (PNG/ZIP) support ok

        #--- FREETYPE2 support ok

        #--------------------------------------------------------------------

        # Add the plone user:

        owner = hostout.effective_user
        sudo('useradd -m %s' % owner)

        #Copy authorized keys to plone user:
        # cp -rp .ssh ~plone/
        #root@domU-12-31-38-00-35-27:~$ chown -R plone:plone ~plone/.ssh

        sudo('cd /%s && chown %s:%s' % (hostout.remote_dir,owner,owner))
        #Login as user plone
        set(fab_user='%s'%owner)

        run('python bootstrap')
        run('bin/buildout install lxml')
        run('bin/buildout')




def postdeploy():
    hostout = get('hostout')


