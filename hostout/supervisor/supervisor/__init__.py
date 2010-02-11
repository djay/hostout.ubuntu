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


def add(list, item):
    return '\n'.join( list.split() + [item] )


class Recipe:
    """hostout.supervisor recipe adds pre and post commands to run supervisor"""

    def __init__(self, buildout, name, options):
        self.name, self.options, self.buildout = name, options, buildout
        supervisor = self.options.get('supervisor','supervisor')
        self.options['supervisor'] = supervisor

        fabfile = resource_filename(__name__, 'fabfile.py')
        self.options['fabfiles'] = add( self.options.get('fabfiles',''), fabfile )

    def install(self):
        return []

    def update(self):
        return []
