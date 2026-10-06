import pytest
from irrigation import FakeBroker, CloudShadow, MockController

SERIAL = "TEST-0001"


@pytest.fixture
def broker():
    return FakeBroker()


@pytest.fixture
def shadow(broker):
    return CloudShadow(broker, SERIAL)


@pytest.fixture
def controller(broker, shadow):
    # shadow is requested first so it is subscribed before the device reports.
    device = MockController(SERIAL, stations=8, broker=broker,
                            flow_gpm={1: 4.5, 3: 12.0})
    yield device
    # teardown: a real harness would reset the device here
    device.running.clear()
    device.schedule.clear()


@pytest.fixture
def telemetry(broker):
    """Returns a function that reads all telemetry messages so far."""
    return lambda: broker.messages(f"devices/{SERIAL}/telemetry")
