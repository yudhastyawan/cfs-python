import numpy as np
from .okada_math import coord_conversion, tensor_trans, okada_dc3d, okada_dc3d0

def okada_elastic_halfspace(xgrid, ygrid, element, young, pois, calcdepth, kode):
    """
    Python equivalent of okada_elastic_halfspace.m
    xgrid, ygrid: 1D numpy arrays of grid coordinates
    element: 2D numpy array of fault elements. Shape (num_faults, M)
             (el: xs, ys, xf, yf, latslip, dipslip, dip, top, bottom)
    young: Young's modulus
    pois: Poisson's ratio
    calcdepth: Calculation depth (km, positive)
    kode: array/list of calculation types (e.g., 100 for rectangular)
    """
    alpha = 1.0 / (2.0 * (1.0 - pois))
    
    if np.isscalar(xgrid) or xgrid.size == 1:
        ncell = 1
        xgrid = np.array([xgrid]).flatten()
        ygrid = np.array([ygrid]).flatten()
    else:
        # Check if xgrid and ygrid are 1D arrays creating a meshgrid,
        # or if they are already parallel arrays (from batch)?
        # Let's assume if they are exactly the same size, they could be a meshgrid OR a 1D parallel list.
        # Wait, if it's a batch file, xgrid, ygrid, calcdepth are parallel 1D lists.
        # But for deformation mesh grids, xv, yv = np.meshgrid(xgrid, ygrid) creates len(x)*len(y).
        pass

    # Better logic: if calcdepth is an array of same size as xgrid, we use parallel 1D computation.
    is_parallel_1d = False
    if isinstance(calcdepth, np.ndarray) and calcdepth.shape == xgrid.shape and xgrid.ndim == 1:
        is_parallel_1d = True

    if is_parallel_1d:
        ncell = len(xgrid)
        xycoord = np.zeros((ncell, 2), dtype=np.float64)
        xycoord[:, 0] = xgrid
        xycoord[:, 1] = ygrid
        zd = calcdepth * (-1.0)
    else:
        ncell = len(xgrid) * len(ygrid) if not (np.isscalar(xgrid) or xgrid.size == 1) else 1
        xycoord = np.zeros((ncell, 2), dtype=np.float64)
        xv, yv = np.meshgrid(xgrid, ygrid, indexing='ij') if ncell > 1 else (xgrid, ygrid)
        if ncell > 1:
            xycoord[:, 0] = xv.flatten()
            xycoord[:, 1] = yv.flatten()
        else:
            xycoord[:, 0] = xgrid
            xycoord[:, 1] = ygrid
        zd = np.full(ncell, calcdepth * (-1.0), dtype=np.float64)

    dc3d_out = np.zeros((ncell, 14), dtype=np.float64)
    
    for i in range(element.shape[0]):
        depth = (element[i, 7] + element[i, 8]) / 2.0  # depth is positive (top+bottom)/2
        c1, c2, c3, c4 = coord_conversion(
            xycoord[:, 0], xycoord[:, 1],
            element[i, 0], element[i, 1],
            element[i, 2], element[i, 3],
            element[i, 7], element[i, 8],
            element[i, 6]
        )
        
        aa = np.full(ncell, alpha, dtype=np.float64)
        zz = zd  # already array of length ncell
        dp = np.full(ncell, depth, dtype=np.float64)
        e7 = np.full(ncell, element[i, 6], dtype=np.float64)
        x = c1.astype(np.float64)
        y = c2.astype(np.float64)
        al = c3.astype(np.float64)
        
        # Determine kode for this element
        kd = kode[i] if isinstance(kode, (list, np.ndarray)) else kode
        
        if kd == 400:
            aw = np.full(ncell, -element[i, 4], dtype=np.float64)
            e5 = np.full(ncell, element[i, 5], dtype=np.float64)
            e6 = np.zeros(ncell, dtype=np.float64)
            zr = np.zeros(ncell, dtype=np.float64)
            
            ux, uy, uz, uxx, uyx, uzx, uxy, uyy, uzy, uxz, uyz, uzz, iret = okada_dc3d0(
                aa[0], x, y, zz, dp, e7, aw, e5, e6, zr
            )
        elif kd == 100:
            aw = c4.astype(np.float64)
            e5 = np.full(ncell, -element[i, 4], dtype=np.float64)  # left-lat positive in Okada
            e6 = np.full(ncell, element[i, 5], dtype=np.float64)
            zr = np.zeros(ncell, dtype=np.float64)
            
            ux, uy, uz, uxx, uyx, uzx, uxy, uyy, uzy, uxz, uyz, uzz, iret = okada_dc3d(
                aa[0], x, y, zz, dp, e7, al, al, aw, aw, e5, e6, zr
            )
        else:
            continue
            
        # Displacement Conversion
        sw = np.sqrt((element[i, 3] - element[i, 1])**2 + (element[i, 2] - element[i, 0])**2)
        sina = (element[i, 3] - element[i, 1]) / float(sw)
        cosa = (element[i, 2] - element[i, 0]) / float(sw)
        
        uxg = ux * cosa - uy * sina
        uyg = ux * sina + uy * cosa
        uzg = uz
        
        # Strain to stress
        sk = young / (1.0 + pois)
        gk = pois / (1.0 - 2.0 * pois)
        vol = uxx + uyy + uzz
        
        # Strain dimension is / 1000
        sxx = sk * (gk * vol + uxx) * 0.001
        syy = sk * (gk * vol + uyy) * 0.001
        szz = sk * (gk * vol + uzz) * 0.001
        sxy = (young / (2.0 * (1.0 + pois))) * (uxy + uyx) * 0.001
        sxz = (young / (2.0 * (1.0 + pois))) * (uxz + uzx) * 0.001
        syz = (young / (2.0 * (1.0 + pois))) * (uyz + uzy) * 0.001
        
        s0 = np.array([sxx, syy, szz, syz, sxz, sxy])  # shape (6, ncell)
        
        # Strain Conversion
        s1 = tensor_trans(sina, cosa, s0)
        
        sxx_n = s1[0, :]
        syy_n = s1[1, :]
        szz_n = s1[2, :]
        syz_n = s1[3, :]
        sxz_n = s1[4, :]
        sxy_n = s1[5, :]
        
        dc3d0_arr = np.column_stack([
            xycoord[:, 0], xycoord[:, 1], x, y, zz,
            uxg, uyg, uzg, sxx_n, syy_n, szz_n, syz_n, sxz_n, sxy_n
        ])
        
        if i == 0:
            dc3d0_final = np.column_stack([
                xycoord[:, 0], xycoord[:, 1], x, y, zz,
                uxg, uyg, uzg, sxx_n, syy_n, szz_n, syz_n, sxz_n, sxy_n
            ])
        else:
            dc3d0_final = np.column_stack([
                np.zeros(ncell), np.zeros(ncell), np.zeros(ncell), np.zeros(ncell), np.zeros(ncell),
                uxg, uyg, uzg, sxx_n, syy_n, szz_n, syz_n, sxz_n, sxy_n
            ])
            
        dc3d_out += dc3d0_final

    return dc3d_out
