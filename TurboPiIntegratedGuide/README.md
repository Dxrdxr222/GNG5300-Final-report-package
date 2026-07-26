# TurboPi Integrated Guide

This folder is an isolated first integration for the HiWonder TurboPi Standard
kit. It does not modify `VisualGuideProject`, `smart_vehicle_backend`, or the
Flutter application.

The first milestone is deliberately small:

1. Run locally on the Raspberry Pi for 10 seconds.
2. Move forward at a conservative speed.
3. Read the Glowy ultrasonic sensor continuously.
4. Stop before every avoidance turn.
5. Turn left or right when the front path is blocked.
6. Stop on timeout, invalid sensor data, an exception, or Ctrl+C.

The four-channel line follower is not used in this milestone because the test
does not yet require following a marked floor line.

## Safety

Lift the wheels off the ground for the first hardware command test. Then test
on the floor at low speed with a clear emergency-stop path. Do not test near
stairs, tables, people, pets, or fragile objects.

The program defaults to simulation. Hardware movement requires both
`--hardware` and `--confirm-motion`.

## Simulation on a laptop

```powershell
python main.py
```

The simulation presents two obstacles during a 10-second run. The first causes
a left turn and the second causes a right turn.

Run unit tests:

```powershell
python -m unittest discover -s tests -v
```

## Raspberry Pi preparation

This code expects the HiWonder image and SDK at `/home/pi/TurboPi`, including:

- `HiwonderSDK.mecanum.MecanumChassis`
- `HiwonderSDK.Sonar.Sonar`

Copy this folder to the Raspberry Pi, then run from inside it:

```bash
python3 main.py --hardware --confirm-motion
```

Useful tuning options:

```bash
python3 main.py --hardware --confirm-motion \
  --seconds 10 \
  --speed 25 \
  --obstacle-cm 35 \
  --clear-cm 45 \
  --turn-seconds 0.5 \
  --turn-yaw 0.4
```

If the physical robot turns in the opposite direction from the labels, use:

```bash
python3 main.py --hardware --confirm-motion --reverse-yaw
```

## Visual-guidance boundary

`visual_guidance.py` contains the simplified part we will reuse from the visual
guide. It accepts only the selected detection center and recommends turning
away from it:

- obstacle on left -> turn right
- obstacle on right -> turn left
- obstacle in center/unknown -> alternating fallback

It intentionally does not include background capture, motion subtraction,
speech, warnings, monocular distance, or debug drawing. The ultrasonic sensor
remains authoritative for stopping. A camera detector can be connected later
through the `turn_advisor` callback without changing the motor safety loop.

## Next integration steps

1. Verify forward, stop, left yaw, and right yaw with wheels raised.
2. Record five stationary ultrasonic readings at 20, 30, 40, and 50 cm.
3. Run the simulation tests on the Pi.
4. Run the physical 10-second test at speed 20-25.
5. Only after that, connect the simplified camera detection supplier.
6. Add the Flask start/status endpoints after local hardware behavior is safe.

