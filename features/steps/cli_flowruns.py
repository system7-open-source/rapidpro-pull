# coding=utf-8
from base import *
# noinspection PyPackageRequirements
from behave import *


use_step_matcher("re")


@then('the program downloads and prints a valid JSON document with all'
      ' matching flow runs "(?P<runs>.*)"')
def step_impl(context, runs):
    """
    :type context: behave.runner.Context
    :type runs: str
    """
    context.execute_steps(
        u'then the program outputs JSON with flow runs with IDs "{}" stored'
        u' in ""'.format(runs))


@then('the program outputs JSON with flow runs with IDs "(?P<runs>.*)" stored '
      'in "(?P<container>.*)"')
def step_impl(context, runs, container):
    """
    :type context: behave.runner.Context
    :type runs: str
    :type container: str
    """
    # expected
    expected_runs = [int(s.strip()) for s in runs.split(',') if s]
    # output
    assert_that(context.stderr, empty())
    result_json = json.loads(context.stdout)
    if len(container):
        assert_that(result_json, has_key(container))
        result_runs = [int(r['run']) for r in result_json[container]]
    else:
        result_runs = [int(r['run']) for r in json.loads(context.stdout)]
    # test
    if len(expected_runs) == 0:
        assert_that(result_runs, empty())
    else:
        assert_that(result_runs, contains_inanyorder(*expected_runs))


@step('the JSON output also contains all associated \(and only those\)'
      ' "(?P<uuids>.*)" stored in "(?P<container>.*)"')
def step_impl(context, uuids, container):
    """
    :type context: behave.runner.Context
    :type uuids: str
    :type container: str
    """
    expected_uuids = [s.strip() for s in uuids.split(',') if s]
    assert_that(context.stderr, empty())
    result_json = json.loads(context.stdout)
    if not expected_uuids and len(container):
        assert container not in result_json
        return
    if len(container):
        assert_that(result_json, has_key(container))
        result_uuids = [o['uuid'] for o in result_json[container]]
    else:
        result_uuids = [o['uuid'] for o in json.loads(context.stdout)]
    if len(expected_uuids) == 0:
        assert_that(result_uuids, empty())
    else:
        assert_that(result_uuids, contains_inanyorder(*expected_uuids))
