# coding=utf-8
from itertools import chain, combinations
import json
import copy

import sqlalchemy
import docopt
import sqlalchemy.exc
import temba_client.v1.types
from temba_client.exceptions import TembaConnectionError, TembaTokenError
import pytest
from hamcrest import *
import mock
import iocapture

import rapidpropull.cache
import rapidpropull.cli
import rapidpropull.download

from utilities import Auxiliary

__author__ = 'Tomasz J. Kotarba <tomasz@kotarba.net>'
__copyright__ = 'Copyright (c) 2016, Tomasz J. Kotarba. All rights reserved.'
__maintainer__ = 'Tomasz J. Kotarba'
__email__ = 'tomasz@kotarba.net'


class TestArgumentProcessor(Auxiliary):
    def test_all_supported_endpoint_selector_constants_defined(self):
        assert '--flow-runs' in \
            rapidpropull.cli.ArgumentProcessor.ENDPOINT_SELECTORS
        assert '--flows' in \
            rapidpropull.cli.ArgumentProcessor.ENDPOINT_SELECTORS
        assert '--contacts' in \
            rapidpropull.cli.ArgumentProcessor.ENDPOINT_SELECTORS

    def _check_get_endpoint_selector(self, selector):
        argv = [selector, '--api-token', 'a-valid-api-token']
        processor = rapidpropull.cli.ArgumentProcessor(argv)
        assert processor.get_endpoint_selector() == selector
        # it should return None when no endpoint selector supplied by user
        processor.arguments[selector] = False
        assert processor.get_endpoint_selector() is None

    def test_flow_runs_get_endpoint_selector(self):
        self._check_get_endpoint_selector('--flow-runs')

    def test_flows_get_endpoint_selector(self):
        self._check_get_endpoint_selector('--flows')

    def test_contacts_get_endpoint_selector(self):
        self._check_get_endpoint_selector('--contacts')

    def test_for_all_actions_accepts_api_token_alone(self):
        """
        It accepts API token alone for all actions that require authentication.
        """
        token = 'an-api-token'
        actions = ['--flow-runs', '--flows', '--contacts']
        for argv0 in [
            ['-t', token],
            ['--api-token', token]
        ]:
            for action in actions:
                argv = argv0[:]
                argv.append(action)
                try:
                    with iocapture.capture():
                        processed_arguments =\
                            rapidpropull.cli.ArgumentProcessor(argv)
                except docopt.DocoptExit as e:
                    pytest.fail('Terminated. DocoptExit. Wrong docopt string?'
                                ' Exception message: "{}"'.format(e.message))
                else:
                    assert processed_arguments.get_endpoint_selector() == action
                    assert processed_arguments.get_api_token() == token

    def test_for_all_actions_accepts_api_token_and_address_together(self):
        """
        It accepts RapidPro address and API token together, for all actions
        that require authentication.
        """
        token = 'an-api-token'
        address = 'rapidpro.kotarba.net'
        actions = ['--flow-runs', '--flows', '--contacts']
        for argv0 in [
            ['-a', address, '-t', token],
            ['--address', address, '--api-token', token]
        ]:
            for action in actions:
                argv = argv0[:]
                argv.append(action)
                try:
                    with iocapture.capture():
                        processed_arguments =\
                            rapidpropull.cli.ArgumentProcessor(argv)
                except docopt.DocoptExit as e:
                    pytest.fail('Terminated. DocoptExit. Wrong docopt string?'
                                ' Exception message: "{}"'.format(e.message))
                else:
                    assert processed_arguments.get_endpoint_selector() == action
                    assert processed_arguments.get_address() == address
                    assert processed_arguments.get_api_token() == token

    def test_requires_api_token_when_address_given(self):
        """
        It requires API token when RapidPro address given, for all actions
        that require authentication.
        """
        address = 'rapidpro.kotarba.net'
        actions = ['--flow-runs', '--flows', '--contacts']
        for invalid_argv0 in [
            ['-a', address],
            ['--address', address]
        ]:
            for action in actions:
                invalid_argv = invalid_argv0[:]
                invalid_argv.append(action)
                try:
                    with iocapture.capture():
                        rapidpropull.cli.ArgumentProcessor(invalid_argv)
                except docopt.DocoptExit:
                    pass
                else:
                    pytest.fail('call with missing argument accepted - wrong '
                                'docopt string?')

    def _check_endpoint_accepts_time_constraints(self, action):
        """It accepts --before or --after (if authentication data provided)."""
        before = '2011-07-11T13:50:19.860000Z'
        after = '2017-07-11T13:50:19.860000Z'
        argv0 = [action, '-t', 'a-valid-api-token']
        for do_before, do_after in ((1, 0), (0, 1), (1, 1)):
            argv = argv0[:]
            if do_before:
                argv.extend(['--before', before])
            if do_after:
                argv.extend(['--after', after])
            try:
                with iocapture.capture():
                    processed_arguments = rapidpropull.cli.ArgumentProcessor(
                        argv)
            except docopt.DocoptExit:
                pytest.fail('Terminated. DocoptExit. Wrong docopt string? '
                            'Checking before={before} & after={after} for'
                            ' {action}'.format(before=do_before, after=do_after,
                                               action=action))
            else:
                if do_before:
                    assert_that(processed_arguments.get_endpoint_kwargs(),
                                has_entry('before', before))
                if do_after:
                    assert_that(processed_arguments.get_endpoint_kwargs(),
                                has_entry('after', after))

    def test_flow_runs_accepts_time_constraints(self):
        self._check_endpoint_accepts_time_constraints('--flow-runs')

    def test_flows_accepts_time_constraints(self):
        self._check_endpoint_accepts_time_constraints('--flows')

    def test_contacts_accepts_time_constraints(self):
        self._check_endpoint_accepts_time_constraints('--contacts')

    def test_sets_default_address_when_no_address_provided(self):
        """
        It sets "rapidpro.io" as default "address" when no "address" provided.
        """
        token = 'an-api-token'
        default_rapidpro_address = 'rapidpro.io'
        try:
            with iocapture.capture():
                arguments = rapidpropull.cli.ArgumentProcessor(
                    ['--flow-runs', '-t', token])
        except docopt.DocoptExit as e:
            pytest.fail('Terminated. DocoptExit. Wrong docopt string?'
                        ' Exception message: "{}"'.format(e.message))
        else:
            assert arguments.get_address() == default_rapidpro_address

    @mock.patch('docopt.docopt')
    def test_passes_argv_to_docopt_if_argv_provided(self, docoptm):
        """It passes argv to docopt if argv provided."""
        argv = ['arg1']
        version = 'v0'
        with mock.patch('rapidpropull.cli.__version__', version):
            rapidpropull.cli.ArgumentProcessor(argv=argv)
        docoptm.assert_called_once_with(rapidpropull.cli.__doc__, argv=argv,
                                        version=version)

    @mock.patch('docopt.docopt', wraps=docopt.docopt)
    def test_correct_defaults_used(self, docopt_mock):
        """
        It uses sys.argv[:1] when constructor invoked without argv or with
        argv=None.
        It uses version=__version__.
        It sets address to rapidpro.io when no address supplied.
        """
        default_rapidpro_address = 'rapidpro.io'
        argv = ['rapidpro-pull', '--flow-runs', '--api-token=123']
        version = 'v0'
        doc = rapidpropull.cli.__doc__
        with mock.patch('sys.argv', argv):
            with mock.patch('rapidpropull.cli.__version__', version):
                with mock.patch('rapidpropull.cli.__doc__', doc):
                    result = rapidpropull.cli.ArgumentProcessor()
        docopt_mock.assert_called_with(doc, argv=argv[1:], version=version)
        assert result.get_address() == default_rapidpro_address

    def test_accepts_zero_or_more_uuids_for_selected_endpoints(self):
        """
        It accepts zero or more UUIDs for all actions that allow it (if
        authentication data provided).
        """
        token = 'a-valid-rapidpro-token'
        actions_where_uuids_allowed = ['--flows', '--contacts']
        argv0 = ['-t', token]
        for action in actions_where_uuids_allowed:
            argv1 = argv0[:]
            argv1.append(action)
            # let us test for UUID sets [[], ['1'], ['1', '2'], ['1', '2', '3']]
            for uuids in [map(str,
                              l) for l in [range(1, i + 1) for i in range(4)]]:
                argv = argv1[:]
                if uuids:
                    argv.extend(['--uuid={}'.format(uuid) for uuid in uuids])
                try:
                    with iocapture.capture():
                        processed_arguments =\
                            rapidpropull.cli.ArgumentProcessor(argv)
                except docopt.DocoptExit:
                    pytest.fail('Terminated. DocoptExit. Wrong docopt string? '
                                'Checking {}.'.format(action))
                else:
                    result = processed_arguments.get_endpoint_kwargs()
                    if uuids:
                        assert_that(
                            result,
                            has_entry('uuids', uuids)
                        )
                    else:
                        assert 'uuids' not in result

    def test_get_selectors_of_requested_associations(self):
        argv0 = ['--flow-runs', '--api-token=a-valid-token']
        s = ('--with-flows', '--with-contacts')  # allowed association requests
        cc = chain(*(combinations(s, r) for r in range(1, len(s) + 1)))
        for c in cc:
            argv = argv0[:]
            argv.extend(c)
            try:
                with iocapture.capture():
                    processed_arguments = rapidpropull.cli.ArgumentProcessor(
                        argv)
            except docopt.DocoptExit:
                pytest.fail('Terminated. DocoptExit. Wrong docopt string?')
            else:
                result = processed_arguments. \
                    get_selectors_of_requested_associations()
                assert isinstance(result, tuple)
                if '--with-flows' in c:
                    assert '--flows' in processed_arguments. \
                        get_selectors_of_requested_associations()
                if '--with-contacts' in c:
                    assert '--contacts' in processed_arguments. \
                        get_selectors_of_requested_associations()

    def test_requested_associations_only_allowed_for_flow_runs(self):
        selectors_to_test = ['--flows', '--contacts']
        argv0 = ['--api-token=a-valid-token']
        s = ('--with-flows', '--with-contacts')  # allowed association requests
        cc = set(chain(*(combinations(s, r) for r in range(1, len(s) + 1))))
        for es in selectors_to_test:
            argv1 = argv0[:]
            argv1.append(es)
            for c in cc:
                argv = argv1[:]
                argv.extend(c)
                with pytest.raises(docopt.DocoptExit):
                    rapidpropull.cli.ArgumentProcessor(argv)
                    pytest.fail('It should have raised DocoptExit for'
                                ' {}'.format(es))

    def test_all_arguments_allowed_for_flow_runs_accepted(self):
        after = '2013-07-11T13:49:10.750000Z'
        before = '2015-07-11T13:49:10.750000Z'
        argv = ['--flow-runs',
                '--api-token=a-valid-token', '--address=some.address.io',
                '--after={}'.format(after),
                '--before={}'.format(before),
                '--with-flows',
                '--with-contacts',
                '--cache', 'sqlite://'
                ]
        endpoint_kwargs = {'after': after, 'before': before}
        processed_arguments = rapidpropull.cli.ArgumentProcessor(argv)
        assert processed_arguments.get_address() == 'some.address.io'
        assert processed_arguments.get_api_token() == 'a-valid-token'
        assert processed_arguments.get_endpoint_selector() == '--flow-runs'
        assert processed_arguments.get_endpoint_kwargs() == endpoint_kwargs
        assert '--flows' in \
               processed_arguments.get_selectors_of_requested_associations()
        assert '--contacts' in \
               processed_arguments.get_selectors_of_requested_associations()
        assert processed_arguments.get_cache_url() == 'sqlite://'

    def test_all_arguments_allowed_for_flows_accepted(self):
        after = '2013-07-11T13:49:10.750000Z'
        before = '2015-07-11T13:49:10.750000Z'
        argv = ['--flows',
                '--api-token=a-valid-token', '--address=some.address.io',
                '--after={}'.format(after),
                '--before={}'.format(before),
                '--uuid=a', '--uuid=b', '--uuid=c',
                '--cache', 'sqlite://'
                ]
        endpoint_kwargs = {'after': after, 'before': before,
                           'uuids': ['a', 'b', 'c']}
        processed_arguments = rapidpropull.cli.ArgumentProcessor(argv)
        assert processed_arguments.get_address() == 'some.address.io'
        assert processed_arguments.get_api_token() == 'a-valid-token'
        assert processed_arguments.get_endpoint_selector() == '--flows'
        assert processed_arguments.get_endpoint_kwargs() == endpoint_kwargs
        assert processed_arguments.get_cache_url() == 'sqlite://'

    def test_all_arguments_allowed_for_contacts_accepted(self):
        after = '2013-07-11T13:49:10.750000Z'
        before = '2015-07-11T13:49:10.750000Z'
        argv = ['--contacts',
                '--api-token=a-valid-token', '--address=some.address.io',
                '--after={}'.format(after),
                '--before={}'.format(before),
                '--uuid=a', '--uuid=b', '--uuid=c',
                '--cache', 'sqlite://'
                ]
        endpoint_kwargs = {'after': after, 'before': before,
                           'uuids': ['a', 'b', 'c']}
        processed_arguments = rapidpropull.cli.ArgumentProcessor(argv)
        assert processed_arguments.get_address() == 'some.address.io'
        assert processed_arguments.get_api_token() == 'a-valid-token'
        assert processed_arguments.get_endpoint_selector() == '--contacts'
        assert processed_arguments.get_endpoint_kwargs() == endpoint_kwargs
        assert processed_arguments.get_cache_url() == 'sqlite://'


