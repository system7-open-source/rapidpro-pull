from base import *
# noinspection PyPackageRequirements
from behave import *

use_step_matcher("re")


@then(
    'the program downloads and prints a valid JSON document with all matching '
    'flows "(?P<flows>.*)"')
def step_impl(context, flows):
    """
    :type context: behave.runner.Context
    :type flows: str
    """
    # expected
    expected_flows = [s.strip() for s in flows.split(',') if s]
    # output
    assert_that(context.stderr, empty())
    result_flows = [f['uuid'] for f in json.loads(context.stdout)]
    # test
    if len(expected_flows) == 0:
        assert_that(result_flows, empty())
    else:
        assert_that(result_flows, contains_inanyorder(*expected_flows))
