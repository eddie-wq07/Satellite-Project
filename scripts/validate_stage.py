"""Validate both native articulations in the single-file factory, independently of Isaac Lab."""

import sim_bootstrap
from isaacsim import SimulationApp

app = SimulationApp({"headless": True, "multi_gpu": False})
import numpy as np
import omni.usd
from isaacsim.core.api import World
from isaacsim.core.prims import SingleArticulation, SingleRigidPrim
from isaacsim.core.utils.types import ArticulationAction

path = sim_bootstrap.ROOT / "src/Satellite_Project/assets/data/environments/factory.usdc"
omni.usd.get_context().open_stage(str(path))
world = World(physics_dt=1 / 120, rendering_dt=1 / 30, stage_units_in_meters=1)
robots = [world.scene.add(SingleArticulation(prim_path="/World/" + name, name=name)) for name in ["Robot", "RobotRear"]]
batch = world.scene.add(SingleRigidPrim(prim_path="/World/Batch", name="batch"))
world.reset()
starts = [robot.get_world_pose()[0].copy() for robot in robots]
for robot in robots:
    assert robot.num_dof == 6
    robot.apply_action(ArticulationAction(joint_positions=np.array([0.06, 0, 0, 0, 0, 0])))
for _ in range(240):
    world.step(render=False)
for robot, start in zip(robots, starts, strict=True):
    position = robot.get_world_pose()[0]
    joints = robot.get_joint_positions()
    assert np.linalg.norm(position - start) < 0.001, (robot.name, start, position)
    assert abs(joints[0] - 0.06) < 0.015, (robot.name, joints)
    assert np.isfinite(joints).all()
    print("STANDALONE_ROBOT_VALIDATED", robot.name, position.tolist(), joints.tolist(), flush=True)
assert 0.71 < float(batch.get_world_pose()[0][2]) < 0.73
print("STANDALONE_FACTORY_VALIDATED", str(path), flush=True)
world.clear()
app.close()
