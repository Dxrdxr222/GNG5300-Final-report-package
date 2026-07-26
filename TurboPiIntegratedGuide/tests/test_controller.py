import math
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import AvoidanceConfig
from controller import AvoidanceController, RunState
from visual_guidance import recommend_turn_away_from_detection


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


class RecordingMotor:
    def __init__(self):
        self.commands = []

    def forward(self, speed):
        self.commands.append(("forward", speed))

    def turn_left(self, yaw):
        self.commands.append(("left", yaw))

    def turn_right(self, yaw):
        self.commands.append(("right", yaw))

    def stop(self):
        self.commands.append(("stop", 0))


class TimedSensor:
    def __init__(self, clock, obstacle_windows=(), invalid=False):
        self.clock = clock
        self.obstacle_windows = obstacle_windows
        self.invalid = invalid

    def read_distance_cm(self):
        if self.invalid:
            return math.nan
        for start, end in self.obstacle_windows:
            if start <= self.clock() < end:
                return 20.0
        return 100.0


def make_config(**changes):
    values = dict(
        run_seconds=1.5,
        loop_interval_seconds=0.05,
        forward_speed=20,
        obstacle_distance_cm=35,
        clear_distance_cm=45,
        turn_duration_seconds=0.15,
        stop_settle_seconds=0.05,
        distance_filter_size=1,
    )
    values.update(changes)
    return AvoidanceConfig(**values)


class AvoidanceControllerTests(unittest.TestCase):
    def test_finishes_and_always_stops(self):
        clock = FakeClock()
        motor = RecordingMotor()
        sensor = TimedSensor(clock)
        controller = AvoidanceController(
            motor,
            sensor,
            make_config(run_seconds=0.3),
            clock=clock,
            sleep=clock.sleep,
            event_sink=lambda _message: None,
        )

        result = controller.run()

        self.assertEqual(RunState.FINISHED, result.state)
        self.assertEqual("stop", motor.commands[-1][0])
        self.assertIn(("forward", 20), motor.commands)

    def test_two_obstacles_alternate_turn_direction(self):
        clock = FakeClock()
        motor = RecordingMotor()
        sensor = TimedSensor(clock, ((0.2, 0.45), (0.8, 1.05)))
        controller = AvoidanceController(
            motor,
            sensor,
            make_config(),
            clock=clock,
            sleep=clock.sleep,
            event_sink=lambda _message: None,
        )

        result = controller.run()

        command_names = [name for name, _value in motor.commands]
        self.assertEqual(RunState.FINISHED, result.state)
        self.assertIn("left", command_names)
        self.assertIn("right", command_names)
        self.assertGreaterEqual(result.obstacle_count, 2)
        self.assertEqual("stop", command_names[-1])

    def test_invalid_sensor_data_causes_fault_and_stop(self):
        clock = FakeClock()
        motor = RecordingMotor()
        sensor = TimedSensor(clock, invalid=True)
        controller = AvoidanceController(
            motor,
            sensor,
            make_config(maximum_consecutive_invalid_readings=2),
            clock=clock,
            sleep=clock.sleep,
            event_sink=lambda _message: None,
        )

        result = controller.run()

        self.assertEqual(RunState.FAULT, result.state)
        self.assertIn("invalid", result.error)
        self.assertEqual("stop", motor.commands[-1][0])
        self.assertNotIn("forward", [name for name, _value in motor.commands])

    def test_visual_advisor_turns_away_from_side_detection(self):
        self.assertEqual(
            "right",
            recommend_turn_away_from_detection({"center": (20, 50)}, 300),
        )
        self.assertEqual(
            "left",
            recommend_turn_away_from_detection({"center": (280, 50)}, 300),
        )
        self.assertIsNone(
            recommend_turn_away_from_detection({"center": (150, 50)}, 300)
        )


if __name__ == "__main__":
    unittest.main()

