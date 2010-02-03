


What does it do?
****************

If you are new to remote application management, hostout can help you to
deploy your first site in minutes. Hostout is compatible with Plone, django, or any other
buildout based environment.
    
Hostout is a zc.buildout recipe_
Hostout generates a script which logs into your remote host(s) and performs preset and customizable commands. e.g.

$ bin/hostout productionserver deploy

$ bin/hostout server1 server2 supervisorctl restart instance1

$ bin/hostout all cmd ls -al

$ bin/hostout staging mylocalfabriccommand

How does it do that?
********************

Commands can easily be added from a local fabric_ script, hostout command plugins or just the
builtin commands to help you bootstrap and deploy your buildout to remote hosts.

Why is hostout awesome?
***********************
Managing multiple environments can be a real pain and a barrier to development.
Hostout puts all of the settings for all of your environments in an easy-to-manage format.

.. _recipe: http://pypi.python.org/pypi/zc.buildout#recipes
.. _fabric: http://fabfile.org

.. contents::

