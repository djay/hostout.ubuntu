import os
import os.path
from fabric import api
from fabric.api import sudo, run, get, put

def _createuser(buildout_user='buildout'):
    """Creates a user account to run the buildout in"""
    #keyname="buildout_dsa.%s"%(buildout_host)
    #if not os.path.exists(keyname):
    if True:
        sudo('test -d ~$(buildout_user) || adduser $(buildout_user)')
        sudo('test -d ~$(buildout_user)/.ssh || mkdir ~$(buildout_user)/.ssh;')
        sudo('(chmod 700 ~$(buildout_user)/.ssh; touch ~$(buildout_user)/.ssh/authorized_keys)')
        sudo('chmod 600 ~$(buildout_user)/.ssh/authorized_keys')
        #run("rm -f /tmp/buildout_dsa")
        #run("ssh-keygen -t dsa -N '' -f /tmp/buildout_dsa")
        #run('rm ~$(buildout_user)/.ssh/buildout_dsa.pub')
        #try:
        #    download('/tmp/buildout_dsa','buildout_dsa')
        #    download('/tmp/buildout_dsa.pub','buildout_dsa.pub')
        #except:
        #    pass
        sudo('cp ~$(buildout_user)/.ssh/authorized_keys ~$(buildout_user)/.ssh/authorized_keys.bak')
        sudo('cat /tmp/buildout_dsa.pub >> ~$(buildout_user)/.ssh/authorized_keys')
    set(fab_key_filename=keyname)


def resetpermissions():
    """Ensure ownership and permissions are correct on buildout and cache """
    hostout = get('hostout')
    set(
        dist_dir = hostout.getDownloadCache(),
        effectiveuser=hostout.effective_user,
        buildout_dir=hostout.remote_dir,
        install_dir=os.path.split(hostout.remote_dir)[0],
        instance=os.path.split(hostout.remote_dir)[1],
        download_cache=hostout.getDownloadCache()
    )


    sudo('sudo chmod -R a+rw  $(dist_dir)')
    sudo(('sudo chmod -R a+rw  %(dc)s'
         '') % dict(dc=hostout.getEggCache()))
    sudo('sudo chown -R $(effectiveuser) $(install_dir)/$(instance)')


def predeploy():
    """Install buildout and its dependencies if needed. Hookpoint for plugins"""

    #run('export http_proxy=localhost:8123') # TODO get this from setting
    
    hostout = api.env['hostout']
    try:
        run('test -f %s/bin/buildout' % api.env.path)
    except:
        bootstrap()

    for cmd in hostout.getPreCommands():
        sudo('sh -c "%s"'%cmd)

    #Login as user plone
    api.env['user'] = api.env['effective-user']

def bootstrap():
    """Install python and users needed to run buildout"""
    hostout = api.env['hostout']

#    effectiveuser=hostout.effective_user
#    buildout_dir=hostout.remote_dir
#    install_dir=os.path.split(hostout.remote_dir)[0]
#    instance=os.path.split(hostout.remote_dir)[1]
#    download_cache=hostout.getDownloadCache()


    unified='Plone-3.2.1r3-UnifiedInstaller'
    unified_url='http://launchpad.net/plone/3.2/3.2.1/+download/Plone-3.2.1r3-UnifiedInstaller.tgz'

    sudo('mkdir -p %(dc)s/dist && sudo chmod -R a+rw  %(dc)s'%dict(dc=api.env.download_cache) )
    sudo(('mkdir -p %(dc)s && sudo chmod -R a+rw  %(dc)s') % dict(dc=hostout.getEggCache()) )

    #install prerequsites
    sudo('which g++ || (sudo apt-get -ym update && sudo apt-get install -ym build-essential libssl-dev libreadline5-dev) || echo "not ubuntu"')

    #Download the unified installer if we don't have it
    sudo('test -f %(buildout_dir)s/bin/buildout || '+
         'test -f %(dist_dir)s/%(unified)s.tgz || '+
         '( cd /tmp && '+
         'wget  --continue %(unified_url)s '+
         '&& sudo mv /tmp/%(unified)s.tgz %(dist_dir)s/%(unified)s.tgz '+
#         '&& sudo chown %(effectiveuser)s %(dist_dir)s/%(unified)s.tgz '+
        ')' % dict(unified=unified, unified_url=unified_url, buildout_dir=api.env.path)
         )
    # untar and run unified installer
    sudo('test -f $(buildout_dir)/bin/buildout || '+
          '(cd /tmp && '+
          'tar -xvf $(dist_dir)/$(unified).tgz && '+
          'test -d /tmp/$(unified) && '+
          'cd /tmp/$(unified) && '+
          'sudo mkdir -p  $(install_dir) && '+
          'sudo ./install.sh --target=$(install_dir) --instance=$(instance) --user=$(effectiveuser) --nobuildout standalone && '+
          'sudo chown -R $(effectiveuser) $(install_dir)/$(instance))'
          )



