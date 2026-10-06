import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from irrigation import FakeBroker, CloudShadow, MockController

scenarios("features/rain_delay.feature")

SERIAL = "BDD-0001"


@pytest.fixture
def system():
    broker = FakeBroker()
    shadow = CloudShadow(broker, SERIAL)
    return {"broker": broker, "shadow": shadow, "controller": None}


@given(parsers.parse("a connected controller with {stations:d} zones"))
def connected_controller(system, stations):
    system["controller"] = MockController(SERIAL, stations, system["broker"])


@given(parsers.parse("zone {zone:d} is scheduled at minute {start:d} for {minutes:d} minutes"))
def schedule(system, zone, start, minutes):
    system["controller"].schedule_zone(zone, start, minutes)


@given(parsers.parse("the clock advances {minutes:d} minute"))
def advance(system, minutes):
    system["controller"].advance(minutes)


@given("the controller goes offline")
def offline(system):
    system["controller"].go_offline()


@when("the app turns rain delay on")
def rain_on(system):
    system["shadow"].set_desired(rain_delay=True)


@when("the controller comes back online")
def online(system):
    system["controller"].go_online(system["shadow"])


@then("no zones are running")
def none_running(system):
    assert system["controller"].status()["running"] == []


@then("the device reports rain delay on")
def reports_rain(system):
    assert system["controller"].status()["rain_delay"] is True


@then("the cloud and device are in sync")
def in_sync(system):
    assert system["shadow"].delta() == {}


@then("the cloud and device are out of sync")
def out_of_sync(system):
    assert system["shadow"].delta() == {"rain_delay": True}


@then(parsers.parse("scheduling zone {zone:d} is rejected"))
def rejected(system, zone):
    with pytest.raises(ValueError):
        system["controller"].schedule_zone(zone, 1, 5)
