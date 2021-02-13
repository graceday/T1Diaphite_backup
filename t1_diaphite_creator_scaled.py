# -*- coding: utf-8 -*-
"""
Type 1 diaphite Creator

A program to create layers of diamond-graphite mixes, known as diaphite.
Adapted from a FORTRAN program by Mark Wilson and previous code from
Matt Bailey.

Based on data from:

Diamond-Graphene Composite Nanostructures

Péter Németh, Kit McColl, Rachael L. Smith, Mara Murri, Laurence A. J. Garvie, 
Matteo Alvaro, Béla Pécz, Adrian P. Jones, Furio Corà, 
Christoph G. Salzmann, and Paul F. McMillan
Nano Letters 2020 20 (5), 3611-3619
DOI: 10.1021/acs.nanolett.0c0055

@author: Grace Day
@date: 2020-02-10
"""

import numpy as np
import argparse

from writer_utils import (
    write_cif,
    write_gro,
    write_lammpsdata,
    write_lammpstrj,
    write_xyz,
)

parser = argparse.ArgumentParser(
    description="Generate input files for diaphite simulations."
)

parser.add_argument(
    "--out_file",
    type=str,
    default="diaphite.data",
    help="Name of the file to output to. \
        Accepts *.xyz, *.cif, *.lammpstrj, *.gro or *.data",
)

parser.add_argument(
    "--g", type=int, default=1, help="Number of graphite layers"
)

parser.add_argument(
    "--d", type=int, default=1, help="Number of diamond layers"
)

parser.add_argument(
    "--nx", type=int, default=1,
    help="Number of unit cell repeats in x direction"
)

parser.add_argument(
    "--ny", type=int, default=1,
    help="Number of unit cell repeats in y direction"
)

parser.add_argument(
    "--nz", type=int, default=1,
    help="Number of unit cell repeats in z direction"
)

# Add scale factor command line option
parser.add_argument(
    "--sfa", type=float, default=1, help="Scale factor a"
)

parser.add_argument(
    "--sfb", type=float, default=1, help="Scale factor b"
)

parser.add_argument(
    "--sfc", type=float, default=1, help="Scale factor c"
)


args = parser.parse_args()
"""
Variables to define:
    original code (|| description) || this code
    nunitcellx || # unit cells in x direction || args.nx
    nunitcelly || same || args.ny
    nunitcellz || no of diamond layers || args.d
    nunitcellgz || no of graphite layers || args.g
    nunitcellpos || no of particles in main unit cell || 4
    nunitcellpos_surf || same but surf || 4
    a0 || cell_a
    b0 || ok
    c0 || ok
    xoff || xoff_d
    yoff || ok
    zoff || ok
    xoffg || xoff_g
    yoffg || ok
    zoffg || ok
    scale || scale
    zshiftg || zshiftg
    zshift2 || NOT USED?
    xl || NOT NEEDED?
    yl || NOT NEEDED?
    zl || NOT NEEDED?
    zdia || zdia
    xlz || zheight
"""
scale = 2.90 * 0.529177249  # Scale to a.u. and then Å
# NOT REFLECTED IN zshiftg right now!!!

CELL_A = 1.732 * args.sfa * scale
CELL_B = 3.0 * args.sfb * scale
CELL_C = 0.666667 * args.sfc * scale


def generate_unit_cell(
        g: int = args.g,
        d: int = args.d,
        cell_a: float = CELL_A,
        cell_b: float = CELL_B,
        cell_c: float = CELL_C,
) -> np.array:

    body_array = np.array(
        [
                        [0.0, 0.3333333333, 0.0],
                        [0.5, 0.8333333333, 0.0],
                        [0.0, 0.0, 0.25],
                        [0.5, 0.5, 0.25],
        ]
                    )

    surface_array = np.array(
            [
                            [0.0, 0.166666667, 1.8],
                            [0.0, 0.833333333, 1.6],
                            [0.5, 0.333333333, 1.8],
                            [0.5, 0.666666667, 1.6],
            ]
                        )

    xshift = 0.0
    yshift = 0.0
    zshift = 0.0

    xoff_d = 0.0
    yoff_d = -0.33333333
    zoff_d = 0.75

    xoff_g = 0.0
    yoff_g = -0.33333333
    zoff_g = 2.03  # modified to reflect graphite layer sep from paper

    coordinates = []
    # Generate diamond section:
    for n in np.arange(d):
        for i in np.arange(4):
            coordinates.append([body_array[i][0] * cell_a + xshift,
                                body_array[i][1] * cell_b + yshift,
                                (body_array[i][2] + n) * cell_c + zshift]
                               )
        xshift = xshift + (xoff_d * cell_a)
        yshift = yshift + (yoff_d * cell_b)
        zshift = zshift + (zoff_d * cell_c)

    # Add reconstructed surface layers...
    # ...ABOVE:
    xshift = xshift - (xoff_d * cell_a)
    yshift = yshift - (yoff_d * cell_b)
    zshift = zshift - (zoff_d * cell_c)

    for i in np.arange(4):
        coordinates.append([surface_array[i][0] * cell_a + xshift,
                            surface_array[i][1] * cell_b + yshift,
                            (surface_array[i][2] + (d-1)) * cell_c + zshift]
                           )

    # ...and BELOW:
    xshift = -(xoff_d * cell_a)
    yshift = -(yoff_d * cell_b)
    zshift = -(zoff_d * cell_c)

    for i in np.arange(4):
        coordinates.append([surface_array[i][0] * cell_a + xshift,
                            surface_array[i][1] * cell_b + yshift,
                            (1 - surface_array[i][2]) * cell_c + zshift]
                           )
    # Generate graphite section:
    xshift = 0.0
    yshift = 0.0
    zshift = 0.0

    # Define zshiftg for use in graphite layers:
    zshiftg = (1.7 + (1+zoff_d) * (d-1) + 3.3135) * cell_c
    """
    Explanation:
        - The surface atoms are found in a layer centred at a height of
        1.7 * cell_c above the diamond section
        - The diamond section has a height of
        (d-1) * (1+zoff_d) * cell_c
        - The first graphite layer is 3.39Å above the centred
        plane of the surface (see Nemeth paper), equivalent to
        3.3135 * cell_c
    """
    zheight = zshiftg + (g * (1 + zoff_g) + 0.26391 + (0.7 + zoff_d)) * cell_c
    """
    Explanation:
        - zshiftg as above
        - g * (1 + zoff_g) * cell_c reflects space occupied by g layers of
        graphite
        - 0.26391 * cell_c reflects additional distance from graphite layer
        to surface, compared to gap between graphite layers.
            - graphite-surface 3.39Å
            - graphite-graphite 3.12Å
            - again from Nemeth paper
        - (0.7 + zoff_d) * cell_c reflects depth of surface 'below' diamond
        section (which actually ends up above diamond section once boundary
        conditions are applied below)
    """

    # Actually write graphite layers:
    for n in np.arange(g):
        for i in np.arange(4):
            coordinates.append([body_array[i][0] * cell_a + xshift,
                                body_array[i][1] * cell_b + yshift,
                                n * cell_c + zshift + zshiftg]
                               )
        xshift = xshift + (xoff_g * cell_a)
        yshift = yshift + (yoff_g * cell_b)
        zshift = zshift + (zoff_g * cell_c)

    # Bring in boundary conditions to get vertical stacking:
    for coord in coordinates:
        if coord[0] < 0.0:
            coord[0] = coord[0] + cell_a
        if coord[1] < 0.0:
            coord[1] = coord[1] + cell_b
        if coord[2] < 0.0:
            coord[2] = coord[2] + zheight

    simulation_cell = np.array([[0.0, cell_a],
                                [0.0, cell_b],
                                [0.0, zheight]])
    return np.array(coordinates), simulation_cell


