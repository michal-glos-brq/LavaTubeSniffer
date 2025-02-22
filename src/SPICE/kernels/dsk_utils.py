import os
import sys
from datetime import timedelta
import logging

import pandas as pd
import numpy as np

import spiceypy
import astropy.units as u
from astropy.coordinates import SphericalRepresentation

sys.path.insert(0, "/".join(__file__.split("/")[:-3]))
from src.SPICE.kernels import dynamic_kernel_loader
from src.SPICE.config import (
    LUNAR_MODEL,
    LUNAR_RADIUS,
    DSK_FILE_FRAME,
    DSK_FILE_CENTER_BODY_ID,
    DSK_FILESURFACE_ID,
    FINSCL,
    CORSCL,
    WORKSZ,
    VOXPSZ,
    VOXLSZ,
    SPXISZ,
    MAKVTL,
    CORPAR,
    CORSYS,
    DCLASS,
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


def xyz_to_dsk_model():
    """
    Converts an XYZ file (generated from TIF with GDAL) to a DSK model.
    """
    # Load kernels needed for computation. If fails, SPICE must be fetched with fetch script.
    sweep_iterator = dynamic_kernel_loader.SweepIterator()
    computation_start = sweep_iterator.min_loaded_time
    computation_timedelta = timedelta(days=1000)
    computation_now = computation_start + computation_timedelta
    sweep_iterator.initiate_sweep(computation_now)

    df = pd.read_csv(LUNAR_MODEL["xyz_file"], sep=" ", names=["x", "y", "z"])

    # Extract coordinates
    x = df["x"].to_numpy()
    y = df["y"].to_numpy()
    z = (df["z"] / 100).to_numpy().astype(np.float32)  # Convert elevation to meters

    lon = np.interp(x, (x.min(), x.max()), (-180, 180)) * u.deg
    lat = (90 - (y - y.min())/(y.max()-y.min()) * 180) * u.deg
    lat = -lat  # Invert latitude

    # Compute the 3D radius and convert to Cartesian
    radius = (LUNAR_RADIUS + z) * u.m
    spherical_coords = SphericalRepresentation(lon, lat, radius)
    cartesian_coords = spherical_coords.to_cartesian()

    batch_rects = np.column_stack([
        cartesian_coords.x.value,
        cartesian_coords.y.value,
        cartesian_coords.z.value
    ]).astype(np.float32)

    # --- Reshape grid and downsample based on latitude ---
    unique_x = np.unique(x)
    unique_y = np.unique(y)
    num_cols = len(unique_x)
    num_rows = len(unique_y)
    assert num_rows * num_cols == len(x), "Data does not form a complete grid."

    # Reshape to 2D grid (rows = latitudes, cols = longitudes)
    vertices_grid = batch_rects.reshape(num_rows, num_cols, 3)
    lon_grid = lon.value.reshape(num_rows, num_cols)
    lat_grid = lat.value.reshape(num_rows, num_cols)

    global_vertices_list = []  # List of downsampled row vertex arrays.
    row_data = []              # List of dicts: {'indices': global indices, 'lons': sampled longitudes}
    global_index = 0

    for i in range(num_rows):
        row_lat = lat_grid[i, 0]
        factor = np.cos(np.deg2rad(abs(row_lat)))
        desired_count = max(1, int(np.round(num_cols * factor)))
        col_indices = np.linspace(0, num_cols - 1, desired_count, dtype=int)

        row_vertices = vertices_grid[i, col_indices, :]
        row_lons = lon_grid[i, col_indices]
        indices = np.arange(global_index, global_index + len(col_indices))
        global_index += len(col_indices)

        global_vertices_list.append(row_vertices)
        row_data.append({'indices': indices, 'lons': row_lons})

    vertices_global = np.concatenate(global_vertices_list, axis=0)

    # --- Stitch adjacent rows into triangles ---
    def stitch_rows(idxA, idxB, lonA, lonB):
        """Merge two rows of vertices into triangles."""
        tris = []
        i, j = 0, 0
        while i < len(idxA)-1 and j < len(idxB)-1:
            diffA = abs(lonA[i+1] - lonB[j])
            diffB = abs(lonB[j+1] - lonA[i])
            if diffA < diffB:
                tris.append([idxA[i], idxB[j], idxA[i+1]])
                i += 1
            else:
                tris.append([idxA[i], idxB[j], idxB[j+1]])
                j += 1
        while i < len(idxA)-1:
            tris.append([idxA[i], idxB[-1], idxA[i+1]])
            i += 1
        while j < len(idxB)-1:
            tris.append([idxA[-1], idxB[j], idxB[j+1]])
            j += 1
        return tris

    triangles = []
    for r in range(len(row_data) - 1):
        idxA = row_data[r]['indices']
        idxB = row_data[r+1]['indices']
        lonA = row_data[r]['lons']
        lonB = row_data[r+1]['lons']

        if len(idxA) == 1:
            for j in range(len(idxB)-1):
                triangles.append([idxA[0], idxB[j], idxB[j+1]])
        elif len(idxB) == 1:
            for i in range(len(idxA)-1):
                triangles.append([idxA[i], idxB[0], idxA[i+1]])
        else:
            triangles.extend(stitch_rows(idxA, idxB, lonA, lonB))

    vertices = np.array(vertices_global)
    triangles = np.array([[x+1, y+1, z+1] for x, y, z in triangles])

    # --- Open DSK File for Writing ---
    if os.path.exists(LUNAR_MODEL["dsk_path"]):
        os.remove(LUNAR_MODEL["dsk_path"])
        logger.info("Existing DSK file removed to avoid conflicts.")

    mncor1, mxcor1 = np.min(vertices[:, 0]), np.max(vertices[:, 0])
    mncor2, mxcor2 = np.min(vertices[:, 1]), np.max(vertices[:, 1])
    mncor3, mxcor3 = np.min(vertices[:, 2]), np.max(vertices[:, 2])

    logger.info("Adjusted Bounds:")
    logger.info("  X: %s to %s", mncor1, mxcor1)
    logger.info("  Y: %s to %s", mncor2, mxcor2)
    logger.info("  Z: %s to %s", mncor3, mxcor3)

    NVXTOT = ((mxcor1 - mncor1) / FINSCL) * ((mxcor2 - mncor2) / FINSCL) * ((mxcor3 - mncor3) / FINSCL)
    logger.info("Estimated Fine Voxel Count (NVXTOT): %s", NVXTOT)

    handle = spiceypy.dskopn(LUNAR_MODEL["dsk_path"], "Generated DSK File", 0)
    logger.info("Opened DSK file: %s", LUNAR_MODEL["dsk_path"])

    # --- Compute Spatial Index ---
    logger.info("Computing spatial index...")
    spaixd, spaixi = spiceypy.dskmi2(
        vertices,
        triangles,
        FINSCL, CORSCL,
        WORKSZ, VOXPSZ, VOXLSZ,
        MAKVTL, SPXISZ
    )
    logger.info("Spatial index computed.")

    # --- Write DSK Segment ---
    logger.info("Writing DSK file...")
    time_start = -1e9  # Arbitrary large negative time (valid for all time)
    time_end = 1e9     # Arbitrary large positive time

    spiceypy.dskw02(
        handle, DSK_FILE_CENTER_BODY_ID, DSK_FILESURFACE_ID, DCLASS, DSK_FILE_FRAME, CORSYS, CORPAR,
        mncor1, mxcor1, mncor2, mxcor2, mncor3, mxcor3, time_start, time_end,
        vertices, triangles, spaixd, spaixi
    )
    logger.info("DSK segment written to %s", LUNAR_MODEL["dsk_path"])

    # --- Close DSK File ---
    spiceypy.dskcls(handle, True)
    logger.info("DSK file closed with compression enabled.")
