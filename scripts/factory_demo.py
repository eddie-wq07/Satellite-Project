"""Reference joint planner for the reconstructed process (not a recovered ABB program)."""

import json

import numpy as np
import torch
from pxr import Usd, UsdPhysics
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from sim_bootstrap import ROOT


class Kinematics:
    def __init__(self):
        stage = Usd.Stage.Open(str(ROOT / "src/Satellite_Project/assets/data/environments/robot.usda"))
        self.frames = []
        self.low = []
        self.high = []
        for i in range(1, 7):
            j = UsdPhysics.RevoluteJoint(stage.GetPrimAtPath(f"/Robot/joints/joint_{i}"))
            frames = []
            for n in [0, 1]:
                pos = getattr(j, f"GetLocalPos{n}Attr")().Get()
                q = getattr(j, f"GetLocalRot{n}Attr")().Get()
                m = np.eye(4)
                m[:3, :3] = Rotation.from_quat([*q.GetImaginary(), q.GetReal()]).as_matrix()
                m[:3, 3] = pos
                frames.append(m)
            axis = {"X": 0, "Y": 1, "Z": 2}[j.GetAxisAttr().Get()]
            self.frames.append((*frames, axis))
            self.low.append(np.deg2rad(j.GetLowerLimitAttr().Get()) + 0.001)
            self.high.append(np.deg2rad(j.GetUpperLimitAttr().Get()) - 0.001)
        self.orientation = self.forward(np.zeros(6))[:3, :3]

    def forward(self, q):
        result = np.eye(4)
        for angle, (a, b, axis) in zip(q, self.frames, strict=True):
            rot = np.eye(4)
            v = np.zeros(3)
            v[axis] = angle
            rot[:3, :3] = Rotation.from_rotvec(v).as_matrix()
            result = result @ a @ rot @ np.linalg.inv(b)
        return result

    def solve(self, xyz, start=None):
        def error(q):
            m = self.forward(q)
            return np.r_[m[:3, 3] - xyz, 0.3 * Rotation.from_matrix(m[:3, :3] @ self.orientation.T).as_rotvec()]

        fit = least_squares(error, np.zeros(6) if start is None else start, bounds=(self.low, self.high), max_nfev=400)
        if np.linalg.norm(error(fit.x)) > 0.003:
            raise RuntimeError(f"Unreachable waypoint {xyz}: {error(fit.x)}")
        return fit.x


def run_demo(env, capture=False, frame_callback=None):
    base = env.unwrapped
    kin = Kinematics()
    base.cfg.reset_noise = 0
    base.cfg.episode_length_s = 40
    base.cfg.terminate_on_success = False
    env.reset()
    start = base.batch.data.root_pos_w.torch[0].cpu().numpy() - base.scene.env_origins[0].cpu().numpy()
    steps = [
        ("approach", [start[0], start[1], 0.94], -1, 90),
        ("contact", [start[0], start[1], 0.886], 1, 90),
        ("lift", [start[0], start[1], 1.08], 1, 100),
        ("transfer", [0.50, -0.70, 1.08], 1, 140),
        ("lower", [0.50, -0.70, 0.879], 1, 100),
        ("release", [0.50, -0.70, 0.879], -1, 15),
        ("retract", [0.50, -0.70, 1.08], -1, 100),
    ]
    reports = []
    previous = None
    for name, xyz, vacuum, count in steps:
        q = kin.solve(np.array(xyz), previous)
        previous = q
        for _ in range(count):
            action = torch.zeros(base.num_envs, 7, device=base.device)
            desired = torch.tensor(q, dtype=torch.float32, device=base.device)
            action[:, :6] = ((desired - base.targets) / base.cfg.joint_step).clamp(-0.4, 0.4)
            action[:, 6] = vacuum
            obs, r, done, trunc, info = env.step(action)
            if frame_callback is not None:
                frame_callback()
            if done.any() or trunc.any():
                print("EPISODE_END", name, info.get("log"), flush=True)
                raise RuntimeError("Unexpected reset before transfer was validated")
                break
        report = {
            "phase": name,
            "joints": base.robot.data.joint_pos.torch[0].tolist(),
            "tip": base.tip()[0].tolist(),
            "batch": base.batch.data.root_pos_w.torch[0].tolist(),
            "attached": bool(base.attached[0]),
            "settled": float(base.settled[0]),
        }
        if capture and name in ["contact", "lift", "transfer", "release"]:
            from recording import capture as screenshot

            screenshot(base.sim, "physics-" + name)
        reports.append(report)
        print("DEMO", json.dumps(report), flush=True)
        if name in ["contact", "lift", "transfer"] and not report["attached"]:
            raise RuntimeError(f"Failed attachment at {name}")
        if name == "lift" and report["batch"][2] < 0.82:
            raise RuntimeError("Batch did not physically lift")
    assert not base.attached.any()
    assert ((base.batch.data.root_pos_w.torch - base.goal).norm(dim=-1) < 0.035).all()
    assert (base.settled >= 10).all()
    print("TRANSFER_VALIDATED", base.num_envs, flush=True)
    (ROOT / "outputs/demo.json").write_text(json.dumps(reports, indent=2) + "\n")
