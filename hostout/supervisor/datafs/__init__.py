##############################################################################
#
# Copyright (c) 2006 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

import logging, os, shutil, tempfile, urllib2, urlparse
import setuptools.archive_util
import datetime
import zc.buildout
import zc.recipe.egg
from os.path import join
import os
from os.path import dirname, abspath
from pkg_resources import resource_string, resource_filename



class Recipe:
    """hostout.upload recipe adds pre and post commands to run supervisor"""

    def __init__(self, buildout, name, options):
        self.name, self.options, self.buildout = name, options, buildout
        supervisor = self.options.get('supervisor','supervisor')
        self.options['supervisor'] = supervisor
        bin = buildout['buildout']['bin-directory']

        self.options['fabfiles'] = fabfile = resource_filename(__name__, 'fabfile.py')


        self.options['pre-commands'] = "%s/%sctl shutdown || echo 'Failed to shutdown'"% (bin,supervisor)
        self.options['post-commands'] = "%s/%sd shutdown"% (bin,supervisor)

        if self.options.get('init.d') is not None:
            # based on
            # http://www.webmeisterei.com/friessnegger/2008/06/03/control-production-buildouts-with-supervisor/
            self.options['post-commands'] += \
                "cd /etc/init.d && ln -s %s/%sd %s-%sd" % (bin, name, supervisor)
            self.options['post-commands'] += \
                "cd /etc/init.d && update-rc.d %s-%sd defaults" % (name, supervisor)


    def install(self):
        return []

    def update(self):
        return []
