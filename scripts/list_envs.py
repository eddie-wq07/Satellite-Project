# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""List this project's supported Gym tasks without loading external task plugins."""

import gymnasium as gym
import sim_bootstrap  # noqa: F401

import Satellite_Project.tasks  # noqa: F401


def main():
    for spec in gym.registry.values():
        if spec.id.startswith("SatelliteProject-"):
            print(f"{spec.id}\n  Environment: {spec.entry_point}")
            print(f"  PPO config: {spec.kwargs['rsl_rl_cfg_entry_point']}")


if __name__ == "__main__":
    main()
