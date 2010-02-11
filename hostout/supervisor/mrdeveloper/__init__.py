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
    """
    hostout.mrdeveloper recipe checks the status of source code before deploying to host
    """

    def __init__(self, buildout, name, options):
        self.name, self.options, self.buildout = name, options, buildout
        # always set mrdeveloper fabfile at first
        self.options['fabfiles'] = '%s\n%s' % (resource_filename(__name__, 'fabfile.py'), self.options.get('fabfiles', ''))

    def install(self):
        return []

    def update(self):
        return []
