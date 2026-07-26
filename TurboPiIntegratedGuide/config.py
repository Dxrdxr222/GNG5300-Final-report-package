from dataclasses import dataclass


@dataclass(frozen=True)
class AvoidanceConfig:
    run_seconds: float = 10.0
    loop_interval_seconds: float = 0.05

    forward_speed_mms: float = 25.0
    obstacle_distance_cm: float = 35.0
    clear_distance_cm: float = 45.0

    turn_duration_seconds: float = 0.5
    turn_yaw_rate: float = 0.4
    stop_settle_seconds: float = 0.08

    minimum_valid_distance_cm: float = 2.0
    maximum_valid_distance_cm: float = 500.0
    distance_filter_size: int = 3
    maximum_consecutive_invalid_readings: int = 3

    reverse_yaw: bool = False

    def validate(self):
        if self.run_seconds <= 0:
            raise ValueError("run_seconds must be positive")
        if not 0 < self.forward_speed <= 100:
            raise ValueError("forward_speed must be in (0, 100]")
        if self.obstacle_distance_cm <= 0:
            raise ValueError("obstacle_distance_cm must be positive")
        if self.clear_distance_cm <= self.obstacle_distance_cm:
            raise ValueError("clear_distance_cm must exceed obstacle_distance_cm")
        if self.turn_duration_seconds <= 0:
            raise ValueError("turn_duration_seconds must be positive")
        if not 0 < self.turn_yaw_rate <= 2:
            raise ValueError("turn_yaw_rate must be in (0, 2]")
        if self.loop_interval_seconds <= 0:
            raise ValueError("loop_interval_seconds must be positive")
        if self.distance_filter_size < 1:
            raise ValueError("distance_filter_size must be at least 1")
        if self.maximum_consecutive_invalid_readings < 1:
            raise ValueError("maximum_consecutive_invalid_readings must be at least 1")

