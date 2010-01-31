
Hostout is a zc.buildout recipe. see (http://pypi.python.org/pypi/zc.buildout#recipes)
Installing hostout generates a script which logs into your remote host(s) and performs
commands. e.g.

$ bin/hostout productionserver deploy

$ bin/hostout server1 server2 supervisorctl restart instance1

$ bin/hostout all cmd ls -al

$ bin/hostout staging mylocalfabriccommand

Installing hostout
******************

First follow instructions and to get your development buildout running on your development machine you're ready.
You can add this recipe to a buildout for Plone, django or any other buildout based environment.

Add the collective.hostout part to our development buildout.

>>> write('buildout.cfg',
... """
... [buildout]
... parts = host1
...
... [host1]
... recipe = collective.hostout
... host = 127.0.0.1:10022
... user = root
... password = root
... path = /usr/local/plone/host1
... """ % globals())

If you don't include your password you will be prompted for it later.    
    
Next rerun your buildout to install the hostout script in your buildout bin directory

>>> print system('bin/buildout -N')
Installing host1.
Generated script '/sample-buildout/bin/hostout'.

The generated script is run with a command and host(s) as arguments

>>> print system('bin/hostout')
cmdline is: bin/hostout host1 [host2...] [all] cmd1 [cmd2...] [arg1 arg2...]
Valid hosts are: host1


Each host refers to the name of a part with recipe=collective.hostout in your buildout.
Each host corresponds to a host and remote path which is the default location for commands to act on.

>>> print system('bin/hostout host1')
cmdline is: bin/hostout host1 [host2...] [all] cmd1 [cmd2...] [arg1 arg2...]
Valid commands are - ['uploadeggs', 'join', 'deploy', 'basename', 'cmd', 'postdeploy', 'resetpermissions', 'uploadbuildout', 'createuser', 'buildout', 'dirname', 'predeploy']

>>> print system('bin/hostout host1 cmd pwd')
Hostout: Running command 'cmd' from '.../fabfile.py'
Logging into the following hosts as root:
    127.0.0.1
[127.0.0.1] sudo: sh -c "cd /usr/local/plone/host1 && pwd"
[127.0.0.1] out: CMD RECIEVED
Done.


Adding your own commands
************************

Hostout uses fabric files (see http://docs.fabfile.org). Create a fabric file.

>>> write('fabfile.py',"""
... def echo(cmdline1):
...    hostout = get('hostout')
...    bin = "%s/bin" % hostout.getRemoteBuildoutPath()
...    option1 = hostout.options['option1']
...    run("echo '%s %s'" % (option1, cmdline1) )
... """)

Reference this file in the fabfiles option of your hostout part.

>>> write('buildout.cfg',
... """
... [buildout]
... parts = host1
...
... [host1]
... recipe = collective.hostout
... host = 127.0.0.1:10022
... fabfiles = fabfile.py
... option1 = buildout
... user = root
... password = root
...
... """ )
>>> print system('bin/buildout -N')
Uninstalling host1.
Installing host1.

>>> print system('bin/hostout host1 echo "is cool"')
Hostout: Running command 'echo' from 'fabfile.py'
Logging into the following hosts as root:
    127.0.0.1
[127.0.0.1] run: echo 'buildout is cool'
[127.0.0.1] out: CMD RECIEVED
Done.



Using builtin deploy command
****************************

Often we have a buildout installed and working on a development machine and we need to get it working on
one or many hosts quickly and easily. 

First you will need a host. You'll need a linux with ssh access and sudo access. VPS and cloud hosting is
now cheap and plentiful with options as low as $11USD a month. If you're not sure, pick a pay per hour 
option pre-configured with Ubuntu and give it a go for example rackspace cloud.

Next you need a production buildout for your application. There are plenty available whether it be for Plone, 
grok, django, BFG, pylons. Often a buildout will come in several files, one for development and one for production. 
Just remember that to get the best performance you will need to understand your buildout.

For this example we've added a development egg
to our buildout as well.

>>> mkdir('example')

>>> write('example', 'example.py',
... """
... def run():
...    print "example"
...
... """)

>>> write('example', 'setup.py',
... """
... from setuptools import setup
...
... setup(
...     name = "example",
...     entry_points = {'zc.buildout': ['mkdir = mkdir:Mkdir']},
...     )
... """)

>>> write('buildout.cfg',
... """
... [buildout]
... parts = example host1
... develop = example
...
... [example]
... recipe = zc.recipe.egg
... eggs = example
... 
... [host1]
... recipe = collective.hostout
... host = 127.0.0.1:10022
... user = root
... password = root
...
... """ % globals())
>>> print system('bin/buildout -N')
Develop: '.../example'
Uninstalling host1.
Installing example.
Installing host1.


The deploy command will login to your host and setup a buildout environment if it doesn't exist, upload
and installs the buildout. The deploy command is actually five commands

predeploy
  Bootstrap the server if needed.
  
uploadeggs
  Any develop eggs are released as eggs and uploaded to the server
  
uploadbuildout
  A special buildout is prepared referencing uploaded eggs and all other eggs pinned to the local picked versions
  
buildout
  Run the buildout on the remote server
  
postdeploy
  Perform any final plugin tasks

>>> print system('bin/hostout host1 deploy')
    running clean
    ...
    creating '...example-0.0.0dev_....egg' and adding '...' to it
    ...
    Hostout: Running command 'predeploy' from '.../collective.hostout/collective/hostout/fabfile.py'
    ...
    Hostout: Running command 'uploadeggs' from '.../collective.hostout/collective/hostout/fabfile.py'
    Hostout: Preparing eggs for transport
    Hostout: Develop egg /sample-buildout/example changed. Releasing with hash ...
    Hostout: Eggs to transport:
    	example = 0.0.0dev-...
    Hostout: Wrote versions to /sample-buildout/host1.cfg
    ...
    Hostout: Running command 'uploadbuildout' from '.../collective.hostout/collective/hostout/fabfile.py'
    ...
    Hostout: Running command 'buildout' from '.../collective/hostout/fabfile.py'
    ...
    Hostout: Running command 'postdeploy' from '.../collective.hostout/collective/hostout/fabfile.py'
    ...


We now have a live version of our buildout deployed to our host

Deploy options
--------------

buildout
  The configuration file you which to build on the remote host. Note this doesn't have
  to be the same .cfg as the hostout section is in but the versions of the eggs will be determined
  from the buildout with the hostout section in. Defaults to buildout.cfg

effective-user
  The user which will own the buildout files. Defaults to #TODO

path
  The absolute path on the remote host where the buildout will be created.
  Defaults to ~${hostout:effective-user}/buildout

pre-commands
  A series of shell commands executed as root before the buildout is run. You can use this 
  to shut down your application. If this command fails it will be ignored.
  
post-commands
  A series of shell commands executed as root after the buildout is run. You can use this 
  to startup your application. If this command fails it will be ignored.

parts
  Runs the buildout with a parts value equal to this
  
include
  Additional configuration files or directories needed to run this buildout
   
buildout-cache
  If you want to override the default location for the buildout-cache on the host



Using command plugins
*********************

You use commands others have made via the extends option.
Name a buildout recipe egg in the extends option and buildout will download
and merge any fabfiles and other configuration options from that recipe into
your current hostout configuration. The following are examples of builtin
plugins others are available on pypi.

collective.hostout:supervisor
-----------------------------
This recipe is an example of a hostout plugin. It will set pre and post commands to stop and then 
restart supervisor after the deployment. It takes the following options

>>> write('buildout.cfg',
... """
... [buildout]
... parts = host1
...
... [host1]
... recipe = collective.hostout
... host = 127.0.0.1:10022
... password = root
... extends = collective.hostout:supervisor
... supervisor = supervisor
... init.d = True
...
... """)

>>> print system('bin/buildout -N')
    Uninstalling host1.
    Uninstalling example.
    Installing host1.

#>>> print system('bin/hostout host1')
cmdline is: bin/hostout host1 [host2...] [all] cmd1 [cmd2...] [arg1 arg2...]
Valid commands are - ['installonstartup',..., 'supervisorstartup',..., 'supervisorshutdown',...'supervisorctl'...]
 

The following commands:
supervisorctl
  Takes command line arguments and runs supervisorctl on the remote host
installonboot
  Installs supervisor into your init.d scripts in order to ensure that supervisor
  is started on book

The following options maybe used

supervisor
  The name of the supervisor part to stop and restart
  
init.d
  If set the supervisord script will be linked into init.d so any machine restart will also
  start supervisor

In addition supervisor plugin will shutdown supervisor during pre-deployment and startup
supervisor during post-deployment.

>>> print system('bin/hostout host1 deploy')
Hostout: Running command 'predeploy' from '.../collective/hostout/supervisor/fabfile.py'
...
[127.0.0.1] sudo: /var/lib/plone/host1/bin/supervisorctl shutdown || echo 'Failed to shutdown'
...
Hostout: Running command 'predeploy' from '.../collective/hostout/fabfile.py'
...
Hostout: Running command 'postdeploy' from '.../collective/hostout/supervisor/fabfile.py'
...
[127.0.0.1] sudo: /var/lib/plone/host1/bin/supervisord
...
[127.0.0.1] sudo: /var/lib/plone/host1/bin/supervisorctl status
Hostout: Running command 'postdeploy' from '.../collective.hostout/collective/hostout/fabfile.py'
...



collective.hostout:mrdeveloper
------------------------------
if you include this extension your hostout deployment will fail if you have any uncommited modifications

>>> write('buildout.cfg',
... """
... [buildout]
... parts = host1
...
... [host1]
... recipe = collective.hostout
... host = 127.0.0.1:10022
... password = root
... extends = collective.hostout:mrdeveloper
...
... """ )

>>> print system('bin/buildout -N')


>>> print system('bin/hostout deploy host1')
Package 'example1' has been modified.
Hostout aborted


collective.hostout:ubuntu
-------------------------
(NOT CURRENTLY IMPLEMENTED)
if you include this extension native ubuntu packages will be used on your remote host instead 
of the more generic plone unified installer.

**Warning: this will change your system packages as needed to get the correct python version**


collective.hostout.datafs 
-------------------------
(NOT IMPLEMENTED)
Adding this extension will provide addition commands for manipulating the ZODB database files
of a zope or plone installation.

>>> write('buildout.cfg',
... """
... [buildout]
... parts = host1
...
... [host1]
... recipe = collective.hostout
... host = localhost:10022
... password = root
... extends = collective.hostout:datafs
... filestorage = 
...    ${buildout:directory}/var/filestorage/Data01.fs
...    ${buildout:directory}/var/filestorage/Data02.fs
... 
...
... """ % globals())

>>> print system('bin/buildout -N')

>>> print system('bin/hostout upload host1')
This will overwrite the following filestorage files on your host.
- var/filestorage/Data.fs
Are you sure you want to do this [y/N]?

>>> print system('bin/hostout download host1')
This will overwrite the following filestorage files on your local buildout directory.
- var/filestorage/Data.fs
Are you sure you want to do this [y/N]?

>>> print system('bin/hostout backup host1')
Running repozo to create backup on remote server 'host1'
...

Sharing hostout options
***********************

For more complicated arrangements you can use the extends value to share defaults 
between multiple hostout definitions

>>> write('buildout.cfg',
... """
... [buildout]
... parts = prod staging
...
... [hostout]
... recipe = collective.hostout
... password = blah
... user = root
... identity-file = id_dsa.pub
... pre-commands =
...    ${buildout:directory}/bin/supervisorctl shutdown || echo 'Unable to shutdown'
... post-commands = 
...    ${buildout:directory}/bin/supervisord
... effective-user = plone
... include = config/haproxy.in
...  
... 
... [prod]
... recipe = collective.hostout
... extends = hostout
... host = www.prod.com
... buildout =
...    config/prod.cfg
... path = /var/plone/prod
...
... [staging]
... recipe = collective.hostout
... extends = hostout
... host = staging.prod.com
... buildout =
...    config/staging.cfg
... path = /var/plone/staging
...
... """ % globals())

>>> print system('bin/buildout -N')
Installing prod.
Installing staging.
Generated script '/sample-buildout/bin/hostout'.

>>> print system('bin/hostout deploy')
Invalid hostout hostouts are: prod staging



Detailed Hostout Options
************************

host
  the IP or hostname of the host to deploy to. by default it will connect to port 22 using ssh.
  You can override the port by using hostname:port

user
  The user which hostout will attempt to login to your host as. Will read a users ssh config to get a default.

password
  The password for the login user. If not given then hostout will ask each time.
  
identity-file
  A public key for the login user.

extends 
  Specifies another part which contains defaults for this hostout
  
fabfiles
  Path to fabric files that contain commands which can then be called from the hostout
  script. Commands can access hostout options via hostout.options from the fabric environment.




Todo list
*********

- use latest fabbric and thus switch to python2.6

- finish ubuntu bootstrap

- plugins for database handling including backing up, moving between development, staging and production
  regardless of location.
  
- plugins for cloud api's such as Amazon Ec2 or Rackspace Cloud

- Integrate with SCM to tag all parts so deployments can be rolled back.

- Handle basic rollback when no SCM exists, for instance when buildout fails.

- Automatically setup host with password-less ssh login.

- Help deploy DNS settings, possibly by hosting company specific plugins

- Incorporate unified installer environment setup scripts directly.

- Support firewalled servers by an optional tunnel back to a client side web proxy.

- Explore ways to make an even easier transition from default plone install to fully hosted site.

Credits
*******

Dylan Jay <software at pretaweb dot com>




