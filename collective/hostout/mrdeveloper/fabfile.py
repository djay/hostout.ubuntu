import commands

def predeploy():
    """ check status of local source code before deployment
    """
    res = True
    # cancel deployment incase mr.developer not installed
    mrdevNotInstalled, msg = commands.getstatusoutput('bin/develop')
    if mrdevNotInstalled:
        print >> sys.stderr, 'mr.developer Not Found'
        return False

    # check status of packages using mr.developer
    allstatus = commands.getoutput('bin/develop st')
    pkgstatus = allstatus.split('\n')
    for status in pkgstatus:
        # catch the status symbol return from command output
        if len(status) > 2 and status[2] <> ' ':
            print >> sys.stderr, 'Package \'%s\' has been modified.' % status[6:]
            res = False

    if res is False:
        print >> sys.stderr, 'Please commit your changes before deployment!'
        return False

    return True
