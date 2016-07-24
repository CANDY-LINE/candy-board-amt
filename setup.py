#!/usr/bin/env python

import os
import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

version = "1.0.0"

class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True
    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    os.system('python setup.py bdist_wheel upload')
    sys.exit()

setup(
    name='candy-board-amt',
    version=version,
    author='Daisuke Baba',
    author_email='baba.daisuke@gmail.com',
    url='http://github.com/CANDY-LINE/candy-board-amt',
    download_url='https://github.com/CANDY-LINE/candy-board-amt/tarball/{0}'.format(version),
    description='Base CANDY LINE boards service for AM Telecom Modules',
    long_description=open('README.md').read() + '\n\n' + open('LICENSE').read(),
    packages=find_packages('lib'),
    package_dir={'': 'lib'},
    license='BSD3',
    classifiers=[
        'Programming Language :: Python',
        'Development Status :: 3 - Alpha',
        'Natural Language :: English',
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX :: Linux',
        'Topic :: System :: Hardware',
    ],
    keywords=(
        'CANDY EGG', 'CANDY LINE'
    ),
    tests_require=['pytest-cov>=2.2.0',
                   'pytest>=2.6.4',
                   'terminaltables>=1.2.1'],
    cmdclass = {'test': PyTest}
)
