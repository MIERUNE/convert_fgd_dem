# convert_fgd_dem

## Overview

You can get the DEM data in xml format for any location from the following site.
[https://fgd.gsi.go.jp/download](https://fgd.gsi.go.jp/download)

Run the tool with downloaded "xml" or "directory containing .xml" or ".zip containing .xml" to generate GeoTiff and Terrain RGB (Tiff).

## Installation

- Install using pip.

```shell
% pip install git+https://github.com/MIERUNE/convert_fgd_dem#egg=convert_fgd_dem
```

- using pipenv

```shell
% pipenv install git+https://github.com/MIERUNE/convert_fgd_dem#egg=convert_fgd_dem
```

## usage

### download DEM

- Download from following link.
  - https://fgd.gsi.go.jp/download/

### write python script

```python
from pathlib import Path

from src.convert_fgd_dem import Dem


def main():
    dem_path = Path("./data/FG-GML-6441-31-DEM5A.zip")
    dem = Dem(dem_path)
    print(dem.bounds_latlng)


if __name__ == '__main__':
    main()
```

### run script

```bash
% pipenv run python main.py
{'lower_left': {'lat': 42.916666667, 'lon': 141.125}, 'upper_right': {'lat': 43.0, 'lon': 141.25}}
```
