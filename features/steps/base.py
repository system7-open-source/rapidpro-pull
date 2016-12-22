import subprocess
import shlex
import json

# noinspection PyPackageRequirements
from behave import *
from hamcrest import *


__author__ = 'Tomasz J. Kotarba <tomasz@kotarba.net>'
__copyright__ = 'Copyright (c) 2016, Tomasz J. Kotarba. All rights reserved.'
__maintainer__ = 'Tomasz J. Kotarba'
__email__ = 'tomasz@kotarba.net'

program_name = 'rapidpro-pull'


def _help_printed(stdout, stderr):
    if isinstance(stdout, file):
        stdout = stdout.read()
    if isinstance(stderr, file):
        stderr = stderr.read()
    help_string = "{} --help".format(program_name)
    return stdout + stderr, help_string


def close_popen_and_wait(popen):
    popen.stdout.close()
    popen.stderr.close()
    popen.wait()


def help_should_be_printed(stdout, stderr):
    stdout, help_string = _help_printed(stdout, stderr)
    assert_that(stdout, contains_string(help_string), 'help should be printed')


def help_should_not_be_printed(stdout, stderr):
    stdout, help_string = _help_printed(stdout, stderr)
    assert_that(
        stdout,
        not_(contains_string(help_string)),
        'help should not be printed'
    )


