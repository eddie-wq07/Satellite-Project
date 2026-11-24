"""Physical six-axis driving plus contact-gated vacuum batch transfer in Isaac Lab."""

import torch

from isaaclab.envs import DirectRLEnv
from isaaclab.utils.math import quat_apply, quat_conjugate, quat_mul


class SatelliteEnv(DirectRLEnv):
    def __init__(self, cfg, render_mode=None, **kwargs):
        super().__init__(cfg, render_mode, **kwargs)
        self.robot = self.scene["robot"]
        self.batch = self.scene["batch"]
        self.flange = self.robot.find_bodies("flange")[0][0]
        self.targets = torch.zeros(self.num_envs, 6, device=self.device)
        self.actions = torch.zeros(self.num_envs, 7, device=self.device)
        self.attached = torch.zeros(self.num_envs, dtype=torch.bool, device=self.device)
        self.ever_lifted = torch.zeros_like(self.attached)
        self.settled = torch.zeros(self.num_envs, device=self.device)
        self.goal = (
            torch.tensor([0.5, -0.70, 0.700], device=self.device).repeat(self.num_envs, 1) + self.scene.env_origins
        )
        # Neutral flange local X points down; cup contact plane is 156.5 mm below wrist.
        self.tip_offset = torch.tensor([0.1565, 0, -0.000125], device=self.device).repeat(self.num_envs, 1)
        self.axis = torch.tensor([-1.0, 0, 0], device=self.device).repeat(self.num_envs, 1)
        self.limits = self.robot.data.joint_pos_limits.torch[0]
        self.grasp_offset = self.tip_offset.clone()
        self.grasp_rotation = torch.zeros(self.num_envs, 4, device=self.device)
        self.grasp_rotation[:, 3] = 1

    def _setup_scene(self):
        pass

    def tip(self):
        d = self.robot.data
        return d.body_pos_w.torch[:, self.flange] + quat_apply(d.body_quat_w.torch[:, self.flange], self.tip_offset)

    def _release(self, i):
        self.attached[i] = False

    def _attach(self, i):
        q = self.robot.data.body_quat_w.torch[i, self.flange]
        bq = self.batch.data.root_quat_w.torch[i]
        self.grasp_offset[i] = self.tip_offset[i]
        self.grasp_rotation[i] = quat_mul(quat_conjugate(q[None]), bq[None])[0]
        self.attached[i] = True

    def _pre_physics_step(self, actions):
        self.actions = actions.clamp(-1, 1)
        self.targets = torch.clamp(
            self.targets + self.cfg.joint_step * self.actions[:, :6], self.limits[:, 0], self.limits[:, 1]
        )
        error = self.tip() - self.batch.data.root_pos_w.torch
        up = quat_apply(self.robot.data.body_quat_w.torch[:, self.flange], self.axis)
        # Require a near-level head and actual proximity; no distance-only teleport pickup.
        close = (
            (error[:, :2].norm(dim=-1) < 0.015) & (error[:, 2].abs() < self.cfg.suction_distance) & (up[:, 2] > 0.99)
        )
        for i in range(self.num_envs):
            if self.attached[i] and (self.actions[i, 6] < 0 or error[i].norm() > 0.06):
                self._release(i)
            elif not self.attached[i] and self.actions[i, 6] > 0.5 and close[i]:
                self._attach(i)

    def _apply_action(self):
        self.robot.actuators.target_command.set_position_index(value=self.targets)
        d = self.robot.data
        b = self.batch.data
        q = d.body_quat_w.torch[:, self.flange]
        offset = quat_apply(q, self.grasp_offset)
        target = d.body_pos_w.torch[:, self.flange] + offset
        velocity = d.body_lin_vel_w.torch[:, self.flange] + torch.cross(
            d.body_ang_vel_w.torch[:, self.flange], offset, dim=-1
        )
        force = 180 * (target - b.root_pos_w.torch) + 4 * (velocity - b.root_lin_vel_w.torch)
        force[:, 2] += 0.12 * 9.81
        force *= torch.clamp(self.cfg.suction_force_limit / force.norm(dim=-1, keepdim=True).clamp(min=0.001), max=1)
        desired = quat_mul(q, self.grasp_rotation)
        error = quat_mul(desired, quat_conjugate(b.root_quat_w.torch))
        torque = 0.4 * error[:, :3] * torch.sign(error[:, 3:]) - 0.012 * b.root_ang_vel_w.torch
        force *= self.attached[:, None]
        torque *= self.attached[:, None]
        self.batch.permanent_wrench_composer.set_forces_and_torques_index(
            forces=force[:, None], torques=torque[:, None], is_global=True
        )
        self.robot.permanent_wrench_composer.set_forces_and_torques_index(
            forces=-force[:, None],
            torques=-torque[:, None],
            positions=b.root_pos_w.torch[:, None],
            body_ids=[self.flange],
            is_global=True,
        )

    def _get_observations(self):
        d = self.robot.data
        b = self.batch.data
        return {
            "policy": torch.cat(
                [
                    d.joint_pos.torch,
                    d.joint_vel.torch * 0.1,
                    self.tip() - b.root_pos_w.torch,
                    self.goal - b.root_pos_w.torch,
                    b.root_lin_vel_w.torch,
                    self.attached[:, None].float(),
                    self.ever_lifted[:, None].float(),
                    (self.settled / 10)[:, None],
                    self.actions,
                ],
                dim=-1,
            )
        }

    def _get_rewards(self):
        p = self.batch.data.root_pos_w.torch
        height = p[:, 2] - self.scene.env_origins[:, 2]
        lifted = height > 0.80
        self.ever_lifted |= lifted
        reach = torch.exp(-15 * (self.tip() - p).norm(dim=-1))
        delivery = torch.exp(-5 * (self.goal - p).norm(dim=-1)) * self.ever_lifted
        reward = reach + 2 * self.attached + 3 * lifted + 5 * delivery - 0.01 * self.actions[:, :6].square().sum(-1)
        reward -= 10 * (height < 0.4)
        self.extras["log"] = {
            "attached_fraction": self.attached.float().mean(),
            "lifted_fraction": lifted.float().mean(),
            "delivered_fraction": (self.settled >= 10).float().mean(),
        }
        return reward * self.step_dt + 100 * (self.settled == 10)

    def _get_dones(self):
        p = self.batch.data.root_pos_w.torch
        at_goal = ((p - self.goal).norm(dim=-1) < 0.035) & (self.batch.data.root_lin_vel_w.torch.norm(dim=-1) < 0.04)
        good = at_goal & ~self.attached & self.ever_lifted
        self.settled = torch.where(good, self.settled + 1, torch.zeros_like(self.settled))
        failed = (p[:, 2] - self.scene.env_origins[:, 2] < 0.4) | ~torch.isfinite(p).all(dim=-1)
        return failed | (
            (self.settled >= 10) & self.cfg.terminate_on_success
        ), self.episode_length_buf >= self.max_episode_length - 1

    def _reset_idx(self, env_ids):
        if env_ids is None:
            env_ids = self.robot._ALL_INDICES
        for i in env_ids:
            self._release(int(i))
        super()._reset_idx(env_ids)
        q = torch.zeros(len(env_ids), 6, device=self.device)
        self.robot.write_joint_position_to_sim_index(position=q, env_ids=env_ids)
        self.robot.write_joint_velocity_to_sim_index(velocity=q, env_ids=env_ids)
        self.robot.actuators.target_command.set_position_index(value=q, env_ids=env_ids, full_data=False)
        self.batch.permanent_wrench_composer.reset(env_ids=env_ids)
        self.robot.permanent_wrench_composer.reset(env_ids=env_ids)
        self.targets[env_ids] = q
        self.actions[env_ids] = 0
        self.ever_lifted[env_ids] = False
        self.settled[env_ids] = 0
        pose = self.batch.data.default_root_pose.torch[env_ids].clone()
        pose[:, :3] += self.scene.env_origins[env_ids]
        pose[:, :2] += (torch.rand(len(env_ids), 2, device=self.device) * 2 - 1) * self.cfg.reset_noise
        self.batch.write_root_pose_to_sim_index(root_pose=pose, env_ids=env_ids)
        self.batch.write_root_velocity_to_sim_index(
            root_velocity=torch.zeros(len(env_ids), 6, device=self.device), env_ids=env_ids
        )
