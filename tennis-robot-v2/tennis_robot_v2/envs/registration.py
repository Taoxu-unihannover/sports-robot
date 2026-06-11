from gymnasium.envs.registration import register

register(
    id="SummitCatcherV2-v0",
    entry_point="tennis_robot_v2.envs.summit_catcher_env:SummitCatcherEnv",
    max_episode_steps=500,
)

register(
    id="TennisNavigationV2-v1",
    entry_point="tennis_robot_v2.envs.tennis_navigation_v2_env:TennisNavigationV2Env",
    max_episode_steps=2000,
)
