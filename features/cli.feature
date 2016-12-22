# __author__ = 'Tomasz J. Kotarba <tomasz@kotarba.net>'
# __copyright__ = 'Copyright (c) 2016, Tomasz J. Kotarba. All rights reserved.'
# __maintainer__ = 'Tomasz J. Kotarba'
# __email__ = 'tomasz@kotarba.net'

Feature: Running the program from the command line to communicate with RapidPro.
  In order to be able to process data gathered by field operatives,
  As a survey manager,
  I want to be able to run a CLI program which can connect to RapidPro.

  Background: Initial test setup for each scenario.
    Given RapidPro is online

  Scenario: Running the program with no options / arguments.
    Given I know the program path
    When I execute the program without any options or arguments
    Then the program prints the help message
    And the program terminates with exit status different than 0

  Scenario Outline: Running the program with an invalid combination of options and arguments.
    Given I know the program path
    When I execute the program with <parameters>
    Then the program prints the help message
    And the program terminates with exit status different than 0
    Examples:
      | parameters                                    |
      | some invalid arguments                        |
      | --some-invalid-option                         |
      | --some --invalid --options                    |
      | --address=hostname.rapidpro.io                |
      | --api-token=a-token                           |
      | --flow-runs                                   |
      | --flows                                       |
      | --uuid=uuid-1                                 |
      | --flow-runs --api-token=a-token --uuid=uuid-1 |
      | --contacts                                    |

