import re
import numpy as np

def open_input_file_cui(filename):
    """
    Parses a Coulomb 3.3 format text file.
    Returns: xvec, yvec, z, el, kode, pois, young, cdepth, fric, rstress
    """
    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        
    num = 0
    pois = 0.25
    cdepth = 7.5
    young = 8e5
    fric = 0.4
    rstress = [0.0, 0.0, 0.0]
    
    grid = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]  # xstart, ystart, xend, yend, xinc, yinc
    map_info = {}
    cross_section = {}
    
    in_fault_elements = False
    in_grid_params = False
    faults = []
    
    for i, line in enumerate(lines):
        # We need to read PR1, YOUNG'S, FRIC. COEFFICIENT, SIGMA1-SIGMA3, Grid parameters
        up_line = line.upper()
        
        if "PR1=" in up_line:
            parts = line.split()
            try:
                pois = float(parts[1])
                cdepth = float(parts[5])
            except: pass
                
        if "YOUNG'S MODULUS" in up_line:
            try: young = float(line.split()[0])
            except: pass
            
        if "FRIC. COEFFICIENT" in up_line:
            try: fric = float(line.split()[0])
            except: pass
            
        if "SIGMA1-SIGMA3" in up_line:
            floats = [float(s) for s in re.findall(r'-?\d+\.?\d*', line)]
            if len(floats) >= 3:
                rstress = floats[:3]
                
        if "X-START" in up_line:
            in_grid_params = True
            
        if "XXX" in up_line:
            in_fault_elements = not in_fault_elements
            continue

        if in_fault_elements:
            parts = line.split()
            if len(parts) >= 11:
                try:
                    xs, ys, xf, yf = map(float, parts[1:5])
                    kode = int(parts[5])
                    
                    if "RAKE" in " ".join(lines).upper():
                        rake, netslip, dip, top, bottom = map(float, parts[6:11])
                        latslip = np.cos(np.deg2rad(rake)) * netslip * -1.0
                        dipslip = np.sin(np.deg2rad(rake)) * netslip
                    else:
                        latslip, dipslip, dip, top, bottom = map(float, parts[6:11])
                        
                    faults.append([xs, ys, xf, yf, latslip, dipslip, dip, top, bottom, kode])
                except ValueError:
                    pass

        # reading grid info
        if "CROSS SECTION DEFAULT" in up_line:
            in_grid_params = False
            in_fault_elements = False
            continue
        elif "MAP INFO" in up_line:
            in_grid_params = False
            in_fault_elements = False
            continue

        if in_grid_params and "=" in line:
            parts = line.split("=")
            if len(parts) == 2:
                try:
                    val = float(parts[1].split()[0])
                    if "X-start" in up_line: grid[0] = val
                    elif "Y-start" in up_line: grid[1] = val
                    elif "X-finish" in up_line: grid[2] = val
                    elif "Y-finish" in up_line: grid[3] = val
                    elif "X-inc" in up_line: grid[4] = val
                    elif "Y-inc" in up_line:
                        grid[5] = val
                        in_grid_params = False
                except:
                    pass

        # We can just look for specific keywords for map info and cross section
        if "=" in line:
            parts = line.split("=")
            if len(parts) == 2:
                try:
                    val = float(parts[1].split()[0])
                    # Cross section
                    if "START-X" in up_line and "DEFAULT" not in up_line and not in_grid_params: cross_section["start_x"] = val
                    elif "START-Y" in up_line and not in_grid_params: cross_section["start_y"] = val
                    elif "FINISH-X" in up_line and not in_grid_params: cross_section["finish_x"] = val
                    elif "FINISH-Y" in up_line and not in_grid_params: cross_section["finish_y"] = val
                    
                    # Map Info
                    elif "MIN. LON" in up_line: map_info["min_lon"] = val
                    elif "MAX. LON" in up_line: map_info["max_lon"] = val
                    elif "ZERO LON" in up_line: map_info["zero_lon"] = val
                    elif "MIN. LAT" in up_line: map_info["min_lat"] = val
                    elif "MAX. LAT" in up_line: map_info["max_lat"] = val
                    elif "ZERO LAT" in up_line: map_info["zero_lat"] = val
                except:
                    pass

    if len(faults) == 0:
        raise ValueError("No valid faults found in the input file.")
        
    faults = np.array(faults)
    el = faults[:, :9]
    kode = faults[:, 9].astype(int)
    
    # safeguard grid increments to prevent memory error
    xin = max(grid[4], 0.001)
    yin = max(grid[5], 0.001)
    
    xvec = np.arange(grid[0], grid[2] + xin*0.5, xin)
    yvec = np.arange(grid[1], grid[3] + yin*0.5, yin)
    z = cdepth

    # Default missing map info to 0.0
    for k in ["min_lon", "max_lon", "zero_lon", "min_lat", "max_lat", "zero_lat"]:
        if k not in map_info:
            map_info[k] = 0.0

    return xvec, yvec, z, el, kode, pois, young, cdepth, fric, rstress, map_info, cross_section


def open_batch_file(filename):
    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        
    data = []
    for line in lines[2:]:
        parts = line.split()
        if len(parts) >= 6:
            try:
                data.append([float(x) for x in parts[:6]])
            except: pass
            
    data = np.array(data)
    pos = data[:, :3]
    strike = data[:, 3]
    dip = data[:, 4]
    rake = data[:, 5]
    
    return pos, strike, dip, rake
