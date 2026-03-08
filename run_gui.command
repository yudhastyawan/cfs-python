#!/bin/bash
cd "$(dirname "$0")"
echo "Launching Coulomb Stress Dashboard..."
source venv/bin/activate
panel serve app_panel.py --show
