# Mathematical Formulas Reference

## 1. DLT Triangulation

Given $n$ cameras with projection matrices $P_i = K_i [R_i | t_i]$, and 2D observations $(u_i, v_i)$:

For each camera $i$, the 3D point $\mathbf{X} = (X, Y, Z, 1)^T$ satisfies:

$$
\begin{bmatrix} u_i \\ v_i \\ 1 \end{bmatrix} \simeq P_i \mathbf{X}
$$

Cross product form:

$$
\begin{bmatrix} u_i \\ v_i \\ 1 \end{bmatrix} \times (P_i \mathbf{X}) = \mathbf{0}
$$

This gives two independent equations per camera:

$$
\begin{aligned}
u_i (P_i^{3} \mathbf{X}) - (P_i^{1} \mathbf{X}) &= 0 \\
v_i (P_i^{3} \mathbf{X}) - (P_i^{2} \mathbf{X}) &= 0
\end{aligned}
$$

Stacking $2n$ equations: $A\mathbf{X} = \mathbf{0}$, solve via SVD.

## 2. Kalman Filter (Constant Velocity Model)

**State vector**: $\mathbf{x} = [p_x, p_y, v_x, v_y]^T$

**Prediction step**:

$$
\begin{aligned}
\hat{\mathbf{x}}_{k|k-1} &= F \hat{\mathbf{x}}_{k-1|k-1} \\
P_{k|k-1} &= F P_{k-1|k-1} F^T + Q
\end{aligned}
$$

where:

$$
F = \begin{bmatrix}
1 & 0 & \Delta t & 0 \\
0 & 1 & 0 & \Delta t \\
0 & 0 & 1 & 0 \\
0 & 0 & 0 & 1
\end{bmatrix}
$$

**Update step**:

$$
\begin{aligned}
\mathbf{y}_k &= \mathbf{z}_k - H \hat{\mathbf{x}}_{k|k-1} \\
S_k &= H P_{k|k-1} H^T + R \\
K_k &= P_{k|k-1} H^T S_k^{-1} \\
\hat{\mathbf{x}}_{k|k} &= \hat{\mathbf{x}}_{k|k-1} + K_k \mathbf{y}_k \\
P_{k|k} &= (I - K_k H) P_{k|k-1}
\end{aligned}
$$

where:

$$
H = \begin{bmatrix}
1 & 0 & 0 & 0 \\
0 & 1 & 0 & 0
\end{bmatrix}
$$

## 3. Extended Kalman Filter (with Air Drag)

**State**: $\mathbf{x} = [p_x, p_y, p_z, v_x, v_y, v_z]^T$

**Nonlinear motion model** (with drag coefficient $k_d$):

$$
\begin{aligned}
p_x(t+\Delta t) &= p_x(t) + v_x \Delta t - \frac{1}{2} k_d \|\mathbf{v}\| v_x \Delta t^2 \\
p_y(t+\Delta t) &= p_y(t) + v_y \Delta t - \frac{1}{2} k_d \|\mathbf{v}\| v_y \Delta t^2 \\
p_z(t+\Delta t) &= p_z(t) + v_z \Delta t - \frac{1}{2} k_d \|\mathbf{v}\| v_z \Delta t^2 - \frac{1}{2} g \Delta t^2 \\
v_x(t+\Delta t) &= v_x - k_d \|\mathbf{v}\| v_x \Delta t \\
v_y(t+\Delta t) &= v_y - k_d \|\mathbf{v}\| v_y \Delta t \\
v_z(t+\Delta t) &= v_z - k_d \|\mathbf{v}\| v_z \Delta t - g \Delta t
\end{aligned}
$$

## 4. Camera Projection

**Pinhole model**:

$$
\begin{bmatrix} u \\ v \\ 1 \end{bmatrix} \simeq
\underbrace{\begin{bmatrix} f_x & 0 & c_x \\ 0 & f_y & c_y \\ 0 & 0 & 1 \end{bmatrix}}_{K}
\underbrace{\begin{bmatrix} R_{3\times3} & t_{3\times1} \end{bmatrix}}_{[R|t]}
\begin{bmatrix} X \\ Y \\ Z \\ 1 \end{bmatrix}
$$

**Coordinate transformation** (camera → world):

$$
\mathbf{X}_{world} = R^T (\mathbf{X}_{cam} - t)
$$

## 5. Stereo Depth from Disparity

$$
Z = \frac{b \cdot f}{d}
$$

where:
- $b$ = baseline (distance between cameras)
- $f$ = focal length (in pixels)
- $d = u_L - u_R$ = disparity

## 6. Trajectory Smoothing (Exponential Weighted)

For a window of $n$ points with timestamps $t_i$:

$$
\hat{p} = \frac{\sum_{i=1}^{n} w_i p_i}{\sum_{i=1}^{n} w_i}, \quad
w_i = e^{-\alpha (t_n - t_i)}
$$

## 7. Latency Budget (DeepMind Reference)

| Component | Mean (ms) | Std (ms) |
|-----------|-----------|----------|
| Ball observation | 40 | 8.2 |
| ABB robot observation | 29 | 8.2 |
| Festo observation | 33 | 9.0 |
| ABB action | 71 | 5.7 |
| Festo action | 64.5 | 11.5 |

Total end-to-end latency modeled as sum of independent Gaussians.
