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

