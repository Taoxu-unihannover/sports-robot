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

## 8. Magnus Effect (Spin Estimation)

The Magnus force on a spinning sphere:

$$
\mathbf{F}_{\text{Magnus}} = C_L \cdot \frac{4}{3}\pi r^3 \rho \cdot \boldsymbol{\omega} \times \mathbf{v}
$$

where:
- $C_L$ = lift coefficient
- $r$ = ball radius
- $\rho$ = air density
- $\boldsymbol{\omega}$ = angular velocity vector
- $\mathbf{v}$ = translational velocity

The Magnus acceleration:

$$
\mathbf{a}_{\text{Magnus}} = \frac{C_L \cdot \frac{4}{3}\pi r^3 \rho}{m} \cdot \boldsymbol{\omega} \times \mathbf{v}
$$

For spin estimation from trajectory, the full flight model is:

$$
\mathbf{a} = \mathbf{g} + \mathbf{a}_{\text{drag}} + \mathbf{a}_{\text{Magnus}}
$$

where drag acceleration:

$$
\mathbf{a}_{\text{drag}} = -k_d \|\mathbf{v}\| \mathbf{v}, \quad k_d = \frac{C_D \rho A}{2m}
$$

Given measured trajectory $\{\mathbf{p}_i\}$, estimate acceleration via finite differences, subtract gravity and drag, then solve for $\boldsymbol{\omega}$ from the residual Magnus acceleration.

## 9. Event Camera Optical Flow (Spin Estimation)

Event camera outputs asynchronous events $(x, y, t, \text{polarity})$ when pixel brightness changes exceed a threshold.

**Ordinal Time Surface**: Each pixel records the timestamp of the most recent event:

$$
T(x, y) = t_{\text{latest event at } (x, y)}
$$

**Event optical flow**: From the time surface gradient, compute the local optical flow:

$$
\mathbf{v}_{\text{flow}} = -\frac{\partial T / \partial t}{\|\nabla T\|^2} \nabla T
$$

**Angular velocity from flow**: For a sphere of radius $r$ at distance $\mathbf{r}$ from center:

$$
\mathbf{v}_{\text{flow}} = \boldsymbol{\omega} \times \mathbf{r}
$$

Solve for $\boldsymbol{\omega}$ via least squares over multiple surface points.

## 10. Perspective-n-Point (Marker-based Spin Estimation)

Given $n$ 2D-3D point correspondences $(\mathbf{u}_i, \mathbf{X}_i)$, solve for camera pose $(\mathbf{R}, \mathbf{t})$:

$$
\mathbf{u}_i \simeq \mathbf{K}[\mathbf{R} | \mathbf{t}]\mathbf{X}_i
$$

From consecutive poses $\mathbf{R}_t$ and $\mathbf{R}_{t+1}$, compute relative rotation:

$$
\Delta\mathbf{R} = \mathbf{R}_{t+1}\mathbf{R}_t^{-1}
$$

Convert to angular velocity via axis-angle representation:

$$
\boldsymbol{\omega} = \frac{\theta}{\Delta t} \hat{\mathbf{n}}
$$

where $\theta$ is the rotation angle and $\hat{\mathbf{n}}$ is the rotation axis of $\Delta\mathbf{R}$.

## 11. Sliding Window Velocity Estimation (LATENT)

$$
\hat{\mathbf{v}}_t = \frac{1}{N-1} \sum_{i=1}^{N-1} \frac{\mathbf{p}_{t-i+1} - \mathbf{p}_{t-i}}{\Delta t}, \quad N=4
$$

Noise variance reduction: $\sigma_v^2$ reduced by factor $1/(N-1) = 1/3$ compared to single-frame differencing.

Additional latency: $\approx (N-1)\Delta t / 2 \approx 30$ ms for $N=4$, $\Delta t = 20$ ms.
