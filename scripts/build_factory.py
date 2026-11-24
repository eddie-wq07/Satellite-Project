"""Build the persistent, locally referenced factory USD. Run with ~/env_isaaclab/bin/python."""

import math
from pathlib import Path

from pxr import Gf, Sdf, Usd, UsdGeom, UsdLux, UsdPhysics, UsdShade

DATA = Path(__file__).resolve().parents[1] / "src/Satellite_Project/assets/data"
OUT = DATA / "environments"
s = None
materials = {}


def xform(path, pos=(0, 0, 0), rot=(0, 0, 0)):
    p = UsdGeom.Xform.Define(s, path)
    p.AddTranslateOp().Set(Gf.Vec3d(*pos))
    p.AddRotateXYZOp().Set(Gf.Vec3f(*rot))
    return p


def material(name, color, metal=0, rough=0.4, opacity=1):
    m = UsdShade.Material.Define(s, "/World/Looks/" + name)
    sh = UsdShade.Shader.Define(s, str(m.GetPath()) + "/Shader")
    sh.CreateIdAttr("UsdPreviewSurface")
    for key, typ, val in [
        ("diffuseColor", Sdf.ValueTypeNames.Color3f, color),
        ("metallic", Sdf.ValueTypeNames.Float, metal),
        ("roughness", Sdf.ValueTypeNames.Float, rough),
        ("opacity", Sdf.ValueTypeNames.Float, opacity),
    ]:
        sh.CreateInput(key, typ).Set(val)
    m.CreateSurfaceOutput().ConnectToSource(sh.ConnectableAPI(), "surface")
    materials[name] = m


def finish(p, pos, mat, collision):
    p.AddTranslateOp().Set(Gf.Vec3d(*pos))
    UsdShade.MaterialBindingAPI.Apply(p.GetPrim()).Bind(materials[mat])
    if collision:
        UsdPhysics.CollisionAPI.Apply(p.GetPrim())
    return p


def box(path, pos, size, mat="Silver", collision=True):
    p = UsdGeom.Cube.Define(s, path)
    p.CreateSizeAttr(1)
    finish(p, pos, mat, collision)
    p.AddScaleOp().Set(Gf.Vec3f(*size))
    return p


def cylinder(path, pos, radius, height, mat="Silver", axis="Z", collision=False):
    p = UsdGeom.Cylinder.Define(s, path)
    p.CreateRadiusAttr(radius)
    p.CreateHeightAttr(height)
    p.CreateAxisAttr(axis)
    return finish(p, pos, mat, collision)


def tube(path, points, width, mat):
    p = UsdGeom.BasisCurves.Define(s, path)
    p.CreateTypeAttr("linear")
    p.CreateCurveVertexCountsAttr([len(points)])
    p.CreatePointsAttr(points)
    p.CreateWidthsAttr([width])
    p.SetWidthsInterpolation("constant")
    UsdShade.MaterialBindingAPI.Apply(p.GetPrim()).Bind(materials[mat])


def cell(path, pos, size=(0.15, 0.09, 0.002), lines=True):
    xform(path, pos)
    box(path + "/Wafer", (0, 0, 0), size, "PV", False)
    if lines:
        for i in range(17):
            box(
                path + f"/Finger{i}",
                (-size[0] * 0.46 + i * size[0] * 0.92 / 16, 0, size[2] / 2 + 0.00015),
                (0.00055, size[1] * 0.96, 0.0002),
                "Conductor",
                False,
            )
        for y in [-size[1] * 0.32, size[1] * 0.32]:
            box(
                path + f"/Bus{int(y > 0)}",
                (0, y, size[2] / 2 + 0.0003),
                (size[0] * 0.96, 0.001, 0.00025),
                "Conductor",
                False,
            )


