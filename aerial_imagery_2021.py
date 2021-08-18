import argparse
import glob
import os
from pathlib import Path

from tqdm import tqdm

from PansharpRaster import rasterio_merge_tiles
from osgeo import gdal

from utils import read_parameters


def main(overwrite: bool = False,
         glob_params: dict = None,
         dry_run: bool = False):
    """
    Preprocess rasters according to chosen parameters. This includes merging tiles and translate to COG.
    :param overwrite: bool
        If True, all existing files are overwritten. Careful!
    :param glob_params: dict (or equivalent returned from yaml file)
        Parameters sent to preprocess_glob.pansharp_glob() function. See function for more details.
    :param dry_run: bool
        If True, script runs normally, except all time-consuming processes are skipped (i.e. no pansharp, no cogging)
    :return:
        Preprocessed rasters (pansharped/cogged), depending on inputted parameters and
        availability of modules (eg. otbApplication and rio_cogeo)
    """

    base_dir = Path(glob_params['base_dir'])
    out_path = Path(glob_params['out_path'])
    out_tif_name = glob_params['out_tif_name']
    os.chdir(base_dir)

    import logging.config  # based on: https://stackoverflow.com/questions/15727420/using-logging-in-multiple-modules
    out_log_path = Path("./logs")
    out_log_path.mkdir(exist_ok=True)
    logging.config.fileConfig(log_config_path)  # See: https://docs.python.org/2.4/lib/logging-config-fileformat.html
    logging.info("Started")

    if dry_run:
        logging.warning("DRY-RUN")

    # 1. BUILD list of images to merge.
    lst_img = [Path(name) for name in glob.glob(str(base_dir) + "/*.tif")]

    logging.info(msg=f"Processing folder {base_dir.parent}")
    os.chdir(base_dir)
    t = tqdm(total=2)

    print("Merge")
    out_merge_name = out_tif_name + "_merge.tif"
    out_merge = out_path / Path(out_merge_name)

    # 2. Merge the list of images.
    _, err = rasterio_merge_tiles(tile_list=lst_img, outfile=out_merge, overwrite=overwrite)

    t.update()

    # 3. COG
    # + de 5 overview, compression lzw.
    options_list = ['-ot Byte', '-of COG', '-co COMPRESS=LZW', '-co BIGTIFF=YES']
    options_string = " ".join(options_list)
    out_cog = Path(out_tif_name + "_COG.tif")
    print("COG")
    gdal.Translate(str(out_path / out_cog), str(out_merge), options=options_string)
    t.update()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Merge and cogify images')
    parser.add_argument('param_file', metavar='DIR', help='Path to preprocessing parameters stored in yaml', default='./config_aerial_imagery.yaml')
    args = parser.parse_args()
    config_path = Path(args.param_file)
    params = read_parameters(args.param_file)

    log_config_path = Path('logging.conf').absolute()

    main(glob_params=params['glob'])