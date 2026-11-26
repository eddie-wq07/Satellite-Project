# Factory reconstruction log

All times use America/Vancouver. Milestones follow S1-Project's
`recordings/MM-DD-YYYY/h:mmam_description.png` convention; diagnostic captures go under
`recordings/misc/MM-DD-YYYY/`. Source footage remains in `assets/starlink-robot/`.

## 11-22-2026 — 11:13pm — Scope and source inspection

- Read `vision.md` and inspected the supplied factory stills; inspected S1 scene authoring and Mars/S1 recording conventions.
- Existing project is an Isaac Lab scaffold with no robot or factory USD and unimplemented environments.
- Scope: persist an offline-loadable composed USD with two articulated ABB arms, broad contact tooling, stacked cells, orange transfer surfaces, guard panels, larger array section, lighting, cameras and collision geometry. Add joint driving, a repeatable handling demonstration, and a trainable task using the existing package layout.
- Evidence boundary: the brief explicitly leaves robot model, dimensions, gripping physics and continuous process unknown. Model identification remains a visual hypothesis; geometry and process timings will be documented as reconstruction choices.
- Checked NVIDIA manipulator catalog and Workr's public USD library. Workr provides an IRB1600 X-120 whose flat upper-arm plate and circular wrist match the visible silhouette more closely than the IRB2600 product image. Exact variant cannot be established from these stills.
- Runtime available: `~/env_isaaclab/bin/python`, Isaac Sim and USD 26.08; RTX 5080. Will reuse this environment, as S1 does.

## 11-22-2026 11:21PM — Factory and first physics validation

- Built locally referenced factory, robot, batch and static training USD layers. Four authored cameras render in Isaac Sim.
- Corrected an initial supply-table overlap with the ABB shoulder housing; a six-axis drive smoke test now holds its commanded 0.145-radian base rotation with near-zero resting velocities.
- Converted project drive gains from radian units to USD angular-degree units and replaced the bare-flange inertia with an estimated tool-loaded inertia. Source robot USD files remain untouched.
- Added a 31-observation, 7-action Isaac Lab task: six joint increments and suction. Pickup is contact-gated; suction applies bounded forces and torques with opposite reactions to the wrist. Cell batch stays a dynamic rigid body.
- Initial rigid-joint attachment experiment failed; replaced with a compliant suction approximation. End-to-end transfer validation is still in progress.
- Initial exterior camera views were obstructed by guarding; moved inspection cameras inside the guard boundary.

### 11-22-2026 11:23PM — physics-contact

![physics-contact](recordings/11-22-2026/11:23pm_physics-contact.png)

### 11-22-2026 11:23PM — physics-lift

![physics-lift](recordings/11-22-2026/11:23pm_physics-lift.png)

### 11-22-2026 11:23PM — physics-transfer

![physics-transfer](recordings/11-22-2026/11:23pm_physics-transfer.png)

### 11-22-2026 11:23PM — physics-release

![physics-release](recordings/11-22-2026/11:23pm_physics-release.png)

### 11-22-2026 11:24PM — physics-contact

![physics-contact](recordings/11-22-2026/11:24pm_physics-contact.png)

### 11-22-2026 11:24PM — physics-lift

![physics-lift](recordings/11-22-2026/11:24pm_physics-lift.png)

### 11-22-2026 11:24PM — physics-transfer

![physics-transfer](recordings/11-22-2026/11:24pm_physics-transfer.png)

### 11-22-2026 11:24PM — physics-release

![physics-release](recordings/11-22-2026/11:24pm_physics-release.png)

## 11-22-2026 11:29PM — Delivery and final validation

- Delivered a 4 MB single-file `src/Satellite_Project/assets/data/environments/factory.usdc` and its editable `factory.usda` composition. Both were opened in Isaac Sim; all four final camera images were inspected.
- Independent native Isaac Sim test drove **both** ABB articulations to a 0.06-radian base target. Fixed bases stayed at their intended locations; the batch remained supported. Moved the rear control cabinet clear of the second arm after this test exposed an overlap.
- All **eight parallel environments** completed contact, lift, transfer, release and retraction. The released batch settled approximately 3.4 mm from the target center in the reported environment. Vacuum stayed off after release. Runtime evidence: `outputs/demo-parallel.log`.
- Manual UI tested for 30 steps, including a slider-model command to 0.1 radians and verification of the simulated joint response: `outputs/drive.log`.
- PPO completed 12 iterations on eight environments; checkpoint `outputs/training/model_11.pt` reloaded and ran for 360 steps. This is pipeline validation, **not** evidence of a learned successful policy.
- Final asset/registration/kinematics tests: **5 passed**. Source SHA-256 tests pass. All local Isaac Lab paths resolve. The one non-file dependency, `OmniPBR.mdl`, is bundled with Isaac Sim.
- Added README commands, source provenance and rebuild/validation scripts. Fixed the inherited test's overlong entry-point line for the repository lint check.
- Screenshot file writes now wait for the renderer's asynchronous writer before shutdown; all four final PNGs exist. Earlier exploratory captures are retained as progress evidence.
- Evidence caveat: supplied Figure 4's JPEG shows the later parallel-element machine, despite its array-section caption. The separate tilted section follows the written brief; the inspection stand, dimensions, eight-cell batch, static belts and physical tuning are reconstruction assumptions. The exact ABB model and real production cycle remain unverified.
- Machine-readable validation manifest: [validation.json](recordings/11-22-2026/validation.json).

