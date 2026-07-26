# Approach Risk Design

Date: 2026-07-11

## Why this exists

The physical distance estimate is not accurate enough to trust as a true meter
reading yet. Instead of depending on exact distance, we now use distance as one
part of a grading system.

The main question becomes:

> Is this object becoming more dangerous over time?

That is better for the current robot prototype than asking:

> Is this object exactly 1.4 meters away?

## Current implementation

Implemented in: `risk_api.py`

Main class:

- `ApproachRiskTracker`

The tracker watches the selected final object over recent frames and grades:

- 9-region movement
- bounding-box area growth
- rough distance trend
- movement speed
- whether the object is moving toward the center path

Risk levels:

- `none`
- `low`
- `medium`
- `high`

Only `medium` and `high` risk can upgrade a far object into a caution warning.

## Important behavior

### Dangerous pattern

Example:

- object starts in `middle_left`
- moves to `middle_center`
- box gets larger
- rough distance gets smaller
- movement is fast

This becomes high risk because the object appears to be entering the user's
path and approaching.

### Not very dangerous pattern

Example:

- object moves from left to center/right
- box does not grow
- rough distance does not decrease

This stays low risk. A random side-to-side crossing should not trigger a strong
warning by itself.

## How this changes warning behavior

Old behavior:

- far objects usually produced no warning.

New behavior:

- far object + medium/high approach risk can produce:
  - `Caution. approaching obstacle ahead.`
  - `Caution. approaching obstacle from left.`
  - `Caution. approaching obstacle from right.`

Close center objects still use the stronger warning:

- `Stop. obstacle ahead.`

## How this uses the 9-region grid

The tracker treats these as stronger danger signals only when size/distance
also suggests approach:

- left/right region moving toward center
- top or middle region moving downward toward middle/bottom
- center offset decreasing, meaning the object is moving toward the user's path

## How this uses distance

Distance is used as a grade/trend, not an exact measurement.

The tracker checks whether the rough distance is decreasing over recent frames.
This supports the idea that the object is coming closer, but it is only one
vote in the score.

## Future implementation for background motion

The user's third idea is important:

When the user walks forward, background points should move in a shared pattern.
An independently moving object may move faster or differently than that shared
background motion.

Future approach:

1. Track several stable background feature points.
2. Estimate global camera/background motion using optical flow.
3. Treat that global motion as the expected background movement.
4. Compare object motion against the expected background movement.
5. Warn only when an object's relative motion is unusual and its size/distance
   trend suggests danger.

This should be tested carefully because optical flow can cost CPU on Raspberry
Pi 4B. A lightweight sparse optical-flow method is probably safer than dense
optical flow.
