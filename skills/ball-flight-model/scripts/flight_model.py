"""Ball flight model with gravity, quadratic drag, and optional Magnus force."""

from dataclasses import dataclass
from typing import Iterable, List

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

