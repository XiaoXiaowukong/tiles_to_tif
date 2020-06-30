# -*- coding:UTF-8 -*-
import os

import gdal
import numpy as np
import osr

import color_config
import util
import sys


def georeference_raster_tile(root, name, o_path):
    x = int(os.path.splitext(name)[0].split("-")[1])
    y = int(os.path.splitext(name)[0].split("-")[2])
    z = int(os.path.splitext(name)[0].split("-")[0])
    bounds = util.get_tile_bbox(z, x, y)
    gdal.Translate(os.path.join(o_path, name).replace(".png", ".tif"),
                   os.path.join(root, name),
                   outputSRS='EPSG:4326',
                   outputBounds=bounds)


def create_singleband_tif(root, name, o_path, all):
    #########
    x = int(os.path.splitext(name)[0].split("-")[1])
    y = int(os.path.splitext(name)[0].split("-")[2])
    z = int(os.path.splitext(name)[0].split("-")[0])
    bounds = util.get_tile_bbox(z, x, y)
    #########
    if not os.path.exists(os.path.join(root, name)):
        print ("file is not exist")
    driver = gdal.GetDriverByName('PNG')
    driver.Register()
    data_set = gdal.Open(os.path.join(root, name), gdal.GA_ReadOnly)
    x_size = data_set.RasterXSize
    y_size = data_set.RasterYSize
    bands = data_set.RasterCount
    if bands == 4:
        r = data_set.GetRasterBand(1).ReadAsArray(0, 0, x_size, y_size)
        g = data_set.GetRasterBand(2).ReadAsArray(0, 0, x_size, y_size)
        b = data_set.GetRasterBand(3).ReadAsArray(0, 0, x_size, y_size)
        all_data = []
        for r_item, g_item, b_item in zip(r, g, b):
            item_data = []
            for r_item_item, g_item_item, b_item_item in zip(r_item, g_item, b_item):
                key = "{}{}{}".format(r_item_item, g_item_item, b_item_item)
                all[key] = 0
                item_data.append(color_config.color_level[key])
            all_data.append(item_data)
        all_data = np.asarray(all_data, dtype=np.uint8)
        wirte_geotiff(all_data, os.path.join(o_path, name).replace(".png", "_test.tif"), bounds)
    elif bands == 1:
        all_data = data_set.GetRasterBand(1).ReadAsArray(0, 0, x_size, y_size)
        wirte_geotiff(all_data, os.path.join(o_path, name).replace(".png", "_test.tif"), bounds)
    del data_set


# 写入tif
def wirte_geotiff(data, export_tif, bounds):
    gtif_driver = gdal.GetDriverByName("GTiff")
    # 写入目标文件
    x, y = data.shape
    out_ds = gtif_driver.Create(export_tif, y, x, 1, gdal.GDT_Float32)
    # 设置裁剪出来图的原点坐标

    dst_transform = (bounds[0], (bounds[2] - bounds[0]) / x, 0.0, bounds[3], 0.0, (bounds[1] - bounds[3]) / y)
    out_ds.SetGeoTransform(dst_transform)
    srs = createSrs("4326")
    if (srs != None):
        # 设置SRS属性（投影信息）
        out_ds.SetProjection(srs)
    out_ds.GetRasterBand(1).WriteArray(data[::-1])
    out_ds.GetRasterBand(1).SetNoDataValue(0)
    # 将缓存写入磁盘
    out_ds.FlushCache()
    print("FlushCache succeed")
    del out_ds


def createSrs(projstr):
    if (projstr == "4326"):
        srs4326 = osr.SpatialReference()
        srs4326.ImportFromEPSG(4326)
    proj = str(srs4326)
    return proj


if __name__ == '__main__':
    args = sys.argv[1:]
    png_root = args[0]
    o_path = args[1]
    type = args[2]

    if not os.path.exists(png_root):
        print("input file dir is not exist")
        exit(1)
    if not os.path.exists(o_path):
        print("output  dir: {} is not exist".format(o_path))
        exit(1)
    all = {}
    for root, dirs, files in os.walk(png_root):
        for name in files:
            if os.path.splitext(name)[-1] != ".png":
                continue
            if type == "old":
                georeference_raster_tile(root, name, o_path)
            elif type == "new":
                create_singleband_tif(root, name, o_path, all)
            else:
                print("type must [ old or snew ]")
                exit(1)
    print(all)
