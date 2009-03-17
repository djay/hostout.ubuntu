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

import os
from setuptools import setup, find_packages

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

name = "collective.recipe.hostout"
setup(
    name = name,
    version = "0.1.1",
    author = "Dylan Jay",
    author_email = "software@pretaweb.com",
    description = "ZC Buildout recipe to create a tool uploading and deploying to a server",
    license = "GPL",
    keywords = "buildout, deploy",
    url='http://www.python.org/pypi/'+name,
    long_description=(
        read('README.txt')
 #       + '\n' +
 #       read('CHANGES.txt')
        + '\n' +
        'Detailed Documentation\n'
        '**********************\n'
        + '\n' +
        read('collective', 'recipe', 'hostout', 'README.txt')
        + '\n' +
        'Download Cache\n'
        '**************\n'
        'The recipe supports use of a download cache in the same way\n'
        'as zc.buildout. See downloadcache.txt for details\n'
        + '\n' +
        'Download\n'
        '**********************\n'
        ),

    packages = find_packages(),
    include_package_data = True,
#    data_files = [('.', ['*.txt'])],
#   package_data = {'':('*.txt')},
    namespace_packages = ['collective', 'collective.recipe'],
    install_requires = ['zc.buildout', 'setuptools', 'Fabric<0.1.0','functools'],
    entry_points = {'zc.buildout':
                    ['default = %s:Recipe' % name]},
    zip_safe = True,
    )
