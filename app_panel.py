"""
Coulomb Stress Change – Interactive Panel Dashboard
====================================================
Run with:  panel serve app_panel.py --show
"""
import io, os, tempfile
import numpy as np
import pandas as pd
import panel as pn
import plotly.graph_objects as go
import geopandas as gpd
from shapely.geometry import Point
import rasterio
from rasterio.transform import from_bounds

from cfs_lib.io_parser import open_input_file_cui, open_batch_file
from cfs_lib.okada_wrapper import okada_elastic_halfspace
from cfs_lib.coulomb_math import calc_coulomb

pn.extension("plotly", sizing_mode="stretch_width", theme="dark")
os.makedirs("cache", exist_ok=True)

# =====================================================================
# STATE
# =====================================================================
STATE = {
    "el": None,           # fault elements (n, 9)
    "kode": None,
    "pois": 0.25,
    "young": 8e5,
    "fric": 0.4,
    "cdepth": 5.0,
    "xvec": None,         # 1-D grid vectors
    "yvec": None,
    "dc3d": None,         # full output (ncell, 14)
    "shear": None,
    "normal_stress": None,
    "coulomb_stress": None,
    "nx": 0,
    "ny": 0,
    "xsec_data": None,    # Store cross-section dataframe for download
    "click_state": "A",   # Which point (A or B) to set next on map click
}

# =====================================================================
# WIDGETS – Sidebar
# =====================================================================
file_input  = pn.widgets.FileInput(name="Source file (.inp)", accept=".inp,.dat", multiple=False)
batch_input = pn.widgets.FileInput(name="Batch / Single-point file (.dat)", accept=".dat,.txt", multiple=False)

calc_mode = pn.widgets.Select(
    name="Calculation Mode",
    options={
        "Grid – Coulomb Stress": "coulomb",
        "Grid – Deformation":    "deformation",
        "Batch (file-based)":    "batch",
        "Single Target Point":   "single",
    },
    value="coulomb",
)

# Grid limits
grid_xmin  = pn.widgets.FloatInput(name="X min (km)",  value=-50., step=1.)
grid_xmax  = pn.widgets.FloatInput(name="X max (km)",  value=50.,  step=1.)
grid_ymin  = pn.widgets.FloatInput(name="Y min (km)",  value=-50., step=1.)
grid_ymax  = pn.widgets.FloatInput(name="Y max (km)",  value=50.,  step=1.)
grid_inc   = pn.widgets.FloatInput(name="Spacing (km)", value=5.,  step=0.1, start=0.1)
grid_depth = pn.widgets.FloatInput(name="Depth (km)",   value=5.,  step=0.1)

# Receiver angles
rec_strike = pn.widgets.FloatInput(name="R. Strike (°)", value=30.)
rec_dip    = pn.widgets.FloatInput(name="R. Dip (°)",    value=90.)
rec_rake   = pn.widgets.FloatInput(name="R. Rake (°)",   value=180.)

# Single point
sp_x      = pn.widgets.FloatInput(name="X (km)",      value=0.)
sp_y      = pn.widgets.FloatInput(name="Y (km)",      value=0.)
sp_z      = pn.widgets.FloatInput(name="Z (km)",      value=5.)
sp_strike = pn.widgets.FloatInput(name="Strike (°)",   value=30.)
sp_dip    = pn.widgets.FloatInput(name="Dip (°)",      value=90.)
sp_rake   = pn.widgets.FloatInput(name="Rake (°)",     value=180.)

run_btn   = pn.widgets.Button(name="▶ Run Calculation", button_type="primary",
                              sizing_mode="stretch_width")
status_md = pn.pane.Markdown("**Status:** waiting for input file",
                             styles={"color": "#999"})

# =====================================================================
# DISPLAY WIDGETS – Main area
# =====================================================================
VAR_OPTIONS = ["ux", "uy", "uz",
               "sxx", "syy", "szz", "sxy", "sxz", "syz",
               "shear", "normal", "coulomb"]
COLORSCALES = [
    "Jet", "Viridis", "Plasma", "Inferno", "Rainbow", "Cividis",
    "balance", "RdBu", "PiYG", "PRGn", "BrBG", "PuOr"
]

plot_var   = pn.widgets.Select(name="Plot variable", options=VAR_OPTIONS, value="coulomb")
map_cmap   = pn.widgets.Select(name="Color Map", options=COLORSCALES, value="Jet", width=120)
map_vmin   = pn.widgets.FloatInput(name="Min value", value=None, width=100)
map_vmax   = pn.widgets.FloatInput(name="Max value", value=None, width=100)
toggle_3d  = pn.widgets.Checkbox(name="3D view", value=False)
refresh_btn = pn.widgets.Button(name="🔄 Refresh Map", button_type="warning", width=150)

map_pane   = pn.pane.Plotly(go.Figure(), height=650, sizing_mode="stretch_width")

