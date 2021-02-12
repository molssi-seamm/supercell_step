#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""supercell_step
A SEAMM plug-in for building supercells of periodic systems.
"""

import sys
from setuptools import setup, find_packages
import versioneer

# from https://github.com/pytest-dev/pytest-runner#conditional-requirement
needs_pytest = {'pytest', 'test', 'ptr'}.intersection(sys.argv)
pytest_runner = ['pytest-runner'] if needs_pytest else []

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

with open('requirements_install.txt') as fd:
    requirements = fd.read()

setup(
    name='supercell_step',
    author="Paul Saxe",
    author_email='psaxe@molssi.org',
    description=__doc__.splitlines()[1],
    long_description=readme + '\n\n' + history,
    long_description_content_type='text/x-rst',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    license="BSD-3-Clause",
    url='https://github.com/molssi-seamm/supercell_step',
    packages=find_packages(include=['supercell_step']),
    include_package_data=True,
    setup_requires=[] + pytest_runner,
    install_requires=requirements,
    test_suite='tests',
    platforms=['Linux',
               'Mac OS-X',
               'Unix',
               'Windows'],
    zip_safe=True,

    keywords=['SEAMM', 'plug-in', 'flowchart', 'supercell', 'unitcell',
              'periodic', 'atomistic'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Chemistry',
        'Topic :: Scientific/Engineering :: Physics',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    entry_points={
        'org.molssi.seamm': [
            'Supercell = supercell_step:SupercellStep',
        ],
        'org.molssi.seamm.tk': [
            'Supercell = supercell_step:SupercellStep',
        ],
    }
)
