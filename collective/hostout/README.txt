 

Often we have a buildout installed and working on a development machine and we need to get it working on
one or many hosts quickly and easily. 

First you will need a host. You'll need a linux with ssh access and sudo access. VPS and cloud hosting is
now cheap and plentiful with options as low as $11USD a month. If you're not sure, pick a pay per hour 
option pre-configured with Ubuntu and give it a go.

Next you need a production buildout for your application. There are plenty available whether it be for Plone, 
grok, django, BFG, pylons. Often a buildout will come in several files, one for development and one for production. 
Just remember that to get the best performance you will need to understand your buildout.

Once you've followed instructions and got your development buildout running on your development machine you're ready.

My buildout works, now how do I host it?
****************************************

First we add the collective.hostout part to our development buildout


>>> write('buildout.cfg',
... """
... [buildout]
... parts = example host1
... develop = src/example
...
... [example]
... recipe = zc.recipe.eggs
... egg = example
... 
... [host1]
... recipe = collective.hostout
... host = localhost:10022
... user = root
... password = root
... path = /usr/local/plone/host1
... """ % globals())

If you don't include your password you will be prompted for it later.    
    
Don't forget to rerun your buildout to install the hostout script in your buildout bin directory

>>> print system('bin/buildout -N')
Installing example.
Installing host1.
Generated script '/sample-buildout/bin/hostout'.

The generated script is run with a command and host(s) as arguments

>>> print system('bin/hostout')
Please specify a command: Commands are: deploy

>>> print system('bin/hostout deploy')
Invalid hostout: Hostouts are: host1 all

The deploy command will login to your host and setup a buildout environment if it doesn't exist, upload
and installs the buildout.

>>> print system('bin/hostout deploy host1')
Logging into the following hosts as root:
    localhost
Password for root@localhost: 
...
Hostout: Preparing eggs for transport
Hostout: Develop egg .../example changed. Releasing with hash ...
...
creating '.../example-1.0dev_...-py2.4.egg' and adding 'build/bdist.../egg' to it
removing 'build/bdist.../egg' (and everything under it)
Hostout: Eggs to transport:
	example = 10dev-...
...
Hostout: Wrote versions to /.../host1.cfg
...
[localhost] put: /.../dist/deploy_....tgz -> /tmp/deploy_....tgz
...
[localhost] sudo: sudo -u plone sh -c "export HOME=~plone && cd /var/plone && bin/buildout -c buildout.cfg"
...
[localhost] out: Installing example.
[localhost] out: Getting distribution for 'example'.
[localhost] out: Got example 1.0dev-....
[localhost] out: Installing host1.
...

We now have a live version of our buildout deployed to our host

For more complicated arrangements you can use the extends value to share defaults 
between multiple hostout definitions

>>> write('buildout.cfg',
... """
... [buildout]
... parts = prod staging
...
... [hostout]
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




Options
*******

host
  the IP or hostname of the host to deploy to. by default it will connect to port 22 using ssh.
  You can override the port by using hostname:port

user
  The user which hostout will attempt to login to your host as. Will read a users ssh config to get a default.

password
  The password for the login user. If not given then hostout will ask each time.
  
identity-file
  A public key for the login user.

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
  
extends 
  Specifies another part which contains defaults for this hostout
  
include
  Additional configuration files or directories needed to run this buildout
  
fabfiles
  Path to fabric files that contain commands which can then be called from the hostout
  script. Each method takes a hostout object
   
buildout-cache
  If you want to override the default location for the buildout-cache on the host

Frequently asked questions
**************************

Who should use this?
====================

Integrators
+++++++++++
Hostout makes deployment quicker and more reliable by automating the process.
This makes it especially useful for integrators that need to deploy to many
different machines.
Hostout puts your deployment information into your buildout file further centralising
your configuration. It allows the deployment process to be shared and run by anyone
in your team.

Beginners 
+++++++++

Often those getting started with a framework can handle downloading a development
version of django or plone and even step through a quick start to start creating 
their site or application. The next step is to host their site.
When using buildout and hostout this becomes simple. The learning curve is reduced
and the server configured in a standard way.

Why not proper versions of eggs?
================================

You can tag your code with versions and set version numbers and still use hostout.
Hostout makes this optionial however, giving you the choice. Future versions will 
integrate with source control to perform prerelease checks. 


Why not use git/svn/hg/bzr to pull the code onto the server?
============================================================

a) it means you have to use SCM to deploy. I wanted a story where someone can download plone/django, 
   customise it a little and then host it in as few steps as possible.

b) It means you don't have to install the SCM on the host and handle that in a SCM neurtral way... 	
   I use got, most plone people use svn, I might look at bzr... its a mess.

c) Really you shouldn't be hacking the configuration on your host. Good development means you test 
   things locally, get it working. check it in and then deploy. Hostout is designed to support that model. 
   Everyone one has to have a developement environment to deploy.

d) We want to be SCM neutral.

Why not use collective.releaser or similar to release to a private pypi index?
==============================================================================

It's a lot more complicated to setup and isn't really needed when your eggs are custom just
to the application which is hosted in only one place. There is nothing to stop you
releasing your eggs seperatly.

Why is it a buildout recipe?
============================

Applications like Plone use buildout to install and configure installations on all platforms.
Adding an extra few lines to the default buildout seemed the easiest solution to allowing those
users to take the next step after installing Plone locally, to deploying it remotely.


What kinds of hosts is it known to work with?
=============================================

It is designed to work with newly installed linux distributions but should
work with almost any linux host.
Hostout currently uses the plone unified installer to setup a buildout
environment. That is designed to work on a large number of linux based
systems. Of course what you put in your own buildout will influence the
results too.

What kind of applications will it work with?
============================================

Hostout deploys buildout based solutions. As long as your code can be built
using buildout and any custom code is in source eggs then hostout should work
for you.



Todo list
*********
- extend directly from recipes to better support plugins

- plugins for database handling including backing up, moving between development, staging and production
  regardless of location.
  
- plugins for cloud api's such as Amazon Ec2 or Rackspace Cloud

- Integrate with SCM to implement an optional check to not deploy unless committed.

- Integrate with SCM to tag all parts so deployments can be rolled back.

- Handle basic rollback when no SCM exists, for instance when buildout fails.

- Automatically setup host with password-less ssh login.

- Help deploy DNS settings, possibly by hosting company specific plugins

- Exploure using paramiko directly.

- Incorporate unified installer environment setup scripts directly.

- Support firewalled servers by an optional tunnel back to a client side web proxy.

- Explore ways to make an even easier transition from default plone install to fully hosted site.

Credits
*******

Dylan Jay <software at pretaweb dot com>




