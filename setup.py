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

name = "hostout.ubuntu"
setup(
    name = name,
    version = "1.0a2",
    author = "Dylan Jay",
    author_email = "software@pretaweb.com",
    description = """Plugin for collective.hostout that bootstraps an ubuntu host ready for hostout deployment""",
    license = "GPL",
    keywords = "buildout, fabric, deploy, deployment, server, plone, django, host, hosting",
    url='https://svn.plone.org/svn/collective/'+name,
    long_description=(
        read('README.txt')
        + '\n' +
        read('hostout', 'ubuntu', 'README.txt')
        + '\n' +
        read('CHANGES.txt')
        + '\n' 
        ),

    packages = find_packages(),
    include_package_data = True,
#    data_files = [('.', ['*.txt'])],
#    package_data = {'':('*.txt')},
    namespace_packages = ['hostout'],
    install_requires = ['zc.buildout',
                        'zc.recipe.egg',
                        'setuptools',
                        'collective.hostout',
                        ],
    entry_points = {'zc.buildout':
                    ['default = hostout.ubuntu:Recipe']
                    },
    zip_safe = False,
    )
