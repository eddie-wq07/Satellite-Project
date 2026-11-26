# Satellite Project — ABB photovoltaic handling cell

A saved OpenUSD factory scene and a working Isaac Lab batch-transfer task, reconstructed from
[vision.md](vision.md). Two articulated ABB arms, distributed tooling, solar-cell supply stacks,
orange transfer surfaces, transparent guards, an array section, controls, lights and four cameras
are composed in metre-scale, Z-up USD.

**Open in Isaac Sim:** [`factory.usdc`](src/Satellite_Project/assets/data/environments/factory.usdc),
a single-file scene with geometry and physics included. The editable composition is
[`factory.usda`](src/Satellite_Project/assets/data/environments/factory.usda); keep its adjacent
`robots/` and `environments/` folders together. Isaac Sim supplies the built-in `OmniPBR.mdl` material.

![Factory overview](recordings/11-26-2026/11:04am_factory-overview.png)

## Run

Run from the repository root with Python 3.12 and an Isaac Sim 6.2 / Isaac Lab 3.0
environment containing RSL-RL, SciPy, and ImageIO/FFmpeg. The commands below use
`~/env_isaaclab/bin/python`; substitute your environment’s Python path if different.
The runner adds `src/` to the import path automatically.

```bash
# Full saved factory; use its Overview, Pickup, Cells or Array cameras.
~/env_isaaclab/bin/python scripts/preview.py

# Interactive physical cell: six joint sliders, vacuum switch and reset button.
~/env_isaaclab/bin/python scripts/run_factory.py --mode drive

# Validated scripted approach → contact → lift → transfer → release → retract.
~/env_isaaclab/bin/python scripts/run_factory.py --mode demo

# Record live physics milestones without opening a desktop window.
~/env_isaaclab/bin/python scripts/run_factory.py --mode demo --capture --record-mp4 recordings/demo.mp4 \
  --visualizer kit --kit_args=--no-window

# Parallel PPO training; this task has seven actions and 31 state observations.
~/env_isaaclab/bin/python scripts/run_factory.py --mode train --num-envs 8 --iterations 500

# Reload the final checkpoint from the 500-iteration run above.
~/env_isaaclab/bin/python scripts/run_factory.py --mode play --num-envs 8 \
  --checkpoint outputs/training/model_499.pt
```

## Code structure and control flow

The only registered task is `SatelliteProject-Satellite-Arm-Direct`. Its implementation lives in
`src/Satellite_Project/tasks/satellite_direct/config/Arm/`:

- `env_cfg.py`: robot, fixtures, simulation settings, seven actions and 31 observations.
- `env.py`: joint/vacuum actions, physical attachment, observations, rewards, resets and completion checks.
- `agents/rsl_rl_ppo_cfg.py`: the supported RSL-RL PPO training configuration.

`run_factory.py` creates this same environment for every mode. In `demo`, `factory_demo.py`
computes joint targets from scripted waypoints; in `drive`, manual controls supply actions;
in `train` and `play`, PPO supplies actions. Each controller uses `env.step()` and the same
physics. Eight parallel environments are independent single-agent copies.

`scripts/build_factory.py` generates the scene assets, `preview.py` displays the full scene,
`validate_stage.py` checks both native robot articulations, and `list_envs.py` lists this project's
task without loading unrelated installed plugins. `recording.py` and `sim_bootstrap.py` are
shared helpers. Unsupported task and agent templates have been removed.

The interactive/task scene uses the same saved fixtures and robot. Its rear arm is a static
visual reference, and room walls are omitted for parallel environments. Both arms are articulated
in the full `factory.usda`. Joint targets can also be edited through Isaac Sim's articulation tools;
the vacuum logic runs in the task, rather than being embedded Python in the USD.

## What is verified

- Isaac Sim rendering of the full composed scene and inspection cameras.
- Physical joint motion and stable holding, collision support for the cell batch, contact-gated pickup,
  lift, transfer, release, and settled delivery checks.
- Parallel Isaac Lab simulation, PPO optimization, checkpoint creation and reload.
- Offline asset composition, six-joint structure, reachable waypoints, and unmodified upstream file hashes.

The short PPO run is an **execution test**, not a successful learned manipulation policy. The completed
handling demonstration uses inverse kinematics and joint drives. Training checkpoints and diagnostics
are under `outputs/`; dated screenshots and the progress history are in [log.md](log.md).

## Reconstruction limits

The robot is the real **ABB IRB1600 X-120 USD** from [Workr's robot library](https://github.com/work-r-labs/robots),
revision `ab6aa489855256de07ba46c7b45887fdbc42b607`. Its geometry closely resembles the supplied footage;
**the exact factory robot variant cannot be confirmed** from the available frames. It is not represented
as a verified exact copy. See [asset provenance](src/Satellite_Project/assets/data/robots/abb_irb1600/source.json)
and the included upstream [license](src/Satellite_Project/assets/data/robots/abb_irb1600/LICENSE).

Dimensions, placement, mass, tooling, drive tuning, vacuum behavior and trajectory are simulation
assumptions. Eight cells are represented as one rigid batch; the twelve-layer supply stacks are static.
Vacuum is a compliant, force-limited attachment with equal and opposite wrist reaction, a 4 mm approach
gate, and release/slip logic. Individual wafer flexure, fracture, leakage, conveyor transport and downstream
manufacturing processes are not simulated. The larger array section is separate from the transferred batch,
in accordance with the montage's uncertain continuity; its inspection stand is an inferred fixture.

## Rebuild and check

```bash
~/env_isaaclab/bin/python scripts/build_factory.py
~/env_isaaclab/bin/python scripts/preview.py --capture
~/env_isaaclab/bin/python scripts/validate_stage.py
~/env_isaaclab/bin/python scripts/run_factory.py --mode smoke --num-envs 8
PYTHONPATH=src ~/env_isaaclab/bin/python -m pytest -q
```

The builder changes project composition layers, never the pinned vendor USDs. The uv source paths
in `pyproject.toml` point to the local Isaac Lab checkout at `../../../../IsaacLab`; update those
paths before using uv on another machine. The commands above use an existing simulator environment.

## Latest validation

[November 26 recording](recordings/11-26-2026/full-demo.mp4): 21.17 seconds at 30 FPS.
Eight environments completed the scripted transfer. Scene rendering, both articulations, manual
controls, PPO training/checkpoint reload, and the asset tests were checked. See the
[validation manifest](recordings/11-26-2026/validation.json) and [progress log](log.md).
Checkpoints and runtime logs under `outputs/` are generated locally and are not included in Git;
run training to produce a checkpoint before using `--mode play`.
