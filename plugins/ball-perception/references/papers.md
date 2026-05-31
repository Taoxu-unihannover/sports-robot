# Reference Papers

## Core Architecture Papers

### DeepMind Table Tennis (2024)
- **Title**: Robotic Table Tennis: A Case Study into a High Speed Learning System
- **Paper**: https://arxiv.org/abs/2309.03315
- **Key contributions**:
  - Raw Bayer image processing (skip demosaicing, save ~1ms latency)
  - 27k-parameter temporal CNN for 2D ball detection
  - DLT triangulation + recursive Kalman filter for 3D tracking
  - Latency modeling as Gaussian distributions in simulation
  - 125 FPS Ximea cameras with hardware sync, 838μs sensor latency
  - Opposing-side camera placement reduces triangulation bias by 10x

### ETH Legged Badminton (2025)
- **Title**: Learning Coordinated Badminton Skills for Legged Manipulators
- **Paper**: https://www.science.org/doi/10.1126/scirobotics.adu3922
- **Key contributions**:
  - 60 Hz perception, 400 Hz state estimation, 100 Hz control (async architecture)
  - HSV color filtering + ZED X stereo depth for 3D ball localization
  - EKF in map frame with IMU prediction + visual update
  - System identification for physics parameters

### One-Shot Shuttle Detection (2026)
- **Title**: One-Shot Badminton Shuttle Detection for Mobile Robots
- **Paper**: https://arxiv.org/abs/2603.06691
- **Code**: https://github.com/leggedrobotics/shuttle_detection
- **Key contributions**:
  - 20,510 frames, 11 backgrounds, 3 difficulty levels
  - YOLOv8 with max_det=1, 1024px input
  - GMM background subtraction + YOLOv8-seg for auto-labeling (85.7% accuracy)
  - Distance-based metric (≤25px = TP) instead of IoU
  - COCO negative samples to reduce false positives

### Sony Ace (2024)
- **Title**: Ace: A Competitive Robot for Table Tennis
- **Paper**: Project page at Sony AI
- **Code**: https://github.com/SonyResearch/ace_public
- **Key contributions**:
  - 9 APS cameras at 200 Hz + 3 event cameras for spin estimation
  - 3.0 mm 3D localization error, 10.2 ms perception latency
  - FPGA-accelerated 2D detection on each camera

## Tracking Methods

### TrackNet Series
- **TrackNetV1** (2019): VGG-16 backbone, 3-frame input, Gaussian heatmap output
  - Code: https://github.com/yastrebksv/TrackNet
  - GitLab: https://gitlab.nol.cs.nycu.edu.tw/open-source/TrackNet
- **TrackNetV2** (2020): MIMO design, weighted BCE loss
- **TrackNetV3** (2023): Trajectory prediction + rectification (inpainting)
  - Accuracy: 97.51%, F1: 98.56%, 25.11 FPS
  - Code: https://github.com/Chang-Chia-Chi/TrackNet-Badminton-Tracking-tensorflow2
  - Paper: https://dl.acm.org/doi/10.1145/3595916.3626384
- **TrackNetV4** (2025): Motion attention maps

### MonoTrack (2022)
- **Title**: MonoTrack: Shuttle trajectory reconstruction from monocular badminton video
- **Paper**: https://arxiv.org/abs/2204.01899
- **Venue**: CVSports @ CVPR 2022
- **Key contributions**:
  - End-to-end 2D/3D trajectory from broadcast video
  - Court recognition + 2D tracking + hit recognition + 3D reconstruction
  - Uses domain knowledge: court dimensions, shot placement, physics

## Datasets

| Dataset | Frames | Source | Link |
|---------|--------|--------|------|
| One-Shot Shuttle Detection | 20,510 | ETH RSL | See GitHub README |
| Shuttlecock Trajectory Dataset | 55,563 | NYCU | Google Drive (see TrackNet repos) |
| TrackNetV1 Dataset | ~18,000 | NYCU | Google Drive (see TrackNetV1 repo) |