# --- Cross-section widgets ---
xsec_ax   = pn.widgets.FloatInput(name="A → X", value=-30., step=1.)
xsec_ay   = pn.widgets.FloatInput(name="A → Y", value=0.,   step=1.)
xsec_bx   = pn.widgets.FloatInput(name="B → X", value=30.,  step=1.)
xsec_by   = pn.widgets.FloatInput(name="B → Y", value=0.,   step=1.)
xsec_zmin = pn.widgets.FloatInput(name="Depth min (km)", value=0.,  step=0.5)
xsec_zmax = pn.widgets.FloatInput(name="Depth max (km)", value=20., step=0.5)
xsec_zinc = pn.widgets.FloatInput(name="Depth step (km)", value=1., step=0.1, start=0.1)
xsec_npts = pn.widgets.IntInput(name="Points along line", value=50, step=5, start=5)
xsec_var  = pn.widgets.Select(name="X-sec variable", options=VAR_OPTIONS, value="coulomb")
xsec_btn  = pn.widgets.Button(name="▶ Compute Cross-Section", button_type="success",
                               sizing_mode="stretch_width")
xsec_cmap = pn.widgets.Select(name="Color Map", options=COLORSCALES, value="Jet", width=120)
xsec_vmin = pn.widgets.FloatInput(name="Min value", value=None, width=100)
xsec_vmax = pn.widgets.FloatInput(name="Max value", value=None, width=100)                               

xsec_pane = pn.pane.Plotly(go.Figure(), height=500, sizing_mode="stretch_width")
xsec_status = pn.pane.Markdown("")
xsec_download = pn.widgets.FileDownload(
    label="⬇️ Download X-Sec Data (.csv)",
    filename="cross_section.csv",
    button_type="primary"
)

# Table
table_pane = pn.pane.DataFrame(pd.DataFrame(), sizing_mode="stretch_width",
                               max_rows=200, height=500)

coord_sys = pn.widgets.RadioBoxGroup(name="Coordinate System", options=["Local (km)", "Lat/Lon"], value="Local (km)", inline=True)
save_format = pn.widgets.Select(name="Save Format", options=["CSV", "SHP", "TIF"], value="CSV", width=100)
save_crs = pn.widgets.Select(name="Save Map CRS", options=["Local (km)", "Lat/Lon"], value="Local (km)", width=100)

map_download = pn.widgets.FileDownload(
    label="⬇️ Download Map Data",
    filename="coulomb_out.csv",
    button_type="success"
)

# =====================================================================
# HELPERS
# =====================================================================
def _save_upload(widget, prefix=""):
    if widget.value is None:
        return None
    path = os.path.join("cache", prefix + widget.filename)
    with open(path, "wb") as f:
        f.write(widget.value)
    return path

def _set_status(msg, error=False):
    color = "red" if error else "#4fc3f7"
    status_md.object = f"**Status:** <span style='color:{color}'>{msg}</span>"

COL_MAP = {"ux": 5, "uy": 6, "uz": 7,
           "sxx": 8, "syy": 9, "szz": 10,
           "syz": 11, "sxz": 12, "sxy": 13}

def _get_vals(var, dc3d=None, shear=None, normal=None, coulomb=None):
    """Return a 1-D array of the chosen variable from dc3d / stress arrays."""
    if dc3d is None:
        return None
    if var in COL_MAP:
        return dc3d[:, COL_MAP[var]]
    elif var == "shear" and shear is not None:
        return shear
    elif var == "normal" and normal is not None:
        return normal
    elif var == "coulomb" and coulomb is not None:
        return coulomb
    return dc3d[:, 5]  # fallback ux


def _draw_faults_2d(fig, el):
    if el is None:
        return
    for i, f in enumerate(el):
        fig.add_trace(go.Scatter(
            x=[f[0], f[2]], y=[f[1], f[3]],
            mode="lines+markers",
            line=dict(color="red", width=3),
            marker=dict(size=5, color="red"),
            name=f"Fault {i}",
            showlegend=(i == 0),
            legendgroup="faults",
        ))

def _draw_faults_3d(fig, el):
    if el is None:
        return
    for i, f in enumerate(el):
        xs, ys, xf, yf = f[0], f[1], f[2], f[3]
        dip = f[6]; top, bot = f[7], f[8]
        dip_rad = np.radians(dip)
        h = (bot - top) / np.tan(dip_rad) if abs(dip) != 90 else 0
        dx, dy = xf - xs, yf - ys
        length = np.sqrt(dx**2 + dy**2)
        if length == 0:
            continue
        nx_v, ny_v = dy / length, -dx / length
        xsb, ysb = xs + nx_v * h, ys + ny_v * h
        xfb, yfb = xf + nx_v * h, yf + ny_v * h
        fig.add_trace(go.Scatter3d(
            x=[xs, xf, xfb, xsb, xs],
            y=[ys, yf, yfb, ysb, ys],
            z=[top, top, bot, bot, top],
            mode="lines",
            line=dict(color="red", width=5),
            name=f"Fault {i}",
            showlegend=(i == 0),
            legendgroup="faults",
        ))

def km_to_deg(dx_km, dy_km, lon0, lat0):
    """Convert local dx/dy (km) to lat/lon based on reference point."""
    lat = lat0 + (dy_km / 111.32)
    # 1 degree of longitude = 111.32 * cos(lat0) km
    lon_deg_per_km = 1.0 / (111.32 * np.cos(np.radians(lat0))) if np.abs(lat0) < 89 else 0
    lon = lon0 + (dx_km * lon_deg_per_km)
    return lon, lat

def deg_to_km(lon, lat, lon0, lat0):
    """Convert lat/lon to local dx/dy (km) based on reference point."""
    dy_km = (lat - lat0) * 111.32
    dx_km = (lon - lon0) * (111.32 * np.cos(np.radians(lat0)))
    return dx_km, dy_km

