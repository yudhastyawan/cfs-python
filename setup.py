from setuptools import setup, find_packages
import os

this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="pycfs-dashboard",
    version="0.1.0",
    description="Python-based Coulomb Stress Change UI Dashboard and API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Yudha Styawan",
    author_email="yudhastyawan97@gmail.com",
    url="https://github.com/yudhastyawan/pycfs-dashboard",
    packages=find_packages(include=["cfs_lib", "cfs_lib.*"]),
    py_modules=["app_panel"],
    install_requires=[
        "numpy",
        "pandas",
        "panel",
        "plotly",
        "param",
        "geopandas",
        "rasterio",
        "shapely"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Physics",
    ],
    python_requires=">=3.8",
)
