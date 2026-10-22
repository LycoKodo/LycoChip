"""Export the simple-first massing model as colored 3D files (GLB, OBJ, STEP)."""
import os, sys, importlib.util
import numpy as np, trimesh, cadquery as cq
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
spec = importlib.util.spec_from_file_location("m", os.path.join(HERE, "simple-first_model.py"))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
from render import as_shape
scene = trimesh.Scene(); asm = cq.Assembly()
for i, (group, name, shape, rgb, op) in enumerate(m.PARTS):
    s = as_shape(shape)
    verts, tris = s.tessellate(0.1, 0.2)
    if not tris: continue
    mesh = trimesh.Trimesh([(v.x, v.y, v.z) for v in verts], tris, process=False)
    c = [int(255*k) for k in rgb] + [int(255*op)]
    mesh.visual = trimesh.visual.ColorVisuals(mesh, face_colors=np.tile(c, (len(tris), 1)))
    scene.add_geometry(mesh, node_name=f"{i}_{name}")
    asm.add(s, name=f"{i}_{name}", color=cq.Color(*rgb, op))
out = os.path.join(HERE, "export")
scene.export(os.path.join(out, "simple-first.glb"))
scene.export(os.path.join(out, "simple-first.obj"))
asm.save(os.path.join(out, "simple-first.step"))
print(len(m.PARTS), "parts;", {f: os.path.getsize(os.path.join(out, f)) for f in os.listdir(out)})
