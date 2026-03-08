import numpy as np
from .io_parser import open_input_file_cui, open_batch_file
from .okada_wrapper import okada_elastic_halfspace
from .coulomb_math import calc_coulomb

def coulomb_cui(sourceFileName='test.dat', calcFunction='deformation', receiver='30/90/180', batchFileName='test.dat', parse_only=False, grid_params=None):
    """
    Python entry point for Coulomb calculations.
    """
    # Parse input file
    try:
        xvec, yvec, z, el, kode, pois, young, cdepth, fric, rstress = open_input_file_cui(sourceFileName)
    except FileNotFoundError:
        print(f"File {sourceFileName} not found.")
        return None, None
        
    # If explicit grid params are provided (e.g. from UI), override the file ones
    if grid_params:
        x_start, x_end, x_inc = grid_params['min_x'], grid_params['max_x'], grid_params['inc']
        y_start, y_end, y_inc = grid_params['min_y'], grid_params['max_y'], grid_params['inc']
        cdepth = grid_params['depth']
        
        # recreate xvec, yvec
        xvec = np.arange(x_start, x_end + x_inc, x_inc)
        yvec = np.arange(y_start, y_end + y_inc, y_inc)
    
    if parse_only:
        # Just return the faults and grid params for UI preview
        results_dict = {
            "faults": el.tolist(),
            "x": xvec.tolist(),
            "y": yvec.tolist(),
            "cdepth": cdepth
        }
        return "parsed", results_dict
        return None
        
    if calcFunction == 'deformation':
        print(f"Calculating deformation for {sourceFileName}...")
        dc3d = okada_elastic_halfspace(xvec, yvec, el, young, pois, cdepth, kode)
        fout = 'halfspace_def_out.dat'
        with open(fout, 'w') as f:
            f.write("x y z ux uy uz sxx syy szz syz sxz sxy\n")
            f.write("(km) (km) (km) (m) (m) (m) (bar) (bar) (bar) (bar) (bar) (bar)\n")
            for i in range(dc3d.shape[0]):
                # print 1:2, 5:14 (0-based: 0, 1 and 4-13)
                row = dc3d[i]
                arr = [row[0], row[1]] + list(row[4:14])
                # format string
                fmt = "".join([f"{x:10.4f}" for x in arr])
                f.write(fmt + " \n")
        print(f"Done. Wrote to {fout}")
        results_dict = {
            "x": dc3d[:, 0].tolist(),
            "y": dc3d[:, 1].tolist(),
            "z": dc3d[:, 4].tolist(),
            "ux": dc3d[:, 5].tolist(),
            "uy": dc3d[:, 6].tolist(),
            "uz": dc3d[:, 7].tolist(),
            "sxx": dc3d[:, 8].tolist(),
            "syy": dc3d[:, 9].tolist(),
            "szz": dc3d[:, 10].tolist(),
            "syz": dc3d[:, 11].tolist(),
            "sxz": dc3d[:, 12].tolist(),
            "sxy": dc3d[:, 13].tolist(),
            "faults": el.tolist()
        }
        return fout, results_dict
        
    elif calcFunction == 'coulomb':
        print(f"Calculating coulomb for {sourceFileName} at {receiver}...")
        dc3d = okada_elastic_halfspace(xvec, yvec, el, young, pois, cdepth, kode)
        
        parts = receiver.split('/')
        strike_m = float(parts[0]) * np.ones(dc3d.shape[0])
        dip_m = float(parts[1]) * np.ones(dc3d.shape[0])
        rake_m = float(parts[2]) * np.ones(dc3d.shape[0])
        friction_m = fric * np.ones(dc3d.shape[0])
        
        # passed array: ss is dc3d(:, 9:14)' -> shape (6, ncell) in MATLAB
        # python dc3d is shape (n, 14), 8-13 is stress (sxx_n to sxy_n)
        ss = dc3d[:, 8:14].T
        
        shear, normal, coulomb = calc_coulomb(strike_m, dip_m, rake_m, friction_m, ss)
        
        fout = 'coulomb_out.dat'
        with open(fout, 'w') as f:
            f.write("x y z strike dip rake shear normal coulomb\n")
            f.write("(km) (km) (km) (deg) (deg) (deg) (bar) (bar) (bar)\n")
            for i in range(dc3d.shape[0]):
                f.write(f"{dc3d[i,0]:10.4f}{dc3d[i,1]:10.4f}{dc3d[i,4]:10.4f}")
                f.write(f"{strike_m[i]:7.1f}{dip_m[i]:6.1f}{rake_m[i]:8.1f}")
                f.write(f"{shear[i]:10.4f}{normal[i]:10.4f}{coulomb[i]:10.4f} \n")
        print(f"Done. Wrote to {fout}")
        results_dict = {
            "x": dc3d[:, 0].tolist(),
            "y": dc3d[:, 1].tolist(),
            "z": dc3d[:, 4].tolist(),
            "ux": dc3d[:, 5].tolist(),
            "uy": dc3d[:, 6].tolist(),
            "uz": dc3d[:, 7].tolist(),
            "sxx": dc3d[:, 8].tolist(),
            "syy": dc3d[:, 9].tolist(),
            "szz": dc3d[:, 10].tolist(),
            "syz": dc3d[:, 11].tolist(),
            "sxz": dc3d[:, 12].tolist(),
            "sxy": dc3d[:, 13].tolist(),
            "shear": shear.tolist(),
            "normal": normal.tolist(),
            "coulomb": coulomb.tolist(),
            "faults": el.tolist()
        }
        return fout, results_dict
        
    elif calcFunction == 'batch':
        print(f"Calculating batch from {batchFileName} using {sourceFileName}...")
        try:
            pos, strike_m, dip_m, rake_m = open_batch_file(batchFileName)
        except FileNotFoundError:
            print(f"Batch file {batchFileName} not found.")
            return None
            
        x_g, y_g, z_g = pos[:, 0], pos[:, 1], pos[:, 2] # actually -z in okada
        cdepth_i = -z_g 
        
        # call okada_elastic_halfspace with all points
        res = okada_elastic_halfspace(x_g, y_g, el, young, pois, cdepth_i, kode)
        dc3d = res
        
        # res shape (n_batch, 14), ss needed shape (6, n_batch) -> 8:14 transposed
        ss = res[:, 8:14].T
        
        s, n_s, c = calc_coulomb(strike_m, dip_m, rake_m, np.full(pos.shape[0], fric), ss)
        shear = s
        normal = n_s
        coulomb = c
            
        fout = 'coulomb_out.dat'
        with open(fout, 'w') as f:
            f.write("x y z strike dip rake shear normal coulomb\n")
            f.write("(km) (km) (km) (deg) (deg) (deg) (bar) (bar) (bar)\n")
            for i in range(dc3d.shape[0]):
                f.write(f"{dc3d[i,0]:10.4f}{dc3d[i,1]:10.4f}{dc3d[i,4]:10.4f}")
                f.write(f"{strike_m[i]:7.1f}{dip_m[i]:6.1f}{rake_m[i]:8.1f}")
                f.write(f"{shear[i]:10.4f}{normal[i]:10.4f}{coulomb[i]:10.4f} \n")
        print(f"Done. Wrote to {fout}")
        results_dict = {
            "x": dc3d[:, 0].tolist(),
            "y": dc3d[:, 1].tolist(),
            "z": dc3d[:, 4].tolist(),
            "ux": dc3d[:, 5].tolist(),
            "uy": dc3d[:, 6].tolist(),
            "uz": dc3d[:, 7].tolist(),
            "sxx": dc3d[:, 8].tolist(),
            "syy": dc3d[:, 9].tolist(),
            "szz": dc3d[:, 10].tolist(),
            "syz": dc3d[:, 11].tolist(),
            "sxz": dc3d[:, 12].tolist(),
            "sxy": dc3d[:, 13].tolist(),
            "shear": shear.tolist(),
            "normal": normal.tolist(),
            "coulomb": coulomb.tolist(),
            "faults": el.tolist()
        }
        return fout, results_dict
    else:
        print("Invalid calcFunction")
        return None, None
        
if __name__ == "__main__":
    import sys
    # test defaults
    coulomb_cui()
