"""Offscreen VTK renderer for CadQuery shapes (no params/box dependency).

    from render import render, as_shape
    render([(shape, (r, g, b), opacity), ...], "out.png", view="iso", title="...")

Views: iso, iso_back, top, front, back, left, right, bottom. `clip=(origin, normal)`
cuts the scene with a plane for section views.
"""
from __future__ import annotations

import cadquery as cq


def as_shape(obj) -> cq.Shape:
    if isinstance(obj, cq.Workplane):
        vals = [v for v in obj.vals() if isinstance(v, cq.Shape)]
        if len(vals) == 1:
            return vals[0]
        return cq.Compound.makeCompound(vals)
    if isinstance(obj, cq.Assembly):
        return obj.toCompound()
    return obj



def _polydata(shape: cq.Shape, tol: float = 0.2):
    import vtk

    verts, tris = shape.tessellate(tol, 0.3)
    pts = vtk.vtkPoints()
    for v in verts:
        pts.InsertNextPoint(v.x, v.y, v.z)
    cells = vtk.vtkCellArray()
    for a, b, c in tris:
        cells.InsertNextCell(3)
        cells.InsertCellPoint(a)
        cells.InsertCellPoint(b)
        cells.InsertCellPoint(c)
    pd = vtk.vtkPolyData()
    pd.SetPoints(pts)
    pd.SetPolys(cells)
    nrm = vtk.vtkPolyDataNormals()
    nrm.SetInputData(pd)
    nrm.SetFeatureAngle(35)
    nrm.Update()
    return nrm.GetOutput()


def render(actors_spec: list, path: str, view: str = "iso", size=(1400, 1000), title: str | None = None,
           clip: tuple | None = None) -> None:
    """actors_spec: list of (shape, rgb tuple, opacity)."""
    import vtk

    ren = vtk.vtkRenderer()
    ren.SetBackground(0.97, 0.97, 0.96)
    for shape, rgb, opacity in actors_spec:
        pd = _polydata(shape)
        mapper = vtk.vtkPolyDataMapper()
        if clip is not None:
            plane = vtk.vtkPlane()
            plane.SetOrigin(*clip[0])
            plane.SetNormal(*clip[1])
            mapper.AddClippingPlane(plane)
        mapper.SetInputData(pd)
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        p = actor.GetProperty()
        p.SetColor(*rgb)
        p.SetOpacity(opacity)
        p.SetSpecular(0.15)
        ren.AddActor(actor)
        # crisp outline edges
        fe = vtk.vtkFeatureEdges()
        fe.SetInputData(pd)
        fe.BoundaryEdgesOn()
        fe.FeatureEdgesOn()
        fe.SetFeatureAngle(35)
        fe.ManifoldEdgesOff()
        fe.NonManifoldEdgesOff()
        em = vtk.vtkPolyDataMapper()
        em.SetInputConnection(fe.GetOutputPort())
        em.ScalarVisibilityOff()
        if clip is not None:
            em.AddClippingPlane(plane)
        ea = vtk.vtkActor()
        ea.SetMapper(em)
        ea.GetProperty().SetColor(0.15, 0.15, 0.15)
        ea.GetProperty().SetOpacity(min(1.0, opacity + 0.2))
        ea.GetProperty().SetLineWidth(1.2)
        ren.AddActor(ea)
    if title:
        txt = vtk.vtkTextActor()
        txt.SetInput(title)
        txt.GetTextProperty().SetFontSize(22)
        txt.GetTextProperty().SetColor(0.1, 0.1, 0.1)
        txt.SetDisplayPosition(20, size[1] - 40)
        ren.AddActor2D(txt)
    cam = ren.GetActiveCamera()
    views = {
        "iso": ((1, -1.3, 1.1), (0, 0, 1)),
        "iso_back": ((-1, 1.3, 1.1), (0, 0, 1)),
        "top": ((0, 0, 1), (0, 1, 0)),
        "front": ((0, -1, 0), (0, 0, 1)),
        "back": ((0, 1, 0), (0, 0, 1)),
        "left": ((-1, 0, 0), (0, 0, 1)),
        "right": ((1, 0, 0), (0, 0, 1)),
        "bottom": ((0, 0, -1), (0, 1, 0)),
    }
    direction, up = views[view]
    cam.SetFocalPoint(0, 0, 0)
    cam.SetPosition(*direction)
    cam.SetViewUp(*up)
    if view in ("top", "front", "back", "left", "right", "bottom"):
        cam.ParallelProjectionOn()
    ren.ResetCamera()
    cam.Zoom(1.15)
    win = vtk.vtkRenderWindow()
    win.SetOffScreenRendering(1)
    win.AddRenderer(ren)
    win.SetSize(*size)
    win.SetMultiSamples(8)
    win.Render()
    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(win)
    w2i.Update()
    png = vtk.vtkPNGWriter()
    png.SetFileName(path)
    png.SetInputConnection(w2i.GetOutputPort())
    png.Write()
