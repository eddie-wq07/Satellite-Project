# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Tests for the project's task registrations."""

import gymnasium as gym

import Satellite_Project.tasks  # noqa: F401


def test_task_registrations():
    """The project tasks must expose valid environment and agent entry points."""
    expected = {
        "SatelliteProject-Satellite-Arm": {
            "entry_point": "Satellite_Project.tasks.satellite.config.Arm.env:SatelliteEnv",
            "env_cfg_entry_point": "Satellite_Project.tasks.satellite.config.Arm.env_cfg:SatelliteEnvCfg",
        },
        "SatelliteProject-Satellite-Arm-Direct": {
            "entry_point": "Satellite_Project.tasks.satellite_direct.config.Arm.env:SatelliteEnv",
            "env_cfg_entry_point": "Satellite_Project.tasks.satellite_direct.config.Arm.env_cfg:SatelliteEnvCfg",
        },
        "SatelliteProject-Satellite-Marl-Arm-Direct": {
            "entry_point": "Satellite_Project.tasks.satellite_marl_direct.config.Arm.env:SatelliteMarlEnv",
            "env_cfg_entry_point": "Satellite_Project.tasks.satellite_marl_direct.config.Arm.env_cfg:SatelliteMarlEnvCfg",
            "default_agent": "skrl",
        },
    }

    for task_id, expected_values in expected.items():
        spec = gym.spec(task_id)
        assert spec.entry_point == expected_values["entry_point"]
        assert spec.kwargs["env_cfg_entry_point"] == expected_values["env_cfg_entry_point"]
        if "default_agent" in expected_values:
            assert spec.kwargs["default_agent"] == expected_values["default_agent"]
