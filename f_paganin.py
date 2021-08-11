from __future__ import (absolute_import, division, print_function, unicode_literals)
import numpy as np
from tomopy.util.misc import (fft2, ifft2)
import tomopy.util.mproc as mproc
import logging
logger = logging.getLogger(__name__)

BOLTZMANN_CONSTANT = 1.3806488e-16  # [erg/k]
SPEED_OF_LIGHT = 299792458e+2  # [cm/s]
PI = 3.14159265359
PLANCK_CONSTANT = 6.58211928e-19  # [keV*s]

def retrieve_phase(tomo, pixel_size=1e-4, dist=50, energy=20, alpha=1e-3,
    pad=True, ncore=None, nchunk=None):
    wavelength = 2 * PI * PLANCK_CONSTANT * SPEED_OF_LIGHT / energy
    # get dimensions of projections as an ndarray
    dx, dy, dz = tomo.shape

    # New dimensions and pad value after padding
    py, pz, val = 0, 0, 0 
    # Calculate new dimensions and pad value after padding
    pad_pix = np.ceil(PI * wavelength * dist / pixel_size ** 2)
    if pad:
        py = int((pow(2, np.ceil(np.log2(dy + pad_pix))) - dy) * 0.5)
        pz = int((pow(2, np.ceil(np.log2(dz + pad_pix))) - dz) * 0.5)
        val = np.mean((tomo[..., 0] + tomo[..., -1]) * 0.5)

    # Compute the reciprocal coordinates y
    ny = dy + 2 * py
    n = ny - 1
    indy = np.arange(-n, ny, 2, dtype = np.float32)
    indy *= 0.5 / (n * pixel_size)
    np.square(indy, out=indy)
    
    # Compute the reciprocal coordinates z
    nz = dz + 2 * pz
    n = nz - 1
    indz = np.arange(-n, nz, 2, dtype = np.float32)
    indz *= 0.5 / (n * pixel_size)
    np.square(indz, out=indz)

    # Compute the reciprocal grid
    w2 = np.add.outer(indy, indz)

    # Filter in Fourier space
    phase_filter = np.fft.fftshift(1 / (wavelength * dist * w2 / (4 * PI) + alpha))
    prj = np.full((dy + 2 * py, dz + 2 * pz), val, dtype='float32')

    # Normalize phase filter
    normalized_phase_filter = phase_filter / phase_filter.max()

    # Perform phase retrieval
    for m in range(dx):
        prj[py:dy + py, pz:dz + pz] = tomo[m]
        prj[:py] = prj[py]
        prj[-py:] = prj[-py-1]
        prj[:, :pz] = prj[:, pz][:, np.newaxis]
        prj[:, -pz:] = prj[:, -pz-1][:, np.newaxis]
        fproj = fft2(prj, extra_info=dx)
        fproj *= normalized_phase_filter
        proj = np.real(ifft2(fproj, extra_info=dx, overwrite_input=True))
        if pad:
            proj = proj[py:dy + py, pz:dz + pz]
        tomo[m] = proj

    return tomo