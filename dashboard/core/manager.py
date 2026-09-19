"""Non-blocking coordinator. At most one worker per configured host.

Workers never mutate visible state. Late results are discarded; daemon workers
allow Ctrl+C even if a resolver or socket is stuck beyond its native timeout.
"""
from collections import deque
from queue import Queue, Empty
from threading import Thread
import time
from dashboard.collectors.api import fetch
from dashboard.core.health import normalize, evaluate
from dashboard.core.models import Event, PollResult, ServerState, ServerStatus


class Monitor:
    def __init__(self, servers, settings, collector=fetch):
        self.settings = settings
        self.states = [ServerState(server) for server in servers]
        self.events = deque(maxlen=30)
        self.collector = collector
        self.results = Queue(maxsize=max(1, len(servers)))
        self.inflight = {}
        self.next_due = {s.name: 0.0 for s in servers}
        self.last_refresh = None
        self.closed = False

    def _worker(self, config, started):
        try:
            result = self.collector(config, self.settings.timeout)
        except Exception:
            result = PollResult(error="Collector failed", failure_status=ServerStatus.UNKNOWN)
        self.results.put((config.name, started, time.monotonic(), time.time(), result))

    def _change(self, state, status, issues, wall):
        before = state.status
        if status != before or issues != state.issues:
            if status == ServerStatus.ONLINE:
                message = "recovered" if before != ServerStatus.UNKNOWN else "online"
            elif status == ServerStatus.OFFLINE:
                message = "became unreachable"
            else:
                message = "; ".join(issues)
            self.events.appendleft(Event(wall, state.config.name, message, status))
        state.status, state.issues = status, issues

    def _failure(self, state, status, message, wall):
        state.metrics = None
        state.cpu_history.clear()
        state.checks = {}
        state.latency_ms = None
        state.previous_network = None
        self._change(state, status, [message], wall)

    def _accept(self, state, result, finished, wall, elapsed):
        if result.data is None:
            self._failure(state, result.failure_status, result.error, wall)
            return
        metrics = normalize(result.data)
        if all(v is None for v in (metrics.cpu, metrics.memory, metrics.disk, metrics.uptime)):
            self._failure(state, ServerStatus.UNKNOWN, "No valid metrics in agent response", wall)
            return
        if metrics.network_counters:
            rx, tx = metrics.network_counters
            previous = state.previous_network
            if previous:
                old_rx, old_tx, old_time, boot = previous
                delta = finished - old_time
                if delta > 0 and rx >= old_rx and tx >= old_tx and boot == metrics.boot_time:
                    metrics.rx, metrics.tx = (rx - old_rx) / delta, (tx - old_tx) / delta
            state.previous_network = (rx, tx, finished, metrics.boot_time)
        else:
            state.previous_network = None
        if metrics.cpu is not None:
            state.cpu_history.append(metrics.cpu)
        state.metrics, state.checks = metrics, result.checks
        state.last_seen, state.last_response = finished, wall
        state.latency_ms = elapsed * 1000
        status, issues = evaluate(metrics, result.checks, self.settings)
        self._change(state, status, issues, wall)

    def tick(self, now=None, wall=None):
        if self.closed:
            return
        now = time.monotonic() if now is None else now
        wall = time.time() if wall is None else wall
        by_name = {s.config.name: s for s in self.states}
        while True:
            try:
                name, started, finished, timestamp, result = self.results.get_nowait()
            except Empty:
                break
            if self.inflight.get(name) != started:
                continue
            del self.inflight[name]
            state = by_name[name]
            self.last_refresh = timestamp
            if finished - started <= self.settings.timeout and now - finished <= self.settings.stale_after:
                self._accept(state, result, finished, timestamp, finished - started)
            else:
                self._failure(state, ServerStatus.OFFLINE, "Poll deadline exceeded", wall)
        for state in self.states:
            name = state.config.name
            started = self.inflight.get(name)
            if started is not None and now - started >= self.settings.timeout:
                self._failure(state, ServerStatus.OFFLINE, "Poll deadline exceeded", wall)
            elif state.metrics is not None and state.last_seen is not None and now - state.last_seen > self.settings.stale_after:
                self._failure(state, ServerStatus.OFFLINE, "Metrics expired", wall)
            if started is None and now >= self.next_due[name]:
                state.last_attempt = now
                self.inflight[name] = now
                self.next_due[name] = now + self.settings.interval
                Thread(target=self._worker, args=(state.config, now), daemon=True,
                       name=f"poll-{name}").start()

    def close(self):
        self.closed = True