def _on_coord_sys_change(event):
    is_latlon = (event.new == "Lat/Lon")
    map_info = STATE.get("map_info", {})
    lon0 = map_info.get("zero_lon", 0.0)
    lat0 = map_info.get("zero_lat", 0.0)
    
    # Update widget names
    unit = "°" if is_latlon else "km"
    grid_xmin.name = f"X min ({unit})"
    grid_xmax.name = f"X max ({unit})"
    grid_ymin.name = f"Y min ({unit})"
    grid_ymax.name = f"Y max ({unit})"
    grid_inc.name  = f"Spacing ({unit})"
    xsec_ax.name   = f"A → X ({unit})"
    xsec_ay.name   = f"A → Y ({unit})"
    xsec_bx.name   = f"B → X ({unit})"
    xsec_by.name   = f"B → Y ({unit})"
    sp_x.name      = f"X ({unit})"
    sp_y.name      = f"Y ({unit})"
    
    # Simple conversion of current values
    if lon0 != 0.0 or lat0 != 0.0:
        if is_latlon:
            # Convert km -> deg
            grid_xmin.value, grid_ymin.value = km_to_deg(grid_xmin.value, grid_ymin.value, lon0, lat0)
            grid_xmax.value, grid_ymax.value = km_to_deg(grid_xmax.value, grid_ymax.value, lon0, lat0)
            grid_inc.value = grid_inc.value / 111.32  # Rough spacing
            xsec_ax.value, xsec_ay.value = km_to_deg(xsec_ax.value, xsec_ay.value, lon0, lat0)
            xsec_bx.value, xsec_by.value = km_to_deg(xsec_bx.value, xsec_by.value, lon0, lat0)
            sp_x.value, sp_y.value = km_to_deg(sp_x.value, sp_y.value, lon0, lat0)
        else:
            # Convert deg -> km
            grid_xmin.value, grid_ymin.value = deg_to_km(grid_xmin.value, grid_ymin.value, lon0, lat0)
            grid_xmax.value, grid_ymax.value = deg_to_km(grid_xmax.value, grid_ymax.value, lon0, lat0)
            grid_inc.value = grid_inc.value * 111.32
            xsec_ax.value, xsec_ay.value = deg_to_km(xsec_ax.value, xsec_ay.value, lon0, lat0)
            xsec_bx.value, xsec_by.value = deg_to_km(xsec_bx.value, xsec_by.value, lon0, lat0)
            sp_x.value, sp_y.value = deg_to_km(sp_x.value, sp_y.value, lon0, lat0)

coord_sys.param.watch(_on_coord_sys_change, "value")

# =====================================================================
# CORE – parse source file on upload
# =====================================================================
def _on_file_upload(event):
    path = _save_upload(file_input)
    if path is None:
        return
    try:
        xvec, yvec, z, el, kode, pois, young, cdepth, fric, _, map_info, cross_section = open_input_file_cui(path)
    except Exception as exc:
        import traceback; traceback.print_exc()
        _set_status(f"Parse error: {exc}", error=True)
        return

    STATE.update(el=el, kode=kode, pois=pois, young=young,
                 fric=fric, cdepth=cdepth, xvec=xvec, yvec=yvec,
                 dc3d=None, shear=None, normal_stress=None, coulomb_stress=None,
                 map_info=map_info)

    # Force Local (km) when new file loads
    coord_sys.value = "Local (km)"
    grid_xmin.name = "X min (km)"
    grid_xmax.name = "X max (km)"
    grid_ymin.name = "Y min (km)"
    grid_ymax.name = "Y max (km)"
    grid_inc.name  = "Spacing (km)"

    grid_xmin.value = float(xvec[0])
    grid_xmax.value = float(xvec[-1])
    grid_ymin.value = float(yvec[0])
    grid_ymax.value = float(yvec[-1])
    if len(xvec) > 1:
        grid_inc.value = float(xvec[1] - xvec[0])
    grid_depth.value = float(cdepth)
    
    # Load default cross section if available
    if cross_section:
        if "start_x" in cross_section: xsec_ax.value = float(cross_section["start_x"])
        if "start_y" in cross_section: xsec_ay.value = float(cross_section["start_y"])
        if "finish_x" in cross_section: xsec_bx.value = float(cross_section["finish_x"])
        if "finish_y" in cross_section: xsec_by.value = float(cross_section["finish_y"])

    _set_status(f"Parsed {len(el)} fault segments from {file_input.filename}")
    _refresh_map()

file_input.param.watch(_on_file_upload, "value")

