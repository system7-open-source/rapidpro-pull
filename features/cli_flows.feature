# __author__ = 'Tomasz J. Kotarba <tomasz@kotarba.net>'
# __copyright__ = 'Copyright (c) 2016, Tomasz J. Kotarba. All rights reserved.'
# __maintainer__ = 'Tomasz J. Kotarba'
# __email__ = 'tomasz@kotarba.net'

Feature: Running the program from the command line to download flows from RapidPro.
  In order to be able to interpret the downloaded flow run data,
  As a survey manager,
  I want to download flows from RapidPro using a CLI program.

  Background: Initial test setup for each scenario.
    Given RapidPro is online
    And RapidPro contains some "flows"

  Scenario: The user provides a valid token and successfully downloads all flows.
    Given I have a valid RapidPro API token
    When I try to download all flows using option "--flows"
    Then the program downloads and prints a valid JSON document with all "flows"
    And the program finishes with exit status 0

  Scenario: The user provides a valid token and hostname and successfully downloads all flows.
    Given I have a valid combination of RapidPro hostname and API token
    When I try to download all flows using option "--flows"
    Then the program downloads and prints a valid JSON document with all "flows"
    And the program finishes with exit status 0

  Scenario: Invalid hostname reported to the user.
    Given I have an invalid RapidPro hostname
    And I have a valid RapidPro API token
    When I try to download all flows using option "--flows"
    Then the program prints an error message containing "Unable to connect to host"
    And the program terminates with exit status different than 0

  Scenario: Invalid token reported to the user.
    Given I have an invalid RapidPro API token
    When I try to download all flows using option "--flows"
    Then the program prints an error message containing "Authentication with provided token failed"
    And the program terminates with exit status different than 0

  Scenario Outline: The user downloads all flows within a given time range.
    Given I have a valid combination of RapidPro hostname and API token
    And RapidPro is ready to respond with "flows" matching --before="<before>" and --after="<after>"
    When I try to download flows matching --before="<before>" and --after="<after>"
    Then the program downloads and prints a valid JSON document with all matching flows "<flows>"
    And the program finishes with exit status 0
    Examples:  # data matching features/fixtures/flows.json
      | before                      | after                       | flows                   |
      | 2012-10-10T12:44:19.596000Z |                             |                         |
      | 2013-10-10T12:44:19.596000Z |                             | 1e-d9                   |
      | 2014-10-10T12:44:19.596000Z |                             | 1e-d9,2d-33             |
      | 2015-10-10T12:44:19.596000Z |                             | 1e-d9,2d-33,30-0e       |
      | 2016-10-10T12:44:19.596000Z |                             | 1e-d9,2d-33,30-0e,4d-33 |
      |                             | 2011-10-10T12:44:19.596000Z | 1e-d9,2d-33,30-0e,4d-33 |
      |                             | 2012-10-10T12:44:19.596000Z | 2d-33,30-0e,4d-33       |
      |                             | 2013-10-10T12:44:19.596000Z | 30-0e,4d-33             |
      |                             | 2014-10-10T12:44:19.596000Z | 4d-33                   |
      |                             | 2015-10-10T12:44:19.596000Z |                         |
      | 2016-10-10T12:44:19.596000Z | 2011-10-10T12:44:19.596000Z | 1e-d9,2d-33,30-0e,4d-33 |
      | 2015-10-10T12:44:19.596000Z | 2012-10-10T12:44:19.596000Z | 2d-33,30-0e             |
      | 2012-10-10T12:44:19.596000Z | 2012-10-10T12:44:19.596000Z |                         |
      | 2014-10-10T12:44:19.999999Z | 2014-10-10T12:44:19.000000Z | 30-0e                   |

  Scenario Outline: The user downloads selected flows using one or more flow UUIDs.
    Given I have a valid combination of RapidPro hostname and API token
    And RapidPro is ready to respond with "flows" matching UUID query "<query>"
    When I try to download "flows" matching the following UUID query "<query>"
    Then the program downloads and prints a valid JSON document with all matching flows "<flows>"
    And the program finishes with exit status 0
    Examples:  # data matching features/fixtures/flows.json
      | query                                  | flows             |
      | --uuid=1e-d9                           | 1e-d9             |
      | --uuid=1e-d9 --uuid=2d-33              | 1e-d9,2d-33       |
      | --uuid=1e-d9 --uuid=2d-33 --uuid=4d-33 | 1e-d9,2d-33,4d-33 |
      | --uuid=99-99                           |                   |
      | --uuid=1e-d9 --uuid=2d-33 --uuid=4d-33 | 1e-d9,2d-33,4d-33 |
