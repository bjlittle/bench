import math
import netCDF4 as nc
import numpy as np
import os
from pathlib import Path
import perfplot
import pyvista as pv

import iris
from iris.experimental.ugrid import PARSE_UGRID_ON_LOAD
from iris.experimental.ugrid.plot import plot


def synthetic(fname, c):
    with nc.Dataset(fname) as dsin:
        data = np.arange(c*c*6, dtype=np.float)
        netcdf_copy(dsin, fname, data)


def netcdf_copy(dsin, fnamein, datain):
    assert datain.ndim == 1, "oops! expected only 1D datain"

    # output file
    fnameout, ext = os.path.splitext(fnamein)
    fnameout = os.path.join(f"{fnameout}_synthetic{ext}")

    dsout = nc.Dataset(fnameout, "w", format=dsin.file_format)

    dnameout = None
    meshout = None
    coordinates = []

    # copy dimensions
    for dname, the_dim in dsin.dimensions.items():
        #print(dname, the_dim.size)
        if the_dim.size == datain.shape[0]:
            dnameout = dname
        dsout.createDimension(dname, the_dim.size if not the_dim.isunlimited() else None)

    # copy variables
    for v_name, varin in dsin.variables.items():
        outVar = dsout.createVariable(v_name, varin.datatype, varin.dimensions)
        #print(v_name, varin.datatype, varin.dimensions)

        # copy variable attributes
        attrs = {k: varin.getncattr(k) for k in varin.ncattrs()}
        outVar.setncatts(attrs)
        outVar[:] = varin[:]

        if "cf_role" in attrs and attrs["cf_role"] == "mesh_topology":
            meshout = v_name
        if len(varin.dimensions) == 1 and varin.dimensions[0] == dnameout:
            coordinates.append(v_name)

    # create the new data variable
    assert dnameout is not None, "oops! no output dimension name found"
    assert meshout is not None, "oops! no output mesh topology found"
    outVar = dsout.createVariable("synthetic", datain.dtype, (dnameout,))
    outVar[:] = datain
    coordinatesout = ' '.join(coordinates)
    attrs = dict(long_name="synthetic", units="1", mesh=meshout, coordinates=coordinatesout, location="face")
    outVar.setncatts(attrs)

    # copy global attributes
    dsout.setncatts({k: dsin.getncattr(k) for k in dsin.ncattrs()})

    # close the output file
    dsout.close()


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


def iris_setup(n):
    fname = f"/project/avd/ng-vat/data/poc-03/synthetic/bill/mesh_C{n}_synthetic_float.nc"
    with PARSE_UGRID_ON_LOAD.context():
        cube = iris.load_cube(fname)
        cube.data
    return cube


def iris_render(cube, projection=None):
    plotter = pv.Plotter(off_screen=True)
    plot(cube, projection=projection, plotter=plotter, n_colors=15)
    c = int(math.sqrt(cube.shape[0] / 6))
    if projection:
        fname = f"vdi_iris_output_C{c}_{projection}.png"
    else:
        fname = f"vdi_iris_output_C{c}.png"
    proj = f" ({projection})" if projection else ""
    plotter.add_title(f"C{c} Synthetic{proj}")
    plotter.show(screenshot=fname)


if __name__ == "__main__":
    perfplot.show(
        setup=iris_setup,
        kernels=[
            lambda cube: iris_render(cube),
            lambda cube: iris_render(cube, projection="eqc"),
            lambda cube: iris_render(cube, projection="moll"),
            lambda cube: iris_render(cube, projection="sinu"),
            lambda cube: iris_render(cube, projection="gins8")
        ],
        n_range=[4, 12, 24, 48, 96, 192, 384, 768],
        labels=[
            "Spherical (VDI)",
            "Plate Carree (VDI)",
            "Mollweider (VDI)",
            "Sinusoidal (VDI)",
            "Ginsburg VIII (VDI)"
        ],
        xlabel="Cubed-Sphere Panel Size / C(N)",
        equality_check=None,
    )