# =====================================================================
# CORE – run calculation
# =====================================================================
def _on_run(event):
    if STATE["el"] is None:
        _set_status("Upload a source file first.", error=True)
        return

    mode  = calc_mode.value
    el    = STATE["el"]
    kode  = STATE["kode"]
    pois  = STATE["pois"]
    young = STATE["young"]
    fric  = STATE["fric"]

    _set_status("Computing … please wait")

    try:
        is_latlon = (coord_sys.value == "Lat/Lon")
        map_info = STATE.get("map_info") or {}
        lon0 = map_info.get("zero_lon", 0.0) if map_info else 0.0
        lat0 = map_info.get("zero_lat", 0.0) if map_info else 0.0

        if mode in ("coulomb", "deformation"):
            xvec_in = np.arange(grid_xmin.value,
                             grid_xmax.value + grid_inc.value * 0.5,
                             grid_inc.value)
            yvec_in = np.arange(grid_ymin.value,
                             grid_ymax.value + grid_inc.value * 0.5,
                             grid_inc.value)
            cdepth = grid_depth.value

            if is_latlon and (lon0 != 0.0 or lat0 != 0.0):
                xvec_km, _ = deg_to_km(xvec_in, np.full_like(xvec_in, lat0), lon0, lat0)
                _, yvec_km = deg_to_km(np.full_like(yvec_in, lon0), yvec_in, lon0, lat0)
                xvec, yvec = xvec_km, yvec_km
            else:
                xvec, yvec = xvec_in, yvec_in

            STATE["xvec"]   = xvec
            STATE["yvec"]   = yvec
            STATE["cdepth"] = cdepth
            STATE["nx"]     = len(xvec)
            STATE["ny"]     = len(yvec)

            dc3d = okada_elastic_halfspace(xvec, yvec, el, young, pois, cdepth, kode)
            STATE["dc3d"] = dc3d

            if mode == "coulomb":
                n = dc3d.shape[0]
                ss = dc3d[:, 8:14].T
                s, nt, c = calc_coulomb(
                    rec_strike.value * np.ones(n),
                    rec_dip.value    * np.ones(n),
                    rec_rake.value   * np.ones(n),
                    fric * np.ones(n), ss)
                STATE["shear"]          = s
                STATE["normal_stress"]  = nt
                STATE["coulomb_stress"] = c
            else:
                STATE["shear"] = STATE["normal_stress"] = STATE["coulomb_stress"] = None

        elif mode == "batch":
            bpath = _save_upload(batch_input, prefix="batch_")
            if bpath is None:
                _set_status("Upload a batch file", error=True)
                return
            pos, strike_m, dip_m, rake_m = open_batch_file(bpath)
            x_g, y_g, z_g = pos[:, 0], pos[:, 1], pos[:, 2]
            
            if is_latlon and (lon0 != 0.0 or lat0 != 0.0):
                x_g, y_g = deg_to_km(x_g, y_g, lon0, lat0)
                
            dc3d = okada_elastic_halfspace(x_g, y_g, el, young, pois, -z_g, kode)
            STATE["dc3d"] = dc3d
            STATE["nx"] = STATE["ny"] = 0
            ss = dc3d[:, 8:14].T
            s, nt, c = calc_coulomb(strike_m, dip_m, rake_m,
                                    np.full(pos.shape[0], fric), ss)
            STATE["shear"]          = s
            STATE["normal_stress"]  = nt
            STATE["coulomb_stress"] = c

        elif mode == "single":
            if is_latlon and (lon0 != 0.0 or lat0 != 0.0):
                x_km, y_km = deg_to_km(np.array([sp_x.value]), np.array([sp_y.value]), lon0, lat0)
                x_g, y_g = x_km, y_km
            else:
                x_g = np.array([sp_x.value])
                y_g = np.array([sp_y.value])
            z_g = np.array([sp_z.value])
            dc3d = okada_elastic_halfspace(x_g, y_g, el, young, pois, -z_g, kode)
            STATE["dc3d"] = dc3d
            STATE["nx"] = STATE["ny"] = 0
            ss = dc3d[:, 8:14].T
            s, nt, c = calc_coulomb(
                np.array([sp_strike.value]),
                np.array([sp_dip.value]),
                np.array([sp_rake.value]),
                np.full(1, fric), ss)
            STATE["shear"]          = s
            STATE["normal_stress"]  = nt
            STATE["coulomb_stress"] = c

        _set_status(f"Done – {dc3d.shape[0]} points computed")
        _refresh_map()
        _refresh_table()
        _update_map_download()

    except Exception as exc:
        import traceback; traceback.print_exc()
        _set_status(f"Error: {exc}", error=True)

run_btn.on_click(_on_run)

