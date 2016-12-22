"""
Usage:
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
"""
from __future__ import print_function
import sys
import json

import temba_client.v1
import temba_client.exceptions
import docopt

import rapidpropull.download

__author__ = 'Tomasz J. Kotarba <tomasz@kotarba.net>'
__copyright__ = 'Copyright (c) 2016, Tomasz J. Kotarba. All rights reserved.'
__maintainer__ = 'Tomasz J. Kotarba'
__email__ = 'tomasz@kotarba.net'
__version__ = 'rapidpro-pull 1.0.0'


class ArgumentProcessor(object):
    """
    A problem domain specific processor of command-line arguments for the
    rapidpro-pull program.  Sanitises arguments and can be queried to provide
    domain relevant information to clients (e.g. to instances of the
    DownloadTask class).
    It depends on a definition in a format compatible with docopt and specified
    in __doc__.
    """
    ENDPOINT_SELECTORS = [
        '--flow-runs',
        '--flows',
        '--contacts'
    ]

    def __init__(self, argv=None):
        """
        Initialise and interact with docopt to process arguments given in argv
        (or sys.argv if argv not provided).
        """
        if argv is None:
            argv = sys.argv[1:]
        self.arguments = docopt.docopt(__doc__, argv=argv, version=__version__)

    def get_address(self):
        """Return the address of a RapidPro service to be used."""
        return self.arguments['--address']

    def get_api_token(self):
        """Return a RapidPro API token provided by the user."""
        return self.arguments['--api-token']

    def get_endpoint_selector(self):
        """
        Return an endpoint selector (see: the RapidPro API). The endpoint
        selector determines which of the endpoints publicly exposed by the
        RapidPro web API will be used to pull data.
        """
        filtered = filter(lambda s: self.arguments.get(s),
                          self.ENDPOINT_SELECTORS)
        if filtered:
            return filtered[0]
        else:
            return None

    def get_endpoint_kwargs(self):
        """
        Return a dictionary of optional arguments the user has provided to
        modify a request to the user-selected endpoint.
        """
        kwargs = {}
        if self.arguments['--before'] is not None:
            kwargs['before'] = self.arguments['--before']
        if self.arguments['--after'] is not None:
            kwargs['after'] = self.arguments['--after']
        if self.arguments['--uuid']:
            kwargs['uuids'] = self.arguments['--uuid']
        return kwargs

    def get_selectors_of_requested_associations(self):
        """
        Return optional endpoint selector[s] to be used to query RapidPro for
        objects associated to the objects downloaded as a result of a request
        sent to the main endpoint selector.  Only the endpoint selectors
        explicitly requested by the user will be returned.
        """
        selectors = []
        if self.arguments['--with-contacts']:
            selectors.append('--contacts')
        if self.arguments['--with-flows']:
            selectors.append('--flows')
        return tuple(selectors)

    def get_cache_url(self):
        """Return a URL to a database to be used as cache (if provided)."""
        return self.arguments['--cache']


def main(argv=None):
    """
    This is an entry point used to automatically generate the rapidpro-pull
    command.
    """
    arguments = ArgumentProcessor(argv)
    downloader = rapidpropull.download.DownloadTask(arguments)
    try:
        downloader.download()
    except temba_client.exceptions.TembaConnectionError:
        print('Unable to connect to host', file=sys.stderr)
        sys.exit(1)
    except temba_client.exceptions.TembaTokenError:
        print('Authentication with provided token failed', file=sys.stderr)
        sys.exit(1)
    else:
        print(json.dumps(downloader.get_downloaded_json_structure()))