class TestDownloadTask(Auxiliary):
    # noinspection PyUnusedLocal
    def test_requires_processed_arguments(self):
        # noinspection PyUnresolvedReferences
        assert 'processed_arguments' in \
               rapidpropull.download.DownloadTask.__init__.__code__.co_varnames
        with pytest.raises(TypeError) as excinfo:
            # noinspection PyArgumentList
            rapidpropull.download.DownloadTask()
        assert excinfo.match('takes .* arguments')
        try:
            mock_argument_processor = mock.Mock()
            rapidpropull.download.DownloadTask(
                processed_arguments=mock_argument_processor)
        except TypeError as e:
            assert "got an unexpected keyword argument" \
                   " 'processed_arguments'" not in e.message

    def test_client_instantiated_by_constructor(self):
        selectors = ['--flow-runs', '--flows', '--contacts']
        token = 'a-valid-token'
        address = 'rapidpro.kotarba.net'
        for selector in selectors:
            argv = [selector, '--api-token', token, '--address', address]
            arguments = rapidpropull.cli.ArgumentProcessor(argv)
            with mock.patch('temba_client.v1.TembaClient') as TC:
                TC.return_value = object()
                download_task = rapidpropull.download.DownloadTask(arguments)
                TC.assert_called_once_with(address, token)
                assert download_task.client is TC()

    # noinspection PyUnusedLocal
    @mock.patch('temba_client.v1.TembaClient')
    def test_cache_set_to_none_if_no_cache_url_given(self, temba_client_class):
        selectors = ['--flow-runs', '--flows', '--contacts']
        token = 'a-valid-token'
        address = 'rapidpro.kotarba.net'
        for selector in selectors:
            argv = [selector, '--api-token', token]
            arguments = rapidpropull.cli.ArgumentProcessor(argv)
            with mock.patch('rapidpropull.cache.RapidProCache') as RPC:
                download_task = rapidpropull.download.DownloadTask(arguments)
                RPC.assert_not_called()
                assert download_task.cache is None

    # noinspection PyUnusedLocal
    @mock.patch('temba_client.v1.TembaClient')
    def test_cache_instantiated_by_constructor_if_cache_url_given(
            self, temba_client_class):
        selectors = ['--flow-runs', '--flows', '--contacts']
        token = 'a-valid-token'
        address = 'rapidpro.kotarba.net'
        cache_url = 'sqlite://'
        for selector in selectors:
            argv = [selector, '--api-token', token, '--cache', cache_url]
            arguments = rapidpropull.cli.ArgumentProcessor(argv)
            with mock.patch('rapidpropull.cache.RapidProCache',
                            autospec=True) as rapidprocache_class:
                download_task = rapidpropull.download.DownloadTask(arguments)
                rapidprocache_class.assert_called_once_with(cache_url)
                assert download_task.cache is rapidprocache_class.return_value

    # noinspection PyUnusedLocal
    @mock.patch('temba_client.v1.TembaClient')
    @mock.patch('rapidpropull.cli.ArgumentProcessor')
    def test_endpoint_selector_set(self, argument_processor_class,
                                   temba_client_class):
        expected = object()
        argument_processor_class.return_value. \
            get_endpoint_selector.return_value = expected
        argument_processor_class.return_value. \
            get_cache_url.return_value = None
        download_task = rapidpropull.download.DownloadTask(
            argument_processor_class())
        assert download_task.endpoint_selector is expected

    # noinspection PyPep8Naming,PyUnusedLocal
    @mock.patch('temba_client.v1.TembaClient')
    @mock.patch('rapidpropull.cli.ArgumentProcessor')
    def test_endpoint_kwargs_set(self, argument_processor_class,
                                 temba_client_class):
        expected = object()
        argument_processor_class.return_value. \
            get_endpoint_kwargs.return_value = expected
        argument_processor_class.return_value. \
            get_cache_url.return_value = None
        download_task = rapidpropull.download.DownloadTask(
            argument_processor_class())
        assert download_task.endpoint_kwargs is expected

    # noinspection PyUnusedLocal
    @mock.patch('temba_client.v1.TembaClient')
    @mock.patch('rapidpropull.cli.ArgumentProcessor')
    def test_selectors_of_requested_associations_set(
            self, argument_processor_class, temba_client_class):
        expected = object()
        argument_processor_class.return_value. \
            get_selectors_of_requested_associations.return_value = expected
        argument_processor_class.return_value. \
            get_cache_url.return_value = None
        download_task = rapidpropull.download.DownloadTask(
            argument_processor_class())
        assert download_task.selectors_of_requested_associations is expected

    @mock.patch('temba_client.v1.TembaClient')
    def test_flow_runs_kwargs_passed_to_temba_client_on_download(
            self, temba_client_class):
        expected = []
        download_task = self.make_download_task('--flow-runs', expected,
                                                temba_client_class)
        download_task.download()
        temba_client_class.return_value.get_runs.assert_called_once_with(
            **download_task.endpoint_kwargs)

    @mock.patch('temba_client.v1.TembaClient')
    def test_endpoint_kwargs_passed_to_temba_client_on_download(
            self, temba_client_class):
        expected = []
        # flow runs
        download_task = self.make_download_task('--flow-runs', expected,
                                                temba_client_class)
        download_task.download()
        temba_client_class.return_value.get_runs.assert_called_once_with(
            **download_task.endpoint_kwargs)
        # flows
        download_task = self.make_download_task('--flows', expected,
                                                temba_client_class)
        download_task.download()
        temba_client_class.return_value.get_flows.assert_called_once_with(
            **download_task.endpoint_kwargs)
        # contacts
        download_task = self.make_download_task('--contacts', expected,
                                                temba_client_class)
        download_task.download()
        temba_client_class.return_value.get_contacts.assert_called_once_with(
            **download_task.endpoint_kwargs)

    @mock.patch('temba_client.v1.TembaClient')
    def test_overwrite_downloaded_data(self, temba_client_class):
        selectors = ['--flow-runs', '--flows', '--contacts']
        for selector in selectors:
            expected = object()
            download_task = self.make_download_task(selector, expected,
                                                    temba_client_class)
            download_task.overwrite_downloaded_data(expected)
            assert download_task.get_downloaded_objects() is expected

    @mock.patch('temba_client.v1.TembaClient')
    def test_download_flow_runs(self, temba_client_class):
        expected_download = [object(), object(), object()]
        download_task = self.make_download_task(
            '--flow-runs', expected_download, temba_client_class)
        download_task.download()
        temba_client_class.return_value.get_runs.assert_called_once_with(
            **download_task.endpoint_kwargs)
        downloaded = download_task.get_downloaded_objects()
        assert_that(downloaded, contains_inanyorder(*expected_download))
        assert_that(downloaded, only_contains(*expected_download))

    @staticmethod
    def _prepare_runs_flows_contacts(temba_client_class):
        runs = []
        flows = []
        contacts = []
        for i in range(3):
            runs.append(mock.MagicMock(spec=temba_client.v1.types.Run, id=i,
                                       contact='contact{}'.format(i),
                                       flow='flow{}'.format(i)))
            flows.append(mock.MagicMock(spec=temba_client.v1.types.Flow,
                                        uuid='flow{}'.format(i),
                                        name='flow{} name'.format(i)))
            contacts.append(mock.MagicMock(spec=temba_client.v1.types.Contact,
                                           uuid='contact{}'.format(i),
                                           name='contact{} name'.format(i)))

        temba_client_class.return_value.get_runs.return_value = runs
        temba_client_class.return_value.get_flows.return_value = flows
        temba_client_class.return_value.get_contacts.return_value = contacts
        return {'runs': runs, 'flows': flows, 'contacts': contacts}

    @mock.patch('temba_client.v1.TembaClient')
    def test_download_flow_runs_with_all_associations(self, temba_client_class):
        expected = self._prepare_runs_flows_contacts(temba_client_class)
        argv = ['--api-token=a-token', '--flow-runs', '--with-flows',
                '--with-contacts']
        download_task = rapidpropull.download.DownloadTask(
            rapidpropull.cli.ArgumentProcessor(argv))
        download_task.download()
        downloaded = download_task.get_downloaded_objects()
        assert isinstance(downloaded, dict)
        assert 'runs' in downloaded
        assert 'flows' in downloaded
        assert 'contacts' in downloaded
        assert downloaded == expected

    @mock.patch('temba_client.v1.TembaClient')
    def test_download_flow_runs_with_associated_flows(self, temba_client_class):
        mock_objects = self._prepare_runs_flows_contacts(temba_client_class)
        expected_runs = mock_objects['runs']
        expected_flows = mock_objects['flows']
        argv = ['--api-token=a-token', '--flow-runs', '--with-flows']
        download_task = rapidpropull.download.DownloadTask(
            rapidpropull.cli.ArgumentProcessor(argv))
        download_task.download()
        downloaded = download_task.get_downloaded_objects()
        assert isinstance(downloaded, dict)
        assert 'runs' in downloaded
        assert 'flows' in downloaded
        assert 'contacts' not in downloaded
        assert downloaded['runs'] == expected_runs
        assert downloaded['flows'] == expected_flows

    @mock.patch('temba_client.v1.TembaClient')
    def test_download_flow_runs_with_associated_contacts(self,
                                                         temba_client_class):
        mock_objects = self._prepare_runs_flows_contacts(temba_client_class)
        expected_runs = mock_objects['runs']
        expected_contacts = mock_objects['contacts']
        argv = ['--api-token=a-token', '--flow-runs', '--with-contacts']
        download_task = rapidpropull.download.DownloadTask(
            rapidpropull.cli.ArgumentProcessor(argv))
        download_task.download()
        downloaded = download_task.get_downloaded_objects()
        assert isinstance(downloaded, dict)
        assert 'runs' in downloaded
        assert 'flows' not in downloaded
        assert 'contacts' in downloaded
        assert downloaded['runs'] == expected_runs
        assert downloaded['contacts'] == expected_contacts

    @mock.patch('temba_client.v1.TembaClient')
    def test_download_flows(self, temba_client_class):
        expected = [object(), object(), object()]
        download_task = self.make_download_task('--flows', expected,
                                                temba_client_class)
        download_task.download()
        temba_client_class.return_value.get_flows.assert_called_once_with(
            **download_task.endpoint_kwargs)
        downloaded = download_task.get_downloaded_objects()
        assert_that(downloaded, contains_inanyorder(*expected))
        assert_that(downloaded, only_contains(*expected))

    @mock.patch('temba_client.v1.TembaClient')
    def test_download_contacts(self, temba_client_class):
        expected = [object(), object(), object()]
        download_task = self.make_download_task('--contacts', expected,
                                                temba_client_class)
        download_task.download()
        temba_client_class.return_value.get_contacts.assert_called_once_with(
            **download_task.endpoint_kwargs)
        downloaded = download_task.get_downloaded_objects()
        assert_that(downloaded, contains_inanyorder(*expected))
        assert_that(downloaded, only_contains(*expected))

    @mock.patch('temba_client.v1.TembaClient')
    def test_download_throws_exception_for_invalid_endpoint_selector(
            self, temba_client_class):
        download_task = self.make_download_task('--flow-runs', None,
                                                temba_client_class)
        download_task.endpoint_selector = 'an-invalid-endpoint-selector'
        with pytest.raises(ValueError) as excinfo:
            download_task.download()
        assert excinfo.match('Invalid endpoint selector "{}"'.format(
            download_task.endpoint_selector))

    @mock.patch('temba_client.v1.TembaClient')
    def test_get_downloaded_data_as_json_structure(self, temba_client_class):
        expected_download = [self.make_serializable(11),
                             self.make_serializable(22),
                             self.make_serializable(33)]
        download_task = self.make_download_task(
            '--flow-runs', expected_download, temba_client_class)
        download_task.download()
        serializable = download_task.get_downloaded_json_structure()
        assert set(serializable) == {11, 22, 33}

    def test_get_downloaded_flow_runs_with_associations_as_json_structure(
            self):
        argv = ['--api-token=a-token', '--flow-runs', '--with-flows',
                '--with-contacts']
        download_task = rapidpropull.download.DownloadTask(
            rapidpropull.cli.ArgumentProcessor(argv))
        expected_download = {'runs': [], 'flows': [], 'contacts': []}
        for i in range(3):
            for k in expected_download:
                expected_download[k].append(
                    self.make_serializable('{}{}'.format(k, i)))
        download_task.overwrite_downloaded_data(expected_download)
        expected = {}
        for k in expected_download:
            expected[k] = [o.serialize() for o in expected_download[k]]
        result = download_task.get_downloaded_json_structure()
        assert result == expected

    def test_get_downloaded_json_structure_returns_none_on_empty(self):
        argv = ['--api-token=a-token', '--flow-runs', '--with-flows',
                '--with-contacts']
        download_task = rapidpropull.download.DownloadTask(
            rapidpropull.cli.ArgumentProcessor(argv))
        download_task.overwrite_downloaded_data(None)
        result = download_task.get_downloaded_json_structure()
        assert result is None

    def _download_should_raise_correct_exception_on_connection_problems(
            self, temba_client_class, exception):
        selectors = ['--flow-runs', '--flows', '--contacts']
        temba_client_class.return_value.get_runs.side_effect = exception
        temba_client_class.return_value.get_flows.side_effect = exception
        temba_client_class.return_value.get_contacts.side_effect = exception
        download_tasks = [self.make_download_task(s, None, temba_client_class)
                          for s in selectors]
        for dt in download_tasks:
            assert_that(
                calling(dt.download),
                raises(exception.__class__, exception.message),
                'Exception "{message}" not raised for {selector}'.format(
                    message=exception.message, selector=dt.endpoint_selector))

    @mock.patch('temba_client.v1.TembaClient')
    def test_unable_to_connect_to_host(self, temba_client_class):
        """
        It raises an exception when unable to connect to the provided host.
        """
        exception = TembaConnectionError()
        self._download_should_raise_correct_exception_on_connection_problems(
            temba_client_class, exception)

    @mock.patch('temba_client.v1.TembaClient')
    def test_invalid_token(self, temba_client_class):
        """
        It raises an exception when unable to authenticate with the
        provided token.
        """
        exception = TembaTokenError()
        self._download_should_raise_correct_exception_on_connection_problems(
            temba_client_class, exception)

    @mock.patch('rapidpropull.cache.RapidProCache', autospec=True)
    @mock.patch('temba_client.v1.TembaClient')
    def _download_substitutes_cached_for_downloaded_and_stores_result(
            self, endpoint_selector, temba_client_class, rapidprocache_class):
        expected_download = [object(), object(), object()]
        substituted = [expected_download[0], object(), object()]
        download_task = self.make_download_task(
            endpoint_selector, expected_download, temba_client_class,
            optional_argv=['--cache', 'sqlite://'])

        def substitute_side_effect(objects):
            objects[1] = substituted[1]
            objects[2] = substituted[2]
        rapidprocache_class.return_value.substitute_cached_for_downloaded.\
            side_effect = substitute_side_effect
        download_task.download()
        # does download task make a request to cache to make substitutions
        rapidprocache_class.return_value.substitute_cached_for_downloaded.\
            assert_called_with(expected_download)
        # does download task make a request to cache to store all new objects
        rapidprocache_class.return_value.insert_objects.\
            assert_called_with(substituted)
        # are objects correctly stored in DownloadTask
        stored = download_task.get_downloaded_objects()
        assert_that(stored, contains_inanyorder(*substituted))
        assert_that(stored, only_contains(*substituted))

    def test_download_flow_runs_uses_cache_as_expected(self):
        self._download_substitutes_cached_for_downloaded_and_stores_result(
            '--flow-runs')

    def test_download_flows_uses_cache_as_expected(self):
        self._download_substitutes_cached_for_downloaded_and_stores_result(
            '--flows')

    def test_download_contacts_uses_cache_as_expected(self):
        self._download_substitutes_cached_for_downloaded_and_stores_result(
            '--contacts')

    @mock.patch('rapidpropull.cache.RapidProCache', autospec=True)
    @mock.patch('temba_client.v1.TembaClient')
    def test_cache_and_downloading_flow_runs_with_all_associations(
            self, temba_client_class, rapidprocache_class):
        # set up mock objects already in cache
        cached_run1 = mock.MagicMock(spec=temba_client.v1.types.Run, id=1,
                                     contact='contact3', flow='flow1')
        cached_contact0 = mock.MagicMock(spec=temba_client.v1.types.Contact,
                                         uuid='contact0',
                                         name='cached contact 0')
        cached_contact3 = mock.MagicMock(spec=temba_client.v1.types.Contact,
                                         uuid='contact3',
                                         name='cached contact 3')
        cached_flow1 = mock.MagicMock(spec=temba_client.v1.types.Flow,
                                      uuid='flow1', name='cached flow 1')
        expected_downloads = self._prepare_runs_flows_contacts(
            temba_client_class)
        # objects already in cache should not be requested and, thus, returned
        expected_downloads['flows'].pop(1)
        expected_downloads['contacts'].pop(0)
        # contact1 should not be requested as cached_run1 references
        # contact3 instead
        expected_downloads['contacts'].pop(0)
        contact_uuids_to_request = {'contact0', 'contact3', 'contact2'}
        uuids_of_contacts_to_download = {'contact2'}
        flow_uuids_to_request = {'flow0', 'flow1', 'flow2'}
        uuids_of_flows_to_download = {'flow0', 'flow2'}
        # update what mock download functions should return
        temba_client_class.return_value.get_contacts.return_value = \
            expected_downloads['contacts']
        temba_client_class.return_value.get_flows.return_value =\
            expected_downloads['flows']
        # the expected result stored in download task afterwards
        expected_runs = {expected_downloads['runs'][0], cached_run1,
                         expected_downloads['runs'][2]}
        expected_contacts = {expected_downloads['contacts'][0]}.union(
            {cached_contact0, cached_contact3})
        expected_flows = set(expected_downloads['flows']).union({cached_flow1})
        # prepare a download task
        argv = ['--api-token=a-token', '--flow-runs', '--with-flows',
                '--with-contacts', '--cache', 'sqlite://']
        download_task = rapidpropull.download.DownloadTask(
            rapidpropull.cli.ArgumentProcessor(argv))

        def mock_get_objects(endpoint_selector, uuids):
            if uuids == contact_uuids_to_request:
                return [cached_contact0,
                        cached_contact3], uuids_of_contacts_to_download
            elif uuids == flow_uuids_to_request:
                return [cached_flow1], uuids_of_flows_to_download
            else:
                raise ValueError('function should not have been called with'
                                 ' ({}, {})'.format(endpoint_selector,
                                                    str(uuids)))
        rapidprocache_class.return_value.get_objects.side_effect =\
            mock_get_objects

        def substitute_side_effect(objects):
            objects[1] = cached_run1
        rapidprocache_class.return_value.substitute_cached_for_downloaded.\
            side_effect = substitute_side_effect

        download_task.download()

        # download task should make a request to cache to make substitutions
        rapidprocache_class.return_value.substitute_cached_for_downloaded. \
            assert_called_once_with(expected_downloads['runs'])
        # download task should get previously cached associations from cache
        expected_get_object_calls = [
            mock.call('--contacts', contact_uuids_to_request),
            mock.call('--flows', flow_uuids_to_request)]
        rapidprocache_class.return_value.get_objects.assert_has_calls(
            expected_get_object_calls, any_order=True)
        # associations missing from cache should be downloaded
        temba_client_class.return_value.get_flows.assert_called_once_with(
            uuids=uuids_of_flows_to_download)
        temba_client_class.return_value.get_contacts.assert_called_once_with(
            uuids=uuids_of_contacts_to_download)

        stored_result = download_task.get_downloaded_objects()
        assert set(stored_result['runs']) == expected_runs
        assert set(stored_result['contacts']) == expected_contacts
        assert set(stored_result['flows']) == expected_flows


