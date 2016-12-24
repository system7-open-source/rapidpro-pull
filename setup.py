"""A setuptools based setup module.
"""
# To use a consistent encoding
import codecs
import os
# setup
import setuptools
# a fix for behave_test in behave 1.2.5
import shlex
import subprocess
import sys
# noinspection PyPep8Naming
from setuptools.command.test import test as TestCommand


__author__ = 'Tomasz J. Kotarba <tomasz@kotarba.net>'
__copyright__ = 'Copyright (c) 2016, Tomasz J. Kotarba. All rights reserved.'
__maintainer__ = 'Tomasz J. Kotarba'
__email__ = 'tomasz@kotarba.net'


# a fix for behave_test in behave 1.2.5
class BehaveTest(TestCommand):
    user_options = [('behave-args=', 'b', 'Arguments to pass to behave')]

    # noinspection PyAttributeOutsideInit
    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.behave_args = []
        #import here, cause outside the egg is not loaded
        from setuptools_behave import behave_test

        class _BehaveTest(behave_test):
            def behave(self, path):
                behave = os.path.join("bin", "behave")
                if not os.path.exists(behave):
                    behave = "-m behave"
                cmd_options = self.distribution.command_options[
                    'behave_test'].get('behave_args', ['', ''])[1]
                self.announce("CMDLINE: python %s %s" % (behave, cmd_options),
                              level=3)
                behave_cmd = shlex.split(behave)
                return subprocess.call(
                    [sys.executable] + behave_cmd + shlex.split(cmd_options))
        self.behave_command = _BehaveTest(self.distribution)

    def finalize_options(self):
        self.behave_command.finalize_options()

    def run(self):
        self.behave_command.run()


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'p', "Arguments to pass to pytest")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = ''

    def run_tests(self):
        import shlex
        import pytest
        errno = pytest.main(shlex.split(self.pytest_args))
        sys.exit(errno)


install_requires = [
    'docopt>=0.6,<1',
    'rapidpro-python>=2.1.1,<3',
    'sqlalchemy>=1.1.3,<2',
]


tests_require = [
    'PyHamcrest>=1.9,<2',
    'behave>=1.2.5,<2',
    'iocapture>=0.1.2,<1',
    'mock>=2,<3',
    'pretenders>=1.4.2,<2',
    'pytest>=3,<4',
    'pytest-cov>=2.4,<3',
    'pytz>=2016.7',
]


here = os.path.abspath(os.path.dirname(__file__))


# Get the long description from the README.rst file
with codecs.open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()


setuptools.setup(
    name='rapidpro-pull',
    version='1.0.1',
    description='An open-source tool to pull and cache data from RapidPro'
                ' servers.',
    long_description=long_description,
    url='https://github.com/system7-open-source/rapidpro-pull',
    author='Tomasz J. Kotarba',
    author_email='tomasz@kotarba.net',
    license='GPLv3+',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: System Administrators',
        'Topic :: Desktop Environment',
        'Topic :: Internet',
        'Topic :: Utilities',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: GNU General Public License v3 or later '
        '(GPLv3+)',
        'Environment :: Console',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],
    keywords='rapidpro',
    package_dir={'': '.'},
    packages=setuptools.find_packages('.', exclude=['features', 'spec']),
    python_requires='>=2.7,!=3.*',
    setup_requires=['behave>=1.2.5,<2'],
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require={'development': tests_require},
    entry_points={
        'console_scripts': [
            'rapidpro-pull = rapidpropull.cli:main',
        ],
    },
    cmdclass={'behave_test': BehaveTest,
              'pytest': PyTest},
)
