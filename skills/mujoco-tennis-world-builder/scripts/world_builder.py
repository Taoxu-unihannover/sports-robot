import mujoco
import numpy as np
import os
import yaml


def load_config(config_path):
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.load(f, Loader=yaml.FullLoader)


COURT_STANDARDS = {
    "tennis": {"length": 11.885, "width": 8.23},
    "badminton": {"length": 6.7, "width": 6.1},
    "table_tennis": {"length": 1.37, "width": 0.7625},
}

BALL_STANDARDS = {
    "tennis": {"radius": 0.067, "rgba": "0.9 0.9 0.9 1.0"},
    "badminton": {"radius": 0.025, "rgba": "1.0 1.0 1.0 1.0"},
    "table_tennis": {"radius": 0.02, "rgba": "1.0 1.0 1.0 1.0"},
}


def generate_assets_xml(output_dir, mesh_dir="./meshes"):
    content = f"""<mujocoinclude>
    <compiler angle="radian" autolimits="true" meshdir="{mesh_dir}"/>
    <statistic meansize="0.767828" extent="17.3945" center="-1.30273 -0.281443 0.819464"/>
    <asset>
        <texture name="texplane" type="2d" builtin="checker" rgb1=".2 .3 .4" rgb2=".1 0.2 0.3" width="512" height="512"/>
        <material name="MatGnd" reflectance="0.5" texture="texplane" texrepeat="1 1" texuniform="true"/>
    </asset>
</mujocoinclude>"""
    path = os.path.join(output_dir, "assets.xml")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def generate_scene_xml(output_dir, sport_type="tennis", court_dims=None, ball_params=None):
    if court_dims is None:
        court_dims = COURT_STANDARDS.get(sport_type, COURT_STANDARDS["tennis"])
    if ball_params is None:
        ball_params = BALL_STANDARDS.get(sport_type, BALL_STANDARDS["tennis"])

    half_l = court_dims["length"] / 2
    half_w = court_dims["width"] / 2
    ball_r = ball_params["radius"]
    ball_rgba = ball_params["rgba"]
    ball_r_vis = ball_r + 0.001

    content = f"""<mujocoinclude>
    <geom name="ground" pos="0 0 -0.01" rgba="0.25 0.26 0.25 1" size="10 10 2" type="plane" contype="1" conaffinity="1"/>

    <body name="goal_body" pos="0 0 {ball_r}">
        <freejoint name="goal_joint"/>
        <geom name="goal_ball" size="{ball_r}" type="sphere" rgba="{ball_rgba}" contype="1" conaffinity="1"/>
        <geom name="goal_lines" size="{ball_r_vis}" type="sphere" rgba="0.0 0.8 0.0 0.3" contype="0" conaffinity="0"/>
    </body>

    <body name="corner_bl" pos="{-half_w} {-half_l} 0.01">
        <geom size="0.05 0.02" type="cylinder" rgba="0.8 0.8 0.8 0.8" contype="0" conaffinity="0"/>
    </body>
    <body name="corner_br" pos="{half_w} {-half_l} 0.01">
        <geom size="0.05 0.02" type="cylinder" rgba="0.8 0.8 0.8 0.8" contype="0" conaffinity="0"/>
    </body>
    <body name="corner_fl" pos="{-half_w} {half_l} 0.01">
        <geom size="0.05 0.02" type="cylinder" rgba="0.8 0.8 0.8 0.8" contype="0" conaffinity="0"/>
    </body>
    <body name="corner_fr" pos="{half_w} {half_l} 0.01">
        <geom size="0.05 0.02" type="cylinder" rgba="0.8 0.8 0.8 0.8" contype="0" conaffinity="0"/>
    </body>

    <body name="baseline_center" pos="0.0 {-half_l} 0.005">
        <geom size="0.05 0.01 0.005" type="box" rgba="1.0 0.0 0.0 0.6" contype="0" conaffinity="0"/>
    </body>

    <light cutoff="4.0" diffuse="1 1 1" dir="-0.9 -0.9 -2.5" directional="true" exponent="20" pos="0.9 0.9 2.5" specular="0 0 0"/>
</mujocoinclude>"""
    path = os.path.join(output_dir, "scene.xml")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def generate_mecanum_robot_xml(output_dir):
    content = """<mujocoinclude>
    <body name="base_footprint" pos="0 0 -0.009">
        <joint type="free" stiffness="0" damping="0" frictionloss="0" armature="0"/>
        <body name="base" pos="0 0 0.127">
            <inertial pos="0 0 0" quat="1 0 0 0" mass="125.0" diaginertia="1.391 6.853 6.125"/>
            <geom type="box" size="0.35 0.25 0.15" rgba="0.2 0.2 0.8 1" contype="1" conaffinity="0" group="1"/>

            <body name="front_right_wheel_link" pos="0.2225 -0.2045 0">
                <inertial pos="0 0 0" quat="0.707107 0 0 0.707107" mass="6.5" diaginertia="0.0524193 0.0303095 0.0303095"/>
                <joint name="front_right_wheel_rolling_joint" pos="0 0 0" axis="0 1 0"/>
                <geom size="0.120 0.0435" quat="0.707107 0.707107 0 0" type="cylinder" rgba="0.2 0.2 0.2 0.5" contype="1" conaffinity="0" group="3"/>
            </body>

            <body name="front_left_wheel_link" pos="0.2225 0.2045 0">
                <inertial pos="0 0 0" quat="0.707107 0 0 0.707107" mass="6.5" diaginertia="0.0524193 0.0303095 0.0303095"/>
                <joint name="front_left_wheel_rolling_joint" pos="0 0 0" axis="0 1 0"/>
                <geom size="0.120 0.0435" quat="0.707107 0.707107 0 0" type="cylinder" rgba="0.2 0.2 0.2 0.5" contype="1" conaffinity="0" group="3"/>
            </body>

            <body name="back_right_wheel_link" pos="-0.2225 -0.2045 0">
                <inertial pos="0 0 0" quat="0.707107 0 0 0.707107" mass="6.5" diaginertia="0.0524193 0.0303095 0.0303095"/>
                <joint name="back_right_wheel_rolling_joint" pos="0 0 0" axis="0 1 0"/>
                <geom size="0.120 0.0435" quat="0.707107 0.707107 0 0" type="cylinder" rgba="0.2 0.2 0.2 0.5" contype="1" conaffinity="0" group="3"/>
            </body>

            <body name="back_left_wheel_link" pos="-0.2225 0.2045 0">
                <inertial pos="0 0 0" quat="0.707107 0 0 0.707107" mass="6.5" diaginertia="0.0524193 0.0303095 0.0303095"/>
                <joint name="back_left_wheel_rolling_joint" pos="0 0 0" axis="0 1 0"/>
                <geom size="0.120 0.0435" quat="0.707107 0.707107 0 0" type="cylinder" rgba="0.2 0.2 0.2 0.5" contype="1" conaffinity="0" group="3"/>
            </body>
        </body>
    </body>
</mujocoinclude>"""
    path = os.path.join(output_dir, "robot.xml")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def generate_actuator_xml(output_dir, ctrl_range="-10 10"):
    content = f"""<mujocoinclude>
    <actuator>
        <motor name="front_right_wheel_rolling_joint" joint="front_right_wheel_rolling_joint" ctrlrange="{ctrl_range}"/>
        <motor name="front_left_wheel_rolling_joint" joint="front_left_wheel_rolling_joint" ctrlrange="{ctrl_range}"/>
        <motor name="back_right_wheel_rolling_joint" joint="back_right_wheel_rolling_joint" ctrlrange="{ctrl_range}"/>
        <motor name="back_left_wheel_rolling_joint" joint="back_left_wheel_rolling_joint" ctrlrange="{ctrl_range}"/>
    </actuator>
</mujocoinclude>"""
    path = os.path.join(output_dir, "actuator.xml")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def generate_world_xml(output_dir, model_name="tennis_world"):
    content = f"""<mujoco model="{model_name}">
    <include file="assets.xml"/>
    <worldbody>
        <include file="scene.xml"/>
        <include file="robot.xml"/>
    </worldbody>
    <include file="actuator.xml"/>
</mujoco>"""
    path = os.path.join(output_dir, f"{model_name}.xml")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def generate_tennis_world(output_dir, sport_type="tennis", court_dims=None, ball_params=None):
    os.makedirs(output_dir, exist_ok=True)
    assets_dir = os.path.join(output_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)

    generate_assets_xml(assets_dir)
    generate_scene_xml(assets_dir, sport_type, court_dims, ball_params)
    generate_mecanum_robot_xml(assets_dir)
    generate_actuator_xml(assets_dir)
    world_path = generate_world_xml(output_dir, f"{sport_type}_world")

    return world_path


def verify_world(xml_path):
    try:
        model = mujoco.MjModel.from_xml_path(xml_path)
        data = mujoco.MjData(model)
        mujoco.mj_step(model, data)
        return True, f"nq={model.nq}, nv={model.nv}, nu={model.nu}"
    except Exception as e:
        return False, str(e)


if __name__ == "__main__":
    import sys
    output = sys.argv[1] if len(sys.argv) > 1 else "./generated_world"
    path = generate_tennis_world(output)
    ok, info = verify_world(path)
    print(f"World generated: {path}")
    print(f"Verification: {'PASS' if ok else 'FAIL'} - {info}")
