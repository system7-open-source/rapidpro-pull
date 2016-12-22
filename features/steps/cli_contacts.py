from base import *
# noinspection PyPackageRequirements
from behave import *

use_step_matcher("re")


@then(
    'the program downloads and prints a valid JSON document with all matching '
    'contacts "(?P<contacts>.*)"')
def step_impl(context, contacts):
    """
    :type context: behave.runner.Context
    :type contacts: str
    """
    # expected
    expected_contacts = [c.strip() for c in contacts.split(',') if c]
    # output
    assert_that(context.stderr, empty())
    result_contacts = [f['uuid'] for f in json.loads(context.stdout)]
    # test
    if len(expected_contacts) == 0:
        assert_that(result_contacts, empty())
    else:
        assert_that(result_contacts, contains_inanyorder(*expected_contacts))
