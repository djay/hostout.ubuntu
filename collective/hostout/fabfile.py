import os
import os.path

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
    hostout = get('hostout')
    set(
        effectiveuser=hostout.effective_user,
        buildout_dir=hostout.remote_dir,
        install_dir=os.path.split(hostout.remote_dir)[0],
        instance=os.path.split(hostout.remote_dir)[1],
        download_cache=hostout.getDownloadCache()
    )

    set(dist_dir = hostout.getDownloadCache(),
        unified='Plone-3.2.1r3-UnifiedInstaller',
        unified_url='http://launchpad.net/plone/3.2/3.2.1/+download/Plone-3.2.1r3-UnifiedInstaller.tgz',
        )

    sudo('mkdir -p $(dist_dir)/dist '+
         '&& sudo chmod -R a+rw  $(dist_dir)'
         '')
    sudo(('mkdir -p %(dc)s '+
         '&& sudo chmod -R a+rw  %(dc)s'
         '') % dict(dc=hostout.getEggCache()))

    #install prerequsites
    sudo('which g++ || (sudo apt-get -ym update && sudo apt-get install -ym build-essential libssl-dev libreadline5-dev) || echo "not ubuntu"')

    #Download the unified installer if we don't have it
    sudo('test -f $(buildout_dir)/bin/buildout || '+
         'test -f $(dist_dir)/$(unified).tgz || '+
         '( cd /tmp && '+
         'wget  --continue $(unified_url) '+
         '&& sudo mv /tmp/$(unified).tgz $(dist_dir)/$(unified).tgz '+
#         '&& sudo chown $(effectiveuser) $(dist_dir)/$(unified).tgz '+
        ')'
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

    for cmd in hostout.getPreCommands():
        sudo('sh -c "%s"'%cmd)



def uploadeggs():
    """Any develop eggs are released as eggs and uploaded to the server """
    
    hostout = get('hostout')
    set(
        effectiveuser=hostout.effective_user,
        buildout_dir=hostout.remote_dir,
        install_dir=os.path.split(hostout.remote_dir)[0],
        instance=os.path.split(hostout.remote_dir)[1],
        download_cache=hostout.getDownloadCache()
    )

    #need to send package. cycledown servers, install it, run buildout, cycle up servers

    for pkg in hostout.localEggs():
        tmp = os.path.join('/tmp', os.path.basename(pkg))
        tgt = os.path.join(hostout.getDownloadCache(), 'dist', os.path.basename(pkg))
        try:
            sudo('test -f %s'%tgt)
        except:
            put(pkg, tmp)
            sudo("mv  -f %s %s"%(tmp,tgt))
            sudo('chmod a+r %s' % tgt)

def uploadbuildout():
    """A special buildout is prepared referencing uploaded eggs and all other eggs pinned to the local picked versions """
    hostout = get('hostout')
    set(
        effectiveuser=hostout.effective_user,
        buildout_dir=hostout.remote_dir,
        install_dir=os.path.split(hostout.remote_dir)[0],
        instance=os.path.split(hostout.remote_dir)[1],
        download_cache=hostout.getDownloadCache()
    )

    package=hostout.getHostoutPackage()
    tmp = os.path.join('/tmp', os.path.basename(package))
    tgt = os.path.join(hostout.getDownloadCache(), os.path.basename(package))

    try:
        sudo('test -f %s'%tgt)
    except:
        put(package, tmp)
        sudo("mv %s %s"%(tmp,tgt))
        sudo('chown $(effectiveuser) %s' % tgt)

    set(
        #fab_key_filename="buildout_dsa",
        dist_dir=hostout.dist_dir,
        install_dir=hostout.remote_dir,
        hostout_file=hostout.getHostoutFile(),
    )

   # sudo('ls -al versions')
    #need a way to make sure ownership of files is ok
    sudo('tar --no-same-permissions --no-same-owner --overwrite --owner $(effectiveuser) -xvf %s --directory=$(install_dir)' % tgt)
#    if hostout.getParts():
#        parts = ' '.jos.path.oin(hostout.getParts())
 #       sudo('sudo -u $(effectiveuser) sh -c "cd $(install_dir) && bin/buildout -c $(hostout_file) install %s"' % parts)
  #  else:
    #Need to set home var for svn to work
    # 

def buildout():
    """Run the buildout on the remote server """

    hostout = get('hostout')
    set(
        effectiveuser=hostout.effective_user,
        buildout_dir=hostout.remote_dir,
        install_dir=os.path.split(hostout.remote_dir)[0],
    )
    set(
        #fab_key_filename="buildout_dsa",
        dist_dir=hostout.dist_dir,
        install_dir=hostout.remote_dir,
        hostout_file=hostout.getHostoutFile(),
    )
    sudo('sudo -u $(effectiveuser) sh -c "export HOME=~$(effectiveuser) && cd $(install_dir) && bin/buildout -c $(hostout_file)"')

#    run('cd $(install_dir) && $(reload_cmd)')
#    sudo('chmod 600 .installed.cfg')
#    sudo('find $(install_dir)  -type d -name var -exec chown -R $(effectiveuser) \{\} \;')
#    sudo('find $(install_dir)  -type d -name LC_MESSAGES -exec chown -R $(effectiveuser) \{\} \;')
#    sudo('find $(install_dir)  -name runzope -exec chown $(effectiveuser) \{\} \;')



def postdeploy():
    """Perform any final plugin tasks """
    
    hostout = get('hostout')
    set(
        effectiveuser=hostout.effective_user,
        buildout_dir=hostout.remote_dir,
        install_dir=os.path.split(hostout.remote_dir)[0],
        instance=os.path.split(hostout.remote_dir)[1],
        download_cache=hostout.getDownloadCache()
    )

    for cmd in hostout.getPostCommands():
        sudo('sh -c "%s"'%cmd)

def run(*cmd):
    """Execute cmd on remote as login user """
    hostout = get('hostout')
    run('sh -c "cd %s && %s"'%(hostout.remote_dir,' '.join(cmd)))

def sudo(*cmd):
    """Execute cmd on remote as root user """
    hostout = get('hostout')
    sudo('sh -c "cd %s && %s"'%(hostout.remote_dir,' '.join(cmd)))

