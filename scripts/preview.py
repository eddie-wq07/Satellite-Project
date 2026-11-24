"""Open the saved factory in Isaac Sim; --capture saves its four authored camera views."""

import argparse
import asyncio
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--capture", action="store_true")
parser.add_argument("--asset", type=Path, default=ROOT / "src/Satellite_Project/assets/data/environments/factory.usda")
args = parser.parse_args()
from isaacsim import SimulationApp

app = SimulationApp({"headless": args.capture, "width": 1600, "height": 1000, "multi_gpu": False})
import omni.usd
from omni.kit.viewport.utility import capture_viewport_to_file, get_active_viewport

omni.usd.get_context().open_stage(str(args.asset.resolve()))
for _ in range(60):
    app.update()
vp = get_active_viewport()
vp.resolution = (1600, 1000)
vp.camera_path = "/World/Cameras/Overview"
if args.capture:
    now = datetime.now(ZoneInfo("America/Vancouver"))
    folder = ROOT / "recordings" / now.strftime("%m-%d-%Y")
    folder.mkdir(parents=True, exist_ok=True)
    for view in ["Overview", "Pickup", "Cells", "Array"]:
        vp.camera_path = "/World/Cameras/" + view
        for _ in range(35):
            app.update()
        stamp = now.strftime("%I:%M%p").lstrip("0").lower()
        dest = folder / f"{stamp}_factory-{view.lower()}.png"

        suffix = 2
        while dest.exists():
            dest = folder / f"{stamp}_factory-{view.lower()}-{suffix}.png"
            suffix += 1

        async def capture(dest=dest):
            await capture_viewport_to_file(vp, str(dest)).wait_for_result()

        pending = asyncio.ensure_future(capture())
        while not pending.done():
            app.update()
        pending.result()
        import omni.kit.renderer_capture

        omni.kit.renderer_capture.acquire_renderer_capture_interface().wait_async_capture()
        assert dest.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
        print("CAPTURE", dest, flush=True)
else:
    while app.is_running():
        app.update()
app.close()
