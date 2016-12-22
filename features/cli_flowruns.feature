# __author__ = 'Tomasz J. Kotarba <tomasz@kotarba.net>'
# __copyright__ = 'Copyright (c) 2016, Tomasz J. Kotarba. All rights reserved.'
# __maintainer__ = 'Tomasz J. Kotarba'
# __email__ = 'tomasz@kotarba.net'

Feature: Running the program from the command line to download flow runs from RapidPro.
  In order to be able to process data gathered by field operatives,
  As a survey manager,
  I want to download flow runs from RapidPro using a CLI program.

  Background: Initial test setup for each scenario.
    Given RapidPro is online
    And RapidPro contains some "flow runs"

  Scenario: The user provides a valid token and successfully downloads all flow runs.
    Given I have a valid RapidPro API token
    When I try to download all flow runs using option "--flow-runs"
    Then the program downloads and prints a valid JSON document with all "flow runs"
    And the program finishes with exit status 0

  Scenario: The user provides a valid token and hostname and successfully downloads all flow runs.
    Given I have a valid combination of RapidPro hostname and API token
    When I try to download all flow runs using option "--flow-runs"
    Then the program downloads and prints a valid JSON document with all "flow runs"
    And the program finishes with exit status 0

  Scenario: Invalid hostname reported to the user.
    Given I have an invalid RapidPro hostname
    And I have a valid RapidPro API token
    When I try to download all flow runs using option "--flow-runs"
    Then the program prints an error message containing "Unable to connect to host"
    And the program terminates with exit status different than 0

  Scenario: Invalid token reported to the user.
    Given I have an invalid RapidPro API token
    When I try to download all flow runs using option "--flow-runs"
    Then the program prints an error message containing "Authentication with provided token failed"
    And the program terminates with exit status different than 0

  Scenario Outline: The user downloads all flow runs within a given time range.
    Given I have a valid combination of RapidPro hostname and API token
    And RapidPro is ready to respond with "flow runs" matching --before="<before>" and --after="<after>"
    When I try to download flow runs matching --before="<before>" and --after="<after>"
    Then the program downloads and prints a valid JSON document with all matching flow runs "<runs>"
    And the program finishes with exit status 0
    Examples:  # data matching features/fixtures/flow_runs.json
      | before                      | after                       | runs                                    |
      | 2013-07-11T13:50:19.860000Z |                             |                                         |
      | 2014-07-11T13:49:10.965000Z |                             | 182641958                               |
      | 2015-06-20T16:00:44.400000Z |                             | 182641958,282637955                     |
      | 2016-06-20T08:35:20.213000Z |                             | 182641958,282637955,370121514           |
      | 2016-06-20T08:35:20.213001Z |                             | 182641958,282637955,370121514,469022761 |
      |                             | 2013-07-11T13:50:19.859999Z | 182641958,282637955,370121514,469022761 |
      |                             | 2013-07-11T13:50:19.860000Z | 282637955,370121514,469022761           |
      |                             | 2014-07-11T13:49:10.965000Z | 370121514,469022761                     |
      |                             | 2015-06-20T16:00:44.400000Z | 469022761                               |
      |                             | 2016-06-20T08:35:20.213000Z |                                         |
      | 2016-06-20T08:35:20.213001Z | 2013-07-11T13:50:19.859999Z | 182641958,282637955,370121514,469022761 |
      | 2016-06-20T08:35:20.213000Z | 2013-07-11T13:50:19.860000Z | 282637955,370121514                     |
      | 2013-07-11T13:50:19.860000Z | 2013-07-11T13:50:19.860000Z |                                         |
      | 2015-06-20T16:00:44.400001Z | 2015-06-20T16:00:44.399999Z | 370121514                               |

  Scenario Outline: The user downloads flow runs together with all associated flows or contacts.
    Given I have a valid combination of RapidPro hostname and API token
    And RapidPro contains a set of specific objects
      | run | contact | flow  |
      | 1   | 1c-cc   | 1f-ff |
      | 2   | 2c-cc   | 2f-ff |
      | 3   | 1c-cc   | 2f-ff |
      | 4   | 2c-cc   | 1f-ff |
      | 5   | 3c-cc   | 1f-ff |
      |     | 4c-cc   | 3f-ff |
      |     | 5c-cc   | 4f-ff |
      |     | 6c-cc   |       |
    When I try to download flow runs with their associated objects using options "<parameters>"
    Then the program outputs JSON with flow runs with IDs "<runs>" stored in "runs"
    And the JSON output also contains all associated (and only those) "<flows>" stored in "flows"
    And the JSON output also contains all associated (and only those) "<contacts>" stored in "contacts"
    And the program finishes with exit status 0
    Examples: # for data matching the table from the earlier step
      | parameters                   | runs      | flows       | contacts          |
      | --flow-runs --with-flows                 | 1,2,3,4,5 | 1f-ff,2f-ff |                   |
      | --flow-runs --with-contacts              | 1,2,3,4,5 |             | 1c-cc,2c-cc,3c-cc |
      | --flow-runs --with-flows --with-contacts | 1,2,3,4,5 | 1f-ff,2f-ff | 1c-cc,2c-cc,3c-cc |
