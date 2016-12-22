from __future__ import print_function
from itertools import chain, combinations
import subprocess
import imp
import os
import sys
import time
import datetime
import json
import random
try:
    # PY3
    # noinspection PyCompatibility
    from urllib.parse import urlencode
except ImportError:
    # PY2
    from urllib import urlencode

import pytz
from pretenders.client.http import HTTPMock
from pretenders.common.constants import FOREVER


__author__ = 'Tomasz J. Kotarba <tomasz@kotarba.net>'
__copyright__ = 'Copyright (c) 2016, Tomasz J. Kotarba. All rights reserved.'
__maintainer__ = 'Tomasz J. Kotarba'
__email__ = 'tomasz@kotarba.net'

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
tests_root = os.path.join(project_root, 'tests')
test_utilities = imp.load_module('utilities',
                                 *imp.find_module('utilities', [tests_root]))

# fixtures
fixtures_path = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__), 'fixtures'))
# a simplified JSON response with some flow runs
flow_runs_fixture_path = os.path.join(fixtures_path, 'flow_runs.json')
# a simplified JSON response with some flows
flows_fixture_path = os.path.join(fixtures_path, 'flows.json')
# a simplified JSON response with some contacts
contacts_fixture_path = os.path.join(fixtures_path, 'contacts.json')


class Endpoints(object):
    class EndpointError(ValueError):
        message = 'Invalid endpoint.'

    class __Endpoint(object):
        def __init__(self, path, fixture_path, datetime_attribute_name, option):
            self.path = path
            self.fixture_path = fixture_path
            self.datetime_attribute_name = datetime_attribute_name
            self.option = option
    __endpoints = set()
    FLOWRUNS = __Endpoint('runs.json', flow_runs_fixture_path, 'modified_on',
                          '--flow-runs')
    __endpoints.add(FLOWRUNS)
    FLOWS = __Endpoint('flows.json', flows_fixture_path, 'created_on',
                       '--flows')
    __endpoints.add(FLOWS)
    CONTACTS = __Endpoint('contacts.json', contacts_fixture_path, 'modified_on',
                          '--contacts')
    __endpoints.add(CONTACTS)

    @classmethod
    def validate(cls, item):
        if item not in cls.__endpoints:
            raise cls.EndpointError()

    @classmethod
    def get_endpoint_by_name(cls, name):
        if name == 'flow runs':
            return cls.FLOWRUNS
        elif name == 'flows':
            return cls.FLOWS
        elif name == 'contacts':
            return cls.CONTACTS
        else:
            raise cls.EndpointError()

    @classmethod
    def make_flow_run(cls, run, flow, contact, modified_dt=None, **kwargs):
        if not modified_dt:
            modified_dt = '{}-07-11T14:10:30.591000Z'.format(
                random.randint(2000, 3000))
        fr = test_utilities.Auxiliary.make_flow_run(
            run=int(run), flow_uuid=flow, contact=contact,
            modified_on=modified_dt, created_on=modified_dt, **kwargs)
        return fr.serialize()

    @classmethod
    def make_flow(cls, uuid, created_dt=None, **kwargs):
        if not created_dt:
            created_dt = '{}-07-11T14:10:30.591000Z'.format(
                random.randint(2000, 3000))
        flow = test_utilities.Auxiliary.make_flow(
            uuid=uuid, name='flow {} name'.format(uuid),
            created_on=created_dt, **kwargs)
        return flow.serialize()

    @classmethod
    def make_contact(cls, uuid, modified_dt=None, **kwargs):
        if not modified_dt:
            modified_dt = '{}-07-11T14:10:30.591000Z'.format(
                random.randint(2000, 3000))
        contact = test_utilities.Auxiliary.make_contact(
            uuid=uuid, name='contact {} name'.format(uuid),
            modified_on=modified_dt, **kwargs)
        return contact.serialize()


