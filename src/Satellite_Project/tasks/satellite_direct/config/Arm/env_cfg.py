"""ABB photovoltaic batch handling; metres, seconds, radians and XYZW quaternions."""

from __future__ import annotations

import isaaclab.sim as sim
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.assets import ArticulationCfg, AssetBaseCfg, RigidObjectCfg
from isaaclab.envs import DirectRLEnvCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.utils import configclass
from isaaclab_physx.physics import PhysxCfg

from Satellite_Project.assets import SATELLITE_PROJECT_ASSETS_DIR

DATA = SATELLITE_PROJECT_ASSETS_DIR / "environments"


@configclass
class SatelliteSceneCfg(InteractiveSceneCfg):
    robot: ArticulationCfg = ArticulationCfg(
        prim_path="{ENV_REGEX_NS}/Robot",
        spawn=sim.UsdFileCfg(usd_path=str(DATA / "robot.usda")),
        init_state=ArticulationCfg.InitialStateCfg(joint_pos={".*": 0.0}),
        actuators={"arm": ImplicitActuatorCfg(joint_names_expr=["joint_.*"], stiffness=None, damping=None)},
    )
    batch: RigidObjectCfg = RigidObjectCfg(
        prim_path="{ENV_REGEX_NS}/Batch",
        spawn=sim.UsdFileCfg(usd_path=str(DATA / "batch.usda")),
        init_state=RigidObjectCfg.InitialStateCfg(pos=(0.717, 0, 0.7228)),
    )
    factory: AssetBaseCfg = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/Factory", spawn=sim.UsdFileCfg(usd_path=str(DATA / "static.usda"))
    )
    floor: AssetBaseCfg = AssetBaseCfg(
        prim_path="/World/Ground",
        spawn=sim.CuboidCfg(size=(100, 100, 0.1), collision_props=sim.CollisionPropertiesCfg()),
        init_state=AssetBaseCfg.InitialStateCfg(pos=(0, 0, -0.05)),
    )
    light: AssetBaseCfg = AssetBaseCfg(prim_path="/World/Light", spawn=sim.DomeLightCfg(intensity=900))


@configclass
class SatelliteEnvCfg(DirectRLEnvCfg):
    decimation: int = 4
    episode_length_s: float = 12
    action_space: int = 7
    observation_space: int = 31
    state_space: int = 0
    sim: sim.SimulationCfg = sim.SimulationCfg(
        device="cpu", dt=1 / 120, render_interval=4, physics=PhysxCfg(solver_type=1, enable_stabilization=False)
    )
    scene: SatelliteSceneCfg = SatelliteSceneCfg(num_envs=8, env_spacing=5, replicate_physics=False)
    joint_step: float = 0.025
    reset_noise: float = 0.008
    terminate_on_success: bool = True
    # A compliant force-limited attachment is the assumed vacuum model, with a finite break force.
    suction_distance: float = 0.004
    suction_force_limit: float = 40
