# PyCFS Dashboard

An interactive dashboard for visualizing and computing Coulomb Stress Changes.
Powered by Python (`numpy`), `Panel`, and `Plotly`.

## Features
- Interactive 2D and 3D map views of fault sources and computed stress variables.
- Dynamically extract Cross-Sectional geometries over user-defined paths.
- Support for Single Point (Lat/Lon or Km), Grid Box mapping, and Custom Receivers matching algorithms.
- Custom Scientific Colormaps configurations (`Viridis`, `Jet`, `balance`, etc.) with manual boundary values (`vmin`/`vmax`).
- High-fidelity exporting: Results available in `.csv` (coordinates included), Georeferenced TIF, and Esri `.shp`.

## Interface Snapshot
This toolkit renders directly in the browser via native WebSockets using the pure Python `Panel` framework.

## Usage
Simply start the dashboard interface locally with:
```bash
panel serve app_panel.py --show
```
