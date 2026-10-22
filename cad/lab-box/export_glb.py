"""Export the full assembly as a coloured GLB (view on a Mac in Reality Converter or a glTF web viewer)."""
import os, sys
import numpy as np, trimesh
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import box
from render import as_shape
scene = trimesh.Scene()
for i, it in enumerate(box.ASSEMBLY()):
    verts, tris = as_shape(it.shape).tessellate(0.1, 0.2)
    if not tris: continue
    mesh = trimesh.Trimesh([(v.x, v.y, v.z) for v in verts], tris, process=False)
    c = [int(255 * k) for k in it.color] + [int(255 * getattr(it, "opacity", 1.0))]
    mesh.visual = trimesh.visual.ColorVisuals(mesh, face_colors=np.tile(c, (len(tris), 1)))
    scene.add_geometry(mesh, node_name=f"{i}_{it.name}")
scene.export(os.path.join(HERE, "parts", "lab_box_assembly.glb"))
print(len(scene.geometry), "meshes")
