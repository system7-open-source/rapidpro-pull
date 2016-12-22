# __author__ = 'Tomasz J. Kotarba <tomasz@kotarba.net>'
# __copyright__ = 'Copyright (c) 2016, Tomasz J. Kotarba. All rights reserved.'
# __maintainer__ = 'Tomasz J. Kotarba'
# __email__ = 'tomasz@kotarba.net'

Feature: Running the program from the command line to download contacts from RapidPro.
  In order to be able to interpret the downloaded flow run data,
  As a survey manager,
  I want to download contacts from RapidPro using a CLI program.

  Background: Initial test setup for each scenario.
    Given RapidPro is online
    And RapidPro contains some "contacts"

  Scenario: The user provides a valid token and successfully downloads all contacts.
    Given I have a valid RapidPro API token
    When I try to download all contacts using option "--contacts"
    Then the program downloads and prints a valid JSON document with all "contacts"
    And the program finishes with exit status 0

  Scenario: The user provides a valid token and hostname and successfully downloads all contacts.
    Given I have a valid combination of RapidPro hostname and API token
    When I try to download all contacts using option "--contacts"
    Then the program downloads and prints a valid JSON document with all "contacts"
    And the program finishes with exit status 0

  Scenario: Invalid hostname reported to the user.
    Given I have an invalid RapidPro hostname
    And I have a valid RapidPro API token
    When I try to download all contacts using option "--contacts"
    Then the program prints an error message containing "Unable to connect to host"
    And the program terminates with exit status different than 0

  Scenario: Invalid token reported to the user.
    Given I have an invalid RapidPro API token
    When I try to download all contacts using option "--contacts"
    Then the program prints an error message containing "Authentication with provided token failed"
    And the program terminates with exit status different than 0

  Scenario Outline: The user downloads all contacts within a given time range.
    Given I have a valid combination of RapidPro hostname and API token
    And RapidPro is ready to respond with "contacts" matching --before="<before>" and --after="<after>"
    When I try to download contacts matching --before="<before>" and --after="<after>"
    Then the program downloads and prints a valid JSON document with all matching contacts "<contacts>"
    And the program finishes with exit status 0
    Examples:  # data matching features/fixtures/contacts.json
      | before                      | after                       | contacts                |
      | 2011-07-11T14:10:30.591000Z |                             |                         |
      | 2012-07-11T14:10:30.591000Z |                             | 19-d9                   |
      | 2013-07-11T14:10:30.591000Z |                             | 19-d9,29-d9             |
      | 2014-07-11T14:10:30.591000Z |                             | 19-d9,29-d9,39-d9       |
      | 2015-07-11T14:10:30.591000Z |                             | 19-d9,29-d9,39-d9,49-d9 |
      |                             | 2010-07-11T14:10:30.591000Z | 19-d9,29-d9,39-d9,49-d9 |
      |                             | 2011-07-11T14:10:30.591000Z | 29-d9,39-d9,49-d9       |
      |                             | 2012-07-11T14:10:30.591000Z | 39-d9,49-d9             |
      |                             | 2013-07-11T14:10:30.591000Z | 49-d9                   |
      |                             | 2014-07-11T14:10:30.591000Z |                         |
      | 2015-07-11T14:10:30.591000Z | 2010-07-11T14:10:30.591000Z | 19-d9,29-d9,39-d9,49-d9 |
      | 2014-07-11T14:10:30.591000Z | 2011-07-11T14:10:30.591000Z | 29-d9,39-d9             |
      | 2011-07-11T14:10:30.591000Z | 2011-07-11T14:10:30.591000Z |                         |
      | 2013-07-11T14:10:30.999000Z | 2013-07-11T14:10:30.000000Z | 39-d9                   |

  Scenario Outline: The user downloads selected contacts using one or more contact UUIDs.
    Given I have a valid combination of RapidPro hostname and API token
    And RapidPro is ready to respond with "contacts" matching UUID query "<query>"
    When I try to download "contacts" matching the following UUID query "<query>"
    Then the program downloads and prints a valid JSON document with all matching contacts "<contacts>"
    And the program finishes with exit status 0
    Examples:  # data matching features/fixtures/contacts.json
      | query                                  | contacts          |
      | --uuid=19-d9                           | 19-d9             |
      | --uuid=19-d9 --uuid=29-d9              | 19-d9,29-d9       |
      | --uuid=19-d9 --uuid=29-d9 --uuid=49-d9 | 19-d9,29-d9,49-d9 |
      | --uuid=99-99                           |                   |
      | --uuid=19-d9 --uuid=29-d9 --uuid=49-d9 | 19-d9,29-d9,49-d9 |
