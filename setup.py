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

name = "collective.hostout"
setup(
    name = name,
    version = "0.9.3",
    author = "Dylan Jay",
    author_email = "software@pretaweb.com",
    description = "one click deployment for buildout based applications",
    license = "GPL",
    keywords = "buildout, deploy, deployment, server, plone, django, host, hosting",
    url='https://svn.plone.org/svn/collective/'+name,
    long_description=(
        read('README.txt')
        + '\n' +
        'Detailed Documentation\n'
        '**********************\n'
        + '\n' +
        read('collective', 'hostout', 'README.txt')
        + '\n' +
        read('CHANGES.txt')
        + '\n' 
        ),

    packages = find_packages(),
    include_package_data = True,
#    data_files = [('.', ['*.txt'])],
#    package_data = {'':('*.txt')},
    namespace_packages = ['collective'],
    install_requires = ['zc.buildout',
                        'zc.recipe.egg',
                        'setuptools',
                        'Fabric<0.1.0', #in order to make it 2.4 compatible
                        'functools' ,#needed for fabric to make it 2.4 compatible
                        ],
    entry_points = {'zc.buildout':
                    ['default = collective.hostout:Recipe',
                    'ubuntu = collective.hostout.ubuntu:Recipe',
                    'mrdeveloper = collective.hostout.mrdeveloper:Recipe',
                    'datafs = collective.hostout.datafs:Recipe',
                    "supervisor = collective.hostout.supervisor:Recipe"]},
    zip_safe = False,
    )
