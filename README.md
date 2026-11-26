# Starlink Manufacturing Project

An Isaac Sim reconstruction of the robot-assisted solar-cell handling shown in Starlink factory footage. An ABB arm picks up a batch of cells, lifts it, transfers it to a table, and releases it using simulated vacuum forces.

**The working demo is scripted.** The project also includes a trainable PPO task, but a reliable learned handling policy has not yet been demonstrated.

[![Watch the 6-second side-by-side comparison](recordings/11-26-2026/comparison-preview.jpg)](recordings/11-26-2026/starlink-side-by-side.mp4)

**[Watch the 6-second comparison](recordings/11-26-2026/starlink-side-by-side.mp4):** source footage on the left, simulation on the right. The SpaceX clip runs continuously at its original speed from 1:28 to 1:34. The full simulation runs at a constant 3.53x speed to match. [Original footage](https://www.youtube.com/watch?v=1dQK2CWAyxE&t=88s).

## Start here

- **Watch the simulation:** [Full handling cycle, 21 seconds](recordings/11-26-2026/full-demo.mp4).
- **Explore the scene:** Open [factory.usdc](src/Satellite_Project/assets/data/environments/factory.usdc) in Isaac Sim. Use its Overview, Pickup, Cells, or Array camera.
- **Understand the implementation:** [vision.md](vision.md#implemented-program-flow) includes the source analysis, file flowcharts, asset dependencies, and training loop.

## Run the demo

Use Python 3.12 with Isaac Sim 6.2, Isaac Lab 3.0, RSL-RL, SciPy, and ImageIO/FFmpeg installed. Run commands from the repository root. Replace `~/env_isaaclab/bin/python` with your environment's Python path if needed.

```bash
~/env_isaaclab/bin/python scripts/run_factory.py --mode demo
```

The arm runs through approach, contact, lift, transfer, release, and retraction. The program checks that the batch reaches the target and settles, then exits.

| What you want to do | Command |
|---|---|
| View the complete factory | `~/env_isaaclab/bin/python scripts/preview.py` |
| Control the arm with sliders | `~/env_isaaclab/bin/python scripts/run_factory.py --mode drive` |
| Test eight independent cells | `~/env_isaaclab/bin/python scripts/run_factory.py --mode demo --num-envs 8` |
| List the supported task | `~/env_isaaclab/bin/python scripts/list_envs.py` |

To record a video and milestone screenshots without opening a window:

```bash
~/env_isaaclab/bin/python scripts/run_factory.py --mode demo --capture \
  --record-mp4 recordings/demo.mp4 --visualizer kit --kit_args=--no-window
```

Use a new output filename for each video. Screenshots are saved in dated folders under `recordings/`.

## Train and run a policy

PPO uses the same environment and physics as the scripted demo. It receives 31 observations and chooses seven actions: six joint increments and one vacuum command.

```bash
# Train across eight independent environments
~/env_isaaclab/bin/python scripts/run_factory.py --mode train --num-envs 8 --iterations 500

# Run the final checkpoint for 360 steps
~/env_isaaclab/bin/python scripts/run_factory.py --mode play --num-envs 8 \
  --checkpoint outputs/training/model_499.pt
```

Training writes metrics and checkpoints to `outputs/training/`. Use `--log-dir` to choose another directory. Checkpoints are generated locally and are not included in Git. A completed training run does not by itself prove successful manipulation.

## Where things live

| Location | Purpose |
|---|---|
| `scripts/run_factory.py` | Starts the environment and selects demo, manual control, training, playback, or smoke testing. |
| `scripts/factory_demo.py` | Scripted waypoints and inverse kinematics for the demonstrated transfer. |
| `src/Satellite_Project/tasks/satellite_direct/config/Arm/` | The single supported task: scene configuration, actions, observations, rewards, resets, and PPO settings. |
| `src/Satellite_Project/assets/data/environments/` | Full factory scene and the robot, batch, and fixture layers used by the task. |
| `src/Satellite_Project/assets/data/robots/` | Original ABB model, source information, and license. |
| `recordings/` | Videos, screenshots, and validation evidence. |
| [vision.md](vision.md) | Footage analysis and Mermaid diagrams of the program and training flow. |
| [log.md](log.md) | Development history and validation results. |

The registered task is `SatelliteProject-Satellite-Arm-Direct`. Demo, manual control, and PPO all send actions through its `env.step()` method. Parallel environments are independent single-agent copies.

## What works and what is simplified

**Verified:** scripted delivery in eight environments, both robot articulations in the full scene, manual controls, scene rendering, PPO training, checkpoint reload, and five automated tests. See the [November 26 validation](recordings/11-26-2026/validation.json) and [latest checks](log.md).

**Simplified:** the task controls one arm; the rear arm is a static visual reference. Eight cells move as one rigid batch, supply stacks are static, and vacuum uses a compliant force-limited attachment. Cell flexure, fracture, leakage, moving conveyors, and downstream manufacturing are not simulated.

The reconstruction is based on edited footage, not a recovered factory program. Dimensions, tooling, motion, and physical settings are assumptions. The model is an [ABB IRB1600 X-120 from Workr](src/Satellite_Project/assets/data/robots/abb_irb1600/SOURCE.md); the exact robot variant in the footage is unconfirmed. The larger array section is a separate visual fixture. Original asset attribution and [license](src/Satellite_Project/assets/data/robots/abb_irb1600/LICENSE) are retained.

## Rebuild and verify

```bash
~/env_isaaclab/bin/python scripts/build_factory.py
~/env_isaaclab/bin/python scripts/validate_stage.py
~/env_isaaclab/bin/python scripts/run_factory.py --mode smoke --num-envs 8
PYTHONPATH=src ~/env_isaaclab/bin/python -m pytest -q
```

The builder regenerates project scene layers without modifying the original vendor assets. Use `factory.usdc` for a single-file scene or `factory.usda` for editable composition, keeping the adjacent `robots/` and `environments/` folders together.

For a different machine, update the local Isaac Lab source paths in `pyproject.toml` before using uv. They currently point to `../../../../IsaacLab`. A fresh installation on a separate machine has not yet been tested.