class TestRapidProCache(Auxiliary):
    @staticmethod
    def _insert_into_cache(cache, list_or_object_to_insert):
        if not isinstance(list_or_object_to_insert, list):
            list_or_object_to_insert = [list_or_object_to_insert]
        for object_to_insert in list_or_object_to_insert:
            if isinstance(object_to_insert, temba_client.v1.types.Run):
                insert = cache.database.tables['flowrun'].insert()
                cache.database.bind.execute(
                    insert, {
                        'run': object_to_insert.id,
                        'json': json.dumps(object_to_insert.serialize()),
                        'contact': object_to_insert.contact,
                        'flow': object_to_insert.flow
                    }
                )
            elif isinstance(object_to_insert, temba_client.v1.types.Flow):
                insert = cache.database.tables['flow'].insert()
                cache.database.bind.execute(
                    insert, {
                        'uuid': object_to_insert.uuid,
                        'json': json.dumps(object_to_insert.serialize()),
                    }
                )
            elif isinstance(object_to_insert, temba_client.v1.types.Contact):
                insert = cache.database.tables['contact'].insert()
                cache.database.bind.execute(
                    insert, {
                        'uuid': object_to_insert.uuid,
                        'json': json.dumps(object_to_insert.serialize()),
                    }
                )
            else:
                raise TypeError(
                    'Wrong type "{}".  The object must be an instance of Run,'
                    ' Flow or Contact.'.format(type(object_to_insert)))

    def test_invalid_type(self):
        assert rapidpropull.cache.RapidProCache.INVALID_TYPE == \
               'Invalid type "{}".  The object must be an instance of Run,' \
               ' Flow or Contact.'

    def test_invalid_endpoint_selector(self):
        assert rapidpropull.cache.RapidProCache.INVALID_ENDPOINT_SELECTOR == \
               'Invalid endpoint selector "{}".'

    def test_constructor_requires_cache_url(self):
        # noinspection PyUnresolvedReferences
        assert 'cache_url' in \
               rapidpropull.cache.RapidProCache.__init__.__code__.co_varnames
        with pytest.raises(TypeError) as excinfo:
            # noinspection PyArgumentList
            rapidpropull.cache.RapidProCache()
        assert excinfo.match('takes .* arguments')
        try:
            rapidpropull.cache.RapidProCache(cache_url='sqlite://')
        except TypeError as e:
            assert "got an unexpected keyword argument" \
                   " 'cache_url'" not in e.message

    def test_constructor_initialises_database(self):
        cache_url = 'sqlite://'
        cache = rapidpropull.cache.RapidProCache(cache_url)
        # Test initialisation and binding of engine and metadata:
        assert getattr(cache, 'database', False)
        assert isinstance(cache.database, sqlalchemy.MetaData)
        # noinspection PyUnresolvedReferences
        assert str(cache.database.bind.url) == cache_url
        # Test database schema:
        # table 'flowrun'
        assert 'flowrun' in cache.database.tables
        flowrun = cache.database.tables['flowrun']
        assert 'run' in flowrun.columns
        assert flowrun.columns['run'].primary_key
        assert isinstance(flowrun.columns['run'].type, sqlalchemy.Integer)
        assert 'json' in flowrun.columns
        assert isinstance(flowrun.columns['json'].type, sqlalchemy.Text)
        assert 'flow_uuid' in flowrun.columns
        assert list(flowrun.columns['flow_uuid'].foreign_keys
                    )[0].target_fullname == 'flow.uuid'
        assert 'contact_uuid' in flowrun.columns
        assert len(flowrun.columns['contact_uuid'].foreign_keys) == 1
        assert list(flowrun.columns['contact_uuid'].foreign_keys
                    )[0].target_fullname == 'contact.uuid'
        # table 'flow'
        assert 'flow' in cache.database.tables
        flow = cache.database.tables['flow']
        assert 'uuid' in flow.columns
        assert flow.columns['uuid'].primary_key
        assert isinstance(flow.columns['uuid'].type, sqlalchemy.String)
        # noinspection PyUnresolvedReferences
        assert flow.columns['uuid'].type.length == 36
        assert 'json' in flow.columns
        assert isinstance(flow.columns['json'].type, sqlalchemy.Text)
        # table 'contact'
        assert 'contact' in cache.database.tables
        contact = cache.database.tables['contact']
        assert 'uuid' in contact.columns
        assert contact.columns['uuid'].primary_key
        assert isinstance(contact.columns['uuid'].type, sqlalchemy.String)
        # noinspection PyUnresolvedReferences
        assert contact.columns['uuid'].type.length == 36
        assert 'json' in contact.columns
        assert isinstance(contact.columns['json'].type, sqlalchemy.Text)

    def test_get_flow_run(self):
        cache_url = 'sqlite://'
        cache = rapidpropull.cache.RapidProCache(cache_url)
        # request a flow run from an empty cache
        result = cache.get_flow_run(run_id=1)
        assert result is None
        # request a cached flow run
        flowrun = self.make_flow_run()
        self._insert_into_cache(cache, flowrun)
        result = cache.get_flow_run(run_id=flowrun.id)
        assert isinstance(result, temba_client.v1.types.Run)
        assert result.id == flowrun.id
        assert result.contact == flowrun.contact
        assert result.flow == flowrun.flow
        assert result.serialize() == flowrun.serialize()
        # request a flow run which has not been cached
        result = cache.get_flow_run(run_id=flowrun.id + 1)
        assert result is None

    def test_get_flow(self):
        cache_url = 'sqlite://'
        cache = rapidpropull.cache.RapidProCache(cache_url)
        # request a flow from an empty cache
        result = cache.get_flow(flow_uuid='some-uuid')
        assert result is None
        # request a cached flow
        flow = self.make_flow()
        self._insert_into_cache(cache, flow)
        result = cache.get_flow(flow_uuid=flow.uuid)
        assert isinstance(result, temba_client.v1.types.Flow)
        assert result.uuid == flow.uuid
        assert result.serialize() == flow.serialize()
        # request a flow run which has not been cached
        result = cache.get_flow(flow_uuid=flow.uuid+'1')
        assert result is None

    def test_get_contact(self):
        cache_url = 'sqlite://'
        cache = rapidpropull.cache.RapidProCache(cache_url)
        # request a contact from an empty cache
        result = cache.get_contact(contact_uuid='some-uuid')
        assert result is None
        # request a cached contact
        contact = self.make_contact()
        self._insert_into_cache(cache, contact)
        result = cache.get_contact(contact_uuid=contact.uuid)
        assert isinstance(result, temba_client.v1.types.Contact)
        assert result.uuid == contact.uuid
        assert result.serialize() == contact.serialize()
        # request a contact run which has not been cached
        result = cache.get_contact(contact_uuid=contact.uuid+'1')
        assert result is None

    def test_insert_objects(self):
        cache_url = 'sqlite://'
        cache = rapidpropull.cache.RapidProCache(cache_url)
        run0 = self.make_flow_run()
        contact0 = self.make_contact()
        flow0 = self.make_flow()
        assert cache.get_flow_run(run0.id) is None
        assert cache.get_flow(flow0.uuid) is None
        assert cache.get_contact(contact0.uuid) is None
        # accepts a dictionary of iterables
        cache.insert_objects({'flows': [flow0]})
        # accepts an iterable
        cache.insert_objects([run0, contact0])
        assert cache.get_flow_run(run0.id).serialize() == run0.serialize()
        assert cache.get_flow(flow0.uuid).serialize() == flow0.serialize()
        assert cache.get_contact(contact0.uuid).serialize() ==\
            contact0.serialize()

    def test_insert_objects_unsupported_type(self):
        cache_url = 'sqlite://'
        cache = rapidpropull.cache.RapidProCache(cache_url)
        unsupported_object = object()
        with pytest.raises(TypeError) as excinfo:
            cache.insert_objects([unsupported_object])
        excinfo.match(cache.INVALID_TYPE.format(type(unsupported_object)))

    def test_insert_objects_skips_already_cached(self):
        cache_url = 'sqlite://'
        cache = rapidpropull.cache.RapidProCache(cache_url)
        run0 = self.make_flow_run()
        contact0 = self.make_contact()
        flow0 = self.make_flow()
        expected_run0_contact = run0.contact
        expected_contact0_name = contact0.name
        expected_flow0_name = flow0.name
        cache.insert_objects([run0, contact0, flow0])
        run0.contact = 'duplicate'
        contact0.name = 'duplicate'
        flow0.name = 'duplicate'
        try:
            cache.insert_objects([run0, contact0, flow0])
        except sqlalchemy.exc.IntegrityError:
            pytest.fail('RapidProCache.insert_objects should not try to'
                        ' reinsert objects already in cache.')
        assert cache.get_flow_run(run0.id).contact == expected_run0_contact
        assert cache.get_contact(contact0.uuid).name == expected_contact0_name
        assert cache.get_flow(flow0.uuid).name == expected_flow0_name

    def test_get_objects(self):
        for endpoint_selector in\
                rapidpropull.cli.ArgumentProcessor.ENDPOINT_SELECTORS:
            id_attr = 'uuid'
            if endpoint_selector == '--flow-runs':
                make_object = self.make_flow_run
                id_attr = 'id'
            elif endpoint_selector == '--flows':
                make_object = self.make_flow
            elif endpoint_selector == '--contacts':
                make_object = self.make_contact
            else:
                raise ValueError('Unknown endpoint selector'
                                 ' "{}".'.format(endpoint_selector))
            cached = []
            uuids = set()
            for i in range(5):
                cached.append(make_object())
                uuids.add(getattr(cached[i], id_attr))
            not_cached = set()
            i = 3
            while i:
                uuid = getattr(make_object(), id_attr)
                if uuid in uuids:
                    continue
                else:
                    not_cached.add(uuid)
                    i -= 1
            cache_url = 'sqlite://'
            cache = rapidpropull.cache.RapidProCache(cache_url)
            self._insert_into_cache(cache, cached)
            objects, missing_uuids = cache.get_objects(endpoint_selector,
                                                       uuids.union(not_cached))
            assert missing_uuids == not_cached
            expected_objects = [o.serialize() for o in cached]
            fetched_objects = [o.serialize() for o in objects]
            assert_that(fetched_objects, contains_inanyorder(*expected_objects))
            assert_that(fetched_objects, only_contains(*expected_objects))

    def test_get_objects_unsupported_endpoint_selector(self):
        cache_url = 'sqlite://'
        cache = rapidpropull.cache.RapidProCache(cache_url)
        invalid_selector = '--unsupported-selector'
        with pytest.raises(ValueError) as excinfo:
            cache.get_objects(invalid_selector, ['uuid1', 'uuid2'])
        excinfo.match(cache.INVALID_ENDPOINT_SELECTOR.format(invalid_selector))

    def test_substitute_cached_for_downloaded(self):
        downloaded = []
        for i in range(5):
            downloaded.append(self.make_flow_run())
            downloaded.append(self.make_contact())
            downloaded.append(self.make_flow())
        expected = [copy.copy(o) for o in downloaded]
        cached = [copy.copy(downloaded[0])]
        cached[0].completed = True
        expected[0] = cached[0]
        cached.append(copy.copy(downloaded[4]))  # contact
        cached[1].name = 'cached contact'
        expected[4] = cached[1]
        cached.append(copy.copy(downloaded[14]))  # flow
        cached[2].name = 'cached flow'
        expected[14] = cached[2]
        expected = [o.serialize() for o in expected]
        cache_url = 'sqlite://'
        cache = rapidpropull.cache.RapidProCache(cache_url)
        for o in cached:
            self._insert_into_cache(cache, o)
        cache.substitute_cached_for_downloaded(downloaded)
        assert [o.serialize() for o in downloaded] == expected

    def test_substitute_cached_for_downloaded_unsupported_type(self):
        cache_url = 'sqlite://'
        cache = rapidpropull.cache.RapidProCache(cache_url)
        unsupported_object = object()
        with pytest.raises(TypeError) as excinfo:
            cache.substitute_cached_for_downloaded([unsupported_object])
        excinfo.match(cache.INVALID_TYPE.format(type(unsupported_object)))