def uploadeggs():
    """Any develop eggs are released as eggs and uploaded to the server """
    
    hostout = api.env['hostout']

#    effectiveuser=hostout.effective_user
#    buildout_dir=hostout.remote_dir
#    install_dir=os.path.split(hostout.remote_dir)[0]
#    instance=os.path.split(hostout.remote_dir)[1]
#    download_cache=hostout.getDownloadCache()

    #need to send package. cycledown servers, install it, run buildout, cycle up servers

    dl = hostout.getDownloadCache()
    contents = api.run('ls %(dl)s'%locals())

    for pkg in hostout.localEggs():
        if pkg not in contents:
            tmp = os.path.join('/tmp', os.path.basename(pkg))
            tgt = os.path.join(hostout.getDownloadCache(), 'dist', os.path.basename(pkg))
            api.put(pkg, tmp)
            api.run("mv -f %(tmp)s %(tgt)s && chmod a+r %(tgt)s" % locals() )

def uploadbuildout():
    """Upload buildout pinned to local picked versions + uploaded eggs """
    hostout = api.env.hostout

    package = hostout.getHostoutPackage()
    tmp = os.path.join('/tmp', os.path.basename(package))
    tgt = os.path.join(hostout.getDownloadCache(), 'dist', os.path.basename(package))

    #api.env.warn_only = True
    if api.run("test -f %(tgt)s || echo 'None'" %locals()) == 'None' :
        api.put(package, tmp)
        api.run("mv %(tmp)s %(tgt)s" % locals() )
        #sudo('chown $(effectiveuser) %s' % tgt)


    effectiveuser=hostout.effective_user
    install_dir=hostout.remote_dir
    api.run('tar --no-same-permissions --no-same-owner --overwrite '
         '--owner %(effectiveuser)s -xvf %(tgt)s '
         '--directory=%(install_dir)s' % locals())
    
#    if hostout.getParts():
#        parts = ' '.jos.path.oin(hostout.getParts())
 #       sudo('sudo -u $(effectiveuser) sh -c "cd $(install_dir) && bin/buildout -c $(hostout_file) install %s"' % parts)
  #  else:
    #Need to set home var for svn to work
    # 

def buildout():
    """Run the buildout on the remote server """

    hostout = api.env.hostout
#    set(
#        effectiveuser=hostout.effective_user,
#        buildout_dir=hostout.remote_dir,
#        install_dir=os.path.split(hostout.remote_dir)[0],
#    )
#    set(
#        #fab_key_filename="buildout_dsa",
#        dist_dir=hostout.dist_dir,
#        install_dir=hostout.remote_dir,
#    )
    hostout_file=hostout.getHostoutFile()
    api.env.user = api.env['effective-user']
    api.env.cwd = hostout.remote_dir
    api.run('bin/buildout -c %(hostout_file)s' % locals())
    #api.sudo('sudo -u $(effectiveuser) sh -c "export HOME=~$(effectiveuser) && cd $(install_dir) && bin/buildout -c $(hostout_file)"')

#    run('cd $(install_dir) && $(reload_cmd)')
#    sudo('chmod 600 .installed.cfg')
#    sudo('find $(install_dir)  -type d -name var -exec chown -R $(effectiveuser) \{\} \;')
#    sudo('find $(install_dir)  -type d -name LC_MESSAGES -exec chown -R $(effectiveuser) \{\} \;')
#    sudo('find $(install_dir)  -name runzope -exec chown $(effectiveuser) \{\} \;')



def postdeploy():
    """Perform any final plugin tasks """
    
    hostout = api.env.get('hostout')
 
    for cmd in hostout.getPostCommands():
        api.run('sh -c "%s"'%cmd)

def run(*cmd):
    """Execute cmd on remote as login user """
    api.run('sh -c "cd %s && %s"'%(api.env.path,' '.join(cmd)))

def sudo(*cmd):
    """Execute cmd on remote as root user """
    api.sudo('sh -c "cd %s && %s"'%(api.env.path,' '.join(cmd)))

