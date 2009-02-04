import os

def createuser(buildout_user='buildout'):
    "Creates a user account to run the buildout in"
    set(keyname="buildout_dsa.$(buildout_host)")
    if not os.path.exists(keyname):
        try:
            run('cd ~$(buildout_user)',fail='abort')
        except:
            sudo("adduser $(buildout_user)")
        try:
            sudo('cd ~$(buildout_user)/.ssh')
        except:
            sudo('mkdir ~$(buildout_user)/.ssh')
            sudo('chmod 700 ~$(buildout_user)/.ssh')
        sudo('touch ~$(buildout_user)/.ssh/authorized_keys')
        sudo('chmod 600 ~$(buildout_user)/.ssh/authorized_keys')
        run("rm -f /tmp/buildout_dsa")
        run("ssh-keygen -t dsa -N '' -f /tmp/buildout_dsa")
        #run('rm ~$(buildout_user)/.ssh/buildout_dsa.pub')
        try:
            download('/tmp/buildout_dsa','buildout_dsa')
            download('/tmp/buildout_dsa.pub','buildout_dsa.pub')
        except:
            pass
        sudo('cp ~$(buildout_user)/.ssh/authorized_keys ~$(buildout_user)/.ssh/authorized_keys.bak')
        sudo('cat /tmp/buildout_dsa.pub >> ~$(buildout_user)/.ssh/authorized_keys')
    set(fab_key_filename=keyname)

def preparebuildout():
    "install buildout and its dependencies"
    try:
        import pdb;pdb.set_trace()
        run('ls $(buildout_dir)')
    except:
        run('mkdir $(buildout_dir)')
#    try:
#        run('ls $(buildout_dir)/bootstrap.py')
#    except:
#        put('bootstrap.py','$(buildout_dir)')
#    try:
#        run('ls $(buildout_dir)/bin')
#    except:
#        run('cd $(buildout_dir); python bootstrap.py')

def sendbuildout():
    "deploy the package of changed cfg files"
    
def sendeggs():
    "get teh eggs we packaged up and send them"
    

def deploy(user='plone', remote_dir='buildout'):
    "Prints hello."
    set(
        fab_user='zope',
        buildout_user=user,
        buildout_dir=remote_dir,
    )
    #createuser()
    set(
        fab_user='$(buildout_user)',
    )
    set(fab_key_filename="buildout_dsa")
    preparebuildout()