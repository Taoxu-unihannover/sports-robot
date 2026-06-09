import numpy as np


class MecanumController:
    def __init__(self, wheel_base=0.445, track_width=0.409, wheel_radius=0.120, torque_limit=50.0):
        self.wheel_base = wheel_base
        self.track_width = track_width
        self.wheel_radius = wheel_radius
        self.torque_limit = torque_limit

    def inverse_kinematics(self, vx, vy, omega):
        front_left = (1.0 / self.wheel_radius) * (vx - vy - omega * (self.wheel_base + self.track_width) / 2)
        front_right = (1.0 / self.wheel_radius) * (vx + vy + omega * (self.wheel_base + self.track_width) / 2)
        back_left = (1.0 / self.wheel_radius) * (vx + vy - omega * (self.wheel_base + self.track_width) / 2)
        back_right = (1.0 / self.wheel_radius) * (vx - vy + omega * (self.wheel_base + self.track_width) / 2)
        return np.array([front_left, front_right, back_left, back_right])

    def action_to_wheel_torques(self, action):
        x_move = action[0]
        y_move = action[1]
        rotate = action[2]

        front_left = x_move - y_move - rotate
        front_right = x_move + y_move + rotate
        back_left = x_move + y_move - rotate
        back_right = x_move - y_move + rotate

        wheel_commands = np.array([front_left, front_right, back_left, back_right])
        max_val = np.max(np.abs(wheel_commands))
        if max_val > 1.0:
            wheel_commands /= max_val

        return wheel_commands * self.torque_limit

    def forward_kinematics(self, wheel_speeds):
        fl, fr, bl, br = wheel_speeds
        r = self.wheel_radius
        vx = r * (fl + fr + bl + br) / 4
        vy = r * (-fl + fr + bl - br) / 4
        omega = r * (-fl + fr - bl + br) / (2 * (self.wheel_base + self.track_width))
        return np.array([vx, vy, omega])
