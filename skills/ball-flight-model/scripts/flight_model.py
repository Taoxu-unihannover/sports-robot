"""Ball flight model with gravity, quadratic drag, and optional Magnus force.

Supports both spherical ball (table tennis / tennis) and high-drag
shuttlecock (badminton) flight regimes.  Provides RK4 integration,
bounce detection, and hit-candidate extraction.
"""

from dataclasses import dataclass, field
from typing import Iterable, List, Optional

import numpy as np


@dataclass
class FlightState:
    position: np.ndarray
    velocity: np.ndarray
    spin: np.ndarray

    def __init__(self, position: Iterable[float], velocity: Iterable[float], spin: Iterable[float] = (0.0, 0.0, 0.0)):
        self.position = np.asarray(list(position), dtype=float)
        self.velocity = np.asarray(list(velocity), dtype=float)
        self.spin = np.asarray(list(spin), dtype=float)


@dataclass
class HitCandidate:
    time: float
    position: np.ndarray
    velocity: np.ndarray


@dataclass
class BouncePoint:
    time: float
    position: np.ndarray
    velocity_before: np.ndarray
    velocity_after: np.ndarray


class BallFlightModel:
    def __init__(
        self,
        mass: float,
        radius: float,
        drag_coefficient: float,
        air_density: float = 1.225,
        magnus_gain: float = 0.0,
        gravity: Iterable[float] = (0.0, 0.0, -9.81),
    ):
        if mass <= 0 or radius <= 0:
            raise ValueError("mass and radius must be positive")
        self.mass = float(mass)
        self.radius = float(radius)
        self.area = float(np.pi * radius * radius)
        self.drag_coefficient = float(drag_coefficient)
        self.air_density = float(air_density)
        self.magnus_gain = float(magnus_gain)
        self.gravity = np.asarray(list(gravity), dtype=float)

    def acceleration(self, state: FlightState) -> np.ndarray:
        v = state.velocity
        speed = float(np.linalg.norm(v))
        drag = np.zeros(3)
        if speed > 1e-9:
            drag_force = -0.5 * self.air_density * self.drag_coefficient * self.area * speed * v
            drag = drag_force / self.mass
        magnus = self.magnus_gain * np.cross(state.spin, v)
        return self.gravity + drag + magnus

    def step(self, state: FlightState, dt: float) -> FlightState:
        if dt <= 0:
            raise ValueError("dt must be positive")

        def deriv(s: FlightState) -> np.ndarray:
            return np.hstack([s.velocity, self.acceleration(s)])

        y0 = np.hstack([state.position, state.velocity])

        def from_y(y: np.ndarray) -> FlightState:
            return FlightState(y[:3], y[3:], state.spin)

        k1 = deriv(from_y(y0))
        k2 = deriv(from_y(y0 + 0.5 * dt * k1))
        k3 = deriv(from_y(y0 + 0.5 * dt * k2))
        k4 = deriv(from_y(y0 + dt * k3))
        y = y0 + dt * (k1 + 2 * k2 + 2 * k3 + k4) / 6.0
        return FlightState(y[:3], y[3:], state.spin)

    def rollout(self, state: FlightState, dt: float, steps: int) -> List[FlightState]:
        out = [state]
        current = state
        for _ in range(steps):
            current = self.step(current, dt)
            out.append(current)
        return out

    def first_plane_crossing(self, state: FlightState, axis: int, value: float, dt: float, max_steps: int):
        previous = state
        previous_distance = previous.position[axis] - value
        for _ in range(max_steps):
            current = self.step(previous, dt)
            distance = current.position[axis] - value
            if previous_distance == 0 or previous_distance * distance <= 0:
                alpha = abs(previous_distance) / max(abs(previous_distance) + abs(distance), 1e-12)
                pos = previous.position * (1 - alpha) + current.position * alpha
                vel = previous.velocity * (1 - alpha) + current.velocity * alpha
                return FlightState(pos, vel, current.spin)
            previous = current
            previous_distance = distance
        return None

    def predict_with_bounces(
        self,
        state: FlightState,
        dt: float,
        duration: float,
        table_height: float = 0.0,
        restitution: float = 0.9,
        friction: float = 0.3,
        max_bounces: int = 3,
    ) -> dict:
        steps = int(duration / dt)
        trajectory = [state]
        bounces: List[BouncePoint] = []
        current = state
        t = 0.0
        for _ in range(steps):
            current = self.step(current, dt)
            t += dt
            if current.position[2] <= table_height and current.velocity[2] < 0:
                if len(bounces) < max_bounces:
                    v_before = current.velocity.copy()
                    vn = current.velocity[2]
                    vt = np.array([current.velocity[0], current.velocity[1], 0.0])
                    vt_norm = float(np.linalg.norm(vt[:2]))
                    if vt_norm > 1e-9 and friction * abs(vn) < vt_norm:
                        scale = 1.0 - friction * abs(vn) / vt_norm
                        vt[:2] *= scale
                    else:
                        vt[:2] *= 0.0
                    current = FlightState(
                        position=np.array([current.position[0], current.position[1], table_height]),
                        velocity=np.array([vt[0], vt[1], -restitution * vn]),
                        spin=current.spin,
                    )
                    bounces.append(BouncePoint(time=t, position=current.position.copy(), velocity_before=v_before, velocity_after=current.velocity.copy()))
                else:
                    break
            trajectory.append(current)
        return {"trajectory": trajectory, "bounces": bounces}

    def extract_hit_candidates(
        self,
        state: FlightState,
        dt: float,
        duration: float,
        hit_zone_center: Iterable[float],
        hit_zone_radius: float,
        table_height: float = 0.0,
        restitution: float = 0.9,
        friction: float = 0.3,
    ) -> List[HitCandidate]:
        result = self.predict_with_bounces(state, dt, duration, table_height, restitution, friction)
        center = np.asarray(list(hit_zone_center), dtype=float)
        candidates: List[HitCandidate] = []
        t = 0.0
        for s in result["trajectory"]:
            dist = float(np.linalg.norm(s.position - center))
            if dist <= hit_zone_radius and s.velocity[2] < 0:
                candidates.append(HitCandidate(time=t, position=s.position.copy(), velocity=s.velocity.copy()))
            t += dt
        return candidates


