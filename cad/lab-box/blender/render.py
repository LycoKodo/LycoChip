"""Blender render of the Lab Box assembly.
blender -b -P render.py -- <glb> <outdir>
"""
import bpy, sys, math, os
from mathutils import Vector
glb, out = sys.argv[sys.argv.index("--") + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
# The GLB was written Z-up (CAD frame) but glTF means Y-up, so the importer tips it over: stand it back up.
from mathutils import Matrix
R = Matrix.Rotation(math.radians(-90), 4, "X")
for o in bpy.context.scene.objects:
    if o.parent is None: o.matrix_world = R @ o.matrix_world
bpy.context.view_layer.update()

LID = ("lid", "acrylic", "captive", "window screws")
CASE = LID + ("base tub", "W I", "rubber feet")
def nm(o): return o.name.split("_", 1)[-1].replace("_", " ")

for o in objs:
    me = o.data
    attr = me.color_attributes[0].name if me.color_attributes else None
    m = bpy.data.materials.new(o.name); m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.5
    n = nm(o)
    if attr:
        a = m.node_tree.nodes.new("ShaderNodeAttribute"); a.attribute_name = attr
        m.node_tree.links.new(a.outputs["Color"], bsdf.inputs["Base Color"])
    if any(k in n for k in ("bridge", "keel", "top plate", "pressure", "spreader", "legs", "ball")):
        bsdf.inputs["Metallic"].default_value = 0.6; bsdf.inputs["Roughness"].default_value = 0.35
    me.materials.clear(); me.materials.append(m)
    for p in me.polygons: p.use_smooth = False

sc = bpy.context.scene
sc.render.engine = "CYCLES"; sc.cycles.samples = 96; sc.cycles.use_denoising = True
try:
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "OPTIX"; prefs.get_devices()
    for d in prefs.devices: d.use = True
    sc.cycles.device = "GPU"
except Exception: pass
sc.render.resolution_x, sc.render.resolution_y = 1920, 1200
sc.view_settings.view_transform = "AgX"
world = bpy.data.worlds.new("w"); sc.world = world; world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.62, 0.65, 0.68, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.6

def bounds(os_):
    pts = [o.matrix_world @ Vector(c) for o in os_ for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
    return lo, hi
lo, hi = bounds(objs); c = (lo + hi) / 2; size = (hi - lo).length
# floor
bpy.ops.mesh.primitive_plane_add(size=size * 6, location=(c.x, c.y, lo.z - 0.1))
fm = bpy.data.materials.new("floor"); fm.use_nodes = True
fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.55, 0.57, 0.6, 1)
bpy.context.object.data.materials.append(fm)
# lights
for loc, e in (((1, -1, 1.6), 3.0), ((-1.2, 0.6, 1.0), 1.2)):
    bpy.ops.object.light_add(type="AREA", location=c + Vector(loc) * size)
    L = bpy.context.object; L.data.energy = e * size * size * 0.8; L.data.size = size * 0.8
    L.rotation_euler = (c - L.location).to_track_quat("-Z", "Y").to_euler()
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 50

def shot(name, hide, d=(1.0, -1.25, 0.95), dist=1.55):
    for o in objs: o.hide_render = any(k in nm(o) for k in hide)
    cam.location = c + Vector(d).normalized() * size * dist
    cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(out, name); bpy.ops.render.render(write_still=True)
    print("wrote", name)
shot("blender_lid_off.png", LID)
shot("blender_caseless.png", CASE)
shot("blender_closed.png", ())
