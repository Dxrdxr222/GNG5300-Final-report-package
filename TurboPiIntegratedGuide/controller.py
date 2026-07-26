import math
import statistics
import time
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

from config import AvoidanceConfig
from hardware import DistanceSensor, Motor


class RunState(str, Enum):
    STARTING = "starting"
    FORWARD = "forward"
    STOPPING = "stopping"
    TURN_LEFT = "turn_left"
    TURN_RIGHT = "turn_right"
    CHECK_CLEAR = "check_clear"
    FINISHED = "finished"
    FAULT = "fault"


@dataclass(frozen=True)
class RunResult:
    state: RunState
    elapsed_seconds: float
    obstacle_count: int
    last_distance_cm: Optional[float]
    error: Optional[str] = None


class AvoidanceController:
    def __init__(
        self,
        motor: Motor,
        distance_sensor: DistanceSensor,
        config: AvoidanceConfig,
        turn_advisor: Optional[Callable[[], Optional[str]]] = None,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
        event_sink: Callable[[str], None] = print,
    ):
        config.validate()
        self.motor = motor
        self.distance_sensor = distance_sensor
        self.config = config
        self.turn_advisor = turn_advisor
        self.clock = clock
        self.sleep = sleep
        self.event_sink = event_sink

        self.state = RunState.STARTING
        self._distances = deque(maxlen=config.distance_filter_size)
        self._invalid_readings = 0
        self._next_fallback_turn = "left"
        self._active_turn = "left"
        self._turn_until = 0.0
        self._resume_after = 0.0
        self._obstacle_count = 0
        self._last_distance_cm = None
        self._last_announced_state = None

    def run(self) -> RunResult:
        started_at = self.clock()
        deadline = started_at + self.config.run_seconds
        error = None

        self.motor.stop()
        self._announce(RunState.STARTING)

        try:
            while self.clock() < deadline:
                now = self.clock()
                distance = self._read_filtered_distance()

                if distance is None:
                    self.motor.stop()
                    if (
                        self._invalid_readings
                        >= self.config.maximum_consecutive_invalid_readings
                    ):
                        raise RuntimeError("ultrasonic sensor data is invalid or unavailable")
                    remaining = max(0.0, deadline - self.clock())
                    self.sleep(min(self.config.loop_interval_seconds, remaining))
                    continue

                if self.state == RunState.STARTING:
                    self.motor.forward(self.config.forward_speed)
                    self._announce(RunState.FORWARD)

                elif self.state == RunState.FORWARD:
                    if distance <= self.config.obstacle_distance_cm:
                        self._obstacle_count += 1
                        self.motor.stop()
                        self._resume_after = now + self.config.stop_settle_seconds
                        self._active_turn = self._choose_turn()
                        self._announce(RunState.STOPPING, distance)

                elif self.state == RunState.STOPPING:
                    if now >= self._resume_after:
                        self._begin_turn(now)

                elif self.state in (RunState.TURN_LEFT, RunState.TURN_RIGHT):
                    if now >= self._turn_until:
                        self.motor.stop()
                        self._resume_after = now + self.config.stop_settle_seconds
                        self._announce(RunState.CHECK_CLEAR, distance)

                elif self.state == RunState.CHECK_CLEAR:
                    if now >= self._resume_after:
                        if distance >= self.config.clear_distance_cm:
                            self.motor.forward(self.config.forward_speed)
                            self._announce(RunState.FORWARD, distance)
                        else:
                            self._active_turn = self._choose_turn()
                            self._begin_turn(now)

                remaining = max(0.0, deadline - self.clock())
                self.sleep(min(self.config.loop_interval_seconds, remaining))

        except KeyboardInterrupt:
            error = "interrupted by user"
            self._announce(RunState.FAULT)
        except Exception as exc:
            error = str(exc)
            self._announce(RunState.FAULT)
        finally:
            self.motor.stop()

        if error is None:
            self._announce(RunState.FINISHED)

        elapsed = max(0.0, self.clock() - started_at)
        return RunResult(
            state=self.state,
            elapsed_seconds=elapsed,
            obstacle_count=self._obstacle_count,
            last_distance_cm=self._last_distance_cm,
            error=error,
        )

    def _read_filtered_distance(self) -> Optional[float]:
        try:
            raw_distance = float(self.distance_sensor.read_distance_cm())
        except Exception:
            raw_distance = math.nan

        valid = (
            math.isfinite(raw_distance)
            and self.config.minimum_valid_distance_cm
            <= raw_distance
            <= self.config.maximum_valid_distance_cm
        )

        if not valid:
            self._invalid_readings += 1
            self._distances.clear()
            return None

        self._invalid_readings = 0
        self._distances.append(raw_distance)
        self._last_distance_cm = float(statistics.median(self._distances))
        return self._last_distance_cm

    def _choose_turn(self) -> str:
        advised_turn = None
        if self.turn_advisor is not None:
            try:
                advised_turn = self.turn_advisor()
            except Exception as exc:
                self.event_sink(f"visual advisor ignored: {exc}")

        if advised_turn in ("left", "right"):
            return advised_turn

        selected = self._next_fallback_turn
        self._next_fallback_turn = "right" if selected == "left" else "left"
        return selected

    def _begin_turn(self, now: float) -> None:
        if self._active_turn == "left":
            self.motor.turn_left(self.config.turn_yaw_rate)
            next_state = RunState.TURN_LEFT
        else:
            self.motor.turn_right(self.config.turn_yaw_rate)
            next_state = RunState.TURN_RIGHT

        self._turn_until = now + self.config.turn_duration_seconds
        self._announce(next_state, self._last_distance_cm)

    def _announce(self, state: RunState, distance_cm: Optional[float] = None) -> None:
        self.state = state
        if state == self._last_announced_state:
            return

        self._last_announced_state = state
        message = f"state={state.value}"
        if distance_cm is not None:
            message += f" distance_cm={distance_cm:.1f}"
        self.event_sink(message)
