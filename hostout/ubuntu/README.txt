
Installing
**********

hostout.ubuntu is a plugin for collective.hostout_. Hostout is a zc.buildout
recipe.

First you need a working buildout_. Google buildout + your fav app framework to findout how to build it.
We'll use a really simple one and add a hostout to our buildout and we extend
hostout by adding the ubuntu plugin using the "extends"
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
...   main=lambda: sys.stdout.write('all your hosts are below to us!!!')
... entry-points = helloworld=__main__:main
...
... [host]
... recipe = collective.hostout
... host = 127.0.0.1:10022
... extends = hostout.ubuntu
...
... """)

>>> print system('bin/buildout -N')
Installing helloworld.
Generated script '/sample-buildout/bin/helloworld'.
Installing host.
Generated script '/sample-buildout/bin/hostout'.

During deployment hostout will check for a working buildout on the remote
host and if not found will execute an ubuntu bootstrap installing
native packages

>>> print system('bin/hostout host deploy')
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
