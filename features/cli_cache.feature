# __author__ = 'Tomasz J. Kotarba <tomasz@kotarba.net>'
# __copyright__ = 'Copyright (c) 2016, Tomasz J. Kotarba. All rights reserved.'
# __maintainer__ = 'Tomasz J. Kotarba'
# __email__ = 'tomasz@kotarba.net'

Feature: Running the program from the command line to download data from RapidPro using cache.
  In order to optimise network traffic and store downloaded data in a database for later processing,
  As a survey manager,
  I want to download tell the CLI program to use a selected database for caching and storage.

  Background: Initial test setup for each scenario.
    Given RapidPro is online

  Scenario Outline: Flow runs and associated objects are saved into the user-provided cache.
    Given I have a valid combination of RapidPro hostname and API token
    And RapidPro contains a set of specific objects
      | run | contact | flow  |
      | 1   | 1c-cc   | 1f-ff |
      | 2   | 2c-cc   | 2f-ff |
      | 3   | 1c-cc   | 2f-ff |
      | 4   | 2c-cc   | 1f-ff |
      | 5   | 3c-cc   | 1f-ff |
    And the following objects are already stored in the provided cache "sqlite:////tmp/rpp_test.db"
      | run | contact | flow |
      |     |         |      |
    When I try to download flow runs with their associated objects using options "<parameters>"
    Then the provided cache now contains table "flowrun" with "<runs>"
    And the provided cache now contains table "flow" with "<flows>"
    And the provided cache now contains table "contact" with "<contacts>"
    And the program finishes with exit status 0
    Examples: # for data matching the tables from the earlier steps
      | parameters                                                                  | runs      | flows       | contacts          |
      | --flow-runs --cache=sqlite:////tmp/rpp_test.db --with-flows                 | 1,2,3,4,5 | 1f-ff,2f-ff |                   |
      | --flow-runs --cache=sqlite:////tmp/rpp_test.db --with-contacts              | 1,2,3,4,5 |             | 1c-cc,2c-cc,3c-cc |
      | --flow-runs --cache=sqlite:////tmp/rpp_test.db --with-flows --with-contacts | 1,2,3,4,5 | 1f-ff,2f-ff | 1c-cc,2c-cc,3c-cc |

  Scenario Outline: Flow runs and associated objects already available in the user-provided cache are retrieved from the cache.
    Given I have a valid combination of RapidPro hostname and API token
    And RapidPro contains a set of specific objects
      | run | contact | flow  |
      | 1   | 1c-cc   | 1f-ff |
      | 2   | 2c-cc   | 2f-ff |
      | 3   | 1c-cc   | 2f-ff |
      | 4   | 2c-cc   | 1f-ff |
      | 5   | 3c-cc   | 1f-ff |
    And the following objects are already stored in the provided cache "sqlite:////tmp/rpp_test.db"
      | run | contact | flow  |
      | 1   | 77-cc   | 55-ff |
      | 2   | 88-cc   | 2f-ff |
      | 3   | 1c-cc   | 88-ff |
    When I try to download flow runs with their associated objects using options "<parameters>"
    Then the program outputs JSON with flow runs with IDs "<runs>" stored in "runs"
    And the JSON output also contains all associated (and only those) "<flows>" stored in "flows"
    And the JSON output also contains all associated (and only those) "<contacts>" stored in "contacts"
    And the provided cache now contains table "flowrun" with "<runs>"
    And the provided cache now contains table "flow" with "<flows>"
    And the provided cache now contains table "contact" with "<contacts>"
    And the program finishes with exit status 0
    Examples: # for data matching the tables from the earlier steps
      | parameters                                                                  | runs      | flows                   | contacts                      |
      | --flow-runs --cache=sqlite:////tmp/rpp_test.db --with-flows                 | 1,2,3,4,5 | 1f-ff,2f-ff,55-ff,88-ff |                               |
      | --flow-runs --cache=sqlite:////tmp/rpp_test.db --with-contacts              | 1,2,3,4,5 |                         | 1c-cc,2c-cc,3c-cc,77-cc,88-cc |
      | --flow-runs --cache=sqlite:////tmp/rpp_test.db --with-flows --with-contacts | 1,2,3,4,5 | 1f-ff,2f-ff,55-ff,88-ff | 1c-cc,2c-cc,3c-cc,77-cc,88-cc |

  Scenario Outline: Flow runs, flows and contacts are saved into the user-provided cache.
    Given I have a valid combination of RapidPro hostname and API token
    And RapidPro contains a set of specific objects
      | run | contact | flow  |
      | 1   | 1c-cc   | 1f-ff |
      | 2   | 2c-cc   | 2f-ff |
      | 3   | 1c-cc   | 2f-ff |
      |     | 3c-cc   | 3f-ff |
      |     | 4c-cc   | 4f-ff |
      |     | 5c-cc   | 5f-ff |
    And the following objects are already stored in the provided cache "sqlite:////tmp/rpp_test.db"
      | run | contact | flow |
      |     |         |      |
    When I try to download all "objects of a specified type" using options "<parameters>"
    Then the provided cache now contains table "flowrun" with "<runs>"
    And the provided cache now contains table "flow" with "<flows>"
    And the provided cache now contains table "contact" with "<contacts>"
    And the program finishes with exit status 0
    Examples: # for data matching the tables from the earlier steps
      | parameters                                     | runs  | flows                         | contacts                      |
      | --flow-runs --cache=sqlite:////tmp/rpp_test.db | 1,2,3 |                               |                               |
      | --flows --cache=sqlite:////tmp/rpp_test.db     |       | 1f-ff,2f-ff,3f-ff,4f-ff,5f-ff |                               |
      | --contacts --cache=sqlite:////tmp/rpp_test.db  |       |                               | 1c-cc,2c-cc,3c-cc,4c-cc,5c-cc |

  Scenario Outline: The system does not overwrite objects already in cache and uses cached objects instead of those on remote RapidPro servers.
    Given I have a valid combination of RapidPro hostname and API token
    And RapidPro contains a set of specific objects
      | object_type | object_id | attribute_names | attribute_values |
      | run         | 1         | contact         | 1c-cc            |
      | run         | 2         | contact         | 2c-cc            |
      | run         | 3         | contact         | 3c-cc            |
      | flow        | 1f-ff     | name            | flow1            |
      | flow        | 2f-ff     | name            | flow2            |
      | flow        | 3f-ff     | name            | flow3            |
      | contact     | 1c-cc     | name            | contact1         |
      | contact     | 2c-cc     | name            | contact2         |
      | contact     | 3c-cc     | name            | contact3         |
    And the following objects are already stored in the provided cache "sqlite:////tmp/rpp_test.db"
      | object_type | object_id | attribute_names | attribute_values |
      | run         | 3         | contact         | 77-cc            |
      | flow        | 2f-ff     | name            | cached flow2     |
      | contact     | 1c-cc     | name            | cached contact1  |
    When I try to download all objects of a specific type using options "<parameters>"
    Then the program prints a valid JSON document containing requested <object_type> with previously cached substituted for their downloadable counterparts
    And the provided cache still contains all the previously cached objects unchanged
    And the provided cache now also contains all previously uncached <object_type>
    And the number of objects in cache is the sum of the previously cached objects and the previously uncached <object_type>
    And the program finishes with exit status 0
    Examples: # for data matching the tables from the earlier steps
      | parameters                                     | object_type |
      | --flow-runs --cache=sqlite:////tmp/rpp_test.db | flow runs   |
      | --flows --cache=sqlite:////tmp/rpp_test.db     | flows       |
      | --contacts --cache=sqlite:////tmp/rpp_test.db  | contacts    |