def run_from_cli(parameters=''):
    popenargs = shlex.split('{} {}'.format(program_name, parameters))
    popen = subprocess.Popen(popenargs,
                             universal_newlines=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
    return popen


use_step_matcher("re")


@given("I know the program path")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    context.path = program_name


@when("I execute the program without any options or arguments")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    context.popen = run_from_cli()
    # output
    context.stderr = context.popen.stderr.read()
    context.stdout = context.popen.stdout.read()


@then("the program prints the help message")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    help_should_be_printed(
        context.stdout,
        context.stderr
    )


@step("the program finishes with exit status 0")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    close_popen_and_wait(context.popen)
    assert_that(context.popen.returncode, equal_to(0))


@step("the program terminates with exit status different than 0")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    close_popen_and_wait(context.popen)
    assert_that(context.popen.returncode, is_not(equal_to(0)))


@when("I execute the program with (?P<parameters>.+)")
def step_impl(context, parameters):
    """
    :type context: behave.runner.Context
    :type parameters: str
    """
    context.popen = run_from_cli(parameters)
    # output
    context.stderr = context.popen.stderr.read()
    context.stdout = context.popen.stdout.read()


@given("I have a valid RapidPro API token")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    context.token_provided = True
    context.valid_token = True


@given("I have a valid combination of RapidPro hostname and API token")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    context.hostname_provided = True
    context.valid_hostname = True
    context.token_provided = True
    context.valid_token = True


@given("I have an invalid RapidPro hostname")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    context.hostname_provided = True
    context.valid_hostname = False


@given("I have an invalid RapidPro API token")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    context.token_provided = True
    context.valid_token = False


@then('the program prints an error message containing "(?P<text>.+)"')
def step_impl(context, text):
    """
    :type context: behave.runner.Context
    :type text: str
    """
    assert_that(context.stderr, contains_string(text))


@given('RapidPro is online')
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    context.hostname_provided = False
    context.valid_hostname = False
    context.token_provided = False
    context.valid_token = False
    context.rapidpro_server.reset_presets()


@given('RapidPro contains some "(?P<endpoint>.+)"')
def step_impl(context, endpoint):
    """
    :type context: behave.runner.Context
    :type endpoint: str
    """
    endpoint = context.endpoints.get_endpoint_by_name(endpoint)
    context.rapidpro_server.setup_datetime_filtered_endpoint(endpoint)


@when('I try to download .+ using options* "(?P<options>.+)"')
def step_impl(context, options):
    """
    :type context: behave.runner.Context
    :type options: str
    """
    address = context.rapidpro_server.get_root_url()
    if context.hostname_provided:
        if not context.valid_hostname:
            address = 'some.invalid.address'
    if context.token_provided:
        if context.valid_token:
            token = '-t {}'.format(context.rapidpro_server.get_valid_token())
        else:
            token = '-t {}'.format(context.rapidpro_server.get_invalid_token())
    else:
        token = ''
    parameters = '{token} -a {address} {options}'.format(address=address,
                                                         token=token,
                                                         options=options)
    context.popen = run_from_cli(parameters)
    # output
    context.stderr = context.popen.stderr.read()
    context.stdout = context.popen.stdout.read()


@then('the program downloads and prints a valid JSON document with all '
      '"(?P<endpoint>.+)"')
def step_impl(context, endpoint):
    """
    :type context: behave.runner.Context
    :type endpoint: str
    """
    endpoint = context.endpoints.get_endpoint_by_name(endpoint)
    # expected
    json_from_server = json.loads(
        context.rapidpro_server.load_json_response(endpoint))

    expected_json = json_from_server['results']
    # output
    assert_that(context.stderr, empty())
    result = json.loads(context.stdout)
    # test
    assert_that(context.stderr, empty())
    assert_that(result, equal_to(expected_json))


@given(
    'RapidPro is ready to respond with "(?P<endpoint>.+)" matching'
    ' --before="(?P<before>.*)" and --after="(?P<after>.*)"'
)
def step_impl(context, endpoint, before, after):
    """
    :type context: behave.runner.Context
    :type endpoint: str
    :type before: str
    :type after: str
    """
    endpoint = context.endpoints.get_endpoint_by_name(endpoint)
    context.rapidpro_server.reset_presets()
    context.rapidpro_server.setup_datetime_filtered_endpoint(
        endpoint, before=before, after=after)


@when(
    'I try to download (?P<endpoint>.+) matching --before="(?P<before>.*)"'
    ' and --after="(?P<after>.*)"')
def step_impl(context, endpoint, before, after):
    """
    :type context: behave.runner.Context
    :type endpoint: str
    :type before: str
    :type after: str
    """
    endpoint = context.endpoints.get_endpoint_by_name(endpoint)
    parameters = endpoint.option
    if before:
        parameters += ' --before {}'.format(before)
    if after:
        parameters += ' --after {}'.format(after)
    context.execute_steps(u'when I try to download objects using options "{}"'
                          u''.format(parameters))


@given(
    'RapidPro is ready to respond with "(?P<endpoint>.+)" matching UUID query'
    ' "(?P<query>.*)"'
)
def step_impl(context, endpoint, query):
    """
    :type context: behave.runner.Context
    :type endpoint: str
    :type query: str
    """
    endpoint = context.endpoints.get_endpoint_by_name(endpoint)
    context.rapidpro_server.reset_presets()
    context.rapidpro_server.setup_uuid_filtered_endpoint(endpoint, query)


@when('I try to download "(?P<endpoint>.+)" matching the following UUID query '
      '"(?P<query>.+)"')
def step_impl(context, endpoint, query):
    """
    :type context: behave.runner.Context
    :type endpoint: str
    :type query: str
    """
    endpoint = context.endpoints.get_endpoint_by_name(endpoint)
    parameters = '{option} {parameters}'.format(option=endpoint.option,
                                                parameters=query)
    context.execute_steps(u'when I try to download objects using options "{}"'
                          u''.format(parameters))


@then(
    'the program downloads and prints a valid JSON document with the following'
    ' "(?P<object_type>.+)" identified by IDs "(?P<ids>.*)"')
def step_impl(context, object_type, ids):
    """
    :type context: behave.runner.Context
    :type object_type: str
    :type ids: str
    """
    # expected
    expected_ids = [s.strip() for s in ids.split(',') if s]
    # output
    assert_that(context.stderr, empty())
    result_ids = [f['uuid'] for f in json.loads(context.stdout)]
    # test
    if len(expected_ids) == 0:
        assert_that(result_ids, empty())
    else:
        assert_that(result_ids, contains_inanyorder(*expected_ids))


@given("RapidPro contains a set of specific objects")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    objects = context.test_utilities.Auxiliary.make_objects(context.table)
    context.remote_objects = objects
    flow_runs = {'count': len(objects['flow runs']),
                 'results': [o.serialize() for o in objects['flow runs']]}
    flows = {'count': len(objects['flows']),
             'results': [o.serialize() for o in objects['flows']]}
    contacts = {'count': len(objects['contacts']),
                'results': [o.serialize() for o in objects['contacts']]}
    context.rapidpro_server.reset_presets()
    context.rapidpro_server.setup_custom_preset(
        endpoint=context.endpoints.get_endpoint_by_name('flow runs'), query={},
        json_response=json.dumps(flow_runs))
    context.rapidpro_server.setup_custom_preset(
        endpoint=context.endpoints.get_endpoint_by_name('flows'), query={},
        json_response=json.dumps(flows))
    context.rapidpro_server.setup_custom_preset(
        endpoint=context.endpoints.get_endpoint_by_name('contacts'), query={},
        json_response=json.dumps(contacts))
    context.rapidpro_server.setup_uuid_filtered_endpoint(
        endpoint=context.endpoints.get_endpoint_by_name('flows'),
        uuids=[flow['uuid'] for flow in flows['results']],
        json_data=json.dumps(flows), powerset=True)
    context.rapidpro_server.setup_uuid_filtered_endpoint(
        endpoint=context.endpoints.get_endpoint_by_name('contacts'),
        uuids=[contact['uuid'] for contact in contacts['results']],
        json_data=json.dumps(contacts), powerset=True)
