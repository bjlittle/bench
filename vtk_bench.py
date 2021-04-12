import math
from pathlib import Path
import perfplot
import pyvista as pv


def vtk_setup(n):
    #fname = Path(".") / "data" / f"pdata_C{n}_synthetic.vtk"
    fname = Path("/project/avd/ng-vat/data/poc-03/synthetic") / f"pdata_C{n}_synthetic.vtk"
    return pv.read(fname)

def vtk_render(mesh):
    plotter = pv.Plotter(off_screen=True)
    plotter.add_mesh(mesh, show_edges=False, n_colors=15)
    c = int(math.sqrt(mesh.n_cells / 6))
    plotter.add_title(f"C{c} Synthetic")
    fname = f"vtk_output_C{c}_vdi.png"
    plotter.show(screenshot=fname)
    del mesh
    del plotter

perfplot.show(
    setup=vtk_setup,
    kernels=[
      lambda mesh: vtk_render(mesh)
    ],
    n_range=[4, 12, 24, 48, 96, 192, 384, 768],
    labels=["VTK Spherical"],
    xlabel="Cubed-Sphere Panel Size / C(N)"
)