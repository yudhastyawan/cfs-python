#!/bin/bash
echo "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
echo "Installing dependencies..."
pip install -r requirements.txt
echo "Environment setup complete. To run the app:"
echo "source venv/bin/activate"
echo "panel serve app_panel.py --show"
