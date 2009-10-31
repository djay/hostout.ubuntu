import os
from os.path import join, basename, dirname



def initdsupervisor():
    hostout = get('hostout')

    # based on
    # http://www.webmeisterei.com/friessnegger/2008/06/03/control-production-buildouts-with-supervisor/
    bin = "%s/bin" % hostout.getRemoteBuildoutPath()
    supervisor = hostout.options['supervisor']
    sudo('sh -c "cd /etc/init.d && ln -s %s/%sd %s-%sd"' % (bin, supervisor, hostout.name, supervisor))
    sudo('sh -c "cd /etc/init.d && update-rc.d %s-%sd defaults"' % (hostout.name, supervisor))



def predeploy():
    hostout = get('hostout')
    bin = "%s/bin" % hostout.getRemoteBuildoutPath()
    supervisor = hostout.options['supervisor']
    sudo("%s/%sctl shutdown || echo 'Failed to shutdown'"% (bin,supervisor) )
    if hostout.options.get('init.d') is not None:
        initdsupervisor(hostout)


def postdeploy():
    hostout = get('hostout')
    bin = "%s/bin" % hostout.getRemoteBuildoutPath()
    supervisor = hostout.options['supervisor']
    sudo("%s/%sd shutdown"% (bin,supervisor))