# =====================================================================
# MAP RENDER
# =====================================================================
def _refresh_map(*_):
    fig = go.Figure()
    dc3d = STATE.get("dc3d")
    el   = STATE.get("el")
    is3d = toggle_3d.value
    is_latlon = (coord_sys.value == "Lat/Lon")
    
    map_info = STATE.get("map_info", {})
    lon0 = map_info.get("zero_lon", 0.0)
    lat0 = map_info.get("zero_lat", 0.0)
    
    def _convert_pts(xs, ys):
        if is_latlon and (lon0 != 0.0 or lat0 != 0.0):
            return km_to_deg(np.array(xs), np.array(ys), lon0, lat0)
        return xs, ys

    # ---- faults ----
    if is3d:
        if el is not None:
            for i, f in enumerate(el):
                xs, ys, xf, yf = f[0], f[1], f[2], f[3]
                dip = f[6]; top, bot = f[7], f[8]
                dip_rad = np.radians(dip)
                h = (bot - top) / np.tan(dip_rad) if abs(dip) != 90 else 0
                dx, dy = xf - xs, yf - ys
                length = np.sqrt(dx**2 + dy**2)
                if length > 0:
                    nx_v, ny_v = dy / length, -dx / length
                    xsb, ysb = xs + nx_v * h, ys + ny_v * h
                    xfb, yfb = xf + nx_v * h, yf + ny_v * h
                    
                    px, py = _convert_pts([xs, xf, xfb, xsb, xs], [ys, yf, yfb, ysb, ys])
                    fig.add_trace(go.Scatter3d(
                        x=px, y=py, z=[top, top, bot, bot, top],
                        mode="lines", line=dict(color="red", width=5),
                        name=f"Fault {i}", showlegend=(i==0), legendgroup="faults"
                    ))
    else:
        if el is not None:
            for i, f in enumerate(el):
                px, py = _convert_pts([f[0], f[2]], [f[1], f[3]])
                fig.add_trace(go.Scatter(
                    x=px, y=py, mode="lines+markers",
                    line=dict(color="red", width=3), marker=dict(size=5, color="red"),
                    name=f"Fault {i}", showlegend=(i==0), legendgroup="faults"
                ))

    # ---- computed data ----
    if dc3d is not None:
        vals = _get_vals(plot_var.value, dc3d,
                         STATE["shear"], STATE["normal_stress"],
                         STATE["coulomb_stress"])
        nx, ny = STATE["nx"], STATE["ny"]
        is_grid = nx > 1 and ny > 1

        px, py = _convert_pts(dc3d[:, 0], dc3d[:, 1])

        if is_grid and not is3d:
            xvec = STATE["xvec"]
            yvec = STATE["yvec"]
            vx, vy = _convert_pts(xvec, yvec)
            
            Z = np.array(vals).reshape(nx, ny).T   # (ny, nx) for Plotly Heatmap
            
            kwargs = {}
            if map_vmin.value is not None: kwargs["zmin"] = map_vmin.value
            if map_vmax.value is not None: kwargs["zmax"] = map_vmax.value
            
            fig.add_trace(go.Heatmap(
                x=vx, y=vy, z=Z,
                colorscale=map_cmap.value,
                colorbar=dict(title=plot_var.value.upper()),
                **kwargs
            ))
        elif is3d:
            marker_args = dict(size=3, color=vals, colorscale=map_cmap.value,
                               showscale=True, colorbar=dict(title=plot_var.value.upper()))
            if map_vmin.value is not None: marker_args["cmin"] = map_vmin.value
            if map_vmax.value is not None: marker_args["cmax"] = map_vmax.value
            
            fig.add_trace(go.Scatter3d(
                x=px, y=py, z=-dc3d[:, 4],
                mode="markers",
                marker=marker_args,
                name=plot_var.value,
            ))
        else:
            marker_args = dict(size=6, color=vals, colorscale=map_cmap.value,
                               showscale=True, colorbar=dict(title=plot_var.value.upper()))
            if map_vmin.value is not None: marker_args["cmin"] = map_vmin.value
            if map_vmax.value is not None: marker_args["cmax"] = map_vmax.value
            
            fig.add_trace(go.Scatter(
                x=px, y=py,
                mode="markers",
                marker=marker_args,
                name=plot_var.value,
            ))

    # ---- layout ----
    unit_str = "°" if is_latlon else "km"
    xlabel = "Lon (°)" if is_latlon else "X (km)"
    ylabel = "Lat (°)" if is_latlon else "Y (km)"

    if is3d:
        fig.update_layout(scene=dict(
            xaxis_title=xlabel, yaxis_title=ylabel, zaxis_title="Depth (km)",
            zaxis=dict(autorange="reversed"),
        ))
    else:
        fig.update_layout(
            xaxis_title=xlabel, yaxis_title=ylabel,
            xaxis=dict(autorange=True, constrain="domain"),
            yaxis=dict(autorange=True, constrain="domain"),
            clickmode="event+select"
        )

    # ---- invisible click-catcher so clicks work anywhere on map ----
    has_grid = (dc3d is not None
                and STATE.get("nx", 0) > 1
                and STATE.get("ny", 0) > 1
                and not is3d)
    if not is3d and not has_grid:
        xmin = grid_xmin.value or -50
        xmax = grid_xmax.value or 50
        ymin = grid_ymin.value or -50
        ymax = grid_ymax.value or 50
        nclick = 51

        cx = np.linspace(xmin, xmax, nclick)
        cy = np.linspace(ymin, ymax, nclick)
        gx, gy = [], []
        for xi in cx:
            for yi in cy:
                gx.append(xi)
                gy.append(yi)
        fig.add_trace(go.Scatter(
            x=gx, y=gy,
            mode="markers",
            marker=dict(size=1, opacity=0),
            hoverinfo="x+y",
            showlegend=False,
            name="_click_catcher",
        ))

    # ---- X-section line ----
    if not is3d and xsec_ax.value is not None:
        fig.add_trace(go.Scatter(
            x=[xsec_ax.value, xsec_bx.value], y=[xsec_ay.value, xsec_by.value],
            mode="lines+markers+text",
            line=dict(color="lime", width=3, dash="dash"),
            marker=dict(size=10, color="lime"),
            text=["A", "B"], textposition="top center",
            textfont=dict(color="lime", size=14),
            name="X-Section line",
            hoverinfo="x+y+text"
        ))

    fig.update_layout(
        margin=dict(l=0, r=0, t=30, b=0),
        template="plotly_dark",
        height=650,
    )
    # FIX 2: replace the entire Plotly pane object to avoid dirty 3D scene state
    map_pane.object = fig

plot_var.param.watch(_refresh_map, "value")
map_cmap.param.watch(_refresh_map, "value")
map_vmin.param.watch(_refresh_map, "value")
map_vmax.param.watch(_refresh_map, "value")
toggle_3d.param.watch(_refresh_map, "value")
refresh_btn.on_click(_refresh_map)

# --- Interactive Map Clicking ---
_click_lock = {"active": False}

