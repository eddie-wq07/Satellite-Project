"""Drive, validate or train the factory task with Isaac Lab's existing runtime."""

import argparse

import sim_bootstrap

from isaaclab.app import add_launcher_args, launch_simulation

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--mode", choices=["smoke", "demo", "train", "play", "drive"], default="smoke")
parser.add_argument("--num-envs", type=int, default=1)
parser.add_argument("--iterations", type=int, default=10)
parser.add_argument("--checkpoint")
parser.add_argument("--capture", action="store_true")
parser.add_argument("--record-mp4", help="Save the demo as a 30 FPS MP4 at this path.")
parser.add_argument(
    "--steps", type=int, default=0, help="Smoke-test manual controls for N steps; zero keeps the window open."
)
add_launcher_args(parser)
parser.set_defaults(device="cpu")
args = parser.parse_args()
if args.mode == "drive" and not args.visualizer:
    args.visualizer = "kit"
if args.record_mp4:
    if args.mode != "demo":
        parser.error("--record-mp4 requires --mode demo")
    args.visualizer = "kit"
if args.mode == "play" and not args.checkpoint:
    parser.error("--mode play requires --checkpoint")
import gymnasium as gym
import torch

from Satellite_Project.tasks.satellite_direct.config.Arm.env_cfg import SatelliteEnvCfg

cfg = SatelliteEnvCfg()
cfg.seed = 7
cfg.scene.num_envs = args.num_envs
cfg.sim.device = args.device
with launch_simulation(cfg, args):
    env = gym.make("SatelliteProject-Satellite-Arm-Direct", cfg=cfg)
    base = env.unwrapped
    obs, _ = env.reset()
    if args.mode == "smoke":
        for i in range(120):
            action = torch.zeros(args.num_envs, 7, device=base.device)
            action[:, 6] = -1
            if 30 < i < 60:
                action[:, :6] = torch.tensor([0.2, 0.02, -0.02, 0.02, 0.02, 0.02], device=base.device)
            obs, reward, terminated, truncated, info = env.step(action)
            assert torch.isfinite(obs["policy"]).all() and torch.isfinite(reward).all()
            assert not terminated.any() and not truncated.any()
        assert (base.robot.data.joint_pos.torch - base.targets).abs().max() < 0.025
        assert base.robot.data.joint_vel.torch.abs().max() < 0.05
        action[:, 6] = 1
        env.step(action)
        assert not base.attached.any(), "Suction must not attach from a distance"
        print("TARGET", base.targets, flush=True)
        print(
            "VELOCITIES",
            base.robot.data.joint_vel.torch,
            base.robot.data.body_lin_vel_w.torch[:, base.flange],
            base.robot.data.body_ang_vel_w.torch[:, base.flange],
            flush=True,
        )
        print(
            "SMOKE",
            base.robot.joint_names,
            base.robot.data.joint_pos.torch,
            base.batch.data.root_pos_w.torch,
            obs["policy"].shape,
            flush=True,
        )
    elif args.mode == "drive":
        from drive_factory import drive

        drive(env, steps=args.steps)
    elif args.mode in ["train", "play"]:
        import importlib.metadata

        from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper, create_rsl_rl_runner, handle_deprecated_rsl_rl_cfg

        from Satellite_Project.tasks.satellite_direct.config.Arm.agents.rsl_rl_ppo_cfg import PPORunnerCfg

        agent = PPORunnerCfg()
        agent.device = args.device
        agent.seed = cfg.seed
        agent.max_iterations = args.iterations
        agent = handle_deprecated_rsl_rl_cfg(agent, importlib.metadata.version("rsl-rl-lib"))
        wrapped = RslRlVecEnvWrapper(env, clip_actions=1.0)
        runner = create_rsl_rl_runner(wrapped, agent, log_dir=str(sim_bootstrap.ROOT / "outputs/training"))
        if args.mode == "train":
            runner.learn(num_learning_iterations=args.iterations, init_at_random_ep_len=True)
        else:
            runner.load(args.checkpoint)
            policy = runner.get_inference_policy(device=args.device)
            obs = wrapped.get_observations()
            for _ in range(360):
                with torch.inference_mode():
                    obs, reward, dones, info = wrapped.step(policy(obs))
                    assert torch.isfinite(reward).all()
            print("CHECKPOINT_RELOAD_VALIDATED", args.checkpoint, flush=True)
    else:
        from factory_demo import run_demo

        if args.record_mp4:
            from recording import VideoRecorder

            with VideoRecorder(base.sim, args.record_mp4) as video:
                run_demo(env, capture=args.capture, frame_callback=video.capture_frame)
        else:
            run_demo(env, capture=args.capture)
    env.close()
