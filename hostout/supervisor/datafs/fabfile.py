import os
from os.path import join, basename, dirname

# based on
# http://www.webmeisterei.com/friessnegger/2008/06/03/control-production-buildouts-with-supervisor/
 
def upload():
    hostout = get('hostout')
    hostout.options['filestorages']

    bin = "%s/bin" % hostout.getRemoteBuildoutPath()
    supervisor = hostout.options['supervisor']
    sudo('sh -c "cd /etc/init.d && ln -s %s/%sd %s-%sd"' % (bin, supervisor, hostout.name, supervisor))
    sudo('sh -c "cd /etc/init.d && update-rc.d %s-%sd defaults"' % (hostout.name, supervisor))

def download():
    hostout = get('hostout')
    hostout.options['filestorages']

    bin = "%s/bin" % hostout.getRemoteBuildoutPath()
    supervisor = hostout.options['supervisor']
    sudo('sh -c "cd /etc/init.d && ln -s %s/%sd %s-%sd"' % (bin, supervisor, hostout.name, supervisor))
    sudo('sh -c "cd /etc/init.d && update-rc.d %s-%sd defaults"' % (hostout.name, supervisor))