def _on_map_click(event):
    if _click_lock["active"]:
        return
    if event.new is None or not isinstance(event.new, dict):
        return
    points = event.new.get("points", [])
    if not points:
        return
    
    # Only allow 2D map clicks for cross section
    if toggle_3d.value:
        return
    
    _click_lock["active"] = True
    try:
        pt = points[0]
        cx = float(pt.get("x", 0))
        cy = float(pt.get("y", 0))
        if STATE["click_state"] == "A":
            xsec_ax.value = round(cx, 2)
            xsec_ay.value = round(cy, 2)
            STATE["click_state"] = "B"
            _set_status(f"Point A set to ({cx:.2f}, {cy:.2f}). Click map for Point B.")
        else:
            xsec_bx.value = round(cx, 2)
            xsec_by.value = round(cy, 2)
            STATE["click_state"] = "A"
            _set_status(f"Point B set to ({cx:.2f}, {cy:.2f}). Ready to compute.")
        # Single refresh after both coords updated
        _refresh_map()
    finally:
        _click_lock["active"] = False

map_pane.param.watch(_on_map_click, "click_data")

# =====================================================================
# CROSS-SECTION  (depth-vs-distance with recalculation)

# =====================================================================
def _on_xsec(event):
    """
    1. Sample `npts` points along the line A→B.
    2. For each depth in [zmin, zmax, step], run okada + coulomb.
    3. Plot heatmap: X = distance along profile, Y = depth.
    """
    if STATE["el"] is None:
        xsec_status.object = "**Upload source file first.**"
        return

    ax, ay = xsec_ax.value, xsec_ay.value
    bx, by = xsec_bx.value, xsec_by.value
    zmin   = xsec_zmin.value
    zmax   = xsec_zmax.value
    zinc   = xsec_zinc.value
    npts   = xsec_npts.value
    var    = xsec_var.value

    el    = STATE["el"]
    kode  = STATE["kode"]
    is_latlon = (coord_sys.value == "Lat/Lon")
    map_info = STATE.get("map_info") or {}
    lon0 = map_info.get("zero_lon", 0.0) if map_info else 0.0
    lat0 = map_info.get("zero_lat", 0.0) if map_info else 0.0

    ax, ay = xsec_ax.value, xsec_ay.value
    bx, by = xsec_bx.value, xsec_by.value
    
    if is_latlon and (lon0 != 0.0 or lat0 != 0.0):
        ax, ay = deg_to_km(ax, ay, lon0, lat0)
        bx, by = deg_to_km(bx, by, lon0, lat0)

    t = np.linspace(0, 1, npts)
    px = ax + (bx - ax) * t
    py = ay + (by - ay) * t
    pois  = STATE["pois"]
    young = STATE["young"]
    fric  = STATE["fric"]

    # Profile points
    dist = np.sqrt((px - ax)**2 + (py - ay)**2)  # distance along profile

    depths = np.arange(zmin, zmax + zinc * 0.5, zinc)
    ndepth = len(depths)

    xsec_status.object = f"Computing {npts} × {ndepth} = **{npts * ndepth}** points …"

    try:
        grid_vals = np.zeros((ndepth, npts))

        for iz, zval in enumerate(depths):
            cdepth_arr = np.full(npts, zval)
            dc3d = okada_elastic_halfspace(px, py, el, young, pois, cdepth_arr, kode)
            dc_arr = np.array(dc3d)

            if var in ("shear", "normal", "coulomb"):
                ss = dc_arr[:, 8:14].T
                s, nt, c = calc_coulomb(
                    rec_strike.value * np.ones(npts),
                    rec_dip.value    * np.ones(npts),
                    rec_rake.value   * np.ones(npts),
                    fric * np.ones(npts), ss)
                if var == "shear":
                    grid_vals[iz, :] = s
                elif var == "normal":
                    grid_vals[iz, :] = nt
                else:
                    grid_vals[iz, :] = c
            else:
                grid_vals[iz, :] = _get_vals(var, dc_arr)

        kwargs = {}
        if xsec_vmin.value is not None: kwargs["zmin"] = xsec_vmin.value
        if xsec_vmax.value is not None: kwargs["zmax"] = xsec_vmax.value

        fig = go.Figure(go.Heatmap(
            x=dist,
            y=depths,
            z=grid_vals,
            colorscale=xsec_cmap.value,
            colorbar=dict(title=var.upper()),
            **kwargs
        ))
        fig.update_layout(
            title=f"Cross-Section  A({ax},{ay}) → B({bx},{by})",
            xaxis_title="Distance along profile (km)",
            yaxis_title="Depth (km)",
            yaxis=dict(autorange="reversed"),
            template="plotly_dark",
            height=500,
            margin=dict(l=50, r=20, t=50, b=50),
            clickmode="none"
        )

        xsec_pane.object = fig
        xsec_status.object = f"✅ Done – {npts * ndepth} points"
        
        # Save X-sec dataframe for download
        rows = []
        
        # We also want to compute exact spatial coordinates for export
        # If the map is using Lat/Lon we might already have the zero reference converted
        map_info = STATE.get("map_info") or {}
        lon0 = map_info.get("zero_lon", 0.0) if map_info else 0.0
        lat0 = map_info.get("zero_lat", 0.0) if map_info else 0.0
        
        has_deg_ref = (lon0 != 0.0 or lat0 != 0.0)
        
        if has_deg_ref:
            lon_arr, lat_arr = km_to_deg(px, py, lon0, lat0)
            
        # For uniform format, we calculate shear/normal/coulomb for EVERY cross-section point 
        # instead of just the plotted `var`.
        for iz, zval in enumerate(depths):
            # Recalculate dc3d to grab raw tensors directly for CSV export
            cdepth_arr = np.full(npts, zval)
            dc_arr = np.array(okada_elastic_halfspace(px, py, el, young, pois, cdepth_arr, kode))
            ss = dc_arr[:, 8:14].T
            s, nt, c = calc_coulomb(
                rec_strike.value * np.ones(npts),
                rec_dip.value    * np.ones(npts),
                rec_rake.value   * np.ones(npts),
                fric * np.ones(npts), ss)
                
            for ip in range(npts):
                r = {
                    "X_km": px[ip],
                    "Y_km": py[ip],
                    "Z_km": dc_arr[ip, 4],
                }
                
                if has_deg_ref:
                    r["Lon"] = lon_arr[ip]
                    r["Lat"] = lat_arr[ip]
                    
                r.update({
                    "ux_m": dc_arr[ip, 5], 
                    "uy_m": dc_arr[ip, 6], 
                    "uz_m": dc_arr[ip, 7],
                    "sxx_bar": dc_arr[ip, 8], 
                    "syy_bar": dc_arr[ip, 9], 
                    "szz_bar": dc_arr[ip, 10],
                    "syz_bar": dc_arr[ip, 11], 
                    "sxz_bar": dc_arr[ip, 12], 
                    "sxy_bar": dc_arr[ip, 13],
                    "Shear_bar": s[ip],
                    "Normal_bar": nt[ip],
                    "Coulomb_bar": c[ip],
                })
                rows.append(r)
                
        STATE["xsec_data"] = pd.DataFrame(rows)
        _update_xsec_download()

    except Exception as exc:
        import traceback; traceback.print_exc()
        xsec_status.object = f"**Error:** {exc}"

