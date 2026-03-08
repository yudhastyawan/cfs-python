import numpy as np

def calc_coulomb(strike_m, dip_m, rake_m, friction_m, ss):
    """
    Calculates shear, normal, and Coulomb stresses on a given fault.
    strike_m, dip_m, rake_m, friction_m: 1D numpy arrays of shape (n,)
    ss: 2D numpy array of shape (6, n) [SXX, SYY, SZZ, SYZ, SXZ, SXY]
    Returns shear, normal, coulomb (each shape (n,))
    """
    n = len(strike_m)
    friction = float(friction_m[0]) if isinstance(friction_m, np.ndarray) else friction_m

    # adjustment for coordinate system from Aki & Richards
    c1 = strike_m >= 180.0
    c2 = strike_m < 180.0
    
    strike = (strike_m - 180.0) * c1 + strike_m * c2
    dip = -1.0 * dip_m * c1 + dip_m * c2
    rake_m = rake_m - 90.0
    
    c1 = rake_m <= -180.0
    c2 = rake_m > -180.0
    rake = (360.0 + rake_m) * c1 + rake_m * c2
    
    strike = np.deg2rad(strike)
    dip = np.deg2rad(dip)
    rake = np.deg2rad(rake)
    
    # Rake rotation
    rsc = -rake
    mtran = np.zeros((3, 3, n), dtype=np.float64)
    # create xrotate matrix for each n
    # rr = makehgtform('xrotate', rsc); in python:
    # [1, 0, 0; 0, cos(a), -sin(a); 0, sin(a), cos(a)]
    for i in range(n):
        c_a = np.cos(rsc[i])
        s_a = np.sin(rsc[i])
        mtran[:, :, i] = np.array([
            [1.0, 0.0, 0.0],
            [0.0, c_a, -s_a],
            [0.0, s_a, c_a]
        ])

    ver = np.pi / 2.0
    
    c1 = strike >= 0.0
    c2 = strike < 0.0
    c3 = strike <= ver
    c4 = strike > ver
    
    c24 = c2 | c4
    
    d1 = dip >= 0.0
    d2 = dip < 0.0
    
    xbeta = -1.0 * strike * d1 + (np.pi - strike) * d2
    ybeta = (np.pi - strike) * d1 + -1.0 * strike * d2
    zbeta = (ver - strike) * d1 + (-1.0 * ver - strike) * d2 * c1 * c3 + (np.pi + ver - strike) * d2 * c24
    
    xdel = ver - np.abs(dip)
    ydel = np.abs(dip)
    zdel = np.zeros(n)
    
    xl = np.cos(xdel) * np.cos(xbeta)
    xm = np.cos(xdel) * np.sin(xbeta)
    xn = np.sin(xdel)
    yl = np.cos(ydel) * np.cos(ybeta)
    ym = np.cos(ydel) * np.sin(ybeta)
    yn = np.sin(ydel)
    zl = np.cos(zdel) * np.cos(zbeta)
    zm = np.cos(zdel) * np.sin(zbeta)
    zn = np.sin(zdel)
    
    t = np.zeros((6, 6, n), dtype=np.float64)
    
    t[0, 0, :] = xl * xl
    t[0, 1, :] = xm * xm
    t[0, 2, :] = xn * xn
    t[0, 3, :] = 2.0 * xm * xn
    t[0, 4, :] = 2.0 * xn * xl
    t[0, 5, :] = 2.0 * xl * xm
    
    t[1, 0, :] = yl * yl
    t[1, 1, :] = ym * ym
    t[1, 2, :] = yn * yn
    t[1, 3, :] = 2.0 * ym * yn
    t[1, 4, :] = 2.0 * yn * yl
    t[1, 5, :] = 2.0 * yl * ym
    
    t[2, 0, :] = zl * zl
    t[2, 1, :] = zm * zm
    t[2, 2, :] = zn * zn
    t[2, 3, :] = 2.0 * zm * zn
    t[2, 4, :] = 2.0 * zn * zl
    t[2, 5, :] = 2.0 * zl * zm
    
    t[3, 0, :] = yl * zl
    t[3, 1, :] = ym * zm
    t[3, 2, :] = yn * zn
    t[3, 3, :] = ym * zn + zm * yn
    t[3, 4, :] = yn * zl + zn * yl
    t[3, 5, :] = yl * zm + zl * ym
    
    t[4, 0, :] = zl * xl
    t[4, 1, :] = zm * xm
    t[4, 2, :] = zn * xn
    t[4, 3, :] = xm * zn + zm * xn
    t[4, 4, :] = xn * zl + zn * xl
    t[4, 5, :] = xl * zm + zl * xm
    
    t[5, 0, :] = xl * yl
    t[5, 1, :] = xm * ym
    t[5, 2, :] = xn * yn
    t[5, 3, :] = xm * yn + ym * xn
    t[5, 4, :] = xn * yl + yn * xl
    t[5, 5, :] = xl * ym + yl * xm
    
    sn = np.zeros((6, n), dtype=np.float64)
    sn9 = np.zeros((3, 3, n), dtype=np.float64)
    
    for k in range(n):
        sn[:, k] = np.dot(t[:, :, k], ss[:, k])
        
        sn9[0, 0, k] = sn[0, k]
        sn9[0, 1, k] = sn[5, k]
        sn9[0, 2, k] = sn[4, k]
        
        sn9[1, 0, k] = sn[5, k]
        sn9[1, 1, k] = sn[1, k]
        sn9[1, 2, k] = sn[3, k]
        
        sn9[2, 0, k] = sn[4, k]
        sn9[2, 1, k] = sn[3, k]
        sn9[2, 2, k] = sn[2, k]
        
        sn9[:, :, k] = np.dot(sn9[:, :, k], mtran[:, :, k])
        
    shear = sn9[0, 1, :]
    normal = sn9[0, 0, :]
    coulomb = shear + friction * normal
    
    return shear, normal, coulomb
