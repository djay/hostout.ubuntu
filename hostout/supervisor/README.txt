
Installing
**********

hostout.supervisor is a plugin for collective.hostout_. Hostout is a zc.buildout
recipe.

First you need a working buildout_ using supervisor. Here's a really simple one.

>>> write('buildout.cfg',
... """
... [buildout]
... parts = helloworld 
...
... [helloworld]
... recipe = zc.recipe.egg:scripts
... eggs = zc.recipe.egg
... initialization = import sys
...   main=lambda: sys.stdout.write('all your hosts are below to us')
... entry-points = helloworld=__main__:main
...
... [supervisor]
... recipe = collective.recipe.supervisor
... programs = 10 helloworld bin/helloworld
...
... """)

>>> print system('bin/buildout -N')
Installing helloworld.
Generated script '/sample-buildout/bin/helloworld'.

>>> print system('bin/helloworld')
all your hosts are below to us

Google buildout + your fav app framework to findout how to build it.

Next we add a hostout to our buildout and we extend hostout by adding the supervisor plugin using the "extends"
option.


>>> write('buildout.cfg',
... """
... [buildout]
... parts = helloworld host
...
... [helloworld]
... recipe = zc.recipe.egg:scripts
... eggs = zc.recipe.egg
... initialization = import sys
...   main=lambda: sys.stdout.write('all your hosts are below to us')
... entry-points = helloworld=__main__:main
...
... [supervisor]
... recipe = collective.recipe.supervisor
... programs = 10 helloworld bin/helloworld
...
... [host]
... recipe = collective.hostout
... host = 127.0.0.1:10022
... extends = hostout.supervisor
... parts = hellowworld supervisor
...
... """)

>>> print system('bin/buildout -N')
    Updating helloworld.
    Installing host.
    Generated script '/sample-buildout/bin/hostout'.
    ...

>>> print system('bin/hostout host')
    cmdline is: bin/hostout host1 [host2...] [all] cmd1 [cmd2...] [arg1 arg2...]
    Valid commands are:
    ...
       supervisorboot     : Installs supervisor into your init.d scripts in order to ensure that supervisor is started on boot
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

.. _buildout: http://pypi.python.org/pypi/zc.buildout
.. _recipe: http://pypi.python.org/pypi/zc.buildout#recipes
.. _fabric: http://fabfile.org
.. _collective.hostout: http://pypi.python.org/pypi/collective.hostout
.. _hostout: http://pypi.python.org/pypi/collective.hostout
.. _supervisor: http://pypi.python.org/pypi/collective.recipe.supervisor