xsec_btn.on_click(_on_xsec)

# =====================================================================
# TABLE
# =====================================================================
def _refresh_table(*_):
    dc3d = STATE["dc3d"]
    if dc3d is None:
        return
    
    dc_arr = np.array(dc3d)
    d = {
        "X_km": dc_arr[:, 0], "Y_km": dc_arr[:, 1], "Z_km": dc_arr[:, 4],
    }
    
    map_info = STATE.get("map_info") or {}
    lon0 = map_info.get("zero_lon", 0.0) if map_info else 0.0
    lat0 = map_info.get("zero_lat", 0.0) if map_info else 0.0
    
    if lon0 != 0.0 or lat0 != 0.0:
        lon, lat = km_to_deg(dc_arr[:, 0], dc_arr[:, 1], lon0, lat0)
        d["Lon"] = lon
        d["Lat"] = lat

    d.update({
        "ux_m": dc_arr[:, 5], "uy_m": dc_arr[:, 6], "uz_m": dc_arr[:, 7],
        "sxx_bar": dc_arr[:, 8], "syy_bar": dc_arr[:, 9], "szz_bar": dc_arr[:, 10],
        "syz_bar": dc_arr[:, 11], "sxz_bar": dc_arr[:, 12], "sxy_bar": dc_arr[:, 13],
    })
    
    if STATE.get("shear") is not None:
        d["Shear_bar"]   = STATE["shear"]
        d["Normal_bar"]  = STATE["normal_stress"]
        d["Coulomb_bar"] = STATE["coulomb_stress"]
        
    table_pane.object = pd.DataFrame(d)