class RapidProServerMock(HTTPMock):
    def __init__(self, port='8888', path='/api/v1', hostname='127.0.0.1',
                 server_logfile=None):
        self.hostname = hostname
        self.port = port
        self.path = path
        self._pretenders = None
        if server_logfile is None:
            self.server_logfile = open(os.devnull, mode='w')
        else:
            self.server_logfile = server_logfile
        self.start_pretenders_server()
        time.sleep(2)  # wait for the server to start
        super(RapidProServerMock, self).__init__('localhost', '8888',
                                                 name='rapidpro')
        self.reset_presets()

    @staticmethod
    def _prepare_uuid_query(uuids):
        query = {'prefix': '', 'query': ''}
        if uuids:
            query['prefix'] = '\?'
        query['query'] = urlencode({'uuid': uuids}, doseq=True)
        return query

    def _prepare_uuid_filtered_json_response(self, endpoint, uuids,
                                             json_data=None):
        Endpoints.validate(endpoint)
        if json_data is None:
            json_all = json.loads(self.load_json_response(endpoint))
        else:
            json_all = json.loads(json_data)
        if not uuids:
            return json.dumps(json_all)
        filtered = []
        for i in range(len(json_all['results'])):
            uuid = json_all['results'][i]['uuid']
            if uuid in uuids:
                filtered.append(json_all['results'][i])
        json_all['results'] = filtered
        json_all['count'] = len(filtered)
        return json.dumps(json_all)

    def _setup_endpoint_presets(self, endpoint, query, json_response):
        Endpoints.validate(endpoint)
        # prepare presets / rules for pretenders
        endpoint_path = endpoint.path.replace('.', '\.')

        self.when(
            '^GET {path}/{endpoint}{prefix}{query}$'.format(
                path=self.path,
                endpoint=endpoint_path,
                prefix=query['prefix'], query=query['query']
            ),
            headers={'Authorization': 'Token {}'.format(self.get_valid_token())}
        ).reply(json_response, status=200, times=FOREVER)

        self.when(
            'POST {path}/{endpoint}'.format(
                path=self.path,
                endpoint=endpoint_path
            ),
            body=query['query'],
            headers={'Authorization': 'Token {}'.format(self.get_valid_token())}
        ).reply(json_response, status=200, times=FOREVER)

    @staticmethod
    def _prepare_time_range_data(before=None, after=None):
        iso_format = '%Y-%m-%dT%H:%M:%S.%fZ'
        prefix = ''
        query = {}
        if before:
            before_dt = datetime.datetime.strptime(before, iso_format).replace(
                tzinfo=pytz.utc)
            query['before'] = before
            prefix = '\?'
        else:
            before_dt = None
        if after:
            after_dt = datetime.datetime.strptime(after, iso_format).replace(
                tzinfo=pytz.utc)
            query['after'] = after
            prefix = '\?'
        else:
            after_dt = None
        time_range_data = {
            'format': iso_format,
            'prefix': prefix,
            'query': urlencode(query),
            'after': after_dt,
            'before': before_dt
        }
        return time_range_data

    def _prepare_datetime_filtered_json_response(
            self, endpoint, time_range_data, json_data=None):
        Endpoints.validate(endpoint)
        dt_attr_name = endpoint.datetime_attribute_name
        if json_data is None:
            json_all = json.loads(self.load_json_response(endpoint))
        else:
            json_all = json.loads(json_data)
        filtered = []
        for i in range(len(json_all['results'])):
            dt = datetime.datetime.strptime(
                json_all['results'][i][dt_attr_name],
                time_range_data['format']).replace(tzinfo=pytz.utc)
            if time_range_data['before']:
                if dt >= time_range_data['before']:
                    continue
            if time_range_data['after']:
                if dt <= time_range_data['after']:
                    continue
            filtered.append(json_all['results'][i])
        json_all['results'] = filtered
        json_all['count'] = len(filtered)
        return json.dumps(json_all)

    def get_url(self):
        return self.get_root_url() + self.path

    def get_root_url(self):
        return 'http://{hostname}:{port}/mockhttp/rapidpro'.format(
            hostname=self.hostname,
            port=self.port)

    def get_endpoint_url(self, endpoint):
        Endpoints.validate(endpoint)
        return '{root_url}/{endpoint}'.format(root_url=self.get_root_url(),
                                              endpoint=endpoint.path)

    @staticmethod
    def get_valid_token():
        return 'this-is-a-valid-token'

    @staticmethod
    def get_invalid_token():
        return 'this-is-an-INVALID-token!'

    def setup_custom_preset(self, endpoint, query, json_response):
        Endpoints.validate(endpoint)
        query_structure = {'prefix': '', 'query': ''}
        if query:
            query_structure['prefix'] = '\?'
            query_structure['query'] = urlencode(query, doseq=True)
        self._setup_endpoint_presets(endpoint=endpoint, query=query_structure,
                                     json_response=json_response)

    def setup_datetime_filtered_endpoint(
            self, endpoint, before=None, after=None, json_data=None):
        Endpoints.validate(endpoint)
        # prepare datetimes and the query
        time_range_data = self._prepare_time_range_data(before, after)
        # prepare JSON response
        json_response = self._prepare_datetime_filtered_json_response(
            endpoint, time_range_data, json_data)
        # prepare presets / rules for pretenders
        self._setup_endpoint_presets(endpoint, time_range_data, json_response)

    def setup_uuid_filtered_endpoint(
            self, endpoint, uuids=None, json_data=None, powerset=False):
        Endpoints.validate(endpoint)
        if uuids is None:
            uuids = []
        elif isinstance(uuids, str) or isinstance(uuids, unicode):
            uuids = uuids.replace('--uuid=', '').split()
        if not powerset:
            uuids_powerset = [uuids]
        else:
            uuids_powerset = set(
                chain(*{combinations(uuids, r) for r in range(len(uuids)+1)}))
        for uuids_subset in uuids_powerset:
            query = self._prepare_uuid_query(uuids_subset)
            # prepare JSON response
            json_response = self._prepare_uuid_filtered_json_response(
                endpoint, uuids_subset, json_data)
            self._setup_endpoint_presets(endpoint, query, json_response)

    def start_pretenders_server(self):
        print('\nStarting pretenders server...')
        if isinstance(self._pretenders, subprocess.Popen):
            self.stop_pretenders_server()
        self._pretenders = subprocess.Popen(
            [
                sys.executable,
                '-m', 'pretenders.server.server',
                '--host', self.hostname,
                '--port', self.port,
            ],
            stdin=self.server_logfile,
            stderr=self.server_logfile
        )
        print('Started.')

    def stop_pretenders_server(self):
        print('\nTerminating pretenders server', end='')
        if isinstance(self._pretenders, subprocess.Popen):
            self._pretenders.terminate()
            i = 0
            while self._pretenders.returncode is None:
                print('.', end='')
                self._pretenders.poll()
                time.sleep(1)
                i += 1
        self._pretenders = None
        if isinstance(self.server_logfile, file):
            self.server_logfile.close()
        print('\nTerminated.')

    def setup_invalid_token(self):
        self.when(
            'POST {path}'.format(path=self.path),
            headers={'Authorization': 'Token {}'.format(
                self.get_invalid_token())}
        ).reply(
            '{"detail":"Invalid token"}',
            status=403,
            times=FOREVER
        )
        self.when(
            '^GET {path}'.format(path=self.path),
            headers={'Authorization': 'Token {}'.format(
                self.get_invalid_token())}
        ).reply(
            '{"detail":"Invalid token"}',
            status=403,
            times=FOREVER
        )

    def reset_presets(self):
        self.reset()
        self.setup_invalid_token()

    @staticmethod
    def load_json_response(endpoint):
        Endpoints.validate(endpoint)
        with open(endpoint.fixture_path) as f:
            json_response = f.read()
        return json_response


def before_all(context):
    context.test_utilities = test_utilities
    context.rapidpro_server = RapidProServerMock()
    context.endpoints = Endpoints


def after_all(context):
    context.rapidpro_server.stop_pretenders_server()