### Final factory overview

![Final composed factory](recordings/11-22-2026/11:29pm_factory-overview.png)

### Final pickup station

![Final tool and cell stacks](recordings/11-22-2026/11:29pm_factory-pickup.png)

### Final array-section view

![Separate array section](recordings/11-22-2026/11:29pm_factory-array.png)

### 11-26-2026 11:03AM — physics-contact

![physics-contact](recordings/11-26-2026/11:03am_physics-contact.png)

### 11-26-2026 11:05AM — physics-contact

![physics-contact](recordings/11-26-2026/11:05am_physics-contact.png)

### 11-26-2026 11:06AM — physics-lift

![physics-lift](recordings/11-26-2026/11:06am_physics-lift.png)

### 11-26-2026 11:06AM — physics-transfer

![physics-transfer](recordings/11-26-2026/11:06am_physics-transfer.png)

### 11-26-2026 11:07AM — physics-release

![physics-release](recordings/11-26-2026/11:07am_physics-release.png)

## 11-26-2026 — Full runtime check and recording

- Recorded [full handling cycle](recordings/11-26-2026/full-demo.mp4): 635 frames, 30 FPS, 1600×1000, 21.17 seconds. Eight parallel environments passed approach, contact, lift, transfer, lower, release and retract; the recorded camera shows one cell. Final batch offset in the reported environment was approximately 3.4 mm from target.
- Rebuilt assets and captured all four authored cameras. Both native ABB articulations passed standalone physics validation. Eight-environment smoke checks, 60-step manual-control check, 12 PPO iterations and a 360-step checkpoint reload passed. Five existing tests passed; lint passed for modified scripts.
- Training artifacts are isolated in `outputs/11-26-2026/training/`; previous checkpoints are retained. Added `--log-dir` to support this.
- Fixed video capture to wait for asynchronous image writes and restore 1600×1000 resolution after Kit startup. Initial incomplete capture and failure log are retained under `outputs/11-26-2026/partial-demo.*`.
- `scripts/list_envs.py` failed because the shared Isaac Lab installation tries to import the missing external `mars_locomotion` plugin. Direct import of this project's three registrations succeeded. No shared installation was changed.
- Scope remains a scripted single-active-arm batch transfer. The rear arm is static in the task scene; both arms are articulated in the full scene. PPO training is an execution check, not a learned successful policy. Manager-based and MARL implementations remain scaffold placeholders.
- Scripts/modes were exercised sequentially and exited after their checks; no simulator was left running. Helper modules were exercised through their callers.
- [Validation manifest](recordings/11-26-2026/validation.json); detailed logs: `outputs/11-26-2026/`.

## 11-26-2026 — Supervisor handoff cleanup

- Removed the unimplemented `satellite/` and `satellite_marl_direct/` task trees. The only registered task is now `SatelliteProject-Satellite-Arm-Direct`.
- Removed unused direct-task AMP, distillation, RL-Games, SKRL and SB3 configurations and their registry entries. Retained RSL-RL PPO; trimmed unused package extras and declared SciPy and ImageIO/FFmpeg dependencies.
- Replaced automatic package scanning with explicit registration. Reworked `list_envs.py` to list project tasks without importing unrelated installed plugins; the earlier missing `mars_locomotion` failure no longer affects this script.
- Updated the registration test, README control-flow explanation, runtime prerequisites, recording command and VS Code launch templates. Removed an unreachable statement and obsolete asset placeholder. Historical evidence and vendor assets remain intact.
- Validation after cleanup: five tests passed; lint, formatting, TOML/JSON parsing and diff whitespace checks passed. All eight environments completed the scripted demo; two PPO iterations produced `outputs/11-26-2026/cleanup/training/model_1.pt`, which reloaded and ran for 360 steps. Runtime logs are in `outputs/11-26-2026/cleanup/`.
- Validation used the existing Isaac environment; a fresh installation on a separate machine has not been tested. Local uv source paths must be adjusted for another checkout location, as documented in README.