def tool(path):
    xform(path)
    cylinder(path + "/Mount", (0, 0, -0.025), 0.045, 0.05)
    for y in [-0.12, 0.12]:
        box(path + f"/Rail{int(y > 0)}", (0, y, -0.07), (0.73, 0.025, 0.025))
    for i, x in enumerate([-0.32, 0, 0.32]):
        box(path + f"/Cross{i}", (x, 0, -0.07), (0.025, 0.29, 0.025))
    for i, x in enumerate([-0.255, -0.085, 0.085, 0.255]):
        for j, y in enumerate([-0.055, 0.055]):
            p = path + f"/Contact{i}_{j}"
            cylinder(p + "Stem", (x, y, -0.105), 0.009, 0.06)
            cylinder(p + "Disc", (x, y, -0.143), 0.034, 0.018)
            cylinder(p + "Seal", (x, y, -0.154), 0.03, 0.005, "Blue")
            box(p + "Valve", (x, y, -0.044), (0.032, 0.025, 0.025), "Blue", False)
            tube(p + "Hose", [(x, y, -0.034), (x, y * 0.5, 0.015), (x * 0.3, 0, 0.03), (0, 0, 0)], 0.007, "Blue")
    tube(path + "/Service", [(0, 0, 0.015), (-0.12, 0, 0.2), (-0.3, 0, 0.27), (-0.45, 0, 0.22)], 0.028, "Black")


def table(path, pos, size):
    xform(path, pos)
    box(path + "/Deck", (0, 0, -0.025), (size[0], size[1], 0.05))
    for i, x in enumerate([-0.5 * size[0] + 0.06, 0.5 * size[0] - 0.06]):
        for j, y in enumerate([-0.5 * size[1] + 0.06, 0.5 * size[1] - 0.06]):
            box(path + f"/Leg{i}{j}", (x, y, -pos[2] / 2), (0.045, 0.045, pos[2]))
            box(path + f"/Foot{i}{j}", (x, y, -pos[2] + 0.025), (0.1, 0.1, 0.05), "Black")
    box(path + "/Brace", (0, 0, -pos[2] + 0.2), (size[0], 0.04, 0.04))


def camera(name, eye, target, focal=35):
    c = UsdGeom.Camera.Define(s, "/World/Cameras/" + name)
    c.CreateFocalLengthAttr(focal)
    c.CreateClippingRangeAttr((0.01, 100))
    c.CreateHorizontalApertureAttr(36)
    c.CreateVerticalApertureAttr(22.5)
    c.AddTransformOp().Set(Gf.Matrix4d().SetLookAt(Gf.Vec3d(*eye), Gf.Vec3d(*target), Gf.Vec3d(0, 0, 1)).GetInverse())


