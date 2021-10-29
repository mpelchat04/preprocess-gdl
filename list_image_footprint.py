import rasterio
import rasterio.features
import rasterio.warp
import argparse
from pathlib import Path
import glob
import fiona
from collections import OrderedDict
import json


def get_footprint(tif_path):
    with rasterio.open(tif_path) as dataset:

        # Read the dataset's valid data mask as a ndarray.
        mask = dataset.dataset_mask()

        # Extract feature shapes and values from the array.
        for geom, val in rasterio.features.shapes(
                mask, transform=dataset.transform):

            # Transform shapes from the dataset's own coordinate
            # reference system to CRS84 (EPSG:4326).
            geom = rasterio.warp.transform_geom(
                dataset.crs, 'EPSG:4326', geom, precision=6)
    return geom


def main(root_folder):
    lst_img = [Path(name) for name in glob.glob(str(root_folder) + "/*.tif")]
    lst_info = []
    print("listing geometries...", end="")
    for tif_path in lst_img:
        geom = get_footprint(tif_path=tif_path)
        tuile = str(Path(tif_path).stem)
        lst_info.append({'geom': geom, 'tuile': tuile})

    print("done")
    data_schema = {
        'geometry': 'Polygon',
        'properties': OrderedDict([
            ('tuile', 'str')
        ])
    }

    print(f"writing list to gpkg {str(root_folder.parent)}_list_tile.gpkg", end="")
    gpkg_path = root_folder / Path(str(root_folder.parent) + "_list_tile.gpkg")
    with fiona.open(gpkg_path, 'w', layer="table1", driver='GPKG', schema=data_schema) as c:
        for elem in lst_info:
            pol_to_write = {
                'geometry': elem['geom'],
                'properties': OrderedDict([
                    ('tuile', elem['tuile'])
                ])

            }
            c.write(pol_to_write)
    print("done")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Merge and cogify images')
    parser.add_argument('root_folder', metavar='DIR', help='Path to folder to process')
    args = parser.parse_args()
    root_folder = Path(args.root_folder)

    main(root_folder=root_folder)
