Feature: Rain delay from the cloud
  As a homeowner
  I want a rain delay sent from the app to stop watering
  So that I don't waste water when it rains

  Background:
    Given a connected controller with 8 zones

  Scenario: Rain delay stops a running zone
    Given zone 1 is scheduled at minute 1 for 10 minutes
    And the clock advances 1 minute
    When the app turns rain delay on
    Then no zones are running
    And the device reports rain delay on
    And the cloud and device are in sync

  Scenario: Rain delay set while offline is applied on reconnect
    Given the controller goes offline
    When the app turns rain delay on
    Then the cloud and device are out of sync
    When the controller comes back online
    Then the device reports rain delay on
    And the cloud and device are in sync

  Scenario Outline: Zone numbers outside the controller are rejected
    Then scheduling zone <zone> is rejected

    Examples:
      | zone |
      | 0    |
      | 9    |
