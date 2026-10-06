import pytest


@pytest.mark.smoke
def test_zone_starts_at_scheduled_time_and_stops_after_duration(controller):
    controller.schedule_zone(zone=3, start=10, minutes=5)

    controller.advance(9)
    assert controller.status()["running"] == []      # not yet

    controller.advance(1)                              # now = 10
    assert controller.status()["running"] == [3]

    controller.advance(5)                              # now = 15
    assert controller.status()["running"] == []


@pytest.mark.smoke
def test_telemetry_reports_start_and_stop_in_order(controller, telemetry):
    controller.schedule_zone(zone=3, start=1, minutes=2)
    controller.advance(3)

    events = [(m["event"], m["zone"], m["t"]) for m in telemetry()]
    assert events == [("zone_started", 3, 1), ("zone_stopped", 3, 3)]


def test_telemetry_flow_reading_matches_simulated_value(controller, telemetry):
    controller.schedule_zone(zone=3, start=1, minutes=1)
    controller.advance(1)

    started = [m for m in telemetry() if m["event"] == "zone_started"][0]
    assert started["flow_gpm"] == pytest.approx(12.0, abs=0.1)   # tolerance, not exact


@pytest.mark.parametrize("zone", [0, 9, -1])
def test_scheduling_invalid_zone_is_rejected(controller, zone):
    with pytest.raises(ValueError, match="out of range"):
        controller.schedule_zone(zone=zone, start=1, minutes=5)


@pytest.mark.sync
def test_shadow_reported_state_matches_device(controller, shadow):
    controller.schedule_zone(zone=1, start=1, minutes=10)
    controller.advance(1)

    assert shadow.reported["running"] == controller.status()["running"] == [1]


@pytest.mark.sync
def test_rain_delay_from_cloud_stops_running_zone(controller, shadow, telemetry):
    controller.schedule_zone(zone=1, start=1, minutes=10)
    controller.advance(1)

    shadow.set_desired(rain_delay=True)

    assert controller.status() == {"running": [], "rain_delay": True}
    assert shadow.delta() == {}                                   # in sync
    assert telemetry()[-1] == {"event": "zone_stopped", "zone": 1,
                               "t": 1, "reason": "rain_delay"}


@pytest.mark.sync
def test_change_made_while_offline_is_applied_on_reconnect(controller, shadow, telemetry):
    controller.go_offline()
    shadow.set_desired(rain_delay=True)          # device misses this message

    assert controller.status()["rain_delay"] is False
    assert shadow.delta() == {"rain_delay": True}  # cloud knows they disagree

    controller.go_online(shadow)

    assert controller.status()["rain_delay"] is True
    assert shadow.delta() == {}                   # converged

    controller.schedule_zone(zone=1, start=controller.now + 1, minutes=5)
    controller.advance(1)
    assert telemetry()[-1]["event"] == "zone_skipped"
