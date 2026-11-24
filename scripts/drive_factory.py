"""Interactive joint and vacuum controls for the live physical task."""

import torch


def drive(env, steps=0):
    import omni.ui as ui

    base = env.unwrapped
    base.cfg.terminate_on_success = False
    base.cfg.episode_length_s = 3600
    window = ui.Window("ABB cell — joint drive", width=360, height=370)
    models = []
    with window.frame, ui.VStack(spacing=8):
        ui.Label("Joint targets (radians). Gently approach the stack before suction.", word_wrap=True)
        for i in range(6):
            with ui.HStack():
                ui.Label(f"Axis {i + 1}", width=65)
                slider = ui.FloatSlider(min=float(base.limits[i, 0]), max=float(base.limits[i, 1]))
                slider.model.set_value(0)
                models.append(slider.model)
        with ui.HStack():
            ui.Label("Vacuum enabled", width=150)
            vacuum = ui.CheckBox().model
        status = ui.Label("Ready", word_wrap=True)

        def reset():
            env.reset()
            for model in models:
                model.set_value(0)
            vacuum.set_value(False)

        ui.Button("Reset cell", clicked_fn=reset)
    # Initialize the task view without creating a recording.
    from recording import setup_view

    setup_view(base.sim)
    if steps:
        models[0].set_value(0.1)
    count = 0
    while base.sim.is_running() and (steps == 0 or count < steps):
        if not base.sim.is_playing():
            base.sim.render()
            continue
        target = torch.tensor([m.get_value_as_float() for m in models], device=base.device)
        action = torch.zeros(base.num_envs, 7, device=base.device)
        action[:, :6] = ((target - base.targets) / base.cfg.joint_step).clamp(-0.3, 0.3)
        action[:, 6] = 1 if vacuum.get_value_as_bool() else -1
        env.step(action)
        count += 1
        status.text = f"Attached: {bool(base.attached[0])} | Delivered: {bool(base.settled[0] >= 10)}"

    if steps:
        assert abs(float(base.robot.data.joint_pos.torch[0, 0]) - 0.1) < 0.025
        print("MANUAL_CONTROLS_VALIDATED", count, flush=True)