# Copied directly from old code
def repeat_unit_cell(
    positions: np.array, simulation_cell: np.array, nx: int, ny: int, nz: int
):
    """
    Repeat the positions nx, ny and nz times in x, y, z directions.

    Leaves xlo, ylo and zlo unchanged,
    extends in the direction of xhi, yhi, zhi.
    Parameters
    ----------
    positions
        An Nx3 array of atomic positions.
    simulation cell
        A 3x2 numpy array in the form [[xlo, xhi], [ylo, yhi], [zlo, zhi]].
    nx
        Number of repeats in the x direction
    ny
        Number of repeats in the y direction
    nz
        Number of repeats in the z direction
    Returns
    -------
    positions
        An Nx3 array of repeated atomic positions
    simulation cell
        A 3x2 numpy array in the form [[xlo, xhi], [ylo, yhi], [zlo, zhi]].
    """
    assert nx >= 1, "nx must be a positive integer"
    assert ny >= 1, "ny must be a positive integer"
    assert nz >= 1, "nz must be a positive integer"
    cell_a = simulation_cell[0, 1] - simulation_cell[0, 0]
    cell_b = simulation_cell[1, 1] - simulation_cell[1, 0]
    cell_c = simulation_cell[2, 1] - simulation_cell[2, 0]

    positions = np.vstack(
        [positions + np.array([i * cell_a, 0.0, 0.0]) for i in range(nx)]
    )
    positions = np.vstack(
        [positions + np.array([0.0, j * cell_b, 0.0]) for j in range(ny)]
    )
    positions = np.vstack(
        [positions + np.array([0.0, 0.0, k * cell_c]) for k in range(nz)]
    )

    # Re-calculate the size of the simulation box
    simulation_cell[0, 1] = simulation_cell[0, 0] + (nx * cell_a)
    simulation_cell[1, 1] = simulation_cell[1, 0] + (ny * cell_b)
    simulation_cell[2, 1] = simulation_cell[2, 0] + (nz * cell_c)
    return positions, simulation_cell


positions, simulation_cell = generate_unit_cell()
positions, simulation_cell = repeat_unit_cell(positions,
                                              simulation_cell,
                                              args.nx, args.ny, args.nz)
write_lammpstrj(args.out_file, positions, simulation_cell)


def main():
    """
    Generate a diaphite sequence and write to a file.
    """
    positions, simulation_cell = generate_unit_cell()
    positions, simulation_cell = repeat_unit_cell(positions,
                                                  simulation_cell,
                                                  args.nx, args.ny, args.nz)
    out_file = args.out_file
    if out_file.endswith(".xyz"):
        write_xyz(out_file, positions, simulation_cell)
    elif out_file.endswith(".cif"):
        write_cif(out_file, positions, simulation_cell)
    elif out_file.endswith(".data"):
        write_lammpsdata(out_file, positions, simulation_cell)
    elif out_file.endswith(".lammpstrj"):
        write_lammpstrj(out_file, positions, simulation_cell)
    elif out_file.endswith(".gro"):
        write_gro(out_file, positions, simulation_cell)
    else:
        raise RuntimeError(
            "Did not add a suffix of the form .xyz, .cif, .data \
                .lammpstrj or .gro to the output file."
        )
    print(f"Successfully wrote the diaphite positions to {out_file}")


if __name__ == "__main__":
    main()
