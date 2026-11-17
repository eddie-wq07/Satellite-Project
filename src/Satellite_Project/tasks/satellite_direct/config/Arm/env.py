# Copyright (c) 2022-2026, The Isaac Lab Project Developers (https://github.com/isaac-sim/IsaacLab/blob/main/CONTRIBUTORS.md).
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

import numpy as np
from gymnasium import spaces
import torch

from isaaclab.envs import DirectRLEnv

if TYPE_CHECKING:
    from .env_cfg import SatelliteEnvCfg


class SatelliteEnv(DirectRLEnv):
    """Implement the task's environment lifecycle."""

    cfg: SatelliteEnvCfg

    def __init__(self, cfg: SatelliteEnvCfg, render_mode: str | None = None, **kwargs):
        super().__init__(cfg, render_mode, **kwargs)
        self.amp_observation_size = self.cfg.num_amp_observations * self.cfg.amp_observation_space
        self.amp_observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(self.amp_observation_size,))
        self.amp_observation_buffer = torch.zeros(
            (self.num_envs, self.cfg.num_amp_observations, self.cfg.amp_observation_space), device=self.device
        )

    def _pre_physics_step(self, actions: torch.Tensor) -> None:
        raise NotImplementedError("Process policy actions.")

    def _apply_action(self) -> None:
        raise NotImplementedError("Apply actions to the simulation.")

    def _get_observations(self) -> dict[str, torch.Tensor]:
        """Compute policy observations and update AMP observation history.

        Set self.extras["amp_obs"] to the flattened history with shape
        (self.num_envs, self.amp_observation_size) on every step.
        """
        raise NotImplementedError("Compute policy observations.")

    def _get_rewards(self) -> torch.Tensor:
        raise NotImplementedError("Compute task rewards.")

    def _get_dones(self) -> tuple[torch.Tensor, torch.Tensor]:
        raise NotImplementedError("Compute termination and timeout conditions.")

    def _reset_idx(self, env_ids: Sequence[int] | None) -> None:
        raise NotImplementedError("Reset selected environments.")

    def collect_reference_motions(self, num_samples: int, current_times: np.ndarray | None = None) -> torch.Tensor:
        raise NotImplementedError("Collect task-specific AMP reference motions.")
