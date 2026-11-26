"""Dated factory milestone captures from the live Isaac viewport."""

import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

from sim_bootstrap import ROOT


class VideoRecorder:
    """Encode live viewport frames at the demo's 30 Hz control rate."""

    def __init__(self, sim, destination):
        import tempfile
        from pathlib import Path

        import imageio.v2 as imageio

        self.sim = sim
        self.viewport = setup_view(sim)
        self.destination = Path(destination).resolve()
        self.destination.parent.mkdir(parents=True, exist_ok=True)
        if self.destination.exists():
            raise FileExistsError(self.destination)
        self.temp = tempfile.TemporaryDirectory(prefix="satellite-video-")
        self.frame_path = Path(self.temp.name) / "frame.png"
        self.writer = imageio.get_writer(
            str(self.destination),
            fps=30,
            codec="libx264",
            quality=8,
            macro_block_size=2,
            ffmpeg_params=["-movflags", "+faststart"],
        )
        self.frames = 0
        for _ in range(25):
            sim.render()
        # Kit may apply its startup window size during the warmup renders.
        self.viewport.resolution = (1600, 1000)
        for _ in range(2):
            sim.render()

    def capture_frame(self):
        import imageio.v2 as imageio
        from omni.kit.viewport.utility import capture_viewport_to_file

        async def save():
            await capture_viewport_to_file(self.viewport, str(self.frame_path)).wait_for_result()

        pending = asyncio.ensure_future(save())
        while not pending.done():
            self.sim.render()
        pending.result()
        import omni.kit.renderer_capture

        omni.kit.renderer_capture.acquire_renderer_capture_interface().wait_async_capture()
        self.writer.append_data(imageio.imread(self.frame_path)[..., :3])
        self.frames += 1
        if self.frames % 100 == 0:
            print(f"VIDEO_FRAMES {self.frames}", flush=True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.writer.close()
        self.temp.cleanup()
        print(f"VIDEO_SAVED {self.destination} ({self.frames} frames)", flush=True)


def setup_view(sim, eye=(1.9, -0.94, 1.65), target=(0.6, -0.2, 0.65)):
    from omni.kit.viewport.utility import get_active_viewport
    from pxr import Gf, UsdGeom

    vp = get_active_viewport()
    if vp is None:
        raise RuntimeError("Captures need --visualizer kit (add --kit_args=--no-window for headless).")
    camera = UsdGeom.Camera.Define(sim.stage, "/World/RecordingCamera")
    camera.CreateFocalLengthAttr(35)
    camera.CreateHorizontalApertureAttr(36)
    camera.CreateClippingRangeAttr((0.01, 100))
    xf = UsdGeom.Xformable(camera)
    xf.ClearXformOpOrder()
    xf.AddTransformOp().Set(Gf.Matrix4d().SetLookAt(Gf.Vec3d(*eye), Gf.Vec3d(*target), Gf.Vec3d(0, 0, 1)).GetInverse())
    vp.camera_path = camera.GetPath()
    vp.resolution = (1600, 1000)
    return vp


def capture(sim, label):
    from omni.kit.viewport.utility import capture_viewport_to_file

    vp = setup_view(sim)
    for _ in range(25):
        sim.render()
    now = datetime.now(ZoneInfo("America/Vancouver"))
    folder = ROOT / "recordings" / now.strftime("%m-%d-%Y")
    folder.mkdir(parents=True, exist_ok=True)
    stem = now.strftime("%I:%M%p").lstrip("0").lower() + "_" + label
    dest = folder / (stem + ".png")
    n = 2
    while dest.exists():
        dest = folder / f"{stem}-{n}.png"
        n += 1

    async def save():
        await capture_viewport_to_file(vp, str(dest)).wait_for_result()

    pending = asyncio.ensure_future(save())
    while not pending.done():
        sim.render()
    pending.result()
    with (ROOT / "log.md").open("a") as log:
        log.write(f"\n### {now:%m-%d-%Y %I:%M%p} — {label}\n\n![{label}]({dest.relative_to(ROOT)})\n")
    return dest