class ShuttleFlightModel:
    def __init__(
        self,
        mass: float = 0.005,
        drag_coefficient: float = 0.6,
        gravity: Iterable[float] = (0.0, 0.0, -9.81),
        decay_rate: float = 0.0,
    ):
        if mass <= 0:
            raise ValueError("mass must be positive")
        self.mass = float(mass)
        self.drag_coefficient = float(drag_coefficient)
        self.gravity = np.asarray(list(gravity), dtype=float)
        self.decay_rate = float(decay_rate)

    def acceleration(self, state: FlightState) -> np.ndarray:
        v = state.velocity
        speed = float(np.linalg.norm(v))
        drag = np.zeros(3)
        if speed > 1e-9:
            drag_accel = self.drag_coefficient * speed
            drag = -drag_accel * v / self.mass
            if self.decay_rate > 0:
                drag *= np.exp(-self.decay_rate * speed)
        return self.gravity + drag

    def step(self, state: FlightState, dt: float) -> FlightState:
        if dt <= 0:
            raise ValueError("dt must be positive")

        def deriv(s: FlightState) -> np.ndarray:
            return np.hstack([s.velocity, self.acceleration(s)])

        y0 = np.hstack([state.position, state.velocity])

        def from_y(y: np.ndarray) -> FlightState:
            return FlightState(y[:3], y[3:], state.spin)

        k1 = deriv(from_y(y0))
        k2 = deriv(from_y(y0 + 0.5 * dt * k1))
        k3 = deriv(from_y(y0 + 0.5 * dt * k2))
        k4 = deriv(from_y(y0 + dt * k3))
        y = y0 + dt * (k1 + 2 * k2 + 2 * k3 + k4) / 6.0
        return FlightState(y[:3], y[3:], state.spin)

    def rollout(self, state: FlightState, dt: float, steps: int) -> List[FlightState]:
        out = [state]
        current = state
        for _ in range(steps):
            current = self.step(current, dt)
            out.append(current)
        return out

