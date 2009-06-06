 

**Warning: This is alpha software. The api and the way it's used may change and using it with production
systems is at your own risk**
 

We have a buildout which we want to deploy to a brand new host

We add collective.	hostout to our development buildout

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... parts = hostout
    ... index = http://pypi.python.org/simple
    ... develop = 
    ...     %(recipe_location)s 
    ... 
    ... [hostout]
    ... recipe = collective.hostout
    ... host = localhost
    ... """ % globals())
    >>> cat('buildout.cfg')
    sdfdf
    
    
 Now we run the buildout

    >>> print system('bin/buildout'),
    ...
    Installing hostout.
    hostout: Creating deployment script bin/hostout
    hostout: Creating hostout.cfg with pinned buildout versions
    ...


We can run the hostout script the first time. It will

1. package our release

2. send it to the server

3. create a buildout environment running under a virtualenv if need be

4. run a buildout pinned to the eggs that were selected when you last ran buildout locally

5. start up your application

Let's see that working

    >>> print system('bin/hostout'),
    Creating release 45454345345
    Producing source distribution for src/example with version 2343243434
    ...
    Packaged eggs and buildout into deploy-5445454.tgz
    ...
    [localhost] put: /Users/dylanjay/Projects/csiro/dist/deploy_1.tgz -> /tmp/deploy_1.tgz
    ...
    Connecting to localhost.
    User 'plone' not found or unable to connect
    If this is the first time running this script please enter your root credentials
    This will prepare your host to recieve your buildout
    user: root
    password: root
    Creating user account 'deploy'
    Creating authorisation key pair
    Logging in as 'deploy'
    Installing python virtualenv
    Pinning egg versions
    Deploying eggs to host...done
    Deploying buildout to host...done
    Stopping remote services...done
    Running remote buildout...done
    Starting remote services...done
    Deployment complete at verson 0.1

We now have a live version of our buildout deployed and running on our host.


Options
*******

host
  the IP or hostname of the host to deploy to. by default it will connect to port 22 using ssh.
  You can override the port by using hostname:port

user
  The user which hostout will attempt to login to your host as. Defaults to root

password
  The password for the login user. If not given then hostout will ask each time.

buildout
  The configuration file you which to build on the remote host. Note this doesn't have
  to be the same .cfg as the hostout section is in but the versions of the eggs will be determined
  from the buildout with the hostout section in. Defaults to buildout.cfg

effective-user
  The user which will own the buildout files. Defaults to #TODO

remote_path
  The absolute path on the remote host where the buildout will be created.
  Defaults to ~${hostout:effective-user}/buildout

start_cmd
  A sh command to start up your application. This will be run as root. It is run after every
  successful running of buildout on the remote host.
  Defaults to ${buildout:bin-directory}/supervisord

stop_cmd
  A sh command to shutdown your application. This will be run as root. It is run before every
  buildout on the remote host. If this command fails it will be ignored.
  Defaults to ${buildout:bin-directory}/supervisorctl shutdown


Frequently asked questions
**************************

Who should use this?
====================

Hostout was primarily created to solve the problem of how to create a hosted
Plone site for $20 in 20minutes even with no knowledge of linux system
administration. It is designed to solve the question "Now I've downloaded and installed
Plone on my windows machine, how do I get a real site?"
However hostout is useful for:

- anyone who wants a quick solution for setting up a new host for a buildout based application and then repeatedly redeploying to it, including django and other buildout based apps.

- anyone who doesn't want to deal with learning how to setup and administer a linux server

- professionals who use a develop/test/commit/deploy cycle who don't already have their own custom deployment processes


Why not use git/svn/hg/bzr to pull the code onto the server?
============================================================

a) it means you have to use SCM to deploy. I wanted a story where someone can download plone/django, customise it a little and then host it in as few steps as possible.

b) It means you don't have to install the SCM on the host and handle that in a SCM neurtral way... 	I use got, most plone people use svn, I might look at bzr... its a mess.

c) Really you shouldn't be hacking the configuration on your host. Good development means you test things locally, get it working. check it in and then deploy. Hostout is designed to support that model. Everyone one has to have a developement environment to deploy.

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

- Handle multiple hosts and multiple locations better including simultaneous deployment.

- Database handling including backing up, moving between development, staging and production
  regardless of location.

- Integrate with SCM to implement an optional check to not deploy unless committed.

- Integrate with SCM to tag all parts so deployments can be rolled back.

- Integrate with SCM to use SCM version numbers.

- Handle basic rollback when no SCM exists, for instance when buildout fails.

- Automatically setup host with password-less ssh login.

- Don't upload eggs unless they have changed.

- Help deploy DNS settings, possibly by hosting company specific plugins

- Exploure using paramiko directly.

- Incorporate unified installer environment setup scripts directly.

- Support firewalled servers by an optional tunnel back to a client side web proxy.

- Explore ways to make an even easier transition from default plone install to fully hosted site.

Credits
*******

Dylan Jay <software at pretaweb dot com>