def build():
    global s
    OUT.mkdir(parents=True, exist_ok=True)
    s = Usd.Stage.CreateNew(str(OUT / "factory.usda"))
    UsdGeom.SetStageUpAxis(s, "Z")
    UsdGeom.SetStageMetersPerUnit(s, 1)
    world = xform("/World")
    s.SetDefaultPrim(world.GetPrim())
    world.GetPrim().SetCustomDataByKey(
        "description", "Evidence-based reconstruction of vision.md; dimensions and exact ABB variant unverified."
    )
    for args in [
        ("Silver", (0.58, 0.62, 0.66), 0.8, 0.28),
        ("White", (0.82, 0.84, 0.85), 0.15, 0.3),
        ("Black", (0.018, 0.022, 0.028), 0.1, 0.45),
        ("Blue", (0.015, 0.2, 0.65), 0.05, 0.3),
        ("Orange", (0.75, 0.16, 0.035), 0, 0.62),
        ("PV", (0.025, 0.035, 0.13), 0.5, 0.2),
        ("Conductor", (0.55, 0.55, 0.61), 0.85, 0.22),
        ("Copper", (0.58, 0.24, 0.08), 0.7, 0.27),
        ("Pink", (0.9, 0.015, 0.29), 0, 0.4),
        ("Floor", (0.39, 0.43, 0.46), 0.1, 0.65),
        ("Glass", (0.55, 0.75, 0.8), 0.1, 0.08, 0.035),
        ("Green", (0.05, 0.8, 0.2), 0, 0.3),
        ("Yellow", (0.9, 0.65, 0.03), 0, 0.5),
        ("Red", (0.7, 0.015, 0.01), 0, 0.4),
    ]:
        material(*args)
    box("/World/Building/Floor", (0, 0, -0.08), (9, 7, 0.16), "Floor")
    for x in [-4, 4]:
        box(f"/World/Building/Wall{int(x > 0)}", (x, 1, 1.8), (0.12, 5, 3.6), "White")
    box("/World/Building/Back", (0, 3.1, 1.8), (8, 0.12, 3.6), "White")
    for x in range(-3, 4):
        box(f"/World/Building/Seam{x + 3}", (x, 0, 0.001), (0.006, 6, 0.001), "Silver", False)
    # Stations measured in metres; local task geometry is centered below the first arm's neutral wrist.
    table("/World/Fixtures/Supply", (0.717, 0, 0.69), (0.72, 0.48))
    for i in range(4):
        for j in range(2):
            x = 0.717 + (i - 1.5) * 0.17
            y = (j - 0.5) * 0.11
            for k in range(12):
                cell(f"/World/Cells/Stack{i}{j}/Layer{k}", (x, y, 0.692 + k * 0.0024), lines=k == 11)
            support = box(f"/World/Fixtures/StackSupport{i}{j}", (x, y, 0.7052), (0.15, 0.09, 0.0284), "PV")
            UsdGeom.Imageable(support).CreateVisibilityAttr("invisible")
            box(f"/World/Fixtures/Marker{i}{j}", (x, y - 0.05, 0.696), (0.015, 0.013, 0.004), "Pink", False)
    # Top batch is one rigid handling surrogate; visible eight cells remain distinct.
    batch = xform("/World/Batch", (0.717, 0, 0.7228))
    UsdPhysics.RigidBodyAPI.Apply(batch.GetPrim())
    UsdPhysics.MassAPI.Apply(batch.GetPrim()).CreateMassAttr(0.12)
    for i in range(4):
        for j in range(2):
            cell(f"/World/Batch/Cell{i}{j}", ((i - 1.5) * 0.17, (j - 0.5) * 0.11, 0))
    proxy = box("/World/Batch/Collision", (0, 0, 0), (0.66, 0.2, 0.002), "PV")
    UsdGeom.Imageable(proxy).CreateVisibilityAttr("invisible")
    batch.GetPrim().SetCustomDataByKey(
        "model", "Rigid top-layer batch surrogate; vacuum assumed, not established by source"
    )
    for n, y in enumerate([0.72, 1.48]):
        p = f"/World/Fixtures/Conveyor{n}"
        table(p, (0.72, y, 0.69), (2, 0.55))
        box(p + "/Belt", (0, 0, 0.008), (1.85, 0.48, 0.015), "Orange")
        for i, x in enumerate([-0.925, 0.925]):
            cylinder(p + f"/End{i}", (x, 0, -0.04), 0.055, 0.48, "Orange", "Y")
        for j, z in enumerate([-0.02, -0.09]):
            box(p + f"/Side{j}", (0, -0.29, z), (2, 0.045, 0.06))
        for i in range(7):
            for j in range(3):
                cell(p + f"/PV{i}{j}", ((i - 3) * 0.17, (j - 1) * 0.11, 0.02))
    table("/World/Fixtures/Placement", (0.50, -0.70, 0.69), (0.98, 0.45))
    box("/World/Fixtures/Placement/Mat", (0, 0, 0.004), (0.84, 0.32, 0.008), "Orange")
    # Two native USD articulations, with stronger project-layer wrist drives for the custom tooling.
    for name, pos, angle in [("Robot", (0, 0, 0), 0), ("RobotRear", (-0.7, 1.48, 0), 0)]:
        p = "/World/" + name
        robot = s.DefinePrim(p, "Xform")
        robot.GetReferences().AddReference("../robots/abb_irb1600/IRB1600_X-120.usd")
        xf = UsdGeom.Xformable(robot)
        xf.ClearXformOpOrder()
        xf.AddTranslateOp().Set(Gf.Vec3d(*pos))
        xf.AddRotateZOp().Set(angle)
        for prim in list(Usd.PrimRange(robot)):
            if prim.IsA(UsdGeom.Mesh):
                UsdShade.MaterialBindingAPI.Apply(prim).Bind(materials["White"])
        for i in range(1, 7):
            joint = s.GetPrimAtPath(p + f"/joints/joint_{i}")
            d = UsdPhysics.DriveAPI(joint, "angular")
            d.CreateStiffnessAttr(20000 * math.pi / 180 if i < 4 else 1500 * math.pi / 180)
            d.CreateDampingAttr(1000 * math.pi / 180 if i < 4 else 80 * math.pi / 180)
            d.CreateMaxForceAttr(1000 if i < 4 else 160)
        inertia = UsdPhysics.MassAPI(s.GetPrimAtPath(p + "/flange"))
        inertia.CreateMassAttr(2.8)
        inertia.CreateCenterOfMassAttr((0.075, 0, 0))
        inertia.CreateDiagonalInertiaAttr((0.16, 0.14, 0.027))
        inertia.CreatePrincipalAxesAttr(Gf.Quatf(1))
        flange = s.GetPrimAtPath(p + "/flange")
        rot = UsdGeom.XformCache().GetLocalToWorldTransform(flange).RemoveScaleShear()
        rot.SetTranslateOnly(Gf.Vec3d(0))
        tool(p + "/flange/Tool")
        t = UsdGeom.Xformable(s.GetPrimAtPath(p + "/flange/Tool"))
        t.ClearXformOpOrder()
        t.AddTransformOp().Set(rot.GetInverse())
        # Cable routes attached to individual links avoid a static cable crossing moving joints.
        tube(p + "/link_2/Cable", [(0, -0.08, 0), (0, -0.09, 0.2), (0, -0.1, 0.46)], 0.026, "Black")
        tube(p + "/link_4/Cable", [(0, 0.07, 0.08), (0.12, 0.07, 0.11), (0.28, 0.04, 0.08)], 0.025, "Black")
    # Guarding remains clear from the overview camera; doorway is open on the south side.
    for i, x in enumerate([-0.65, 0.45, 1.55, 2.4]):
        for j, y in enumerate([-0.98, 2.05]):
            box(f"/World/Guard/Post{i}{j}", (x, y, 1.05), (0.04, 0.04, 2.1))
    for j, y in enumerate([-0.98, 2.05]):
        for k, z in enumerate([0.18, 1.05, 2.1]):
            box(f"/World/Guard/Rail{j}{k}", (0.875, y, z), (3.1, 0.04, 0.04))
        for i, x in enumerate([-0.1, 1, 1.975]):
            if j == 0 and i == 0:
                continue
            box(f"/World/Guard/Panel{j}{i}", (x, y, 1.57), (1.04 if i < 2 else 0.81, 0.008, 1.0), "Glass")
    table("/World/Fixtures/ArrayStand", (1.95, 1.1, 0.65), (0.55, 0.8))
    arr = xform("/World/ArraySection", (1.95, 1.1, 1.22), (0, 68, 0))
    box("/World/ArraySection/Backing", (0, 0, 0), (1.05, 0.78, 0.014), "Black")
    for i in range(6):
        for j in range(7):
            cell(f"/World/ArraySection/Cell{i}_{j}", ((i - 2.5) * 0.17, (j - 3) * 0.105, 0.009))
    for i, y in enumerate([-0.37, 0.37]):
        box(f"/World/ArraySection/Edge{i}", (0, y, 0.015), (1.05, 0.018, 0.006), "Copper")
    arr.GetPrim().SetCustomDataByKey(
        "description", "Later montage section represented on an inspection stand; not claimed as the same batch"
    )
    # Background controls and the subsequent parallel-element machine, kept separate from handling.
    box("/World/Controls/Cabinet", (-1.4, 2.5, 0.65), (0.6, 0.48, 1.3), "White")
    box("/World/Controls/Screen", (-1.4, 2.25, 0.92), (0.32, 0.02, 0.23), "Black", False)
    cylinder("/World/Controls/TowerStem", (-1.4, 2.5, 1.4), 0.012, 0.2, "Black")
    for i, mat in enumerate(["Green", "Yellow", "Red"]):
        cylinder(f"/World/Controls/Tower{i}", (-1.4, 2.5, 1.5 + i * 0.07), 0.035, 0.06, mat)
    table("/World/NextMachine", (2.4, 2.65, 0.75), (1.3, 0.5))
    for i in range(20):
        box(f"/World/NextMachine/Guide{i}", ((i - 9.5) * 0.06, 0, 0.025), (0.018, 0.45, 0.05), "Black")
        box(f"/World/NextMachine/Contact{i}", ((i - 9.5) * 0.06, -0.23, 0.025), (0.018, 0.035, 0.03), "Copper", False)
    physics = UsdPhysics.Scene.Define(s, "/World/Physics")
    physics.CreateGravityDirectionAttr((0, 0, -1))
    physics.CreateGravityMagnitudeAttr(9.81)
    dome = UsdLux.DomeLight.Define(s, "/World/Lighting/Fill")
    dome.CreateIntensityAttr(600)
    for i, (x, y) in enumerate([(-1, 0), (1, 0), (0, 2), (2, 2)]):
        light = UsdLux.RectLight.Define(s, f"/World/Lighting/Softbox{i}")
        light.CreateIntensityAttr(1600)
        light.CreateWidthAttr(2)
        light.CreateHeightAttr(1)
        light.AddTranslateOp().Set(Gf.Vec3d(x, y, 3.4))
    camera("Overview", (2.9, -0.86, 2.5), (0.6, 0.7, 0.8), 28)
    camera("Pickup", (1.25, -0.83, 1.03), (0.67, 0, 0.79), 42)
    camera("Cells", (1.8, -0.1, 1.8), (0.75, 0.72, 0.70), 55)
    camera("Array", (3.4, -0.3, 1.9), (1.9, 1.1, 1.2), 50)
    s.GetRootLayer().Save()
    s.Flatten().Export(str(OUT / "factory.usdc"))
    # Extract portable training assets with their materials inside the referenced root.
    flat = s.GetRootLayer()
    for name in ["Robot", "Batch"]:
        dest = Usd.Stage.CreateNew(str(OUT / (name.lower() + ".usda")))
        Sdf.CopySpec(flat, "/World/" + name, dest.GetRootLayer(), "/" + name)
        Sdf.CopySpec(flat, "/World/Looks", dest.GetRootLayer(), "/" + name + "/Looks")
        for prim in dest.Traverse():
            for rel in prim.GetRelationships():
                targets = rel.GetTargets()
                if targets:
                    rel.SetTargets(
                        [
                            Sdf.Path(
                                str(t)
                                .replace("/World/Looks", "/" + name + "/Looks")
                                .replace("/World/" + name, "/" + name)
                            )
                            for t in targets
                        ]
                    )
        dest.SetDefaultPrim(dest.GetPrimAtPath("/" + name))
        UsdGeom.SetStageUpAxis(dest, "Z")
        UsdGeom.SetStageMetersPerUnit(dest, 1)
        # Spawn configurations supply the batch world transform.
        if name == "Batch":
            UsdGeom.Xformable(dest.GetDefaultPrim()).ClearXformOpOrder()
        dest.GetRootLayer().Save()
    static = Usd.Stage.CreateNew(str(OUT / "static.usda"))
    UsdGeom.SetStageUpAxis(static, "Z")
    UsdGeom.SetStageMetersPerUnit(static, 1)
    static.DefinePrim("/World", "Xform").GetReferences().AddReference("factory.usda")
    static.SetDefaultPrim(static.GetPrimAtPath("/World"))
    for name in ["Robot", "Batch", "Physics", "Lighting", "Cameras", "Building"]:
        static.OverridePrim("/World/" + name).SetActive(False)
    static.GetPrimAtPath("/World/RobotRear").GetVariantSet("Physics").SetVariantSelection("None")
    static.GetRootLayer().Save()
    print(OUT / "factory.usda", len(list(s.Traverse())), "prims")


if __name__ == "__main__":
    build()
