import sys
from pathlib import Path
from typing import Protocol


class Motor(Protocol):
    def forward(self, speed: float) -> None:
        ...

    def turn_left(self, yaw_rate: float) -> None:
        ...

    def turn_right(self, yaw_rate: float) -> None:
        ...

    def stop(self) -> None:
        ...


class DistanceSensor(Protocol):
    def read_distance_cm(self) -> float:
        ...


class TurboPiMotor:
    """Thin adapter over HiWonder's MecanumChassis API."""

    def __init__(self, sdk_root: str = "/home/pi/TurboPi", reverse_yaw: bool = False):
        root = str(Path(sdk_root))
        if root not in sys.path:
            sys.path.insert(0, root)

        try:
            from HiwonderSDK import mecanum
        except ImportError as error:
            raise RuntimeError(
                f"HiWonder mecanum SDK not found under {root}. "
                "Run this on the TurboPi Raspberry Pi image."
            ) from error

        self._chassis = mecanum.MecanumChassis()
        self._yaw_sign = -1.0 if reverse_yaw else 1.0

    def forward(self, speed: float) -> None:
        self._chassis.set_velocity(float(speed), 90, 0)

    def turn_left(self, yaw_rate: float) -> None:
        self._chassis.set_velocity(0, 90, -abs(float(yaw_rate)) * self._yaw_sign)

    def turn_right(self, yaw_rate: float) -> None:
        self._chassis.set_velocity(0, 90, abs(float(yaw_rate)) * self._yaw_sign)

    def stop(self) -> None:
        self._chassis.set_velocity(0, 90, 0)


class GlowyUltrasonicSensor:
    """Adapter for TurboPi's I2C Glowy ultrasonic sensor."""

    def __init__(self, sdk_root: str = "/home/pi/TurboPi"):
        root = str(Path(sdk_root))
        if root not in sys.path:
            sys.path.insert(0, root)

        try:
            from HiwonderSDK import Sonar
        except ImportError as error:
            raise RuntimeError(
                f"HiWonder Sonar SDK not found under {root}. "
                "Run this on the TurboPi Raspberry Pi image."
            ) from error

        self._sonar = Sonar.Sonar()

    def read_distance_cm(self) -> float:
        # The HiWonder SDK reports millimetres.
        return float(self._sonar.getDistance()) / 10.0


class SimulatedMotor:
    def __init__(self, clock):
        self._clock = clock
        self.commands = []
        self._last_command = None

    def _record(self, command: str, value: float = 0.0) -> None:
        item = (round(self._clock(), 3), command, float(value))
        if self._last_command != item[1:]:
            self.commands.append(item)
            self._last_command = item[1:]
            print(f"[{item[0]:5.2f}s] motor={command} value={value:.2f}")

    def forward(self, speed: float) -> None:
        self._record("forward", speed)

    def turn_left(self, yaw_rate: float) -> None:
        self._record("turn_left", yaw_rate)

    def turn_right(self, yaw_rate: float) -> None:
        self._record("turn_right", yaw_rate)

    def stop(self) -> None:
        self._record("stop")


class TimedSimulationSensor:
    """Two repeatable obstacles for laptop verification."""

    def __init__(self, clock):
        self._clock = clock

    def read_distance_cm(self) -> float:
        elapsed = self._clock()
        if 2.0 <= elapsed < 2.7:
            return 22.0
        if 5.5 <= elapsed < 6.2:
            return 25.0
        return 100.0

