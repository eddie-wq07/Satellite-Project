"""Offline scene integrity, source preservation and robot kinematics checks."""

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from pxr import Usd, UsdGeom, UsdPhysics, UsdUtils

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "src/Satellite_Project/assets/data"
sys.path.insert(0, str(ROOT / "scripts"))
from factory_demo import Kinematics  # noqa: E402


def test_downloaded_sources_unchanged():
    folder = DATA / "robots/abb_irb1600"
    manifest = json.loads((folder / "source.json").read_text())
    for item in manifest["files"]:
        assert hashlib.sha256((folder / item["path"]).read_bytes()).hexdigest() == item["sha256"]


def test_scene_composition_and_units():
    for name in ["factory.usda", "factory.usdc", "robot.usda", "batch.usda", "static.usda"]:
        path = DATA / "environments" / name
        stage = Usd.Stage.Open(str(path))
        assert stage.GetDefaultPrim()
        assert not stage.GetCompositionErrors()
        assert UsdGeom.GetStageMetersPerUnit(stage) == 1
        assert UsdGeom.GetStageUpAxis(stage) == "Z"
        _, _, unresolved = UsdUtils.ComputeAllDependencies(str(path))
        assert set(unresolved) <= {"OmniPBR.mdl"}  # Built into the Isaac Sim runtime.


def test_articulated_robots_and_dynamic_batch():
    stage = Usd.Stage.Open(str(DATA / "environments/factory.usda"))
    for name in ["Robot", "RobotRear"]:
        joints = [p for p in Usd.PrimRange(stage.GetPrimAtPath("/World/" + name)) if p.IsA(UsdPhysics.RevoluteJoint)]
        assert len(joints) == 6
        for p in joints:
            joint = UsdPhysics.RevoluteJoint(p)
            assert joint.GetLowerLimitAttr().Get() < joint.GetUpperLimitAttr().Get()
            assert joint.GetBody0Rel().GetTargets() and joint.GetBody1Rel().GetTargets()
            assert UsdPhysics.DriveAPI(p, "angular").GetMaxForceAttr().Get() > 0
    assert stage.GetPrimAtPath("/World/Batch").HasAPI(UsdPhysics.RigidBodyAPI)
    assert UsdPhysics.CollisionAPI(stage.GetPrimAtPath("/World/Batch/Collision"))


def test_waypoints_are_reachable_and_orientation_preserved():
    kin = Kinematics()
    for target in [[0.717, 0, 0.876], [0.717, 0, 1.08], [0.5, -0.7, 1.08], [0.5, -0.7, 0.861]]:
        q = kin.solve(np.array(target))
        pose = kin.forward(q)
        assert np.linalg.norm(pose[:3, 3] - target) < 0.001
        assert np.linalg.norm(pose[:3, :3] - kin.orientation) < 0.01
