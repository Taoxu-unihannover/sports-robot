from gymnasium.envs.registration import register


def register_envs():
    register(
        id="TennisNavigation-v1",
        entry_point="tennis_robot.envs.tennis_navigation_env:TennisNavigationEnv",
        max_episode_steps=2000,
    )
