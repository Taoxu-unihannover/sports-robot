"""Rigid-body dynamics reference model for ball-striking robots.

Provides forward dynamics (ABA-style), inverse dynamics (RNEA-style),
mass matrix (CRBA-style), and torque feasibility checks for planar
serial manipulators. The same interfaces map to Pinocchio for full 3D
URDF-backed models.
"""

from dataclasses import dataclass, field
from typing import Iterable, List, Optional

import numpy as np


@dataclass
class LinkParams:
    mass: float
    length: float
    com_ratio: float = 0.5
    inertia: float = 0.0

    def __post_init__(self):
        if self.mass <= 0 or self.length <= 0:
            raise ValueError("mass and length must be positive")
        if self.inertia <= 0:
            self.inertia = self.mass * self.length ** 2 / 12.0


@dataclass
class FrictionParams:
    viscous: np.ndarray = field(default_factory=lambda: np.zeros(1))
    coulomb: np.ndarray = field(default_factory=lambda: np.zeros(1))


class PlanarDynamicsModel:
    def __init__(self, links: Iterable[LinkParams], gravity: float = 9.81):
        self.links = list(links)
        self.n = len(self.links)
        self.gravity = gravity

    def _check_q(self, q: Iterable[float], name: str = "q") -> np.ndarray:
        arr = np.asarray(list(q), dtype=float)
        if arr.shape != (self.n,):
            raise ValueError(f"{name} expected {self.n} values, got {arr.shape}")
        return arr

    def _link_com_jacobian(self, q_arr: np.ndarray, link_idx: int) -> np.ndarray:
        cum_angles = np.cumsum(q_arr)
        Jp = np.zeros((2, self.n))
        for j in range(link_idx):
            angle_j = float(cum_angles[j])
            for k in range(self.n):
                if k <= j:
                    Jp[0, k] += -self.links[j].length * np.sin(angle_j)
                    Jp[1, k] += self.links[j].length * np.cos(angle_j)
        angle_i = float(cum_angles[link_idx])
        for k in range(self.n):
            if k <= link_idx:
                Jp[0, k] += -self.links[link_idx].length * self.links[link_idx].com_ratio * np.sin(angle_i)
                Jp[1, k] += self.links[link_idx].length * self.links[link_idx].com_ratio * np.cos(angle_i)
        return Jp

    def mass_matrix(self, q: Iterable[float]) -> np.ndarray:
        q_arr = self._check_q(q)
        M = np.zeros((self.n, self.n))
        for i in range(self.n):
            Jp = self._link_com_jacobian(q_arr, i)
            M += self.links[i].mass * (Jp.T @ Jp)
            cum_angles = np.cumsum(q_arr)
            for j in range(i + 1):
                M[j, j] += self.links[i].inertia if j == i else 0.0
        M = 0.5 * (M + M.T)
        for i in range(self.n):
            M[i, i] = max(M[i, i], self.links[i].inertia)
        return M

    def coriolis_gravity(self, q: Iterable[float], qd: Iterable[float]) -> np.ndarray:
        q_arr = self._check_q(q)
        qd_arr = self._check_q(qd, "qd")
        tau_g = np.zeros(self.n)
        cum_angles = np.cumsum(q_arr)
        for i in range(self.n):
            m_eff = sum(link.mass for link in self.links[i:])
            com_x = 0.0
            for m in range(i):
                com_x += self.links[m].length * np.cos(float(cum_angles[m]))
            com_x += self.links[i].length * self.links[i].com_ratio * np.cos(float(cum_angles[i]))
            tau_g[i] = m_eff * self.gravity * com_x
        return tau_g

    def inverse_dynamics(self, q: Iterable[float], qd: Iterable[float], qdd: Iterable[float],
                         friction: Optional[FrictionParams] = None) -> np.ndarray:
        q_arr = self._check_q(q)
        qd_arr = self._check_q(qd, "qd")
        qdd_arr = self._check_q(qdd, "qdd")
        M = self.mass_matrix(q_arr)
        cg = self.coriolis_gravity(q_arr, qd_arr)
        tau = M @ qdd_arr + cg
        if friction is not None:
            v = np.asarray(friction.viscous, dtype=float)
            c = np.asarray(friction.coulomb, dtype=float)
            if v.shape == (self.n,):
                tau += v * qd_arr
            if c.shape == (self.n,):
                tau += c * np.sign(qd_arr)
        return tau

    def forward_dynamics(self, q: Iterable[float], qd: Iterable[float], tau: Iterable[float],
                         friction: Optional[FrictionParams] = None) -> np.ndarray:
        q_arr = self._check_q(q)
        qd_arr = self._check_q(qd, "qd")
        tau_arr = np.asarray(list(tau), dtype=float)
        M = self.mass_matrix(q_arr)
        cg = self.coriolis_gravity(q_arr, qd_arr)
        tau_eff = tau_arr - cg
        if friction is not None:
            v = np.asarray(friction.viscous, dtype=float)
            c = np.asarray(friction.coulomb, dtype=float)
            if v.shape == (self.n,):
                tau_eff -= v * qd_arr
            if c.shape == (self.n,):
                tau_eff -= c * np.sign(qd_arr)
        try:
            qdd = np.linalg.solve(M, tau_eff)
        except np.linalg.LinAlgError:
            qdd = np.linalg.lstsq(M, tau_eff, rcond=None)[0]
        return qdd

    def torque_feasibility(self, q: Iterable[float], qd: Iterable[float], qdd: Iterable[float],
                           tau_max: Iterable[float], friction: Optional[FrictionParams] = None) -> dict:
        tau = self.inverse_dynamics(q, qd, qdd, friction)
        tau_max_arr = np.asarray(list(tau_max), dtype=float)
        margin = float(np.min((tau_max_arr - np.abs(tau)) / tau_max_arr))
        feasible = bool(np.all(np.abs(tau) <= tau_max_arr))
        return {"feasible": feasible, "tau": tau, "margin": margin}


def step_dynamics(model: PlanarDynamicsModel, q: List[float], qd: List[float], tau: List[float],
                  dt: float, friction: Optional[FrictionParams] = None) -> tuple:
    q_arr = np.asarray(q, dtype=float)
    qd_arr = np.asarray(qd, dtype=float)
    qdd = model.forward_dynamics(q_arr, qd_arr, tau, friction)
    qd_new = qd_arr + qdd * dt
    q_new = q_arr + qd_new * dt
    return q_new.tolist(), qd_new.tolist()
