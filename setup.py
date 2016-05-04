#!/usr/bin/env python3
from distutils.core import setup

VERSION = open('VERSION').readline()[:-1]
setup(
    name = 'gmxscript',
    version = VERSION,
    description = 'Gromacs scripting framework',
    author = 'Pedro Sousa Lacerda',
    author_email = 'pslacerda+gmx@gmail.com',
    url = 'https://github.com/pslacerda/gmx',
    download_url = 'https://github.com/pslacerda/gmx/tarball/%s' % VERSION,
    py_modules = ['gmxscript'],
 )
