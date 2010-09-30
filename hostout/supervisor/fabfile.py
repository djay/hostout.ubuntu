import os
import os.path  #import os.path.join, os.path.basename, os.path.dirname
from fabric import api, contrib

initd = """
#!/bin/sh
#
# Supervisor init script.
#
# chkconfig: 2345 80 20
# description: supervisord

# Source function library.
#. /etc/rc.d/init.d/functions

ENV=plonedev
BUILDOUT=%(bin)s
SUPERVISORD="%(supervisor)sd"
SUPERVISORCTL="%(supervisor)sctl"

RETVAL=0

start() {
     echo -n "Starting $SUPERVISORD: "
     $BUILDOUT/$SUPERVISORD
     RETVAL=$?
     [ $RETVAL -eq 0 ] && touch /var/lock/subsys/$SUPERVISORD-$ENV
     echo
     return $RETVAL
}

stop() {
     echo -n "Stopping $SUPERVISORD: "
     $BUILDOUT/$SUPERVISORCTL shutdown
     RETVAL=$?
     [ $RETVAL -eq 0 ] && rm -f /var/lock/subsys/$SUPERVISORD-$ENV
     echo
     return $RETVAL
}

case "$1" in
         start)
             start
             ;;

         stop)
             stop
             ;;

         restart)
             stop
             start
             ;;
esac

exit $REVAL
"""

initd_old ="""
#! /bin/sh
### BEGIN INIT INFO
# Provides:          supervisor
# Default-Start:     2 3 4 5
# Default-Stop:      S 0 1 6
# Short-Description: Starts/stops the supervisor daemon
# Description:       This starts and stops the supervisor dameon
#                    which is used to run and monitor arbitrary programs as
#                    services, e.g. application servers etc.
### END INIT INFO
#
# Author:    Christopher Arndt <chris@chrisarndt.de>
#
# Version:    @(#)supervisor  1.0  05-Dec-2006
#

set -e

PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
DESC="supervisor daemon"
NAME="%(supervisor)s"
DAEMON="%(bin)s/${NAME}d"
PIDFILE="/var/run/${NAME}d.pid"
SCRIPTNAME="/etc/init.d/$NAME"
#CONFFILE="/etc/${NAME}d.conf"

# Gracefully exit if the package has been removed.
test -x "$DAEMON" || exit 0

# supervisord not start up without a configuration
#test -r "$CONFFILE" || exit 0

# Read config file if it is present.
#if [ -r "/etc/default/$NAME" ]; then
#    . "/etc/default/$NAME"
#fi

#test "x$START_SUPERVISOR" = "xyes" || exit 0

#
#    Function that starts the daemon/service.
#
d_start() {
    start-stop-daemon --start --quiet --pidfile "$PIDFILE" \
        --exec "$DAEMON" \
        || echo -n " already running"
}

#
#    Function that stops the daemon/service.
#
d_stop() {
    start-stop-daemon --stop --quiet --pidfile "$PIDFILE" \
        --name "$NAME" \
        || echo -n " not running"
}

#
#    Function that sends a SIGHUP to the daemon/service.
#
d_reload() {
    start-stop-daemon --stop --quiet --pidfile "$PIDFILE" \
        --name "$NAME" --signal 1
}

case "$1" in
  start)
    echo -n "Starting $DESC: $NAME"
    d_start
    echo "."
    ;;
  stop)
    echo -n "Stopping $DESC: $NAME"
    d_stop
    echo "."
    ;;
  reload|force-reload)
    echo -n "Reloading $DESC configuration..."
    d_reload
    echo "done."
  ;;
  restart)
    echo -n "Restarting $DESC: $NAME"
    d_stop
    # One second might not be time enough for a daemon to stop,
    # if this happens, d_start will fail (and dpkg will break if
    # the package is being upgraded). Change the timeout if needed
    # be, or change d_stop to have start-stop-daemon use --retry.
    # Notice that using --retry slows down the shutdown process somewhat.
    sleep 1
    d_start
    echo "."
    ;;
  *)
    echo "Usage: "$SCRIPTNAME" {start|stop|restart|force-reload}" >&2
    exit 3
    ;;
esac

exit 0
"""


def supervisorboot():
    """Ensure that supervisor is started on boot"""
    hostout = api.env.hostout

    # based on
    # http://www.webmeisterei.com/friessnegger/2008/06/03/control-production-buildouts-with-supervisor/
    bin = "%s/bin" % hostout.getRemoteBuildoutPath()
    supervisor = hostout.options['supervisor']
    script = initd % locals()
    name = hostout.name
    path = '/etc/rc.d/init.d'
    api.sudo('test -f %(path)s/%(name)s-%(supervisor)s && rm %(path)s/%(name)s-%(supervisor)s || echo "pass"'%locals())
    contrib.files.append(script, '%(path)s/%(name)s-%(supervisor)s'%locals(), use_sudo=True)
    api.sudo('chmod +x %(path)s/%(name)s-%(supervisor)s'%locals())
    api.sudo(('(which update-rc.d && update-rc.d %(name)s-%(supervisor)s defaults) || '
             '(test -f /sbin/chkconfig && /sbin/chkconfig --add %(name)s-%(supervisor)s)') % locals())
    #sudo('sh -c "cd /etc/init.d && ln -s %s/%sd %s-%sd"' % (bin, supervisor, hostout.name, supervisor))
    #sudo('sh -c "cd /etc/init.d && update-rc.d %s-%sd defaults"' % (hostout.name, supervisor))



def predeploy():
    hostout = api.env.hostout
    supervisorshutdown()
    if hostout.options.get('install-on-startup') is not None:
        installonstartup()

def postdeploy():
    supervisorstartup()
    
def supervisorstartup():
    """Start the supervisor daemon"""
    hostout = api.env.hostout
    path = hostout.getRemoteBuildoutPath()
    bin = "%(path)s/bin" % locals()
    supervisor = hostout.options['supervisor']
    api.sudo("%(bin)s/%(supervisor)sd"% locals())
    api.sudo("%(bin)s/%(supervisor)sctl status"% locals())

def supervisorshutdown():
    """Shutdown the supervisor daemon"""
    hostout = api.env.hostout
    path = hostout.getRemoteBuildoutPath()
    bin = "%(path)s/bin" % locals()
    supervisor = hostout.options['supervisor']
    api.sudo("%(bin)s/%(supervisor)sctl shutdown || echo 'Failed to shutdown'"% locals() )

def supervisorctl(*args):
    """Runs remote supervisorlctl with given args"""
    hostout = api.env.hostout
    path = hostout.getRemoteBuildoutPath()
    bin = "%(path)s/bin" % locals()
    supervisor = hostout.options['supervisor']
    if not args:
        args = ['status']
    args = ' '.join(args)
    api.sudo("%(bin)s/%(supervisor)sctl %(args)s" % locals())


def restart(*args):
    """ supervisorctl restart command """
    api.env.hostout.supervisorctl('restart', *args)

def start(*args):
    """ supervisorctl start command """
    api.env.hostout.supervisorctl('start', *args)
def stop(*args):
    """ supervisorctl stop command """
    api.env.hostout.supervisorctl('stop', *args)
def status(*args):
    """ supervisorctl status command """
    api.env.hostout.supervisorctl('status', *args)
def tail(*args):
    """ supervisorctl tail command """
    api.env.hostout.supervisorctl('tail', *args)
