collective.hostout:supervisor
-----------------------------
This recipe is an example of a hostout plugin. It will set pre and post commands to stop and then 
restart supervisor after the deployment. It takes the following options


Installing
**********

hostout.supervisor is a plugin to collective.hostout. Hostout is a zc.buildout
recipe.

1. Install and get working your buildout

>>> write('buildout.cfg',
... """
... [buildout]
...
... """)

>>> print system('bin/buildout -N')

Normally it would contain other parts to install parts of your application.

2. Add a hostout to your buildout

>>> write('buildout.cfg',
... """
... [buildout]
... parts = host1
...
... [host1]
... recipe = collective.hostout
... host = 127.0.0.1:10022
... password = root
...
... """)

>>> print system('bin/buildout -N')

This will give you a hostout script to run commands on the server including
the deployment command

>>> print system('bin/hostout host1 deploy')

You use commands others have made via the extends option.
Name a hostout plugin egg in the extends option and hostout will download
and merge any fabfiles and other configuration options from that recipe into
your current hostout configuration. 

>>> write('buildout.cfg',
... """
... [buildout]
... parts = host1
...
... [host1]
... recipe = collective.hostout
... host = 127.0.0.1:10022
... password = root
...
... extends = collective.hostout:supervisor
... supervisor = supervisor
... init.d = True
...
... """)

>>> print system('bin/buildout -N')
    Uninstalling host1.
    Uninstalling example.
    Installing host1.

>>> print system('bin/hostout host1')
    cmdline is: bin/hostout host1 [host2...] [all] cmd1 [cmd2...] [arg1 arg2...]
    Valid commands are:
    ...
       installonstartup   : Installs supervisor into your init.d scripts in order to ensure that supervisor is started on boot
    ...
       supervisorctl      : Takes command line arguments and runs supervisorctl on the remote host
       supervisorshutdown : Shutdown the supervisor daemon
       supervisorstartup  : Start the supervisor daemon
    ...
 
The following options maybe used

supervisor
  The name of the supervisor part to stop and restart
  
init.d
  If set the supervisord script will be linked into init.d so any machine restart will also
  start supervisor

In addition supervisor plugin will shutdown supervisor during pre-deployment and startup
supervisor during post-deployment.

>>> print system('bin/hostout host1 deploy')
    Hostout: Running command 'predeploy' from '/.../collective/hostout/supervisor/fabfile.py'
    Logging into the following hosts as :
        127.0.0.1
    [127.0.0.1] sudo: /var/lib/plone/host1/bin/supervisorctl shutdown || echo 'Failed to shutdown'
    ...
    Hostout: Running command 'postdeploy' from '/.../collective/hostout/supervisor/fabfile.py'
    ...
    [127.0.0.1] sudo: /var/lib/plone/host1/bin/supervisord
    ...
    [127.0.0.1] sudo: /var/lib/plone/host1/bin/supervisorctl status
    ...
    Hostout: Running command 'postdeploy' from '.../collective.hostout/collective/hostout/fabfile.py'
    ...

Credits
*******

Dylan Jay ( software at pretaweb dot com )




