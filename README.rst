=============
rapidpro-pull
=============
|pypi-release| |pypi-status| |pypi-format| |pypi-licence|

|linux-ci| |macos-ci| |windows-ci| |coveralls|

|code-quality| |code-health| |codecov|

`rapidpro-pull`_ is an open-source command-line tool for pulling data from
`RapidPro`_ servers, printing it in the JSON format and caching it in local or
remote relational databases (any database supported by `SQLAlchemy`_ - e.g.
PostgreSQL, Oracle, SQLite).  It has been developed for `UNICEF`_ to create a
foundation for a new `ETL`_ subsystem for `IMAMD`_ but it is a standalone tool
which can be used independently.

Intallation and usage
---------------------

To install and get started::

    $ pip install rapidpro-pull
    $ rapidpro-pull --help

Usage::

  rapidpro-pull --flow-runs --api-token=<api-token> [--address=<address>]
                            [--before=<before> --after=<after>]
                            [--with-contacts --with-flows]
                            [--cache=<database-url>]

  rapidpro-pull --flows --api-token=<api-token> [--address=<address>]
                            [--before=<before> --after=<after>]
                            [--uuid=<uuid> ...]
                            [--cache=<database-url>]

  rapidpro-pull --contacts --api-token=<api-token> [--address=<address>]
                            [--before=<before> --after=<after>]
                            [--uuid=<uuid> ...]
                            [--cache=<database-url>]

  rapidpro-pull --help

  Options:
  --flow-runs                        download flow runs
  --flows                            download flows
  --contacts                         download contacts
  -a, --address=<address>            a RapidPro server [default: rapidpro.io]
  -t, --api-token=<api-token>        a RapidPro API token

  -h, --help                         display this help and exit

  --before=<before>                  download all older than ISO 8601 date/time
  --after=<after>                    download all newer than ISO 8601 date/time

  --uuid=<uuid>                      fetch objects matching UUID(s) (repeatable)

  --with-flows                       download associated flows, too
  --with-contacts                    download associated contacts, too

  --cache=<database-url>             use database-url as cache (store retrieved
                                     objects in cache; retrieve objects from
                                     cache instead of downloading from RapidPro
                                     when possible)


Examples:


rapidpro-pull --api-token=a-token -flow-runs >all-flow-runs.json
  Use a RapidPro API token a-token to download all flow runs and save them into
  a JSON file all-flow-runs.json.


rapidpro-pull -t a-token --address https://rapidpro.kotarba.net --flow-runs
  Use a RapidPro API token a-token to download all flow runs from an alternative
  RapidPro service rapidpro.kotarba.net over HTTPS and print them in the JSON
  format.


rapidpro-pull -t a-token --flow-runs --with-flows  --cache=sqlite:////tmp/rp.db
  Use token a-token to download all flow runs and their associated flows.  Do
  not download flows already cached in the provided SQLite database in file
  /tmp/rp.db and do not overwrite cached flow runs.  Add all newly downloaded
  objects to the database for later processing.


rapidpro-pull --flow-runs --with-flows --with-contacts --api-token=a-token
  Use a RapidPro API token a-token to download all flow runs together with all
  associated flows and contacts


rapidpro-pull -t a-token --flows --after 2016-01-01T12:12:12.596000Z
  Use token a-token to download all flows newer than 2016-01-01T12:12:12.596Z.


rapidpro-pull -t a-token --contacts --uuid=a --uuid=b --uuid=c
  Use token a-token to download contacts with UUIDs a, b or c.


Development
-----------
|code-quality-dev| |code-health-dev| |coveralls-dev|

|linux-ci-dev| |macos-ci-dev| |windows-ci-dev| |codecov-dev|

Working on `rapidpro-pull`_ requires the installation of a small number of
development dependencies (in addition to the dependencies required to just run
the program).  These dependencies are listed in tests_require in the setup.py
file but one does not need to install them by hand unless one chooses to invoke
the project test runners manually (see: alternative ways to run tests).  In
order to get started one may want to do the following::

    $ # Create a virtualenv and activate it, e.g.: mkvirtualenv rapidpro-pull
    $ git clone https://github.com/system7-open-source/rapidpro-pull.git
    $ cd rapidpro-pull
    $ pip install --editable .

To use the alternative ways of running tests one needs to explicitly install
the aforementioned additional dependencies (this step is optional and not
required to run tests)::

    $ pip install --editable .[development]

The project has been developed using the BDD / outside-in TDD approach and
there are two separate groups of tests: features and scenarios describing the
high-level/system behaviour using the Gherkin syntax (and, underneath, Python),
and the low-level unit tests (the author is not a mockist but a classicist which
means that mocking and stubbing is used where it seems to make sense instead of
everywhere ;) ).  The provided unit tests ensure 100% code coverage (statement
+ branch).  Apart from the coverage reports printed after each execution of unit
tests, one can view the latest HTML report stored in the htmlcov directory.

The functional tests (features/scenarios) are found in the features/
directory.  To execute them::

    $ python setup.py behave_test  #  please use -b to pass arguments to behave
    $ behave  #  an alternative way of running tests, please see: behave --help

The unit tests are found in the tests/ directory.  To execute them::

    $ python setup.py pytest  #  please use -p to pass arguments to py.test
    $ python setup.py test  #  an alias for pytest
    $ py.test  #  an alternative way of running tests, please see: py.test -h

Alternatively, to run all tests on all supported implementations and versions of
Python, one can just execute the following command::

    $ tox

Continuous Integration
----------------------

We use tox together with various continuous integration services to analyse the
code quality and test rapidpro-pull on all supported platforms (Linux, MacOS,
Windows) and on all supported implementations and versions of Python.  The
status of the current stable release can be easily checked by looking at the
status badges at the top of this document (`rapidpro-pull`_).  For developers,
the status of the develop branch is displayed in the `Development`_ section.

