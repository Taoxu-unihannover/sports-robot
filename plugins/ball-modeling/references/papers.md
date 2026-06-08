# Ball Modeling 参考资料

## 运动学与动力学
- Pinocchio: rigid-body kinematics and dynamics (Lie-group FK/IK/Jacobian).
- Featherstone: RNEA inverse dynamics, ABA forward dynamics, CRBA mass matrix.
- Siciliano: Robotics — Modelling, Planning and Control (workspace & singularity).

## 飞行模型
- MIT robotic table tennis: lumped drag and paddle impact model.
- ETH badminton robot: shuttlecock aerodynamic identification (high-drag exponential decay).
- Cross: Aerodynamics of a tennis ball (quadratic drag + Magnus effect).

## 接触与碰撞
- Stronge: Impact Mechanics (impulse-based contact, restitution, friction).
- MuJoCo / Drake: compliant contact model (spring-damper + Coulomb friction).

## 参数辨识
- Ljung: System Identification — batch NLS, RLS, dual EKF.
- ETH: online aerodynamic parameter identification for shuttlecocks.
- Wensing: parameter identification with physical constraints (bounds, freeze conditions).

## 不确定性与风险
- Bar-Shalom: Estimation with Applications to Tracking and Navigation (covariance propagation, Mahalanobis gating).
- Rockafellar: CVaR optimization for risk-aware control.
- ACE: multi-sensor state fusion, model switching, and uncertainty handling.

## 传感器标定
- Kalibr: camera-IMU extrinsic calibration, time offset estimation.
- Furgale: unified spatiotemporal calibration framework.
- OpenCV: distortion correction and intrinsic calibration.
