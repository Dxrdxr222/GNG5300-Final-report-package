import argparse
import time

from config import AvoidanceConfig
from controller import AvoidanceController
from hardware import (
    GlowyUltrasonicSensor,
    SimulatedMotor,
    TimedSimulationSensor,
    TurboPiMotor,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Safe 10-second TurboPi ultrasonic obstacle-avoidance test"
    )
    parser.add_argument("--hardware", action="store_true", help="use real TurboPi hardware")
    parser.add_argument(
        "--confirm-motion",
        action="store_true",
        help="required acknowledgement before enabling motors",
    )
    parser.add_argument("--sdk-root", default="/home/pi/TurboPi")
    parser.add_argument("--seconds", type=float, default=10.0)
    parser.add_argument("--speed", type=float, default=25.0)
    parser.add_argument("--obstacle-cm", type=float, default=35.0)
    parser.add_argument("--clear-cm", type=float, default=45.0)
    parser.add_argument("--turn-seconds", type=float, default=0.5)
    parser.add_argument("--turn-yaw", type=float, default=0.4)
    parser.add_argument("--reverse-yaw", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = AvoidanceConfig(
        run_seconds=args.seconds,
        forward_speed=args.speed,
        obstacle_distance_cm=args.obstacle_cm,
        clear_distance_cm=args.clear_cm,
        turn_duration_seconds=args.turn_seconds,
        turn_yaw_rate=args.turn_yaw,
        reverse_yaw=args.reverse_yaw,
    )

    if args.hardware:
        if not args.confirm_motion:
            print("Refusing hardware motion without --confirm-motion.")
            return 2
        motor = TurboPiMotor(args.sdk_root, reverse_yaw=config.reverse_yaw)
        sensor = GlowyUltrasonicSensor(args.sdk_root)
        print("REAL HARDWARE MODE: keep the emergency-stop area clear.")
    else:
        started_at = time.monotonic()
        simulation_clock = lambda: time.monotonic() - started_at
        motor = SimulatedMotor(simulation_clock)
        sensor = TimedSimulationSensor(simulation_clock)
        print("SIMULATION MODE: no hardware commands will be sent.")

    controller = AvoidanceController(motor, sensor, config)
    result = controller.run()

    print(
        f"result={result.state.value} elapsed={result.elapsed_seconds:.2f}s "
        f"obstacles={result.obstacle_count} last_distance_cm={result.last_distance_cm}"
    )
    if result.error:
        print(f"error={result.error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