Contact
-------

Please feel free to use this project issue tracker where appropriate, fork
this repository and generate pull requests.  The author can also be contacted
via e-mail_: Tomasz J. Kotarba <tomasz@kotarba.net>.

Special Thanks
--------------

Special thanks to Robert Johnston (a crusading saint of UNICEF, always ready to
fight dragons to save those in need) without whom this project would never be.

----

.. _rapidpro-pull: https://github.com/system7-open-source/rapidpro-pull/
.. _RapidPro: https://rapidpro.github.io/rapidpro/
.. _SQLAlchemy: https://en.wikipedia.org/wiki/SQLAlchemy
.. _UNICEF: http://www.unicef.org/
.. _ETL: https://en.wikipedia.org/wiki/Extract,_transform,_load
.. _IMAMD: https://github.com/system7-open-source/imamd
.. _e-mail: mailto:tomasz@kotarba.net?subject=rapidpro-pull:

.. |pypi-release| image:: https://img.shields.io/pypi/v/rapidpro-pull.svg
   :target: https://pypi.python.org/pypi/rapidpro-pull
   :alt: Release on PyPI

.. |pypi-status| image:: https://img.shields.io/pypi/status/rapidpro-pull.svg
   :target: https://pypi.python.org/pypi/rapidpro-pull
   :alt: Status on PyPI

.. |pypi-format| image:: https://img.shields.io/pypi/format/rapidpro-pull.svg
   :target: https://pypi.python.org/pypi/rapidpro-pull
   :alt: Format

.. |pypi-licence| image:: https://img.shields.io/pypi/l/rapidpro-pull.svg
   :target: https://pypi.python.org/pypi/rapidpro-pull
   :alt: Licence

.. |code-quality| image:: https://img.shields.io/scrutinizer/g/system7-open-source/rapidpro-pull/master.svg
   :target: https://scrutinizer-ci.com/g/system7-open-source/rapidpro-pull/?branch=master
   :alt: Code Quality (Scrutinizer)

.. |code-health| image:: https://landscape.io/github/system7-open-source/rapidpro-pull/master/landscape.svg?style=flat
   :target: https://landscape.io/github/system7-open-source/rapidpro-pull/master
   :alt: Code Health (Landscape / Prospector)

.. |linux-ci| image:: https://img.shields.io/travis/system7-open-source/rapidpro-pull/master.svg?label=CI%3A%20Linux
   :target: https://travis-ci.org/system7-open-source/rapidpro-pull
   :alt: Continuous Integration Testing (Linux)

.. |macos-ci| image:: https://img.shields.io/travis/system7-open-source/rapidpro-pull/master.svg?label=CI%3A%20MacOS
   :target: https://travis-ci.org/system7-open-source/rapidpro-pull
   :alt: Continuous Integration Testing (MacOS)

.. |windows-ci| image:: https://img.shields.io/appveyor/ci/system7ltd/rapidpro-pull/master.svg?label=CI%3A%20Windows
   :target: https://ci.appveyor.com/project/system7ltd/rapidpro-pull?branch=master
   :alt: Continuous Integration Testing (Windows)

.. |coveralls| image:: https://coveralls.io/repos/github/system7-open-source/rapidpro-pull/badge.svg?branch=master
   :target: https://coveralls.io/github/system7-open-source/rapidpro-pull?branch=master
   :alt: Test Coverage (coveralls)

.. |codecov| image:: https://codecov.io/gh/system7-open-source/rapidpro-pull/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/system7-open-source/rapidpro-pull
   :alt: Test Coverage (codecov)

.. |code-quality-dev| image:: https://img.shields.io/scrutinizer/g/system7-open-source/rapidpro-pull/develop.svg
   :target: https://scrutinizer-ci.com/g/system7-open-source/rapidpro-pull/?branch=develop
   :alt: Code Quality (Scrutinizer)

.. |code-health-dev| image:: https://landscape.io/github/system7-open-source/rapidpro-pull/develop/landscape.svg?style=flat
   :target: https://landscape.io/github/system7-open-source/rapidpro-pull/develop
   :alt: Code Health (Landscape / Prospector)

.. |windows-ci-dev| image:: https://img.shields.io/appveyor/ci/system7ltd/rapidpro-pull/develop.svg?label=CI%3A%20Windows
   :target: https://ci.appveyor.com/project/system7ltd/rapidpro-pull?branch=develop
   :alt: Continuous Integration Testing (Windows)

.. |linux-ci-dev| image:: https://img.shields.io/travis/system7-open-source/rapidpro-pull/develop.svg?label=CI%3A%20Linux
   :target: https://travis-ci.org/system7-open-source/rapidpro-pull
   :alt: Continuous Integration Testing (Linux)

.. |macos-ci-dev| image:: https://img.shields.io/travis/system7-open-source/rapidpro-pull/develop.svg?label=CI%3A%20MacOS
   :target: https://travis-ci.org/system7-open-source/rapidpro-pull
   :alt: Continuous Integration Testing (MacOS)

.. |coveralls-dev| image:: https://coveralls.io/repos/github/system7-open-source/rapidpro-pull/badge.svg?branch=develop
   :target: https://coveralls.io/github/system7-open-source/rapidpro-pull?branch=develop
   :alt: Test Coverage (coveralls)

.. |codecov-dev| image:: https://codecov.io/gh/system7-open-source/rapidpro-pull/branch/develop/graph/badge.svg
   :target: https://codecov.io/gh/system7-open-source/rapidpro-pull
   :alt: Test Coverage (codecov)

