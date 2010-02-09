

Installing hostout
******************

First follow the instructions and to get your development buildout running on your development machine.
You can add this recipe to a buildout for Plone, django or any other buildout based environment.

Add the collective.hostout part to your development buildout.

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
Valid commands are:
   bootstrap        : Install python and users needed to run buildout
   buildout         : Run the buildout on the remote server
   deploy           : predeploy, uploadeggs, uploadbuildout, buildout and then postdeploy
   postdeploy       : Perform any final plugin tasks
   predeploy        : Install buildout and its dependencies if needed. Hookpoint for plugins
   resetpermissions : Ensure ownership and permissions are correct on buildout and cache
   run              : Execute cmd on remote as login user
   sudo             : Execute cmd on remote as root user
   uploadbuildout   : Upload buildout pinned to local picked versions + uploaded eggs
   uploadeggs       : Any develop eggs are released as eggs and uploaded to the server
<BLANKLINE>


>>> print system('bin/hostout host1 run pwd')
Hostout: Running command 'run' from '.../fabfile.py'
Logging into the following hosts as root:
    127.0.0.1
[127.0.0.1] run: sh -c "cd /usr/local/plone/host1 && pwd"
[127.0.0.1] out: CMD RECIEVED
Done.

Definitions
***********

buildout
  zc.buildout is a tool for creating an isolated environment for running applications. It is controlled
  by a configuration file(s) called a buidout file.

buildout recipe
  A buildout file consists of parts each of which has a recipe which is in charge of installing a particular
  piece of softare. 
  
deploy
  Take a an application you are developing and move it to a host server for use. Often deployment will be
  to a staging location for limited use in testing or production for mainstream use. Production, staging
  and development often have different but related to buildouts and could involve different numbers of hosts
  for each.

host
  In the context of this document this a machine or VPS running linux which you would like to deploy your
  application to.

fabric file
  see fabric_

Using builtin deploy command
****************************

Often we have a buildout installed and working on a development machine and we need to get it working on
one or many hosts quickly and easily. 

First you will need a linux host. You'll need a linux with ssh access and sudo access. VPS and cloud hosting is
now cheap and plentiful with options as low as $11USD a month. If you're not sure, pick a pay per hour 
option pre-configured with Ubuntu and give it a go for example rackspacecloud or amazon EC2.

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
...     entry_points = {'default': ['mkdir = mkdir:Mkdir']},
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
... """ )
>>> print system('bin/buildout -N')
Develop: '.../example'
Uninstalling host1.
Installing example.
Installing host1.

Hostout will record the versions of eggs in a local file

>>> print open('hostoutversions.cfg').read()
[versions]
collective.hostout = 0.9.4
<BLANKLINE>
# Required by collective.hostout 0.9.4
Fabric = ...


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

The buildout file used on the host pins pins the uploaded eggs

    >>> print open('host1.cfg').read()
    [buildout]
    develop = 
    eggs-directory = /var/lib/plone/buildout-cache/eggs
    versions = versions
    newest = true
    extends = buildout.cfg hostoutversions.cfg
    download-cache = /var/lib/plone/buildout-cache/downloads
    <BLANKLINE>
    [versions]
    example = 0.0.0dev-...


Bootstrapping
-------------

Hostout has a builtin bootstrap command that is called if the predeploy command doesn't find buildout
installed at the remote path.
Bootstrap not only installs buildout but
also installs the correct version of python, development tools, needed libraries and creates users needed to
manage the buildout. The buildin bootstrap may not work for all versions of linux so look
for hostout plugins that match the distribution of linux you installed.

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
  to shut down your application. If these commands fail they will be ignored.
  
post-commands
  A series of shell commands executed as root after the buildout is run. You can use this 
  to startup your application. If these commands fail they will be ignored.

parts
  Runs the buildout with a parts value equal to this
  
include
  Additional configuration files or directories needed to run this buildout
   
buildout-cache
  If you want to override the default location for the buildout-cache on the host

python-version
  The version of python to install during bootstrapping. Defaults to version
  used in the local buildout. (UNIMPLIMENTED) 


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


collective.hostout:mrdeveloper
------------------------------
if you include this extension your hostout deployment will fail if you have any uncommited modifications

>>> write('buildout.cfg',
... """
... [buildout]
... parts = host1 example
... extensions =
...    mr.developer
... sources = sources
... sources-dir = .
... auto-checkout = example
... [sources]
... example = fs example
...
... [example]
... recipe = zc.recipe.egg
... eggs = example
...
... [host1]
... recipe = collective.hostout
... host = 127.0.0.1:10022
... password = root
... extends = collective.hostout:mrdeveloper
...
... """ )

>>> print system('bin/buildout -N')
    mr.developer: Filesystem package 'example' doesn't need a checkout.
    Develop: '/sample-buildout/./example'
    Uninstalling host1.
    Installing _mr.developer.
    Getting distribution for 'elementtree'.
    Got elementtree 1.2.6-20050316.
    Generated script '/sample-buildout/bin/develop'.
    Installing example.
    Installing host1.


#>>> print system('bin/hostout host1 deploy')
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

#>>> print system('bin/buildout -N')

#>>> print system('bin/hostout host1 upload')
This will overwrite the following filestorage files on your host.
- var/filestorage/Data.fs
Are you sure you want to do this [y/N]?

#>>> print system('bin/hostout host1 download')
This will overwrite the following filestorage files on your local buildout directory.
- var/filestorage/Data.fs
Are you sure you want to do this [y/N]?

#>>> print system('bin/hostout host1 backup')
Running repozo to create backup on remote server 'host1'
...


Adding your own commands
************************

Hostout uses fabric files. Fabric is any easy way to write python that
colls commands on a host over ssh. You can create your own fabric files as follows:


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
Uninstalling example.
Uninstalling _mr.developer.
Installing host1.


>>> print system('bin/hostout host1 echo "is cool"')
Hostout: Running command 'echo' from 'fabfile.py'
Logging into the following hosts as root:
    127.0.0.1
[127.0.0.1] run: echo 'buildout is cool'
[127.0.0.1] out: CMD RECIEVED
Done.



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
... host = localhost:10022
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
    Uninstalling host1.
    Installing hostout.
    Installing staging.
    Installing prod.

#>>> print system('bin/hostout deploy')
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

- use latest fabric and thus switch to python2.6

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

Dylan Jay ( software at pretaweb dot com )




