# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 CERN.
# Copyright (C) 2018 RERO.
#
# Invenio-Circulation is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module for the circulation of bibliographic items."""

import os

from setuptools import find_packages, setup

readme = open('README.rst').read()
history = open('CHANGES.rst').read()

tests_require = [
    'check-manifest>=0.25',
    'coverage>=4.0',
    'isort>=4.3.3',
    'mock>=1.3.0',
    'pydocstyle>=1.0.0',
    'pytest-cache>=1.0',
    'pytest-cov>=1.8.0',
    'pytest-pep8>=1.0.6',
    'pytest>=2.8.0',
]

invenio_search_version = '1.0.1'
invenio_db_version = '1.0.2'

extras_require = {
    'elasticsearch5': [
        'invenio-search[elasticsearch5]>={}'.format(invenio_search_version),
    ],
    'elasticsearch6': [
        'invenio-search[elasticsearch6]>={}'.format(invenio_search_version),
    ],
    'docs': [
        'Sphinx>=1.5.1',
    ],
    'mysql': [
        'invenio-db[mysql,versioning]>={}'.format(invenio_db_version),
    ],
    'postgresql': [
        'invenio-db[postgresql,versioning]>={}'.format(invenio_db_version),
    ],
    'sqlite': [
        'invenio-db[versioning]>={}'.format(invenio_db_version),
    ],
    'pygraphviz': [
        'pygraphviz>=1.3.1'
    ],
    'tests': tests_require
}

extras_require['all'] = []
for name, reqs in extras_require.items():
    if name in ('mysql', 'postgresql', 'sqlite', 'elasticsearch5',
                'elasticsearch6'):
        continue
    extras_require['all'].extend(reqs)

setup_requires = [
    'Babel>=1.3',
    'pytest-runner>=2.6.2',
]

install_requires = [
    'Flask-BabelEx>=0.9.3',
    'transitions>=0.6.8',
    'invenio-base>=1.0.1',
    'invenio-pidstore>=1.0.0',
    'invenio-records>=1.0.0',
    'invenio-records-rest>=1.1.2',
    'invenio-rest>=1.0.0'
]

packages = find_packages()


# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join('invenio_circulation', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
    version = g['__version__']

setup(
    name='invenio-circulation',
    version=version,
    description=__doc__,
    long_description=readme + '\n\n' + history,
    keywords='invenio TODO',
    license='MIT',
    author='CERN',
    author_email='info@inveniosoftware.org',
    url='https://github.com/inveniosoftware/invenio-circulation',
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'flask.commands': [
            'circulation = invenio_circulation.cli:circulation',
        ],
        'invenio_base.apps': [
            'invenio_circulation = invenio_circulation:InvenioCirculation',
        ],
        'invenio_i18n.translations': [
            'messages = invenio_circulation',
        ],
        'invenio_pidstore.fetchers': [
            'circ_loanid = invenio_circulation.pid.fetchers:loanid_fetcher',
        ],
        'invenio_pidstore.minters': [
            'circ_loanid = invenio_circulation.pid.minters:loanid_minter',
        ],
    },
    extras_require=extras_require,
    install_requires=install_requires,
    setup_requires=setup_requires,
    tests_require=tests_require,
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Development Status :: 1 - Planning',
    ],
)
