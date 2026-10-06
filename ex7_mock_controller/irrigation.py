"""A pretend irrigation system for practice: a controller, an MQTT-like broker,
and a cloud "device shadow". Everything runs in memory with a fake clock,
so tests are fast and never need sleep()."""
import json


class FakeBroker:
    """Tiny stand-in for an MQTT broker: publish/subscribe by topic."""

    def __init__(self):
        self.subscribers = {}   # topic -> list of callbacks
        self.log = []           # every (topic, payload) ever published

    def subscribe(self, topic, callback):
        self.subscribers.setdefault(topic, []).append(callback)

    def publish(self, topic, payload: dict):
        message = json.dumps(payload)          # real MQTT sends bytes/text
        self.log.append((topic, message))
        for callback in self.subscribers.get(topic, []):
            callback(json.loads(message))

    def messages(self, topic):
        return [json.loads(m) for t, m in self.log if t == topic]


class CloudShadow:
    """Cloud copy of device state: 'desired' (what the app wants)
    and 'reported' (what the device says)."""

    def __init__(self, broker, serial):
        self.broker = broker
        self.serial = serial
        self.desired = {}
        self.reported = {}
        broker.subscribe(f"devices/{serial}/shadow/reported", self._on_reported)

    def _on_reported(self, state):
        self.reported.update(state)

    def set_desired(self, **changes):
        self.desired.update(changes)
        self.broker.publish(f"devices/{self.serial}/shadow/desired", self.desired)

    def delta(self):
        """Keys where desired and reported disagree."""
        return {k: v for k, v in self.desired.items() if self.reported.get(k) != v}


class MockController:
    def __init__(self, serial, stations, broker, flow_gpm=None):
        self.serial = serial
        self.stations = stations
        self.broker = broker
        self.flow_gpm = flow_gpm or {}      # zone -> simulated flow reading
        self.now = 0                        # fake clock, in minutes
        self.schedule = []                  # list of (start, zone, minutes)
        self.running = {}                   # zone -> stop time
        self.rain_delay = False
        self.online = True
        self._pending_desired = None
        broker.subscribe(f"devices/{serial}/shadow/desired", self._on_desired)

    # ----- commands -----
    def schedule_zone(self, zone, start, minutes):
        if not 1 <= zone <= self.stations:
            raise ValueError(f"zone {zone} out of range 1-{self.stations}")
        if not 1 <= minutes <= 240:
            raise ValueError(f"duration {minutes} out of range 1-240")
        self.schedule.append((start, zone, minutes))

    def advance(self, minutes):
        """Move the fake clock forward one minute at a time."""
        for _ in range(minutes):
            self.now += 1
            self._stop_finished_zones()
            self._start_due_zones()

    def go_offline(self):
        self.online = False

    def go_online(self, shadow):
        self.online = True
        # On reconnect a real device asks the cloud for the latest desired state.
        self._apply_desired(shadow.desired)

    def status(self):
        return {"running": sorted(self.running), "rain_delay": self.rain_delay}

    # ----- internals -----
    def _start_due_zones(self):
        for start, zone, minutes in list(self.schedule):
            if start == self.now:
                self.schedule.remove((start, zone, minutes))
                if self.rain_delay:
                    self._telemetry("zone_skipped", zone, reason="rain_delay")
                    continue
                self.running[zone] = self.now + minutes
                self._telemetry("zone_started", zone,
                                flow_gpm=self.flow_gpm.get(zone, 0.0))
                self._report()

    def _stop_finished_zones(self):
        for zone, stop_at in list(self.running.items()):
            if self.now >= stop_at:
                del self.running[zone]
                self._telemetry("zone_stopped", zone)
                self._report()

    def _on_desired(self, desired):
        if self.online:
            self._apply_desired(desired)
        # If offline, the message is simply missed (like a real dropped link).

    def _apply_desired(self, desired):
        if "rain_delay" in desired:
            self.rain_delay = desired["rain_delay"]
            if self.rain_delay:
                for zone in list(self.running):
                    del self.running[zone]
                    self._telemetry("zone_stopped", zone, reason="rain_delay")
        self._report()

    def _telemetry(self, event, zone, **extra):
        if self.online:
            self.broker.publish(f"devices/{self.serial}/telemetry",
                                {"event": event, "zone": zone, "t": self.now, **extra})

    def _report(self):
        if self.online:
            self.broker.publish(f"devices/{self.serial}/shadow/reported", self.status())