# =====================================================================
# SAVE FILE → FILE DOWNLOAD
# =====================================================================
def _update_map_download(*_):
    df = table_pane.object
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        map_download.file = None
        return

    mode = calc_mode.value
    fmt = save_format.value
    save_in_latlon = (save_crs.value == "Lat/Lon")
    
    nx, ny = STATE.get("nx", 0), STATE.get("ny", 0)
    
    # Common variables
    base_name = "coulomb_out" if mode in ("coulomb", "batch", "single") else "halfspace_def_out"
    ext = fmt.lower()
    fname = f"{base_name}.{ext}"
    map_download.filename = fname

    # --- EXPORT LOGIC ---
    if fmt == "CSV":
        # Save CSV to memory
        buf = io.StringIO()
        df.to_csv(buf, index=False)
        buf.seek(0)
        map_download.file = buf
        return

    # Use a temporary file for rasterio and geopandas since they need actual paths or complex file-like objects
    tmp_path = os.path.join("cache", fname)
    
    if fmt == "SHP":
        # Save Shapefile
        if save_in_latlon and "Lon" in df.columns:
            gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.Lon, df.Lat), crs="EPSG:4326")
        else:
            gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.X_km, df.Y_km)) # Local CRS
        
        # Shapefile involves multiple files (.shp, .shx, .dbf, etc).
        # We will create a zip file for the shapefile.
        import zipfile
        zip_fname = f"{base_name}.zip"
        zip_path = os.path.join("cache", zip_fname)
        
        # Save shapefile parts to cache dir
        shp_path = os.path.join("cache", fname)
        gdf.to_file(shp_path)
        
        # Zip them up
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for ext_name in ['.shp', '.shx', '.dbf', '.prj', '.cpg']:
                p = os.path.join("cache", f"{base_name}{ext_name}")
                if os.path.exists(p):
                    zipf.write(p, arcname=f"{base_name}{ext_name}")
                    
        # Serve the zip
        map_download.filename = zip_fname
        map_download.file = os.path.abspath(zip_path)

    elif fmt == "TIF":
        nx, ny = STATE.get("nx", 0), STATE.get("ny", 0)
        if nx <= 1 or ny <= 1:
            _set_status("TIF export only supports Grid calculations.", error=True)
            map_download.file = None
            return
            
        # Get target variable
        vals = _get_vals(plot_var.value, STATE.get("dc3d"), STATE.get("shear"), STATE.get("normal_stress"), STATE.get("coulomb_stress"))
        if vals is None:
            return
            
        grid_data = np.array(vals).reshape(nx, ny).T.astype(np.float32) # Reshape to (nx, ny) then Transpose to (ny, nx) for image coordinates
        
        if save_in_latlon and "Lon" in df.columns:
            xmin = df["Lon"].min()
            xmax = df["Lon"].max()
            ymin = df["Lat"].min()
            ymax = df["Lat"].max()
            crs = "EPSG:4326"
        else:
            xmin = df["X_km"].min()
            xmax = df["X_km"].max()
            ymin = df["Y_km"].min()
            ymax = df["Y_km"].max()
            crs = None

        # When we write to a Raster using `nx, ny`, the raster takes the absolute bounding box.
        # Since df["Lon"] max/min are point centers, adding half-pixel allows the edge to align.
        # However, due to QGIS coordinate logic on degrees, we must be precise.
        # Actually, let's just use from_bounds without manual half-pixel pad. Rasterio handles it.
        # Wait, from_bounds(west, south, east, north)
        
        # In QGIS, if we use from_bounds(xmin, ymin, xmax, ymax) it considers the corners as the centers.
        # In QGIS, if we use from_bounds(xmin, ymin, xmax, ymax) it considers the corners as the centers.
        transform = from_bounds(xmin, ymin, xmax, ymax, nx, ny)
        
        with rasterio.open(
            tmp_path, 'w', driver='GTiff',
            height=grid_data.shape[0], width=grid_data.shape[1],
            count=1, dtype=str(grid_data.dtype),
            crs=crs, transform=transform,
        ) as dst:
            dst.write(np.flipud(grid_data), 1)

        map_download.file = os.path.abspath(tmp_path)
        
save_format.param.watch(_update_map_download, 'value')
save_crs.param.watch(_update_map_download, 'value')

def _update_xsec_download():
    df = STATE.get("xsec_data", None)
    if df is None or df.empty:
        xsec_download.file = None
        return
    
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    xsec_download.file = buf

# =====================================================================
# LAYOUT

# =====================================================================
grid_box = pn.Column(
    "### Grid Limits",
    pn.Row(grid_xmin, grid_xmax),
    pn.Row(grid_ymin, grid_ymax),
    pn.Row(grid_inc, grid_depth),
)
receiver_box = pn.Column(
    "### Receiver Angles",
    pn.Row(rec_strike, rec_dip, rec_rake),
)
batch_box = pn.Column(
    "### Batch Target File",
    batch_input,
)
single_box = pn.Column(
    "### Target Coordinates",
    pn.Row(sp_x, sp_y, sp_z),
    "### Target Fault Angles",
    pn.Row(sp_strike, sp_dip, sp_rake),
)

@pn.depends(calc_mode.param.value)
def _mode_panel(mode):
    if mode in ("coulomb", "deformation"):
        return pn.Column(grid_box, receiver_box)
    elif mode == "batch":
        return pn.Column(batch_box, pn.pane.Markdown("*Receiver angles read from file.*"))
    elif mode == "single":
        return single_box
    return pn.Column()

sidebar = pn.Column(
    "# ⚡ Coulomb Stress",
    pn.layout.Divider(),
    file_input,
    calc_mode,
    coord_sys,
    _mode_panel,
    pn.layout.Divider(),
    run_btn,
    status_md,
    width=360,
    sizing_mode="stretch_height",
)

# Move cross-section to map tab
map_view_tools = pn.Column(
    pn.Row(plot_var, map_cmap, map_vmin, map_vmax),
    pn.Row(toggle_3d, refresh_btn, save_format, save_crs, map_download),
    pn.layout.Divider(),
    "**Define Profile Line A → B**",
    pn.Row(xsec_ax, xsec_ay, pn.pane.Markdown("**→**", margin=(10, 10)), xsec_bx, xsec_by),
)

# Cross-section tab contents (only keep depth, points, computation)
xsec_tab = pn.Column(
    "### Profile configurations",
    pn.Row(xsec_zmin, xsec_zmax, xsec_zinc),
    pn.Row(xsec_npts, xsec_var),
    pn.Row(xsec_cmap, xsec_vmin, xsec_vmax),
    xsec_btn,
    xsec_status,
    pn.Row(xsec_download),
    xsec_pane,
)

main_tabs = pn.Tabs(
    ("2D / 3D Map", pn.Column(map_view_tools, map_pane)),
    ("Cross Section View", xsec_tab),
    ("Table Preview", pn.Column(table_pane)),
    dynamic=True,
)

template = pn.template.FastListTemplate(
    title="Coulomb Stress Change Dashboard",
    sidebar=[sidebar],
    main=[main_tabs],
    accent_base_color="#4fc3f7",
    header_background="#1e1e2e",
    theme="dark",
)

template.servable()
