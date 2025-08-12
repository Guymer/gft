# Global Flying Times (GFT)

!["mypy" GitHub Action Status](https://github.com/Guymer/gft/actions/workflows/mypy.yaml/badge.svg) !["pylint" GitHub Action Status](https://github.com/Guymer/gft/actions/workflows/pylint.yaml/badge.svg)

This project aims to show how a plane flies around the globe - building heavily upon [GST](https://github.com/Guymer/gst).

## Running `complexity.py`

To generate the data needed, [complexity.py](complexity.py) will run commands like:

```sh
python3.12 -m gft 0.0 0.0 500.0 --duration 0.01 --freqLand 64 --freqPlot 8 --freqSimp 8 --GSHHG-resolution c --nAng 9 --NE-resolution 110m --precision 116000.0
python3.12 -m gft 0.0 0.0 500.0 --duration 0.01 --freqLand 128 --freqPlot 16 --freqSimp 16 --GSHHG-resolution c --nAng 17 --NE-resolution 50m --precision 58000.0
python3.12 -m gft 0.0 0.0 500.0 --duration 0.01 --freqLand 256 --freqPlot 32 --freqSimp 32 --GSHHG-resolution c --nAng 33 --NE-resolution 10m --precision 29000.0
```

## Dependencies

GFT requires the following Python modules to be installed and available in your `PYTHONPATH`.

* [cartopy](https://pypi.org/project/Cartopy/)
* [geojson](https://pypi.org/project/geojson/)
* [GST](https://github.com/Guymer/gst)
* [matplotlib](https://pypi.org/project/matplotlib/)
* [numpy](https://pypi.org/project/numpy/)
* [PIL](https://pypi.org/project/Pillow/)
* [pyguymer3](https://github.com/Guymer/PyGuymer3)
* [shapely](https://pypi.org/project/Shapely/)

GFT uses some [Global Self-Consistent Hierarchical High-Resolution Geography](https://www.ngdc.noaa.gov/mgg/shorelines/) resources and some [Natural Earth](https://www.naturalearthdata.com/) resources via the [cartopy](https://pypi.org/project/Cartopy/) module. If they do not exist on your system then [cartopy](https://pypi.org/project/Cartopy/) will download them for you in the background. Consequently, a working internet connection may be required the first time you run GFT.
