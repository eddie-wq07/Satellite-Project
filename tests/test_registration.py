# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Check the public task registry and its supported training configuration."""

from importlib import import_module

import gymnasium as gym

import Satellite_Project.tasks  # noqa: F401


def test_task_registrations():
    task_id = "SatelliteProject-Satellite-Arm-Direct"
    assert {key for key in gym.registry if key.startswith("SatelliteProject-")} == {task_id}
    spec = gym.spec(task_id)
    module = "Satellite_Project.tasks.satellite_direct.config.Arm"
    assert spec.entry_point == f"{module}.env:SatelliteEnv"
    assert spec.kwargs == {
        "env_cfg_entry_point": f"{module}.env_cfg:SatelliteEnvCfg",
        "rsl_rl_cfg_entry_point": f"{module}.agents.rsl_rl_ppo_cfg:PPORunnerCfg",
    }
    agent_module, agent_class = spec.kwargs["rsl_rl_cfg_entry_point"].split(":")
    assert getattr(import_module(agent_module), agent_class)().obs_groups == {"actor": ["policy"], "critic": ["policy"]}