class TestMain(Auxiliary):
    # noinspection PyBroadException,PyUnusedLocal
    @mock.patch('rapidpropull.download.DownloadTask')
    @mock.patch('rapidpropull.cli.ArgumentProcessor')
    def test_argv_passed_to_argument_processor(self, argument_processor, *args):
        """
        It passes argv to ArgumentProcessor when argv different than None
        has been supplied.
        """
        argv_example = ['1', '2', '3']
        # it passes argv to cli.process_arguments without any changes
        with iocapture.capture():
            try:
                rapidpropull.cli.main(argv=argv_example)
            except:
                pass
        argument_processor.assert_called_with(argv_example)

    @mock.patch('temba_client.v1.TembaClient')
    def test_print_out_downloaded_data_as_json(self, temba_client_class):
        selectors = ['--flow-runs', '--flows', '--contacts']
        token = 'a-valid-rapidpro-token'
        expected_download = [self.make_serializable(i) for i in range(3)]
        expected_json = [s.serialize() for s in expected_download]
        temba_client_class.return_value. \
            get_runs.return_value = expected_download
        temba_client_class.return_value. \
            get_flows.return_value = expected_download
        temba_client_class.return_value. \
            get_contacts.return_value = expected_download
        for endpoint_selector in selectors:
            with iocapture.capture() as captured_out:
                rapidpropull.cli.main([endpoint_selector, '--api-token', token])
                result = json.loads(captured_out.stdout)
            assert_that(result, equal_to(expected_json))

    @mock.patch('temba_client.v1.TembaClient')
    def test_handles_temba_connection_errors(self, temba_client_class):
        """
        It catches TembaConnectionError, prints a relevant message and exits
        with exit status different than 0 when unable to connect.
        """
        selectors = ['--flow-runs', '--flows', '--contacts']
        token = 'a-valid-rapidpro-token'
        error_message = 'Unable to connect to host'
        temba_client_class.return_value. \
            get_runs.side_effect = TembaConnectionError()
        temba_client_class.return_value. \
            get_flows.side_effect = TembaConnectionError()
        temba_client_class.return_value. \
            get_contacts.side_effect = TembaConnectionError()
        for endpoint_selector in selectors:
            with iocapture.capture() as captured_out:
                try:
                    rapidpropull.cli.main([endpoint_selector, '--api-token',
                                           token])
                except TembaConnectionError:
                    pytest.fail('TembaConnectionError not intercepted')
                except SystemExit as e:
                    if e.message == 0:
                        pytest.fail('exit status should not be 0')
                finally:
                    result = captured_out.stderr
                assert error_message in result

    @mock.patch('temba_client.v1.TembaClient')
    def test_handles_temba_token_errors(self, temba_client_class):
        """
        It catches TembaConnectionError, prints a relevant message and exits
        with exit status different than 0 when unable to connect.
        """
        selectors = ['--flow-runs', '--flows', '--contacts']
        token = 'a-valid-rapidpro-token'
        error_message = 'Authentication with provided token failed'
        temba_client_class.return_value. \
            get_runs.side_effect = TembaTokenError()
        temba_client_class.return_value. \
            get_flows.side_effect = TembaTokenError()
        temba_client_class.return_value. \
            get_contacts.side_effect = TembaTokenError()
        for endpoint_selector in selectors:
            with iocapture.capture() as captured_out:
                try:
                    rapidpropull.cli.main([endpoint_selector, '--api-token',
                                           token])
                except TembaTokenError:
                    pytest.fail('TembaTokenError not intercepted')
                except SystemExit as e:
                    if e.message == 0:
                        pytest.fail('exit status should not be 0')
                finally:
                    result = captured_out.stderr
                assert error_message in result

    @mock.patch('temba_client.v1.TembaClient')
    def test_does_not_catch_unknown_exceptions_from_temba(
            self, temba_client_class):
        """It does not catch unknown exceptions."""
        selectors = ['--flow-runs', '--flows', '--contacts']
        token = 'a-valid-rapidpro-token'
        error_message = 'a random exception'
        temba_client_class.return_value. \
            get_runs.side_effect = Exception(error_message)
        temba_client_class.return_value. \
            get_flows.side_effect = Exception(error_message)
        temba_client_class.return_value. \
            get_contacts.side_effect = Exception(error_message)
        for endpoint_selector in selectors:
            with pytest.raises(Exception) as excinfo:
                rapidpropull.cli.main([endpoint_selector, '--api-token', token])
            assert excinfo.match(error_message)
