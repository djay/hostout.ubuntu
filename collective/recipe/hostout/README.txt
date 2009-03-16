
Hostout. one click deployment for plone.

Goals:
1. solution for deploying plone with just a local buildout, ssh access and no server experience.
  - designed to lower the barrier of entry for hobbyists wanting to host. 
  - $20/m plone site in 2min.
  - few dependencies. clean server install and no source control or 3rd party servers needed.
  - work with buildout so that eventually hostout can be a part of unifiedinstaller
2. work with professional setups where source control and private pypi servers exist.
  - put an easy to implement best practices deployment model in place so you don't have to think hard to make controlled
    repeatable buildouts
  - be SCM neutral - plugin archetecture to use git or svn or whatever. 
3. Make repeatable best practice deployments
  - make it easy to roll back to a previous version from the client
  - make it possible to have more than one server each with differetn versions of code - staging.
  - make it easy to work with databases between dev, staging and production.
4. If possible not assume plone/zope. Allow it to be a buildout based deployer.


How will it do this?

Recipe collects info on eggs used and creates a deployment script. Lets you choose where you want to deploy it
and which buildout file to deploy.
Deployment will
- work with creating version numbers of dev packages and buildout.
- might need to halt if source isn't in state to release 
- handle checking in and storing versions of code to be deployed. make sure we have a solid tags abnd pointers
  to everything in the whole project release.
  

  

Create a release of each dev egg, auto incrementing the version numbers. To do this it will have to compare the code to a hash to see if its changed. The release is a egg which is zipped and sent to folder on the server

So all dev references are in dev.cfg but not in prod.cfg

Then we need to pin the versions of all the eggs. We can use buildout to tell us what the current versions are and put that in a versions.cfg file (which only gets used in production)

Then we need to version the buildout. The reason is we may want to roll back the server to a previous setup. So we'd tar the buildout files, hash it and date it, send it to a dir on the server and then kill the old files and add the new.

Backup the db to the same buildout tag, stop servers, rerun buildout and then restart the servers.

To roll back we can issue the roll back command which will copy back the last buildout files

--

We have a buildout which we want to deploy to a brand new host

We add collective.recipe.hostout to our development buildout

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... parts = deploy
    ...
    ... [deploy]
    ... recipe = collective.recipe.hostout
    ... host = localhost
    ... """

Now we run the buildout
 
    >>> print system('bin/buildout'),
    Installing deploy.
    foo: Creating deployment script bin/deploy

The recipe also creates the parts directory:

    >>> ls(sample_buildout, 'parts')
    d  hostout

We can run the deployment script the first time

    >>> print system('bin/deploy'),
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
    

Thinking out loud here, the recipe would do the following,

Create a release of each dev egg, auto incrementing the version numbers. To do this it will have to compare the code to a hash to see if its changed. The release is a egg which is zipped and sent to folder on the server

So all dev references are in dev.cfg but not in prod.cfg

Then we need to pin the versions of all the eggs. We can use buildout to tell us what the current versions are and put that in a versions.cfg file (which only gets used in production)

Then we need to version the buildout. The reason is we may want to roll back the server to a previous setup. So we'd tar the buildout files, hash it and date it, send it to a dir on the server and then kill the old files and add the new.

Backup the db to the same buildout tag, stop servers, rerun buildout and then restart the servers.

To roll back we can issue the roll back command which will copy back the last buildout files

--
At the start it would 

